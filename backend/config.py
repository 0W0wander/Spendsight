import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    UPLOAD_FOLDER = BASE_DIR / os.getenv('UPLOAD_FOLDER', 'data/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'csv'}
    
    GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
    GOOGLE_CREDENTIALS_PATH = BASE_DIR / os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
    
    PORT = int(os.getenv('PORT', 5000))
    
    @staticmethod
    def init_app():
        Config.UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
        (BASE_DIR / 'data').mkdir(exist_ok=True)
    
    @classmethod
    def reload(cls):
        load_dotenv(BASE_DIR / ".env", override=True)
        cls.SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key')
        cls.GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '')
        cls.init_app()
