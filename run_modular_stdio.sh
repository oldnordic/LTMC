#!/bin/bash
# LTMC MCP Server Startup Script
# ============================
#
# Starts the LTMC MCP server with proper stdio transport for Claude Code.
# This script handles the environment setup and launches the FastMCP server.

# Set error handling
set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Ensure Python path includes the project root
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Set up logging to stderr only (never stdout - it corrupts stdio transport)
export PYTHONUNBUFFERED=1

# Execute the LTMC MCP server with consolidated tools (graceful degradation)
exec python3 ltms/mcp_server.py