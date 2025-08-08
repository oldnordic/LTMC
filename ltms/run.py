"""Entry point for LTMC FastAPI server."""

import os
import uvicorn
from ltms.api.main import app


def create_app():
    """Create and return the FastAPI application.
    
    Returns:
        FastAPI application instance
    """
    return app


def main():
    """Main entry point for the LTMC server."""
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "false").lower() == "true"
    
    # Start the server
    uvicorn.run(
        "ltms.api.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()
