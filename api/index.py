"""
Vercel Serverless Entry Point for Department Cup 2026.
Exports the FastAPI `app` instance for Vercel's @vercel/python builder.
"""

import sys
import os

# Ensure the root project directory is in python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from database.config import setup_database
from main import app

# Ensure database / storage cache is initialized on cold start
try:
    setup_database()
except Exception as e:
    print(f"[Vercel Startup] setup_database error: {e}")

# Vercel looks for `app` at module level
__all__ = ["app"]
