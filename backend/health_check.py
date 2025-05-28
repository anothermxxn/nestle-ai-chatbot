#!/usr/bin/env python3
"""
Health check script for Azure App Service
"""
import sys
import os

def check_imports():
    """Check if all required modules can be imported."""
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("✓ Core dependencies imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def check_app():
    """Check if the FastAPI app can be imported."""
    try:
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from src.main import app
        print("✓ FastAPI app imported successfully")
        print(f"✓ App title: {app.title}")
        return True
    except Exception as e:
        print(f"✗ App import error: {e}")
        return False

def main():
    """Run health checks."""
    print("Running health checks...")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    
    checks = [
        check_imports(),
        check_app()
    ]
    
    if all(checks):
        print("\n✓ All health checks passed!")
        return 0
    else:
        print("\n✗ Some health checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 