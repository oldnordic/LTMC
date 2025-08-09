#!/usr/bin/env python3
"""LTMC Server Entry Point

This script starts the LTMC (Long-Term Memory Core) FastAPI server.
"""

import os
import sys
import uvicorn

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ltms.api.main import app


def main():
    """Main entry point for the LTMC server."""
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    print(f"Starting LTMC server on {host}:{port}")
    print(f"Database: {os.getenv('DB_PATH', 'ltmc.db')}")
    print(f"FAISS Index: {os.getenv('FAISS_INDEX_PATH', 'faiss_index')}")
    print(f"Reload mode: {reload}")
    print("Press Ctrl+C to stop the server")
    
    # Start the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
