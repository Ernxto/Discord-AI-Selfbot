#!/usr/bin/env python3
"""
Smart bot with clean instructions
"""
import os
import sys
import time
import discord
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ai import generate_response, limit_response
from utils.helpers import load_instructions, get_env_path
from utils.memory import build_context_prompt

TARGET = 1470478653606461532
COOLDOWN_SECONDS = 60

# Track state
last_reply_time = None
last_processed_message_id = None

client = discord.Client()

@client.event
async def on_ready():
    print(f"\n{'='*60}")
    print(f"✓ SMART BOT: {client.user.name}")
    print(f"{'='*60}")
    print(f"Watching: {TARGET}")
    print(f"Cooldown: {COOLDOWN_SECONDS}s")
    print(f"{'='*60}")
    print("Send a message!")
    print(f"{'='*60}\n")

@client.event
async def on_message(message):
    # Skip if not target
    if message.channel.id != TARGET:
        return

    # Skip own messages
    if message.author.id == client.user.id:
        return

    # Skip already processed
    global last_processed_message_id
    if last_processed_message_id == message.id:
        return

    content = message.content.strip()
    if len(content) < 2:
        return

    print(f"\n[MSG] {message.author}: {content}")

    # Check cooldown
    global last_reply_time
    if last_reply_time:
        time_since = time.time() - last_reply_time
        if time_since < COOLDOWN_SECONDS:
            print(f"  -> Cooldown ({time_since:.0f}s), skipping")
            return

    # Mark as processed
    last_processed_message_id = message.id

    try:
        # Load instructions
        instructions = load_instructions() or "Be friendly."

        # Get context
        context = build_context_prompt(message.channel.id, content, message.author.id)

        # Build prompt with instructions FIRST
        prompt = f"""{instructions}

CONVERSATION CONTEXT:
{context}

CURRENT MESSAGE:
{content}

Reply as Raphie. Be natural, have personality, and vary your response length."""

        # Generate response
        response = await generate_response(prompt, instructions, history=[], model_override="smart")

        if not response or len(response.strip()) < 2:
            print("  -> No response")
            return

        response = response.strip()

        # Limit response length (max 2 sentences, 30 words)
        response = limit_response(response, max_sentences=2, max_words=30)

        # Type briefly (3 seconds) before sending
        print(f"[TYPING] {response[:30]}...")
        async with message.channel.typing():
            import asyncio
            await asyncio.sleep(3)

        # Send reply
        print(f"[SEND] {response[:60]}")
        await message.reply(response, mention_author=False)

        # Update cooldown (set when we send, not when we generate)
        last_reply_time = time.time()
        print(f"  -> Sent! Cooldown reset\n")

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    load_dotenv(dotenv_path=get_env_path())
    TOKEN = os.getenv("DISCORD_TOKEN")

    if not TOKEN:
        print("ERROR: No DISCORD_TOKEN")
        sys.exit(1)

    print("Starting smart bot...")
    client.run(TOKEN)
