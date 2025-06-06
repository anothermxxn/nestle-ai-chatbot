#!/usr/bin/env python3

import sys
import os

def debug_startup():
    """Debug script to test imports and diagnose startup issues."""
    
    print("=== Startup Debug Script ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"PYTHONPATH env: {os.environ.get('PYTHONPATH', 'Not set')}")
    print()
    
    # Test basic imports
    try:
        print("Testing basic imports...")
        import fastapi
        print("✓ FastAPI imported successfully")
        
        import uvicorn
        print("✓ Uvicorn imported successfully")
        
        import pydantic
        print("✓ Pydantic imported successfully")
        
    except Exception as e:
        print(f"✗ Basic import failed: {e}")
        return False
    
    # Test main application import
    try:
        print("\nTesting main application import...")
        from src.main import app
        print("✓ Main application imported successfully")
        
    except Exception as e:
        print(f"✗ Main application import failed: {e}")
        return False
    
    # Test config imports
    try:
        print("\nTesting config imports...")
        from config import AZURE_OPENAI_CONFIG
        print("✓ Config imported successfully")
        
    except Exception as e:
        print(f"✗ Config import failed: {e}")
        print("Trying backend.config...")
        try:
            from backend.config import AZURE_OPENAI_CONFIG
            print("✓ backend.config imported successfully")
        except Exception as e2:
            print(f"✗ backend.config import also failed: {e2}")
            return False
    
    # Test chat service import
    try:
        print("\nTesting chat service import...")
        from src.chat.services import NestleChatClient
        print("✓ Chat service imported successfully")
        
    except Exception as e:
        print(f"✗ Chat service import failed: {e}")
        return False
    
    print("\n=== All imports successful! ===")
    return True

if __name__ == "__main__":
    success = debug_startup()
    sys.exit(0 if success else 1) 