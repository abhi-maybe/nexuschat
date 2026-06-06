"""Vercel serverless entry point."""
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

from server.app import create_app

app = create_app()
