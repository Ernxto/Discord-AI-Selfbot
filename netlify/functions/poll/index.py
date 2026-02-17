"""
Serverless Discord Bot - Netlify Function
"""
import os
import json
import time
import sqlite3
from datetime import datetime
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not DISCORD_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Missing environment variables")

# Discord API configuration
DISCORD_API = "https://discord.com/api/v10"
TARGET_CHANNEL = 1470478653606461532
COOLDOWN_SECONDS = 30

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
        print(f"[ERROR] DB init failed: {e}")

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
        print(f"[ERROR] Store failed: {e}")

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
        print(f"[ERROR] Get messages failed: {e}")
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
        print(f"[ERROR] AI failed: {e}")
        return None

def handler(event, context):
    """Netlify function handler"""

    # Health check for cron - simple 200 response
    http_method = event.get('httpMethod', 'GET')
    path = event.get('path', '')
    query_params = event.get('queryStringParameters', {})

    # If it's a cron/health check, return 200 immediately
    if http_method == 'GET' and (path == '/' or path == '/health' or 'health' in query_params):
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"status": "ok", "bot": "alive"})
        }

    init_db()

    print(f"[{datetime.now().isoformat()}] Bot triggered")

    try:
        # Get bot user info
        user = discord_get("/users/@me")
        if not user:
            return {"statusCode": 500, "body": json.dumps({"error": "Failed to authenticate"})}

        user_id = user.get("id")
        print(f"[INFO] Bot: {user.get('username')} ({user_id})")

        # Fetch messages
        messages = discord_get(f"/channels/{TARGET_CHANNEL}/messages?limit=20")
        if not messages:
            return {"statusCode": 200, "body": json.dumps({"success": True, "messages": 0})}

        print(f"[INFO] Fetched {len(messages)} messages")

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

            print(f"[MSG] {msg.get('author', {}).get('username')}: {content[:50]}")

            # Store message
            msg_author_id = msg.get("author", {}).get("id")
            store_message(TARGET_CHANNEL, msg_author_id, msg.get("author", {}).get("username"), content)

            # Generate response
            response = generate_response(content, context)
            if not response or len(response.strip()) < 2:
                print("[SKIP] No valid response")
                return {"statusCode": 200, "body": json.dumps({"success": True, "skipped": True})}

            # Limit response
            sentences = response.split('.')
            response = ' '.join([s.strip() for s in sentences[:2] if s.strip()])

            words = response.split()
            if len(words) > 30:
                response = ' '.join(words[:30])

            print(f"[REPLY] {response[:50]}")

            # Send reply
            discord_post(f"/channels/{TARGET_CHANNEL}/messages", {
                "content": response,
                "message_reference": {"message_id": msg.get("id"), "guild_id": False}
            })

            # Store bot response
            store_message(TARGET_CHANNEL, user_id, user.get("username"), response, is_bot=True)

            print("[DONE] Response sent")
            return {"statusCode": 200, "body": json.dumps({"success": True, "responded": True})}

        print("[INFO] No new messages to respond to")
        return {"statusCode": 200, "body": json.dumps({"success": True, "responded": False})}

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

# Netlify export
def main(event, context):
    """Main entry point for Netlify"""
    return handler(event, context)
