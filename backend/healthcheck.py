#!/usr/bin/env python3

import sys
import httpx

def health_check():
    """
    Health check script for Docker container.
    Tests the /health endpoint and exits with code 0 if healthy, 1 if not.
    """
    try:
        response = httpx.get("http://localhost:8000/health", timeout=10)
        if response.status_code == 200:
            print("Health check passed")
            sys.exit(0)
        else:
            print(f"Health check failed with status code: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Health check failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    health_check() 