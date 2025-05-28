#!/usr/bin/env python3
"""
Startup script for Azure App Service
"""
import os
import sys
import subprocess

def main():
    """Main startup function for Azure App Service"""
    # Get the port from environment variable (Azure sets this)
    port = os.environ.get('PORT', '8000')
    
    # Set PYTHONPATH to include the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Start uvicorn server
    cmd = [
        sys.executable, '-m', 'uvicorn',
        'src.main:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', '1'
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == '__main__':
    main() 