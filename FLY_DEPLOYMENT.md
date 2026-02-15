# Fly.io Deployment Guide

Deploy your Discord AI Selfbot to Fly.io with free credits.

## Prerequisites

1. **Fly.io Account**: Sign up at https://fly.io (comes with free credits)
2. **Flyctl CLI**: Install Fly.io command-line tool
3. **Discord Token**: Your Discord account token
4. **OpenRouter API Key**: Get one at https://openrouter.ai/keys

## Step 1: Install Flyctl CLI

**macOS:**
```bash
brew install flyctl
```

**Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

**Windows:**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

Verify installation:
```bash
flyctl version
```

## Step 2: Authenticate with Fly.io

```bash
flyctl auth signup
```

Or if you already have an account:
```bash
flyctl auth login
```

Follow the browser prompts to authenticate.

## Step 3: Configure Fly.io

### 3.1 Set Environment Variables

Open `fly.toml` and replace the placeholder values:

```toml
[env]
  DISCORD_TOKEN = "your_actual_discord_token_here"
  OPENROUTER_API_KEY = "your_actual_openrouter_key_here"
```

### 3.2 (Optional) Change Region

The default region is `iad` (Ashburn, Virginia). For better latency, choose one closer to you:

- `ewr` - Newark (US East)
- `ord` - Chicago (US Central)
- `iad` - Ashburn (US East) - default
- `dfw` - Dallas (US South)
- `sea` - Seattle (US West)
- `lax` - Los Angeles (US West)
- `syd` - Sydney (Australia)
- `lhr` - London (UK)
- `ams` - Amsterdam (Netherlands)
- `fra` - Frankfurt (Germany)
- `cdg` - Paris (France)

Change it in `fly.toml`:
```toml
app = "discord-ai-selfbot"
primary_region = "your_chosen_region"
```

## Step 4: Launch Your App

### 4.1 Initialize Fly.io (first time)

```bash
cd /Users/raphie/Discord-AI-Selfbot
flyctl launch
```

Follow the prompts:
- App name: Enter `discord-ai-selfbot` or your preferred name
- Region: Choose your preferred region
- Would you like to deploy now? **No** (we'll do it manually with env vars)

### 4.2 Set Environment Variables

```bash
flyctl secrets set DISCORD_TOKEN=your_actual_discord_token_here
flyctl secrets set OPENROUTER_API_KEY=your_actual_openrouter_key_here
```

Note: Secrets are encrypted and stored securely. They override values in `fly.toml`.

### 4.3 Deploy

```bash
flyctl deploy
```

Wait for deployment to complete (~2-3 minutes).

## Step 5: Monitor Your Bot

### View Logs
```bash
flyctl logs
```

### Monitor Status
```bash
flyctl status
```

### View App Details
```bash
flyctl info
```

### Restart Bot
```bash
flyctl restart
```

### SSH into App (for debugging)
```bash
flyctl ssh console
```

## Troubleshooting

### Bot won't start
- Check secrets: `flyctl secrets list`
- View logs: `flyctl logs` for error messages
- Verify Discord token is correct
- Verify OpenRouter API key is valid

### Bot starts but doesn't respond
- Check logs for "Connected to Gateway"
- Verify target channel ID in `final_smart.py`
- Check if bot is hitting rate limits
- Verify DISCORD_TOKEN is set as a secret

### Deployment fails
- Check Dockerfile for syntax errors
- Verify all dependencies are in `requirements.txt`
- View build logs: `flyctl logs --type build`
- Ensure `flyctl` is updated: `flyctl version`

### Out of free credits
- Fly.io gives free credits for new accounts
- After free credits, cost is ~$5-7/month for a single bot
- View usage: `flyctl info` → check cost estimate
- Scale down if needed: `flyctl scale count 1 --app discord-ai-selfbot`

### Bot keeps restarting
- View logs: `flyctl logs --tail 50`
- Check for memory issues (bots need minimal memory)
- Verify Discord token isn't invalid (would cause auth failures)
- Check for rate limiting from Discord

## Cost

**Free Credits:**
- New accounts get ~$5-15 in free credits
- Good for testing and initial deployment

**Paid Pricing** (after free credits):
- $5-7/month for a single Discord bot instance
- 256MB RAM, 1 shared CPU
- 3GB bandwidth
- Billing: Pay only for what you use

**Scaling:**
- 1 instance is sufficient for a single Discord bot
- Multiple instances require multiple Discord accounts (not recommended)

## Managing Your Bot

### Update Bot
After making changes to code:
```bash
flyctl deploy
```

### Change Secrets
```bash
# Set new secret
flyctl secrets set DISCORD_TOKEN=new_token

# Remove secret
flyctl secrets unset DISCORD_TOKEN

# List all secrets
flyctl secrets list
```

### Scale Resources
```bash
# Increase memory
flyctl scale memory 512 --app discord-ai-selfbot

# Decrease memory
flyctl scale memory 256 --app discord-ai-selfbot
```

### Delete App
```bash
flyctl apps destroy discord-ai-selfbot
```

## Security Notes

⚠️ **Important**:
- Always use `flyctl secrets` for sensitive data (never in fly.toml)
- Use a burner Discord account (selfbots violate Discord TOS)
- Monitor your bot's activity regularly
- Secrets are encrypted and stored securely by Fly.io
- Never commit tokens to git

## Alternatives

If Fly.io free credits are exhausted:

**Render** (free tier available):
- Background Workers with 750 hours/month free
- See `RENDER_DEPLOYMENT.md` for setup

**Replit** (free with Always On):
- See `REPLIT_DEPLOYMENT.md` for setup

**Railway** (starts at $5/mo):
- Easy deployment from GitHub
- Supports persistent Python workers

## Next Steps

1. **Test bot**: Send a message to your target Discord channel
2. **Monitor logs**: Watch for errors or unusual activity
3. **Adjust settings**: Edit `config/instructions.txt` to change personality
4. **Scale resources**: Adjust memory/CPU if needed

## Support

- **Fly.io Docs**: https://fly.io/docs
- **Flyctl Reference**: https://fly.io/docs/flyctl/
- **Discord Support**: https://discord.gg/yUWmzQBV4P
- **Issues**: Open an issue on GitHub for bugs or questions
