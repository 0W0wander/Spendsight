#!/usr/bin/env python3
"""
Spendsight - Personal Budget Tracking
Quick start script to run the application.

When running as a PyInstaller executable, this runs without a console window
and shows a system tray icon instead.
"""
import os
import sys
import platform
import threading
import webbrowser
import logging
from pathlib import Path

# Resolve the base directory:
# - Frozen (PyInstaller): folder containing the exe
# - Source: folder containing this run.py
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
    IS_FROZEN = True
else:
    BASE_DIR = Path(__file__).resolve().parent
    IS_FROZEN = False

# Force working directory to the base directory so bundled deps load cleanly
os.chdir(BASE_DIR)

# Ensure base directory is first on sys.path for imports
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Set up logging to file when running as frozen executable (no console)
if IS_FROZEN:
    log_file = BASE_DIR / 'spendsight.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
        ]
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# Import Flask app
from backend.app import app, needs_setup
from backend.config import Config


def get_url():
    """Get the URL for the app."""
    if needs_setup():
        return f"http://localhost:{Config.PORT}/setup"
    return f"http://localhost:{Config.PORT}"


def open_browser():
    """Open the app in the default web browser."""
    url = get_url()
    logger.info(f"Opening browser: {url}")
    webbrowser.open(url)


def run_flask_server():
    """Run the Flask server in a thread."""
    logger.info(f"Starting Flask server on port {Config.PORT}")
    # Suppress Flask's default logging when running as frozen app
    if IS_FROZEN:
        import logging as flask_logging
        flask_logging.getLogger('werkzeug').setLevel(flask_logging.ERROR)
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=False,  # Must be False for threading
        use_reloader=False,
        threaded=True
    )


def run_with_tray():
    """Run the app with a system tray icon (for frozen executable)."""
    try:
        import pystray
        from PIL import Image
    except ImportError:
        logger.error("pystray or Pillow not installed, falling back to console mode")
        run_console_mode()
        return
    
    # Find icon file - check multiple locations
    # Prefer ICO format for Windows system tray (better compatibility)
    # For PyInstaller bundles, check sys._MEIPASS first (where bundled data is extracted)
    icon_path = None
    
    # Build list of paths to check
    possible_paths = []
    
    # PyInstaller bundled data directory (when running as frozen exe)
    if hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)
        possible_paths.extend([
            meipass / 'spendsighticon.ico',
            meipass / 'spendsighticon.png',
            meipass / 'frontend' / 'static' / 'spendsighticon.png',
        ])
    
    # Also check relative to executable/script directory
    possible_paths.extend([
        BASE_DIR / 'spendsighticon.ico',  # ICO preferred for Windows
        BASE_DIR / 'spendsighticon.png',
        BASE_DIR / 'frontend' / 'static' / 'spendsighticon.png',
    ])
    
    for path in possible_paths:
        if path.exists():
            icon_path = path
            logger.info(f"Found icon file: {icon_path}")
            break
    
    # Create icon image
    if icon_path:
        try:
            icon_image = Image.open(icon_path)
            logger.info(f"Loaded icon: size={icon_image.size}, mode={icon_image.mode}")
            
            # Convert to RGBA for proper transparency support
            if icon_image.mode != 'RGBA':
                icon_image = icon_image.convert('RGBA')
            
            # For ICO files, PIL loads them at their largest size, resize for tray
            # Windows system tray typically uses 16x16 or 32x32
            if icon_image.size[0] > 64:
                icon_image = icon_image.resize((64, 64), Image.Resampling.LANCZOS)
                logger.info(f"Resized icon to 64x64 for system tray")
            
            logger.info(f"Loaded tray icon from: {icon_path}")
        except Exception as e:
            logger.warning(f"Could not load icon from {icon_path}: {e}, using generated icon")
            icon_image = create_default_icon()
    else:
        logger.info("Icon file not found, using generated icon")
        icon_image = create_default_icon()
    
    # Start Flask server in background thread
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    import time
    time.sleep(1.5)
    
    # Auto-open browser
    open_browser()
    
    def on_open(icon, item):
        """Open browser when clicked."""
        open_browser()
    
    def on_quit(icon, item):
        """Quit the application."""
        logger.info("Shutting down Spendsight...")
        icon.stop()
        # Force exit since Flask server is in a daemon thread
        os._exit(0)
    
    # Create system tray menu
    menu = pystray.Menu(
        pystray.MenuItem("Open Spendsight", on_open, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit)
    )
    
    # Create and run the system tray icon
    icon = pystray.Icon(
        "Spendsight",
        icon_image,
        "Spendsight - Budget Tracker",
        menu
    )
    
    logger.info("System tray icon created, app is running")
    icon.run()


def create_default_icon():
    """Create a simple default icon if the icon file is not found."""
    from PIL import Image, ImageDraw
    
    # Create a 32x32 image with a green circle (matching the mint accent color)
    size = 32
    image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw a filled circle with mint green color (#4ade80)
    margin = 2
    draw.ellipse(
        [margin, margin, size - margin - 1, size - margin - 1],
        fill=(74, 222, 128, 255)  # Mint green
    )
    
    # Draw a simple "$" symbol in the center
    try:
        draw.text((size//2 - 4, size//2 - 6), "$", fill=(10, 10, 12, 255))
    except:
        pass
    
    return image


def run_console_mode():
    """Run in traditional console mode (for development or fallback)."""
    print("=" * 60)
    print("[*] Starting Spendsight...")
    print("=" * 60)
    
    # Check if setup is needed
    if needs_setup():
        print("\n[!] First time setup detected!")
        print(f"[>] Please open: http://localhost:{Config.PORT}/setup")
        print("    Follow the setup wizard to configure Spendsight\n")
    else:
        print("\n[+] Configuration loaded successfully!")
        print(f"[>] Open: http://localhost:{Config.PORT}")
    
    print(f"\n[OK] Server running at: http://localhost:{Config.PORT}")
    print("[OK] Press CTRL+C to stop the server\n")
    print("=" * 60)
    
    # Auto-open browser in console mode too
    threading.Timer(1.5, open_browser).start()
    
    # Disable reloader on Windows to avoid socket issues
    use_reloader = Config.DEBUG and platform.system() != 'Windows'
    
    app.run(
        host='0.0.0.0',
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=use_reloader
    )


if __name__ == '__main__':
    logger.info("Spendsight starting...")
    
    if IS_FROZEN:
        # Running as PyInstaller executable - use system tray
        run_with_tray()
    else:
        # Running from source - use console mode
        run_console_mode()
