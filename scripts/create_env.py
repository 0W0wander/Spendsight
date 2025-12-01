#!/usr/bin/env python3
"""
Helper script to create .env file with random secret key
"""
import secrets
from pathlib import Path

def create_env_file():
    """Create .env file if it doesn't exist."""
    env_file = Path('.env')
    
    if env_file.exists():
        print("[ERROR] .env file already exists!")
        print("   Delete it first if you want to regenerate it.")
        return
    
    # Generate random secret key
    secret_key = secrets.token_hex(32)
    
    env_content = f"""# Spendsight Environment Configuration
# Auto-generated on first setup

# Google Sheets Configuration (Optional - leave empty to skip)
GOOGLE_SHEETS_ID=
GOOGLE_CREDENTIALS_PATH=credentials.json

# Flask Configuration
FLASK_SECRET_KEY={secret_key}
FLASK_ENV=development
FLASK_DEBUG=True

# Upload Configuration
UPLOAD_FOLDER=data/uploads
MAX_CONTENT_LENGTH=16777216

# Port Configuration
PORT=5000
"""
    
    env_file.write_text(env_content)
    print("[OK] Created .env file successfully!")
    print(f"   Secret key: {secret_key[:20]}...")
    print("\nNext steps:")
    print("   1. If using Google Sheets, add your GOOGLE_SHEETS_ID to .env")
    print("   2. Add your credentials.json file to the project root")
    print("   3. Run: python run.py")

if __name__ == '__main__':
    print("Spendsight Environment Setup")
    print("=" * 50)
    create_env_file()

