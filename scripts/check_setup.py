#!/usr/bin/env python3
"""
Check if Spendsight is properly set up
"""
from pathlib import Path
import sys

def check_file(path, name, required=True):
    """Check if a file exists."""
    if Path(path).exists():
        print(f"[OK] {name} found")
        return True
    else:
        icon = "[X]" if required else "[!]"
        status = "REQUIRED" if required else "OPTIONAL"
        print(f"{icon} {name} not found ({status})")
        return not required

def check_setup():
    """Check if setup is complete."""
    print("Checking Spendsight Setup")
    print("=" * 50)
    
    all_good = True
    
    # Check Python files
    all_good &= check_file("backend/app.py", "Backend app")
    all_good &= check_file("backend/config.py", "Config file")
    all_good &= check_file("requirements.txt", "Requirements file")
    all_good &= check_file("run.py", "Run script")
    
    print("\nChecking packages...")
    all_good &= check_file("backend/parsers/chase_parser.py", "Chase parser")
    all_good &= check_file("backend/parsers/discover_parser.py", "Discover parser")
    all_good &= check_file("backend/sheets/sheets_client.py", "Sheets client")
    all_good &= check_file("backend/analytics/categorizer.py", "Categorizer")
    all_good &= check_file("backend/analytics/insights.py", "Insights generator")
    
    print("\nChecking frontend...")
    all_good &= check_file("frontend/templates/base.html", "Base template")
    all_good &= check_file("frontend/templates/index.html", "Index page")
    all_good &= check_file("frontend/static/css/style.css", "Stylesheet")
    
    print("\nChecking configuration...")
    env_exists = check_file(".env", "Environment file (.env)", required=False)
    if not env_exists:
        print("   -> Run: python scripts/create_env.py")
    
    creds_exists = check_file("credentials.json", "Google credentials", required=False)
    if not creds_exists:
        print("   -> See SETUP.md for Google Sheets setup")
    
    print("\nChecking directories...")
    data_dir = Path("data")
    if not data_dir.exists():
        print("[!] data/ directory will be created on first run")
    else:
        print("[OK] data/ directory exists")
    
    uploads_dir = Path("data/uploads")
    if not uploads_dir.exists():
        print("[!] data/uploads/ directory will be created on first run")
    else:
        print("[OK] data/uploads/ directory exists")
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("[OK] All required files are present!")
        print("\nNext steps:")
        if not env_exists:
            print("   1. Run: python scripts/create_env.py")
            print("   2. (Optional) Set up Google Sheets (see SETUP.md)")
            print("   3. Run: python run.py")
        else:
            print("   1. (Optional) Set up Google Sheets (see SETUP.md)")
            print("   2. Run: python run.py")
    else:
        print("[ERROR] Some required files are missing!")
        print("   Please check the installation.")
        sys.exit(1)

if __name__ == '__main__':
    check_setup()

