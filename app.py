"""
PowerBI Data Extractor - Application Launcher
Starts the interactive local server on http://localhost:8600

Usage:
  python app.py
  python app.py --port 8600
"""

import argparse
import os
import sys
import webbrowser
import uvicorn

# Ensure src is on Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from server import app


def main():
    parser = argparse.ArgumentParser(description="Launch PowerBI Data Extractor")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host IP address")
    parser.add_argument("--port", type=int, default=8600, help="Port number")
    parser.add_argument("--no-browser", action="store_true", help="Do not automatically open browser")
    args = parser.parse_args()

    url = f"http://{args.host}:{args.port}"
    print("\n" + "=" * 60)
    print("  [*] PowerBI Data Extractor (Bypass Export Lock)")
    print(f"  [+] Serveur Web demarre sur : {url}")
    print("=" * 60 + "\n")

    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
