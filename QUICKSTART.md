# Quick Start Guide

This guide will help you get Drakyn Agent up and running in about 15-20 minutes.

## Step 1: DNS Configuration

Add this A record to your domain at name.com:

```
Type: A
Host: agent (or agent.drakyn.ai depending on interface)
Value: 20.59.111.132
TTL: 3600
```

Wait a few minutes for DNS propagation. Test with:
```bash
ping agent.drakyn.ai
```

## Step 2: Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client ID"
5. Configure consent screen if needed (Internal or External)
6. Application type: **Web application**
7. Name: **Drakyn Agent**
8. Authorized redirect URIs: `https://agent.drakyn.ai/auth/callback`
9. Click "Create"
10. Copy the **Client ID** and **Client Secret**

## Step 3: Get Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Navigate to "API Keys"
3. Create a new key
4. Copy the API key (starts with `sk-ant-`)

## Step 4: Configure Environment

```bash
cd ~/drakyn-agent

# Create .env file
cp .env.example .env

# Generate a secret key
openssl rand -hex 32

# Edit .env with your favorite editor
nano .env
```

Fill in these values in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-...  # Your Anthropic API key
GOOGLE_CLIENT_ID=...          # From Step 2
GOOGLE_CLIENT_SECRET=...      # From Step 2
SECRET_KEY=...                # Generated above
ALLOWED_EMAIL=your@email.com  # Your Google email
BASE_URL=https://agent.drakyn.ai
PORT=8000
```

## Step 5: Run Setup Script

```bash
cd ~/drakyn-agent
./setup.sh
```

The script will:
- Create Python virtual environment
- Install dependencies
- Configure Nginx
- Set up SSL with Let's Encrypt
- Create and start systemd service

Follow the prompts. When asked about DNS, confirm it's configured.

## Step 6: Verify Installation

Check the service is running:
```bash
sudo systemctl status drakyn-agent
```

View logs:
```bash
sudo journalctl -u drakyn-agent -f
```

## Step 7: Access Your Agent

1. Open browser to: `https://agent.drakyn.ai`
2. Click "Sign in with Google"
3. Authorize with your Google account (the one in ALLOWED_EMAIL)
4. Start chatting!

## Troubleshooting

### DNS not resolving
- Check DNS record is correct
- Wait for propagation (can take 5-60 minutes)
- Try `nslookup agent.drakyn.ai`

### SSL certificate failed
- Ensure DNS is working first
- Check port 80 and 443 are open
- Run: `sudo certbot --nginx -d agent.drakyn.ai`

### Service won't start
- Check logs: `sudo journalctl -u drakyn-agent -n 50`
- Verify .env file has all required values
- Check Python virtual environment: `source venv/bin/activate && python --version`

### Authentication fails
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are correct
- Check redirect URI in Google Console matches exactly: `https://agent.drakyn.ai/auth/callback`
- Ensure ALLOWED_EMAIL matches your Google account email

### Can't connect to Claude
- Verify ANTHROPIC_API_KEY is correct
- Check API key has credits/quota
- Test API key: `curl https://api.anthropic.com/v1/messages -H "x-api-key: YOUR_KEY" -H "anthropic-version: 2023-06-01"`

## Useful Commands

```bash
# Restart service
sudo systemctl restart drakyn-agent

# Stop service
sudo systemctl stop drakyn-agent

# Start service
sudo systemctl start drakyn-agent

# View logs (live)
sudo journalctl -u drakyn-agent -f

# Check Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx

# Renew SSL (automatic, but can be manual)
sudo certbot renew

# Edit environment
cd ~/drakyn-agent
nano .env
sudo systemctl restart drakyn-agent
```

## Next Steps

Once running, you can:
- Chat with your AI agent 24/7
- Create multiple conversations
- All data persists in SQLite database
- Access from anywhere via HTTPS

For future enhancements, see README.md.

## Support

Issues? Check:
1. Service logs: `sudo journalctl -u drakyn-agent -f`
2. Nginx logs: `sudo tail -f /var/log/nginx/error.log`
3. GitHub repo: https://github.com/drakyn-ai/drakyn-agent
