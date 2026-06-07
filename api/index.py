"""Vercel serverless entry point."""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.app import create_app

app = create_app()
