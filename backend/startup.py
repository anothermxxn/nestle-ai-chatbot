#!/usr/bin/env python3
"""
Startup script for Azure App Service deployment.
This script configures the FastAPI application for production deployment.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for production
os.environ.setdefault("PYTHONPATH", str(backend_dir))

if __name__ == "__main__":
    # Get port from environment (Azure App Service sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    ) 