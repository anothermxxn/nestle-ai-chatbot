#!/bin/bash

echo "=== Azure App Service Startup Script ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Azure deploys files to /home/site/wwwroot
# Check the standard Azure deployment location
AZURE_PATHS=(
    "$(pwd)"
    "/home/site/wwwroot"
)

# Function to start the app
start_app() {
    local dir=$1
    echo "=== Attempting to start app from directory: $dir ==="
    
    if [ ! -d "$dir" ]; then
        echo "Directory $dir does not exist"
        return 1
    fi
    
    cd "$dir"
    echo "Changed to: $(pwd)"
    echo "Files in this directory:"
    ls -la
    
    if [ -f "app.py" ] && [ -d "src" ]; then
        echo "✓ Found app.py and src directory. Starting application..."
        export PYTHONPATH="$dir:$PYTHONPATH"
        python app.py
        return $?
    elif [ -f "app.py" ]; then
        echo "✓ Found app.py but no src directory. Trying anyway..."
        export PYTHONPATH="$dir:$PYTHONPATH"
        python app.py
        return $?
    else
        echo "✗ app.py not found in $dir"
        return 1
    fi
}

# Try each possible path
for path in "${AZURE_PATHS[@]}"; do
    echo "Checking path: $path"
    if start_app "$path"; then
        echo "✓ Successfully started from $path"
        exit 0
    fi
done

# If direct paths don't work, search for app.py
echo "=== Searching for app.py in common locations ==="
for search_dir in "/home/site/wwwroot" "/home" "/tmp"; do
    if [ -d "$search_dir" ]; then
        echo "Searching in: $search_dir"
        find "$search_dir" -name "app.py" -type f 2>/dev/null | while read -r app_file; do
            app_dir=$(dirname "$app_file")
            echo "Found app.py at: $app_file (directory: $app_dir)"
            if start_app "$app_dir"; then
                echo "✓ Successfully started from $app_dir"
                exit 0
            fi
        done
    fi
done

echo "=== ERROR: Could not find or start app.py ==="
echo "Debug information:"
echo "Current working directory: $(pwd)"
echo "Environment variables:"
echo "  HOME: ${HOME:-Not set}"
echo "  PORT: ${PORT:-Not set}"
echo "  WEBSITE_SITE_NAME: ${WEBSITE_SITE_NAME:-Not set}"

echo "Available files and directories in /home/site/wwwroot:"
if [ -d "/home/site/wwwroot" ]; then
    ls -la /home/site/wwwroot
else
    echo "  /home/site/wwwroot does not exist"
fi

exit 1 