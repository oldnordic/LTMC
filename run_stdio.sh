#!/bin/bash

# LTMC MCP Server Stdio Transport
# This script runs the stdio transport directly for MCP client integration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting LTMC MCP Server (Stdio Transport)...${NC}"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Set required environment variables
export DB_PATH="${DB_PATH:-ltmc.db}"
export FAISS_INDEX_PATH="${FAISS_INDEX_PATH:-faiss_index}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"

echo -e "${GREEN}✓ Environment configured${NC}"
echo -e "${YELLOW}Ready for MCP protocol on stdin/stdout${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"

# Run the stdio transport
cd "$SCRIPT_DIR"
exec python ltmc_mcp_server.py