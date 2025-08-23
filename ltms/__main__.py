#!/usr/bin/env python3
"""
LTMC Package Main Entry Point

Allows running the LTMC MCP server using: python -m ltms
"""

from ltms.main import main
import anyio

if __name__ == "__main__":
    anyio.run(main)