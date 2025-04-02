# Update ALLOWED_PAGES
ALLOWED_PAGES = ["contact.html", "login.html", "signup.html", "profile.html"] 

import os
import logging
from dotenv import load_dotenv

load_dotenv()

# Application configuration
APP_NAME = "Small Happiness Club"
HOST = "127.0.0.1"
PORT = 8000
DEBUG = True

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ) 