# Serverless Deployment Guide (Vercel / Netlify)

⚠️ **Important Warning**: Vercel and Netlify are **serverless platforms** with execution limits (10-60 seconds). Discord selfbots require persistent WebSocket connections, which is impossible on these platforms.

This guide provides a **workaround** using Discord's HTTP API with polling, but expect:
- Higher latency (30-60 second delays)
- Less reliability
- Rate limiting issues
- Limited functionality

**Recommendation**: Use Render, Fly.io, or Railway instead (see other deployment guides).

---

## Why Serverless Doesn't Work Well for Discord

### Discord Gateway Requirements
- Persistent WebSocket connection (24/7)
- Real-time event handling
- Continuous heartbeat (every 40 seconds)
- Session state management

### Serverless Limitations
- ❌ Functions run max 10-60 seconds then terminate
- ❌ No persistent WebSocket connections
- ❌ Functions restart fresh every time (no state)
- ❌ Can't maintain Discord session

### The Workaround: HTTP API Polling

Instead of WebSocket gateway, we:
1. Poll Discord's HTTP API every 30-60 seconds
2. Check for new messages mentioning the trigger word
3. Send responses via HTTP API
4. Store last seen message to avoid duplicates

**Trade-offs:**
- ✅ Works on Vercel/Netlify
- ❌ Slow responses (30-60s delays)
- ❌ Higher rate limit hits
- ❌ Less reliable
- ❌ Can't handle DMs or complex features

---

## Deployment Options

### Option 1: Vercel Serverless (API Polling)

**Use this if you must use Vercel, expect delays.**

#### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

#### Step 2: Deploy
```bash
cd /Users/raphie/Discord-AI-Selfbot
vercel deploy
```

#### Step 3: Set Environment Variables
In Vercel dashboard → Settings → Environment Variables:
- `DISCORD_TOKEN`
- `OPENROUTER_API_KEY`

#### Step 4: Create Cron Job
Set up a Vercel Cron Job to trigger the bot every 30-60 seconds:
```vercel.json
{
  "crons": [{
    "path": "/api/poll",
    "schedule": "*/30 * * * *"
  }]
}
```

---

### Option 2: Netlify Serverless (API Polling)

**Use this if you must use Netlify, expect delays.**

#### Step 1: Install Netlify CLI
```bash
npm i -g netlify-cli
```

#### Step 2: Deploy
```bash
cd /Users/raphie/Discord-AI-Selfbot
netlify deploy --prod
```

#### Step 3: Set Environment Variables
In Netlify dashboard → Site settings → Environment:
- `DISCORD_TOKEN`
- `OPENROUTER_API_KEY`

#### Step 4: Create Cron Function
Use Netlify cron jobs to poll every 30-60 seconds.

---

### Option 3: Hybrid Approach (Recommended)

**Best of both worlds: Discord connection elsewhere, AI on serverless.**

#### Architecture:
1. **Discord Relay Service** (on Render/Fly.io):
   - Maintains WebSocket connection
   - Receives messages from Discord
   - Forwards messages to Vercel/Netlify API

2. **AI Service** (on Vercel/Netlify):
   - Receives messages from relay
   - Generates AI responses
   - Sends back to relay

3. **Discord Response** (via relay):
   - Relay receives AI response
   - Sends to Discord via WebSocket

#### Benefits:
- ✅ Fast real-time responses
- ✅ Use serverless for AI (cheap/free)
- ✅ Minimal relay cost (~$5/mo)
- ✅ Scalable AI processing

#### Setup:
See `HYBRID_DEPLOYMENT.md` for detailed guide.

---

## Code Modifications for Serverless

The bot needs to be rewritten to work as an HTTP API endpoint instead of a WebSocket client.

### Required Changes:

1. **Replace Discord.py HTTP Client**
   - Remove WebSocket client (`discord.Client`)
   - Use `discord.py`'s HTTP API (`discord.http.Route`)
   - Implement message polling

2. **State Management**
   - Store last seen message ID in database or file
   - Maintain conversation context in database (no in-memory)
   - Handle multiple users concurrently

3. **API Endpoints**
   - `GET /api/status` - Check if bot is running
   - `POST /api/poll` - Check for new messages and respond
   - `POST /api/message` - Receive message from relay (hybrid)

4. **Cron Job Trigger**
   - Vercel/Netlify cron calls `/api/poll` every 30-60s
   - Bot fetches new messages via HTTP API
   - Responds to new messages

### Example Serverless API Structure:

```python
# api/poll.py (Vercel/Netlify function)
import discord
from utils.ai import generate_response, limit_response

# Poll for new messages
def handler(request):
    # Fetch recent messages via HTTP API
    messages = discord.http.Route("GET", f"/channels/{TARGET}/messages?limit=10")

    # Check for new messages
    new_messages = filter_unseen(messages)

    # Respond to each new message
    for msg in new_messages:
        response = generate_response(msg.content)
        response = limit_response(response, max_sentences=2, max_words=30)

        # Send via HTTP API
        discord.http.Route("POST", f"/channels/{TARGET}/messages", data={
            "content": response,
            "message_reference": {"message_id": msg.id}
        })

    return {"success": True, "responded": len(new_messages)}
```

---

## Why This is Not Recommended

### Problems with Polling
1. **High Latency**: 30-60 second delays between check and response
2. **Rate Limits**: HTTP API has stricter limits than WebSocket
3. **Reliability**: Messages can be missed if polling fails
4. **Resource Waste**: API calls even when no messages exist
5. **Cost**: May hit paid API limits faster

### Better Alternatives
- **Render** - Free Background Worker tier
- **Fly.io** - Free credits, persistent workers
- **Railway** - $5/mo, easy deployment
- **Replit** - Free with Always On

---

## Quick Comparison

| Platform | Works Well? | Cost | Latency | Reliability |
|----------|--------------|-------|----------|-------------|
| **Render** | ✅ Yes | Free | Instant | High |
| **Fly.io** | ✅ Yes | Free credits | Instant | High |
| **Railway** | ✅ Yes | $5/mo | Instant | High |
| **Replit** | ✅ Yes | Free | Instant | Medium |
| **Vercel** (polling) | ⚠️ Meh | Free | 30-60s | Low |
| **Netlify** (polling) | ⚠️ Meh | Free | 30-60s | Low |

---

## Recommendation

**Don't use Vercel/Netlify for Discord bots unless you have no other choice.**

The polling workaround is slow, unreliable, and will frustrate users with 30+ second delays.

**Use Render, Fly.io, or Railway instead** for real-time, reliable Discord bot functionality.

If you **must** use Vercel/Netlify, use the **Hybrid Approach** (Option 3) which keeps Discord connection fast while leveraging serverless for AI processing.

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Netlify Docs**: https://docs.netlify.com
- **Discord Support**: https://discord.gg/yUWmzQBV4P
- **Issues**: Open an issue on GitHub for bugs or questions
