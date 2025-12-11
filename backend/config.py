"""Configuration management for Spendsight."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Base directory
# When running from source: project root (two levels up from this file)
# When running as a PyInstaller executable: directory containing the .exe
if getattr(sys, "frozen", False):
    # PyInstaller onefile/onedir executable
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env in the base directory
load_dotenv(BASE_DIR / ".env")

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
    
    @classmethod
    def reload(cls):
        """Reload configuration from .env file without server restart.
        
        This is useful after setup wizard writes a new .env file,
        allowing the app to pick up the new config immediately.
        """
        # Reload environment variables from .env
        load_dotenv(BASE_DIR / ".env", override=True)
        
        # Update class attributes with new values
        cls.SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
        cls.DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        cls.ENV = os.getenv('FLASK_ENV', 'development')
        cls.UPLOAD_FOLDER = BASE_DIR / os.getenv('UPLOAD_FOLDER', 'data/uploads')
        cls.MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
        cls.GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
        cls.GOOGLE_CREDENTIALS_PATH = BASE_DIR / os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        cls.PORT = int(os.getenv('PORT', 5000))
        
        # Ensure directories exist
        cls.init_app()
        
        return True

