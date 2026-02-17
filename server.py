#!/usr/bin/env python3
"""
Discord Bot - Long-running Server for Render Web Service
"""
import os
import sys
import json
import time
import sqlite3
import asyncio
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Setup file logging immediately
log_file = open("/tmp/bot.log", "a")
sys.stdout = log_file

def log(msg):
    """Write to both stdout and file"""
    print(msg)
    log_file.flush()  # Force write to disk immediately

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not DISCORD_TOKEN or not OPENROUTER_API_KEY:
    log("[ERROR] Missing environment variables")
    sys.exit(1)

# Discord API configuration
DISCORD_API = "https://discord.com/api/v10"
TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL", "1470478653606461532"))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# OpenRouter client
ai_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Memory database
DB_PATH = "/tmp/discord_memory.db"

def init_db():
    """Initialize SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER,
                user_id INTEGER,
                username TEXT,
                content TEXT,
                timestamp REAL,
                is_bot INTEGER
            )
        """)
        c.execute("CREATE INDEX IF NOT EXISTS idx_channel ON messages(channel_id, timestamp)")
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"[ERROR] DB init failed: {e}")

def store_message(channel_id, user_id, username, content, is_bot=False):
    """Store a message"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO messages (channel_id, user_id, username, content, timestamp, is_bot)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (channel_id, user_id, username, content, time.time(), is_bot))
        c.execute("DELETE FROM messages WHERE id IN (SELECT id FROM messages ORDER BY timestamp DESC LIMIT -1 OFFSET 100)")
        conn.commit()
        conn.close()
    except Exception as e:
        log(f"[ERROR] Store failed: {e}")

def get_recent_messages(channel_id, limit=10):
    """Get recent messages"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            SELECT user_id, username, content, is_bot
            FROM messages
            WHERE channel_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (channel_id, limit))
        messages = c.fetchall()
        conn.close()
        messages.reverse()
        return messages
    except Exception as e:
        log(f"[ERROR] Get messages failed: {e}")
        return []

def discord_get(url):
    """Discord API GET"""
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    response = requests.get(f"{DISCORD_API}{url}", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def discord_post(url, data):
    """Discord API POST"""
    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    response = requests.post(f"{DISCORD_API}{url}", headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    return None

def generate_response(content, context):
    """Generate AI response"""
    try:
        prompt = f"""You are a helpful Discord bot.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE: {content}

Respond naturally. Keep it short (1-2 sentences, under 30 words)."""

        response = ai_client.chat.completions.create(
            model="google/gemini-2.5-flash-lite",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"[ERROR] AI failed: {e}")
        return None

def process_messages():
    """Process Discord messages and send replies"""
    try:
        # Get bot user info
        user = discord_get("/users/@me")
        if not user:
            log("[ERROR] Failed to authenticate")
            return

        user_id = user.get("id")
        log(f"[INFO] Bot: {user.get('username')} ({user_id})")

        # Fetch messages
        messages = discord_get(f"/channels/{TARGET_CHANNEL}/messages?limit=20")
        if not messages:
            log("[INFO] No messages")
            return

        log(f"[INFO] Fetched {len(messages)} messages")

        # Get recent context
        recent = get_recent_messages(TARGET_CHANNEL, 10)
        context_lines = ["Recent conversation:"]
        for msg in recent:
            prefix = "Bot" if msg[3] else msg[1]
            context_lines.append(f"[{prefix}]: {msg[2]}")
        context = "\n".join(context_lines)

        # Process last message (skip bot's own)
        for msg in messages:
            if msg.get("author", {}).get("id") == user_id:
                continue

            content = msg.get("content", "").strip()
            if len(content) < 3:
                continue

            log(f"[MSG] {msg.get('author', {}).get('username')}: {content[:50]}")

            # Store message
            msg_author_id = msg.get("author", {}).get("id")
            store_message(TARGET_CHANNEL, msg_author_id, msg.get("author", {}).get('username'), content)

            # Generate response
            response = generate_response(content, context)
            if not response or len(response.strip()) < 2:
                log("[SKIP] No valid response")
                return

            # Limit response
            sentences = response.split('.')
            response = ' '.join([s.strip() for s in sentences[:2] if s.strip()])

            words = response.split()
            if len(words) > 30:
                response = ' '.join(words[:30])

            log(f"[REPLY] {response[:50]}")

            # Send reply
            discord_post(f"/channels/{TARGET_CHANNEL}/messages", {
                "content": response,
                "message_reference": {"message_id": msg.get("id"), "guild_id": False}
            })

            # Store bot response
            store_message(TARGET_CHANNEL, user_id, user.get("username"), response, is_bot=True)

            log("[DONE] Response sent")
            return

        log("[INFO] No new messages to respond to")

    except Exception as e:
        log(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

class HealthHandler(BaseHTTPRequestHandler):
    """Health check endpoint for Render"""
    def do_GET(self):
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "bot": "alive"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_HEAD(self):
        # Handle HEAD requests from Render health checks
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def run_http_server():
    """Run HTTP server for health checks"""
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    log(f"[INFO] Health server running on port {port}")
    return server

def main():
    """Main loop"""
    log("[STARTUP] Bot starting, PID: " + str(os.getpid()))
    log("[STARTUP] TARGET_CHANNEL: " + str(TARGET_CHANNEL))
    log("[STARTUP] CHECK_INTERVAL: " + str(CHECK_INTERVAL))
    
    try:
        log("[DEBUG] Initializing database...")
        init_db()
        log("[DEBUG] Database initialized")
    except Exception as e:
        log(f"[ERROR] DB init failed: {e}")
        return

    log(f"[{datetime.now().isoformat()}] Bot starting")

    # Check env vars
    log(f"[DEBUG] DISCORD_TOKEN set: {bool(os.getenv('DISCORD_TOKEN'))}")
    log(f"[DEBUG] OPENROUTER_API_KEY set: {bool(os.getenv('OPENROUTER_API_KEY'))}")
    log(f"[DEBUG] TARGET_CHANNEL: {os.getenv('TARGET_CHANNEL')}")
    log(f"[DEBUG] CHECK_INTERVAL: {os.getenv('CHECK_INTERVAL')}")

    # Start HTTP server in background thread
    import threading
    log("[DEBUG] Starting HTTP server...")
    http_server = run_http_server()
    http_thread = threading.Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    log("[DEBUG] HTTP server thread started")

    # Main bot loop
    log("[DEBUG] Starting main loop...")
    loop_count = 0
    while True:
        try:
            loop_count += 1
            log(f"[DEBUG] Loop iteration {loop_count}")
            process_messages()
            log(f"[DEBUG] Sleeping for {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("[INFO] Shutting down...")
            break
        except Exception as e:
            log(f"[ERROR] Loop error: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

if __name__ == "__main__":
    main()
