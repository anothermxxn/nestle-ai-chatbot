#!/usr/bin/env python3
"""
Azure-specific startup script that handles file location detection
"""
import os
import sys
import subprocess
from pathlib import Path

def find_app_files():
    """Find app.py and src directory in Azure's deployment structure"""
    print("=== Azure App Service Python Startup ===")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Azure deploys files to /home/site/wwwroot
    # The working directory should already be /home/site/wwwroot
    search_paths = [
        Path.cwd(),
        Path("/home/site/wwwroot"),
    ]
    
    print(f"Searching in paths: {[str(p) for p in search_paths]}")
    
    for path in search_paths:
        print(f"\nChecking: {path}")
        if not path.exists():
            print(f"  ✗ Path does not exist")
            continue
            
        print(f"  ✓ Path exists")
        try:
            files = [f.name for f in path.iterdir() if f.is_file()][:10]
            print(f"  Files: {files}")
        except PermissionError:
            print(f"  ⚠ Permission denied listing files")
            continue
        
        app_py = path / "app.py"
        src_dir = path / "src"
        
        if app_py.exists():
            print(f"  ✓ Found app.py")
            if src_dir.exists():
                print(f"  ✓ Found src directory")
                return path
            else:
                print(f"  ⚠ No src directory, but app.py exists - will try anyway")
                return path
        else:
            print(f"  ✗ No app.py found")
    
    # If not found in standard paths, search common locations
    print("\n=== Searching common locations for app.py ===")
    search_locations = ["/home/site/wwwroot", "/home", "/tmp"]
    
    for root in search_locations:
        try:
            root_path = Path(root)
            if root_path.exists():
                for app_file in root_path.rglob("app.py"):
                    print(f"Found app.py at: {app_file}")
                    return app_file.parent
        except (PermissionError, OSError) as e:
            print(f"  ⚠ Error searching {root}: {e}")
            continue
    
    return None

def start_application(app_dir):
    """Start the FastAPI application"""
    print(f"\n=== Starting application from {app_dir} ===")
    
    # Change to app directory
    os.chdir(app_dir)
    print(f"Changed to directory: {os.getcwd()}")
    
    # Set up Python path
    app_dir_str = str(app_dir)
    if app_dir_str not in sys.path:
        sys.path.insert(0, app_dir_str)
    
    # Set PYTHONPATH environment variable
    pythonpath = os.environ.get('PYTHONPATH', '')
    if app_dir_str not in pythonpath:
        os.environ['PYTHONPATH'] = f"{app_dir_str}:{pythonpath}" if pythonpath else app_dir_str
    
    print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
    
    # Get port from environment
    port = os.environ.get('PORT', '8000')
    print(f"Port: {port}")
    
    # Try to start with app.py first
    app_py = Path("app.py")
    if app_py.exists():
        print("Starting with app.py...")
        try:
            subprocess.run([sys.executable, "app.py"], check=True)
            return
        except subprocess.CalledProcessError as e:
            print(f"app.py failed: {e}")
    
    # Fallback to direct uvicorn
    src_main = Path("src/main.py")
    if src_main.exists():
        print("Fallback: Starting with uvicorn directly...")
        cmd = [
            sys.executable, '-m', 'uvicorn',
            'src.main:app',
            '--host', '0.0.0.0',
            '--port', port
        ]
        print(f"Command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    else:
        raise FileNotFoundError("Neither app.py nor src/main.py could be started")

def main():
    """Main function"""
    try:
        app_dir = find_app_files()
        if app_dir is None:
            print("ERROR: Could not find app.py in any location")
            print("\n=== Debug Information ===")
            print(f"Current working directory: {os.getcwd()}")
            print("Environment variables:")
            for key in ['HOME', 'PYTHONPATH', 'PORT', 'WEBSITE_SITE_NAME']:
                print(f"  {key}: {os.environ.get(key, 'Not set')}")
            
            print("\nDirectory contents:")
            try:
                for item in Path.cwd().iterdir():
                    print(f"  {item}")
            except Exception as e:
                print(f"  Error listing directory: {e}")
            
            sys.exit(1)
        
        start_application(app_dir)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 