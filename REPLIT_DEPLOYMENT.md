# Replit Deployment Guide

Deploy your Discord AI Selfbot to Replit with "Always On" feature (free).

## Prerequisites

1. **Replit Account**: Sign up at https://replit.com (free)
2. **Discord Token**: Your Discord account token
3. **OpenRouter API Key**: Get one at https://openrouter.ai/keys

## Step 1: Create New Replit

1. Go to https://replit.com
2. Click **"+ Create Repl"**
3. Choose **"Import from GitHub"**
4. Enter your repo: `Ernxto/Discord-AI-Selfbot`
5. Click **"Import from GitHub"**

Or manually:
1. Click **"+ Create Repl"**
2. Template: **Python**
3. Name: `discord-ai-selfbot`
4. Click **"Create Repl"**
5. Upload all files from `/Users/raphie/Discord-AI-Selfbot`

## Step 2: Configure Environment Variables

1. Click **"Secrets"** (lock icon on left sidebar)
2. Add these secrets:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | Your Discord account token |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

3. Click **"Add Secret"** for each one

## Step 3: Install Dependencies

1. Open **Shell** (bottom panel)
2. Run:
```bash
pip install -r requirements.txt
```

## Step 4: Enable Always On

1. Click **"Deployments"** (top navigation)
2. Click **"Create Deployment"**
3. Configure:
   - **Title**: `Discord AI Selfbot`
   - **Description**: `Persistent Discord bot with AI`
   - **Version**: Select **Python 3.9+**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 final_smart.py`
4. Click **"Create Deployment"**
5. Wait for build to complete (~1-2 minutes)
6. **Important**: Enable **"Always On"** toggle (keeps bot running 24/7)

## Step 5: Monitor Your Bot

- **Shell**: View live logs in bottom panel
- **Deployments**: See deployment status and logs
- **Console**: Check for errors or warnings
- **Logs**: View persistent logs (if you add file logging)

## Step 6: Test the Bot

1. Go to your target Discord channel
2. Send a message: `Hi Raphie`
3. Bot should respond within a few seconds
4. Check Replit Shell to see activity

## Troubleshooting

### Bot won't start
- Check environment variables in "Secrets" tab
- Ensure all dependencies are installed
- Check Shell for error messages

### Bot starts but doesn't respond
- Verify target channel ID in `final_smart.py`
- Check if bot is connected to Discord (logs show "Connected to Gateway")
- Check cooldown timer (60 seconds between responses)

### Always On not available
- Free accounts may have limited Always On
- Consider upgrading to Replit Core ($7/month) for guaranteed 24/7 uptime
- Or use alternative: https://uptimekuma.com to ping your bot regularly

### Bot keeps restarting
- Check logs for repeated errors
- May be hitting memory limits
- Reduce AI response length or cooldown

### Discord rate limiting
- Bot will show "Gateway is ratelimited" in logs
- Wait for rate limit to clear (~60 seconds)
- Reduce message frequency if it's frequent

## Cost

**Free Tier:**
- Always On: Limited availability
- 512MB RAM
- Shared CPU
- 10GB storage

**Core Plan** ($7/month):
- Always On: Guaranteed 24/7
- 1GB RAM
- Dedicated CPU
- 50GB storage

**Hacker Plan** ($20/month):
- Always On: Guaranteed 24/7
- 8GB RAM
- More CPU
- 100GB storage

Free tier is sufficient for a single Discord bot instance.

## Security Notes

⚠️ **Important**:
- Use Secrets for sensitive data (never hardcode tokens)
- Use a burner Discord account (selfbots violate Discord TOS)
- Monitor your bot's activity regularly
- Replit secrets are private and secure

## Keeping Your Bot Running 24/7

**Option 1: Always On (Free)**
- Enable in Deployments settings
- May pause if not accessed frequently
- Check periodically to keep it active

**Option 2: Uptime Monitor**
- Use https://uptimerobot.com (free)
- Pings your deployment every 5 minutes
- Keeps it from sleeping

**Option 3: Upgrade to Core**
- Guaranteed 24/7 uptime
- No interruptions
- Better performance

## Next Steps

1. **Test bot**: Send a message to your target channel
2. **Monitor logs**: Watch for errors or unusual activity
3. **Adjust settings**: Edit `config/instructions.txt` to change personality
4. **Scale up**: If you need 24/7 guaranteed uptime, upgrade to Core

## Support

- **Replit Docs**: https://docs.replit.com
- **Discord Support**: https://discord.gg/yUWmzQBV4P
- **Issues**: Open an issue on GitHub for bugs or questions
