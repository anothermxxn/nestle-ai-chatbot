"""
Alternative entry point for Azure App Service
"""
import os
import sys
from pathlib import Path

def find_app_directory():
    """Find the directory containing src/ and config/"""
    current_dir = Path.cwd()
    
    # Check current directory first
    if (current_dir / "src").exists() and (current_dir / "config").exists():
        return current_dir
    
    # Check if we're in a parent directory and need to go into backend/
    backend_dir = current_dir / "backend"
    if backend_dir.exists() and (backend_dir / "src").exists() and (backend_dir / "config").exists():
        return backend_dir
    
    # Check subdirectories for the app files
    for subdir in current_dir.iterdir():
        if subdir.is_dir():
            if (subdir / "src").exists() and (subdir / "config").exists():
                return subdir
    
    return current_dir  # fallback to current directory

def setup_python_path():
    """Setup Python path for imports"""
    # Find the correct app directory
    app_dir = find_app_directory()
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"App directory found: {app_dir}")
    
    # Change to app directory if needed
    if app_dir != Path.cwd():
        os.chdir(app_dir)
        print(f"Changed to directory: {os.getcwd()}")
    
    # Add the app directory to Python path
    app_dir_str = str(app_dir)
    
    if app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)
    
    # Set PYTHONPATH environment variable
    pythonpath = os.environ.get('PYTHONPATH', '')
    if app_dir_str not in pythonpath:
        os.environ['PYTHONPATH'] = f"{app_dir_str}:{pythonpath}" if pythonpath else app_dir_str
    
    print(f"Python path setup complete")
    print(f"App directory: {app_dir_str}")
    print(f"Python sys.path: {sys.path[:3]}...")
    
    # Verify required directories exist
    if not (Path("src").exists()):
        print("ERROR: src directory not found!")
        print("Files in current directory:")
        for item in Path(".").iterdir():
            print(f"  {item.name}")
        raise FileNotFoundError("src directory not found")
    
    if not (Path("config").exists()):
        print("ERROR: config directory not found!")
        raise FileNotFoundError("config directory not found")

# Setup path before importing
setup_python_path()

try:
    # Import the FastAPI app
    from src.main import app
    print("✓ Successfully imported FastAPI app")
except ImportError as e:
    print(f"✗ Failed to import FastAPI app: {e}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Files in current directory: {os.listdir('.')}")
    if os.path.exists('src'):
        print(f"Files in src directory: {os.listdir('src')}")
    raise

# This is what Azure will import
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting uvicorn server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 