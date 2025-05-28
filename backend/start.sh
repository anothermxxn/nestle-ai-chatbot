#!/bin/bash

echo "=== Azure App Service Startup Script ==="
echo "Current directory: $(pwd)"
echo "Files in current directory:"
ls -la

# Function to start the app
start_app() {
    local dir=$1
    echo "Attempting to start app from directory: $dir"
    cd "$dir"
    echo "Changed to: $(pwd)"
    echo "Files in this directory:"
    ls -la
    
    if [ -f "app.py" ] && [ -d "src" ]; then
        echo "Found app.py and src directory. Starting application..."
        python app.py
        return $?
    else
        echo "app.py or src directory not found in $dir"
        return 1
    fi
}

# Try current directory first
if start_app "$(pwd)"; then
    exit 0
fi

# Try backend subdirectory
if [ -d "backend" ]; then
    if start_app "$(pwd)/backend"; then
        exit 0
    fi
fi

# Try any subdirectory that has app.py and src
for dir in */; do
    if [ -f "$dir/app.py" ] && [ -d "$dir/src" ]; then
        if start_app "$(pwd)/$dir"; then
            exit 0
        fi
    fi
done

echo "ERROR: Could not find app.py and src directory in any location"
echo "Available directories:"
find . -name "app.py" -o -name "src" -type d
exit 1 