#!/usr/bin/env python3
"""
Startup script for Azure App Service
"""
import os
import sys
import subprocess
from pathlib import Path

def find_app_directory():
    """Find the directory containing app.py and src/"""
    current_dir = Path.cwd()
    
    # Check current directory first
    if (current_dir / "app.py").exists() and (current_dir / "src").exists():
        return current_dir
    
    # Check if we're in a parent directory and need to go into backend/
    backend_dir = current_dir / "backend"
    if backend_dir.exists() and (backend_dir / "app.py").exists() and (backend_dir / "src").exists():
        return backend_dir
    
    # Check subdirectories for the app files
    for subdir in current_dir.iterdir():
        if subdir.is_dir():
            if (subdir / "app.py").exists() and (subdir / "src").exists():
                return subdir
    
    return current_dir  # fallback to current directory

def main():
    """Main startup function for Azure App Service"""
    # Get the port from environment variable (Azure sets this)
    port = os.environ.get('PORT', '8000')
    
    # Find the correct app directory
    app_dir = find_app_directory()
    
    print(f"Starting server...")
    print(f"Current working directory: {os.getcwd()}")
    print(f"App directory found: {app_dir}")
    print(f"Port: {port}")
    
    # Change to app directory
    os.chdir(app_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Set PYTHONPATH to include the app directory
    app_dir_str = str(app_dir)
    if app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)
    
    # Set PYTHONPATH environment variable as well
    pythonpath = os.environ.get('PYTHONPATH', '')
    if app_dir_str not in pythonpath:
        os.environ['PYTHONPATH'] = f"{app_dir_str}:{pythonpath}" if pythonpath else app_dir_str
    
    print(f"Python path: {sys.path[:3]}...")
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Verify files exist
    if not (Path("app.py").exists()):
        print("ERROR: app.py not found in current directory!")
        print("Files in current directory:")
        for item in Path(".").iterdir():
            print(f"  {item.name}")
        sys.exit(1)
    
    if not (Path("src").exists()):
        print("ERROR: src directory not found!")
        sys.exit(1)
    
    # Start uvicorn server
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'src.main:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', '1'
    ]
    
    print(f"Executing command: {' '.join(cmd)}")
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 