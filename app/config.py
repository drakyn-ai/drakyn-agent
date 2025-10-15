"""Application configuration."""
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic API
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# Security
SECRET_KEY = os.getenv("SECRET_KEY")
ALLOWED_EMAIL = os.getenv("ALLOWED_EMAIL")

# Server
BASE_URL = os.getenv("BASE_URL", "https://agent.drakyn.ai")
PORT = int(os.getenv("PORT", "8000"))

# OAuth
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"
REDIRECT_URI = f"{BASE_URL}/auth/callback"

# Database
DATABASE_PATH = "data/conversations.db"
