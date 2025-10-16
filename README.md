# Drakyn Agent

A 24/7 AI agent powered by Claude, accessible via a secure web interface.

## Features

- **Secure Authentication**: Google OAuth 2.0 login
- **Gmail Integration**: Read, search, and manage your Gmail inbox via AI assistant
- **Real-time Chat**: WebSocket-based streaming responses
- **Tool Use**: Claude can access your emails and perform actions
- **Conversation History**: Persistent storage with SQLite
- **24/7 Availability**: Runs as a systemd service
- **SSL/HTTPS**: Secure communication with Let's Encrypt
- **Responsive UI**: Clean, modern chat interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: HTML/CSS/JavaScript with WebSockets
- **AI**: Anthropic Claude API
- **Auth**: Google OAuth 2.0
- **Database**: SQLite
- **Web Server**: Nginx (reverse proxy)
- **SSL**: Let's Encrypt (Certbot)

## Setup

### Prerequisites

- Python 3.9+
- Nginx
- Domain name pointing to server (agent.drakyn.ai)
- Google OAuth credentials
- Anthropic API key

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd ~/drakyn-agent
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Set up Google OAuth and Gmail API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or use existing
   - Enable **Google+ API** and **Gmail API**
   - Create OAuth 2.0 credentials
   - Add authorized redirect URI: `https://agent.drakyn.ai/auth/callback`
   - Copy Client ID and Client Secret to `.env`
   - **Important**: The OAuth consent screen must include the Gmail read-only scope

5. **Install and configure Nginx:**
   ```bash
   sudo apt update
   sudo apt install nginx certbot python3-certbot-nginx
   ```

6. **Set up SSL certificate:**
   ```bash
   sudo certbot --nginx -d agent.drakyn.ai
   ```

7. **Configure Nginx** (see `nginx.conf` in repo)

8. **Set up systemd service** (see `drakyn-agent.service` in repo)

9. **Start the service:**
   ```bash
   sudo systemctl enable drakyn-agent
   sudo systemctl start drakyn-agent
   ```

## Configuration

### Environment Variables

- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `SECRET_KEY`: Secret key for session encryption
- `ALLOWED_EMAIL`: Email address allowed to access (your email)
- `BASE_URL`: Your domain URL (https://agent.drakyn.ai)
- `PORT`: Internal port (default: 8000)

### Security

- Only the specified email (`ALLOWED_EMAIL`) can access the agent
- Google OAuth provides secure authentication
- HTTPS enforced via Nginx and Let's Encrypt
- Session tokens stored in secure HTTP-only cookies
- WebSocket connections authenticated via JWT

## Usage

1. Navigate to `https://agent.drakyn.ai`
2. Click "Sign in with Google"
3. Authorize with your Google account (including Gmail access)
4. Start chatting with your AI agent!

### Gmail Integration

Once authenticated, Claude has access to your Gmail inbox and can:

- **List recent emails**: "Show me my recent emails"
- **Search emails**: "Find emails from john@example.com" or "Show unread messages from last week"
- **Read email content**: "Read the email about the project deadline"
- **Check unread emails**: "Do I have any unread emails?"

**Example queries:**
- "What are my 5 most recent emails?"
- "Search for emails about 'project update' from this month"
- "Show me unread emails from my boss"
- "Read the full content of that email about the meeting"

**Gmail Search Syntax:**
Claude supports full Gmail search operators:
- `from:email@example.com` - Emails from specific sender
- `to:email@example.com` - Emails to specific recipient
- `subject:keyword` - Emails with keyword in subject
- `is:unread` - Unread emails only
- `is:starred` - Starred emails
- `has:attachment` - Emails with attachments
- `after:2024/1/1` - Emails after specific date
- `newer_than:7d` - Emails from last 7 days

**Security Note**: Your Gmail OAuth tokens are securely stored in the database and only accessible by your authenticated session. Claude can only read your emails (readonly access), not send or delete them.

## Development

Run locally for development:

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Monitoring

Check service status:
```bash
sudo systemctl status drakyn-agent
```

View logs:
```bash
sudo journalctl -u drakyn-agent -f
```

## Future Enhancements

- [x] Gmail integration (read-only access)
- [ ] Gmail compose and send capabilities
- [ ] Calendar integration
- [ ] Google Drive integration
- [ ] Web search integration
- [ ] File upload/download
- [ ] Code execution
- [ ] Multi-user support
- [ ] Conversation sharing
- [ ] Custom system prompts per conversation
- [ ] Voice input/output
- [ ] Mobile app

## License

Private use only.

## Repository

GitHub: `drakyn-ai/drakyn-agent`
