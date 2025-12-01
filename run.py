#!/usr/bin/env python3
"""
Spendsight - Personal Budget Tracking
Quick start script to run the application.
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the Flask app
from backend.app import app, needs_setup
from backend.config import Config

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Spendsight...")
    print("=" * 60)
    
    # Check if setup is needed
    if needs_setup():
        print("\n⚙️  First time setup detected!")
        print(f"📱 Please open: http://localhost:{Config.PORT}/setup")
        print("   Follow the setup wizard to configure Spendsight\n")
    else:
        print("\n✅ Configuration loaded successfully!")
        print(f"📱 Open: http://localhost:{Config.PORT}")
    
    print(f"\n[OK] Server running at: http://localhost:{Config.PORT}")
    print("[OK] Press CTRL+C to stop the server\n")
    print("=" * 60)
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG
    )

