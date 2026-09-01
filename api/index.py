"""
Vercel Serverless Entry Point for FastAPI.
Exposes the FastAPI application as `app` under /api routes.
"""

import sys
import os

# Add project root and src directory to Python path
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.server import app

# Handler for Vercel Serverless Functions
handler = app
