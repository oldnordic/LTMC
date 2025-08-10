#!/bin/bash

# LTMC Modular FastMCP Server - Stdio Transport
# =============================================
# 
# Direct stdio transport for MCP clients (Cursor, MCP Inspector, etc.)
# Uses the new modular FastMCP architecture

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"
SERVER_SCRIPT="ltmc_mcp_server/main.py"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}" >&2
    echo -e "${YELLOW}Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}" >&2
    exit 1
fi

# Check if server script exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo -e "${RED}❌ Server script not found: $SERVER_SCRIPT${NC}" >&2
    exit 1
fi

# Activate virtual environment silently
source "$VENV_PATH/bin/activate"

# Load environment variables if .env exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Set required environment variables with defaults
export DB_PATH="${DB_PATH:-ltmc.db}"
export LTMC_DATA_DIR="${LTMC_DATA_DIR:-$(pwd)/data}"
export FAISS_INDEX_PATH="${FAISS_INDEX_PATH:-$LTMC_DATA_DIR/faiss_index}"
export LOG_LEVEL="${LOG_LEVEL:-WARNING}"  # Less verbose for stdio
export REDIS_ENABLED="${REDIS_ENABLED:-true}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6382}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-ltmc_cache_2025}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
export NEO4J_USER="${NEO4J_USER:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-kwe_password}"

# Create data directory if needed
mkdir -p "$LTMC_DATA_DIR" 2>/dev/null

# Quick dependency check (silent)
if ! python -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null; then
    echo -e "${RED}❌ MCP SDK not available. Please install: pip install mcp${NC}" >&2
    exit 1
fi

# For debug mode, show configuration
if [ "$1" = "--debug" ] || [ "$1" = "-d" ]; then
    echo -e "${BLUE}🔧 LTMC Modular FastMCP Server - Stdio Mode${NC}" >&2
    echo -e "${BLUE}============================================${NC}" >&2
    echo -e "${GREEN}✓ Server: $SERVER_SCRIPT${NC}" >&2
    echo -e "${GREEN}✓ Database: $DB_PATH${NC}" >&2
    echo -e "${GREEN}✓ Data dir: $LTMC_DATA_DIR${NC}" >&2
    echo -e "${GREEN}✓ Log level: $LOG_LEVEL${NC}" >&2
    echo -e "${GREEN}✓ Redis: $REDIS_HOST:$REDIS_PORT${NC}" >&2
    echo -e "${YELLOW}Starting stdio transport...${NC}" >&2
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}" >&2
fi

# Change to script directory
cd "$SCRIPT_DIR"

# Execute the modular FastMCP server with stdio transport
# The server's main.py handles transport selection automatically
exec python "$SERVER_SCRIPT"