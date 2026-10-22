"""Vercel serverless entrypoint.

Vercel's Python runtime looks for a WSGI/ASGI callable named `app` in files
under /api. We simply re-export the Flask app from the project root.
"""

import os
import sys

# Make the project root importable (api/ -> project root)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402,F401
