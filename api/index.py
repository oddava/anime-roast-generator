"""Vercel serverless entry point for Anime Roast Generator API."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the FastAPI app from backend
from backend.main import app
from mangum import Mangum

# Create handler for AWS Lambda/Vercel
handler = Mangum(app, lifespan="off")
