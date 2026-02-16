#!/usr/bin/env python3
"""
Final working bot - runs continuously and responds to channel 1470478653606461532
"""
import os
import sys
import sqlite3
import discord
from dotenv import load_dotenv
import time

# Add to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai import generate_response
from utils.helpers import load_instructions, get_env_path
from utils.memory import store_message, build_context_prompt

TARGET_CHANNEL = 1470478653606461532

# Init database
os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/memory.db")
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id INTEGER,
        user_id INTEGER,
        username TEXT,
        content TEXT,
        timestamp REAL,
        is_bot INTEGER,
        keywords TEXT
    )
""")
conn.commit()
conn.close()

# Create Discord client
client = discord.Client()

recent_responses = {}

def is_good_response(response):
    if not response or len(response) < 3:
        return False
    bad = ["i am an ai", "i cannot", "i don't know", "sorry, i can't"]
    return not any(phrase in response.lower() for phrase in bad)

def check_duplicate(channel_id, response):
    response = response.lower().strip()
    recent = recent_responses.get(channel_id, [])
    return response not in recent

def record_response(channel_id, response):
    if channel_id not in recent_responses:
        recent_responses[channel_id] = []
    recent_responses[channel_id].append(response.lower().strip())
    if len(recent_responses[channel_id]) > 10:
        recent_responses[channel_id].pop(0)

@client.event
async def on_ready():
    print("\n" + "=" * 60)
    print(f"✓ BOT ONLINE: {client.user.name}")
    print("=" * 60)
    print(f"ID: {client.user.id}")
    print("=" * 60)
    print(f"Target Channel ID: {TARGET_CHANNEL}")
    print("=" * 60)
    print("Watching for messages...")

@client.event
async def on_message(message):
    # Check channel
    if message.channel.id != TARGET_CHANNEL:
        return

    # Skip self
    if message.author.id == client.user.id:
        return

    # Skip short
    content = message.content.strip()
    if len(content) < 3:
        return

    print(f"\n[MSG] {message.author}: {content}")

    try:
        # Store
        store_message(message.channel.id, message.author.id, message.author.display_name, content)

        # Build prompt with full context
        context = build_context_prompt(message.channel.id, content, message.author.id)

        prompt = f"""You are Raphie, a friendly Discord user.

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE: {content}

Respond naturally and casually. Keep it short (1-2 sentences, under 25 words). Be witty if appropriate."""

        # Generate
        instructions = load_instructions()
        response = await generate_response(prompt, instructions, history=[], model="smart")

        if not response or not is_good_response(response):
            print("  -> Skipping (bad response)")
            return

        response = response.strip()

        if len(response) < 3:
            print("  -> Skipping (too short)")
            return

        if not check_duplicate(message.channel.id, response):
            print("  -> Skipping (duplicate)")
            return

        # Send
        print(f"[REPLY] {response}")
        await message.reply(response, mention_author=False)
        record_response(message.channel.id, response)

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    load_dotenv(dotenv_path=get_env_path())
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("ERROR: No token")
        sys.exit(1)

    print("Starting bot...")
    client.run(TOKEN)
