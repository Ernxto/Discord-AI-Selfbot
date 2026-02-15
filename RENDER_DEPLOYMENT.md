# Render Deployment Guide

This guide will help you deploy the Discord AI Selfbot to Render (free tier).

## Prerequisites

1. **Render Account**: Sign up at https://render.com
2. **GitHub Account**: Fork this repository to your own GitHub account
3. **Discord Token**: Your Discord account token (from DevTools)
4. **OpenRouter API Key**: Get one at https://openrouter.ai/keys

## Step 1: Fork the Repository

1. Go to https://github.com/Najmul190/Discord-AI-Selfbot
2. Click "Fork" in the top right
3. Choose your GitHub account as the destination

## Step 2: Connect Your Fork to Render

1. Log in to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Select "Connect GitHub repository"
4. Authorize Render to access your GitHub
5. Find and select your forked repository
6. Click "Connect"

## Step 3: Configure Render Service

**Important**: Click "Advanced" to switch from "Web Service" to "Background Worker"

### General Settings
- **Name**: `discord-ai-selfbot` (or your preferred name)
- **Region**: Choose closest to your Discord servers
- **Branch**: `main`
- **Runtime**: `Python`
- **Root Directory**: Leave blank (default)

### Build Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python3 final_smart.py`

### Environment Variables (Required)

Add these in the "Advanced" → "Environment Variables" section:

| Key | Value |
|-----|-------|
| `DISCORD_TOKEN` | Your Discord account token |
| `OPENROUTER_API_KEY` | Your OpenRouter API key |

**Note**: Mark these as "Not synced" to keep them private.

## Step 4: Deploy

1. Click "Create Background Worker"
2. Wait for the build to complete (~2-3 minutes)
3. Your bot will start automatically after deployment
4. Check the "Logs" tab to see bot activity

## Step 5: Monitor Your Bot

- **Logs**: View real-time bot activity in the Logs tab
- **Metrics**: Monitor CPU, memory, and network usage
- **Events**: See deployment and restart events
- **Manual Restart**: Click "Manual Deploy" → "Clear build cache & deploy" if needed

## Troubleshooting

### Bot won't start
- Check that `DISCORD_TOKEN` and `OPENROUTER_API_KEY` are set correctly
- View logs for error messages
- Try a manual restart

### Bot not responding
- Check if the bot is connected to Discord (logs should show "Connected to Gateway")
- Verify the target channel ID in `final_smart.py`
- Check logs for rate limiting or errors

### Deployment fails
- Check that all dependencies are in `requirements.txt`
- Verify Python version compatibility (Render uses Python 3.9+)
- Review build logs for specific errors

### Bot keeps restarting
- Check logs for repeated errors
- May be hitting memory limits (free tier: 512MB)
- Consider upgrading to Starter plan ($7/mo) for more resources

## Cost

- **Free Tier**: $0/month (512MB RAM, 0.1 CPU)
- **Starter Tier**: $7/month (1GB RAM, 0.5 CPU)
- **Standard Tier**: $25/month (2GB RAM, 1 CPU)

The free tier is sufficient for a single Discord bot instance.

## Security Notes

⚠️ **Important**:
- Never commit your Discord token or API keys to GitHub
- Always use environment variables for sensitive data
- Use a burner Discord account (selfbots violate Discord TOS)
- Monitor your bot's activity regularly

## Next Steps

1. **Test the bot**: Send a message to your target channel
2. **Monitor logs**: Watch for errors or unusual activity
3. **Adjust settings**: Edit `config/instructions.txt` to change personality
4. **Scale up**: If you need more resources, upgrade your Render plan

## Support

- **Render Docs**: https://render.com/docs
- **Discord Support**: https://discord.gg/yUWmzQBV4P
- **Issues**: Open an issue on GitHub for bugs or questions
