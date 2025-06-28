#!/usr/bin/env python3
"""
Main startup script for the Supervity AP Agent.
This script sets up the path and runs the FastAPI application using uvicorn.
"""
import sys
import os
import uvicorn

def main():
    """Configures path and starts the Uvicorn server."""
    # Add the 'src' directory to the Python path
    # This allows us to import 'app' as a top-level module
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

    print("🚀 Starting Supervity AP Agent API server...")
    print("API Documentation will be available at: http://127.0.0.1:8000/docs")
    print("API Root endpoint: http://127.0.0.1:8000/")
    print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        "app.main:app",        # The import string for the application
        host="127.0.0.1",
        port=8000,
        reload=True,           # Enable auto-reloading for development
        reload_dirs=["src"],   # Watch the 'src' directory for changes
        log_level="info"
    )

if __name__ == "__main__":
    main() 