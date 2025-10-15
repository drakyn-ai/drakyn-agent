#!/bin/bash
set -e

echo "================================"
echo "Drakyn Agent Setup Script"
echo "================================"
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please run this script as a normal user, not root."
    echo "The script will use sudo when needed."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your credentials:"
    echo "  - ANTHROPIC_API_KEY"
    echo "  - GOOGLE_CLIENT_ID"
    echo "  - GOOGLE_CLIENT_SECRET"
    echo "  - SECRET_KEY (generate with: openssl rand -hex 32)"
    echo "  - ALLOWED_EMAIL"
    echo ""
    read -p "Press Enter after you've configured .env..."
fi

# Create Python virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Create data directory
echo "Creating data directory..."
mkdir -p data

# Install Nginx if not installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Install Certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing Certbot..."
    sudo apt install -y certbot python3-certbot-nginx
fi

# Setup Nginx configuration
echo "Setting up Nginx configuration..."
sudo cp nginx.conf /etc/nginx/sites-available/drakyn-agent

# Enable site
if [ ! -L /etc/nginx/sites-enabled/drakyn-agent ]; then
    sudo ln -s /etc/nginx/sites-available/drakyn-agent /etc/nginx/sites-enabled/
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Reload Nginx
echo "Reloading Nginx..."
sudo systemctl reload nginx

echo ""
echo "================================"
echo "DNS Configuration Required"
echo "================================"
echo "Before continuing, please add the following DNS record:"
echo ""
echo "  Type: A"
echo "  Host: agent"
echo "  Value: $(curl -s ifconfig.me)"
echo "  TTL: 3600"
echo ""
echo "This will make agent.drakyn.ai point to this server."
echo ""
read -p "Press Enter once DNS is configured and propagated..."

# Setup SSL certificate
echo "Setting up SSL certificate with Let's Encrypt..."
sudo certbot --nginx -d agent.drakyn.ai

# Setup systemd service
echo "Setting up systemd service..."
sudo cp drakyn-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable drakyn-agent
sudo systemctl start drakyn-agent

# Check service status
echo ""
echo "Checking service status..."
sudo systemctl status drakyn-agent --no-pager

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Your Drakyn Agent is now running at:"
echo "  https://agent.drakyn.ai"
echo ""
echo "Useful commands:"
echo "  - Check status: sudo systemctl status drakyn-agent"
echo "  - View logs: sudo journalctl -u drakyn-agent -f"
echo "  - Restart: sudo systemctl restart drakyn-agent"
echo "  - Stop: sudo systemctl stop drakyn-agent"
echo ""
echo "Before accessing, make sure you've configured Google OAuth:"
echo "  1. Go to https://console.cloud.google.com/"
echo "  2. Create OAuth 2.0 credentials"
echo "  3. Add redirect URI: https://agent.drakyn.ai/auth/callback"
echo "  4. Update .env with Client ID and Secret"
echo "  5. Restart service: sudo systemctl restart drakyn-agent"
echo ""
