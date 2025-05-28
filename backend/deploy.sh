#!/bin/bash

# Azure App Service deployment script for Python

echo "Starting deployment..."

# Ensure we're in the right directory
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Install Python dependencies
if [ -f requirements.txt ]; then
    echo "Installing Python dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
else
    echo "requirements.txt not found!"
    exit 1
fi

# Verify critical files exist
if [ ! -f app.py ]; then
    echo "ERROR: app.py not found!"
    exit 1
fi

if [ ! -f startup.py ]; then
    echo "ERROR: startup.py not found!"
    exit 1
fi

if [ ! -d src ]; then
    echo "ERROR: src directory not found!"
    exit 1
fi

echo "Deployment completed successfully!"
echo "Files ready for startup:"
ls -la *.py 