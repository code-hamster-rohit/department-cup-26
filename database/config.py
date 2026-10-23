"""
Configuration and Database initialization for Department Cup Scoreboard.
Provides dual persistence: fast atomic local JSON store + live MongoDB Atlas sync.
Also manages Google OAuth 2.0 credentials and session configuration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI: str = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI", "")
DATABASE_NAME: str = os.getenv("DATABASE_NAME", "department_cup")
SECRET_KEY: str = os.getenv("SECRET_KEY", "department-cup-iitr-2026-secret-key-super-secure")

# Domain detection (Local vs Vercel / Production)
BASE_URL: str = os.getenv("BASE_URL") or (f"https://{os.getenv('VERCEL_URL')}" if os.getenv("VERCEL_URL") else "http://localhost:8000")

# Google OAuth 2.0 credentials
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI_AUDIENCE: str = os.getenv("GOOGLE_REDIRECT_URI_AUDIENCE", f"{BASE_URL.rstrip('/')}/")
GOOGLE_REDIRECT_URI_ADMIN: str = os.getenv("GOOGLE_REDIRECT_URI_ADMIN", f"{BASE_URL.rstrip('/')}/admin")

# Storage & Mongo engine
from database.storage import init_storage
from database.mongo import get_mongo_client

def setup_database():
    """Initializes local storage cache and validates MongoDB connection."""
    init_storage()
    if MONGO_URI:
        client = get_mongo_client()
        if client:
            print("[Storage] MongoDB Atlas connected. Dual-persistence active for database:", DATABASE_NAME)
        else:
            print("[Storage] Warning: MongoDB connection failed. Falling back to atomic local store.")
    else:
        print("[Storage] Using high-performance local persistent store (matches.json).")
