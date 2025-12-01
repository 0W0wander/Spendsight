"""Configuration management for Spendsight."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    """Application configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    ENV = os.getenv('FLASK_ENV', 'development')
    
    # Upload settings
    UPLOAD_FOLDER = BASE_DIR / os.getenv('UPLOAD_FOLDER', 'data/uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Google Sheets
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
    GOOGLE_CREDENTIALS_PATH = BASE_DIR / os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    # Port
    PORT = int(os.getenv('PORT', 5000))
    
    # Ensure directories exist
    @staticmethod
    def init_app():
        """Initialize application directories."""
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'data').mkdir(exist_ok=True)

