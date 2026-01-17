# Configuration file for Apartment Hunter backend
# Loads API keys and environment variables

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from gemini.env - for Gemini API key
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / 'gemini.env'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
else:
    print(f"  Warning: Could not find gemini.env at {env_path.resolve()}")

# Google Gemini API Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables!")

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'

# File Upload Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max per image
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGES = 5  # Maximum number of images per analysis

# Reddit Mock Data (no credentials needed)
REDDIT_MOCK_MODE = True  # Using mock data due to Nov 2025 API policy changes

print(f"✅ Config loaded successfully")
print(f"   Gemini API Key: {'Set ✓' if GEMINI_API_KEY else 'Missing ✗'}")
print(f"   Using mock Reddit data: {REDDIT_MOCK_MODE}")
