# Serverless Discord Bot - Quick Start

This is a **serverless version** of Discord AI Selfbot for Vercel/Netlify.

⚠️ **Important**: This uses HTTP API polling (30-60s delays). For real-time responses, use Render/Fly.io instead.

---

## Deployment to Vercel

### 1. Install Vercel CLI
```bash
npm i -g vercel
```

### 2. Deploy
```bash
cd /Users/raphie/Discord-AI-Selfbot
vercel deploy --prod
```

### 3. Set Environment Variables
Go to Vercel dashboard → Project → Settings → Environment Variables:
- `DISCORD_TOKEN` = your Discord token
- `OPENROUTER_API_KEY` = your OpenRouter key

### 4. Verify Cron Job
Vercel should automatically set up cron to run every 30 seconds.

---

## Deployment to Netlify

### 1. Install Netlify CLI
```bash
npm i -g netlify-cli
```

### 2. Login
```bash
netlify login
```

### 3. Deploy
```bash
cd /Users/raphie/Discord-AI-Selfbot
netlify deploy --prod
```

### 4. Set Environment Variables
Go to Netlify dashboard → Site → Site settings → Environment variables:
- `DISCORD_TOKEN` = your Discord token
- `OPENROUTER_API_KEY` = your OpenRouter key

### 5. Set Up Cron Job
Go to Netlify dashboard → Site → Functions → Scheduled functions:
- Create function: `/api/poll.py`
- Schedule: Every 30 minutes (or use external cron like easycron.com)

---

## Testing

### Test Vercel Endpoint
```bash
curl https://your-project.vercel.app/api/poll
```

### Test Netlify Endpoint
```bash
curl https://your-project.netlify.app/api/poll
```

Expected response:
```json
{
  "success": true,
  "processed": 5,
  "responded": 1,
  "last_seen": "1234567890123456789"
}
```

---

## Expected Behavior

1. **Cron triggers function** every 30-60 seconds
2. **Fetches last 20 messages** from Discord channel
3. **Checks for new messages** (not seen before)
4. **Generates AI response** for qualifying messages
5. **Sends reply** via Discord HTTP API
6. **Updates last seen** message ID

---

## Configuration

### Change Target Channel
Edit `api/poll.py`:
```python
TARGET_CHANNEL = 1470478653606461532  # Change this
```

### Change Cooldown
Edit `api/poll.py`:
```python
COOLDOWN_SECONDS = 60  # Change this
```

### Change AI Model
Edit `api/poll.py`:
```python
PRIMARY_MODEL_ID = "google/gemini-2.5-flash-lite"  # Change this
```

### Change Response Limits
Edit `api/poll.py`:
```python
response = limit_response(response, max_sentences=2, max_words=30)  # Change limits
```

---

## Limitations

### Why This is Slow
- Polling happens every 30-60 seconds (not real-time)
- Discord HTTP API has rate limits
- Messages may be missed if polling fails
- High latency between message and response (30-90s)

### Why Use This Anyway
- Works on Vercel/Netlify (serverless)
- Free tier available
- Good for testing/concepts
- Easy deployment

### Better Alternatives
- **Render** - Real-time, free Background Worker
- **Fly.io** - Real-time, free credits
- **Railway** - Real-time, $5/mo

---

## Troubleshooting

### Function returns error 500
- Check environment variables are set
- Verify DISCORD_TOKEN is valid
- Verify OPENROUTER_API_KEY works
- Check logs for specific error

### Bot doesn't respond
- Cron job may not be running
- Check last_seen state (function may be resetting)
- Verify target channel ID is correct
- Check cooldown timer

### Cron job not triggering
- Vercel: Check vercel.json cron configuration
- Netlify: Use external cron service (e.g., cron-job.org)
- Verify function URL is correct

### Rate limiting from Discord
- Slow down polling (60-90 seconds instead of 30)
- Reduce message limit (10 instead of 20)
- Use better token (different account)

---

## Support

- **Vercel Docs**: https://vercel.com/docs
- **Netlify Docs**: https://docs.netlify.com
- **Discord Support**: https://discord.gg/yUWmzQBV4P
