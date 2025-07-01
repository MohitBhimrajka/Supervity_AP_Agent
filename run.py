#!/usr/bin/env python3
"""
Main startup script for the Supervity AP Command Center.
This script sets up the path and runs the FastAPI application using uvicorn.
It can run in 'development' (default) or 'production' mode.
"""
import sys
import os
import uvicorn

def main():
    """Configures path and starts the Uvicorn server."""
    # Add the 'src' directory to the Python path
    # This allows us to import 'app' as a top-level module
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

    # Check for production mode (for Docker)
    is_production = os.getenv("APP_ENV") == "production"
    host = "0.0.0.0" if is_production else "127.0.0.1"
    port = 8000
    
    print("🚀 Starting Supervity AP Command Center API server...")
    if is_production:
        print("   Mode: Production")
    else:
        print("   Mode: Development (auto-reloading enabled)")
    
    print(f"API Documentation will be available at: http://{host}:{port}/docs")
    print(f"API Root endpoint: http://{host}:{port}/")
    print("\nPress Ctrl+C to stop the server")

    uvicorn.run(
        "app.main:app",        # The import string for the application
        host=host,
        port=port,
        reload=not is_production,
        reload_dirs=["src"] if not is_production else None,
        log_level="info"
    )

if __name__ == "__main__":
    main() 