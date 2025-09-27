"""
Configuration settings for the Satellite Image Predictor application.
Loads environment variables and defines various paths and constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY', 'a_default_secret_key_if_not_set')

# Define paths (relative to project root)
USER_UPLOADS_DIR = 'data/user_uploads'
PREDICTIONS_DIR = 'data/predictions'
OUTPUT_VIDEO_DIR = 'data/output'
LOGS_DIR = 'logs'

# Other configuration options
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
VIDEO_FPS = 10