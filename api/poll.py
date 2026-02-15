"""
Serverless Discord Bot - HTTP API Polling Version
For Vercel / Netlify deployment

⚠️ This uses polling (HTTP API) instead of WebSocket gateway.
Expect 30-60 second delays between message check and response.
Not recommended for production use.
"""

import os
import json
import time
from datetime import datetime
import requests
from openai import AsyncOpenAI as OpenAI
from dotenv import load_dotenv
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not DISCORD_TOKEN or not OPENROUTER_API_KEY:
    raise ValueError("Missing environment variables")

# Discord API configuration
DISCORD_API = "https://discord.com/api/v10"
TARGET_CHANNEL = 1470478653606461532  # Your target channel ID
COOLDOWN_SECONDS = 60

# AI Configuration
PRIMARY_MODEL_ID = "google/gemini-2.5-flash-lite"

# State (in production, use Redis/database)
LAST_SEEN_MESSAGE = None
LAST_REPLY_TIME = 0

# OpenRouter client
ai_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)


def load_instructions() -> str:
    """Load bot instructions"""
    try:
        with open("config/instructions.txt", "r") as f:
            return f.read()
    except:
        return "You are a helpful, friendly assistant."


def limit_response(text: str, max_sentences: int = 2, max_words: int = 30) -> str:
    """Limit response length"""
    sentences = text.split('.')
    sentences = [s.strip() for s in sentences if s.strip()]
    limited = ' '.join(sentences[:max_sentences])

    words = limited.split()
    if len(words) > max_words:
        limited = ' '.join(words[:max_words])

    limited = limited.strip()
    if limited and limited[-1] not in '.!?':
        limited += '.'

    return limited


def discord_get(url: str) -> Dict:
    """Make GET request to Discord API"""
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.get(f"{DISCORD_API}{url}", headers=headers)
    response.raise_for_status()
    return response.json()


def discord_post(url: str, data: Dict) -> Dict:
    """Make POST request to Discord API"""
    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{DISCORD_API}{url}", headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_current_user() -> Dict:
    """Get bot user info"""
    return discord_get("/users/@me")


def get_messages(channel_id: str, limit: int = 20) -> List[Dict]:
    """Get recent messages from channel"""
    try:
        return discord_get(f"/channels/{channel_id}/messages?limit={limit}")
    except requests.HTTPError as e:
        print(f"[ERROR] Failed to fetch messages: {e}")
        return []


def send_message(channel_id: str, content: str, reply_to: str = None) -> Dict:
    """Send message to channel"""
    data = {"content": content}

    if reply_to:
        data["message_reference"] = {"message_id": reply_to, "guild_id": False}

    try:
        return discord_post(f"/channels/{channel_id}/messages", data=data)
    except requests.HTTPError as e:
        print(f"[ERROR] Failed to send message: {e}")
        return {}


async def generate_response(prompt: str, instructions: str) -> Optional[str]:
    """Generate AI response"""
    try:
        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ]

        response = await ai_client.chat.completions.create(
            model=PRIMARY_MODEL_ID,
            messages=messages,
            max_tokens=600,
            temperature=0.7
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] AI generation failed: {e}")
        return None


def should_process_message(message: Dict, user_id: str) -> bool:
    """Check if message should trigger bot response"""
    # Skip own messages
    if message.get("author", {}).get("id") == user_id:
        return False

    # Skip empty messages
    content = message.get("content", "").strip()
    if len(content) < 2:
        return False

    # Check cooldown
    global LAST_REPLY_TIME
    time_since = time.time() - LAST_REPLY_TIME
    if time_since < COOLDOWN_SECONDS:
        return False

    # Check for trigger word (optional: uncomment if you want trigger)
    # if "raphie" not in content.lower():
    #     return False

    return True


def handler(event, context):
    """
    Serverless function handler
    Called by Vercel cron or external trigger
    """
    global LAST_SEEN_MESSAGE, LAST_REPLY_TIME

    print(f"[{datetime.now().isoformat()}] Bot triggered")

    try:
        # Get current user
        user = get_current_user()
        user_id = user.get("id")
        print(f"[INFO] Bot user: {user.get('username')} ({user_id})")

        # Fetch recent messages
        messages = get_messages(TARGET_CHANNEL, limit=20)
        print(f"[INFO] Fetched {len(messages)} messages")

        if not messages:
            return {"statusCode": 200, "body": json.dumps({"success": True, "messages": 0})}

        # Find new messages
        new_messages = []
        if LAST_SEEN_MESSAGE:
            # Find messages newer than last seen
            for msg in messages:
                if msg.get("id") == LAST_SEEN_MESSAGE:
                    break
                new_messages.append(msg)
        else:
            # First run: process last 3 messages
            new_messages = messages[:3]

        if not new_messages:
            print(f"[INFO] No new messages")
            return {"statusCode": 200, "body": json.dumps({"success": True, "new": 0})}

        print(f"[INFO] Processing {len(new_messages)} new messages")

        # Process each new message
        instructions = load_instructions()
        responded = 0

        for msg in reversed(new_messages):  # Process in order
            if should_process_message(msg, user_id):
                content = msg.get("content", "")
                author = msg.get("author", {}).get("username", "Unknown")

                print(f"[MSG] {author}: {content[:50]}")

                # Generate response
                import asyncio
                response = asyncio.run(generate_response(content, instructions))

                if not response or len(response.strip()) < 2:
                    print(f"[SKIP] No valid response")
                    continue

                response = limit_response(response, max_sentences=2, max_words=30)
                print(f"[RESP] {response[:50]}")

                # Send reply
                send_message(TARGET_CHANNEL, response, reply_to=msg.get("id"))
                LAST_REPLY_TIME = time.time()
                responded += 1

                # Only respond to one message per run
                break

        # Update last seen message
        if messages:
            LAST_SEEN_MESSAGE = messages[0].get("id")

        print(f"[DONE] Responded to {responded} message(s)")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "success": True,
                "processed": len(new_messages),
                "responded": responded,
                "last_seen": LAST_SEEN_MESSAGE
            })
        }

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# For local testing
if __name__ == "__main__":
    handler({}, {})
