import os
from datetime import timedelta

# Database settings
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'fabric.db')}"
USERS_DATABASE_URL = DATABASE_URL
DEFECTS_DATABASE_URL = DATABASE_URL

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Upload settings
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# Model settings
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # goes from app/config.py -> app -> backend
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # goes from backend -> FYP Final (project root)
MEDIUM_MODEL = os.path.join(PROJECT_ROOT, "medium.pt")
NANO_MODEL = os.path.join(PROJECT_ROOT, "nano.pt")

# ESP32 settings
ESP32_URL = os.getenv("ESP32_URL", "http://172.22.115.216:81/stream")

# Class names for defects
CLASS_NAMES = ['hole', 'knot', 'line', 'stain']
CLASS_COLORS = {
    'hole': (0, 0, 255),      # Red (BGR)
    'knot': (0, 140, 255),    # Orange (BGR)
    'line': (0, 255, 0),      # Green (BGR)
    'stain': (128, 0, 128)    # Purple (BGR)
}

# Detection settings
CONF_THRESHOLD = 0.1
