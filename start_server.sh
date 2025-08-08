#!/bin/bash

# LTMC MCP Server Startup Script - Dual Transport (Stdio + HTTP)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/ltmc_mcp.pid"
HTTP_PID_FILE="$SCRIPT_DIR/ltmc_http.pid"
LOG_FILE="$SCRIPT_DIR/logs/ltmc_mcp.log"
HTTP_LOG_FILE="$SCRIPT_DIR/logs/ltmc_http.log"
VENV_PATH="$SCRIPT_DIR/venv"
HTTP_PORT="${HTTP_PORT:-5050}"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo -e "${BLUE}Starting LTMC MCP Server (Dual Transport)...${NC}"

# Check if servers are already running
if [ -f "$PID_FILE" ] || [ -f "$HTTP_PID_FILE" ]; then
    echo -e "${RED}Server processes already running. Stopping first...${NC}"
    bash "$SCRIPT_DIR/stop_server.sh"
    sleep 2
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check if required packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python -c "import mcp" 2>/dev/null; then
    echo -e "${RED}MCP package not found. Installing...${NC}"
    pip install mcp
fi

if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${RED}FastAPI package not found. Installing...${NC}"
    pip install -r requirements.txt
fi

# Check Redis connection (required for orchestration)
echo -e "${YELLOW}Checking LTMC Redis connection (port 6381)...${NC}"
if ! python -c "import redis; r=redis.Redis(host='localhost', port=6381, decode_responses=True, password='ltmc_cache_2025'); r.ping()" 2>/dev/null; then
    echo -e "${YELLOW}Warning: LTMC Redis not available on port 6381. Starting Redis service...${NC}"
    ./redis_control.sh start
    
    # Wait for Redis to start and verify
    sleep 3
    if python -c "import redis; r=redis.Redis(host='localhost', port=6381, decode_responses=True, password='ltmc_cache_2025'); r.ping()" 2>/dev/null; then
        echo -e "${GREEN}✓ LTMC Redis started successfully${NC}"
    else
        echo -e "${YELLOW}Warning: Redis failed to start. Orchestration will be disabled.${NC}"
    fi
else
    echo -e "${GREEN}✓ LTMC Redis connection successful${NC}"
fi

# Set environment variables for LTMC
export DB_PATH="${DB_PATH:-ltmc.db}"
export FAISS_INDEX_PATH="${FAISS_INDEX_PATH:-faiss_index}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export HTTP_HOST="${HTTP_HOST:-localhost}"
export HTTP_PORT="$HTTP_PORT"

# Set orchestration environment variables
export ORCHESTRATION_MODE="${ORCHESTRATION_MODE:-basic}"
export REDIS_ENABLED="${REDIS_ENABLED:-true}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6381}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-ltmc_cache_2025}"
export CACHE_ENABLED="${CACHE_ENABLED:-true}"
export BUFFER_ENABLED="${BUFFER_ENABLED:-true}"
export SESSION_STATE_ENABLED="${SESSION_STATE_ENABLED:-true}"

echo -e "${YELLOW}Environment variables:${NC}"
echo -e "  DB_PATH: $DB_PATH"
echo -e "  FAISS_INDEX_PATH: $FAISS_INDEX_PATH"
echo -e "  LOG_LEVEL: $LOG_LEVEL"
echo -e "  HTTP_HOST: $HTTP_HOST"
echo -e "  HTTP_PORT: $HTTP_PORT"
echo -e "  ORCHESTRATION_MODE: $ORCHESTRATION_MODE"
echo -e "  REDIS_ENABLED: $REDIS_ENABLED"
echo -e "  REDIS_PORT: $REDIS_PORT"

# Start the HTTP transport server
echo -e "${YELLOW}Starting HTTP transport server...${NC}"
cd "$SCRIPT_DIR"
nohup python -c "
import uvicorn
from ltms.mcp_server_http import app
import os
os.environ['DB_PATH'] = '$DB_PATH'
os.environ['FAISS_INDEX_PATH'] = '$FAISS_INDEX_PATH'
uvicorn.run(app, host='$HTTP_HOST', port=$HTTP_PORT, log_level='info')
" > "$HTTP_LOG_FILE" 2>&1 &
HTTP_PID=$!

# Save HTTP PID
echo $HTTP_PID > "$HTTP_PID_FILE"

# Wait a moment and check if HTTP server started successfully
sleep 3
if ps -p $HTTP_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ HTTP transport server started successfully (PID: $HTTP_PID)${NC}"
    echo -e "${GREEN}✓ HTTP endpoint: http://$HTTP_HOST:$HTTP_PORT${NC}"
    echo -e "${GREEN}✓ HTTP log file: $HTTP_LOG_FILE${NC}"
else
    echo -e "${RED}✗ Failed to start HTTP server${NC}"
    echo -e "${YELLOW}Check HTTP log file: $HTTP_LOG_FILE${NC}"
    rm -f "$HTTP_PID_FILE"
    exit 1
fi

# Start the stdio transport server (for MCP client integration)
echo -e "${YELLOW}Starting stdio transport server...${NC}"
cd "$SCRIPT_DIR"
# Set environment variables for stdio server
export DB_PATH="$DB_PATH"
export FAISS_INDEX_PATH="$FAISS_INDEX_PATH"
nohup python ltmc_mcp_server.py > "$LOG_FILE" 2>&1 &
STDIO_PID=$!

# Save stdio PID
echo $STDIO_PID > "$PID_FILE"

# Wait a moment and check if stdio server started successfully
sleep 2
if ps -p $STDIO_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Stdio transport server started successfully (PID: $STDIO_PID)${NC}"
    echo -e "${GREEN}✓ Stdio log file: $LOG_FILE${NC}"
else
    echo -e "${RED}✗ Failed to start stdio server${NC}"
    echo -e "${YELLOW}Check stdio log file: $LOG_FILE${NC}"
    rm -f "$PID_FILE"
    # Stop HTTP server if stdio failed
    if [ -f "$HTTP_PID_FILE" ]; then
        HTTP_PID=$(cat "$HTTP_PID_FILE")
        kill -TERM $HTTP_PID 2>/dev/null
        rm -f "$HTTP_PID_FILE"
    fi
    exit 1
fi

echo -e "${GREEN}✓ LTMC MCP Server started successfully with dual transport!${NC}"
echo -e "${BLUE}Transport Details:${NC}"
echo -e "  ${GREEN}✓ HTTP Transport:${NC} http://$HTTP_HOST:$HTTP_PORT"
echo -e "  ${GREEN}✓ Stdio Transport:${NC} Available for MCP clients"
echo -e "  ${GREEN}✓ Health Check:${NC} http://$HTTP_HOST:$HTTP_PORT/health"
echo -e "  ${GREEN}✓ Orchestration Health:${NC} http://$HTTP_HOST:$HTTP_PORT/orchestration/health"
echo -e "  ${GREEN}✓ Tools List:${NC} http://$HTTP_HOST:$HTTP_PORT/tools"
echo -e "${YELLOW}To test HTTP: curl http://$HTTP_HOST:$HTTP_PORT/health${NC}"
echo -e "${YELLOW}To test orchestration: curl http://$HTTP_HOST:$HTTP_PORT/orchestration/health${NC}"
echo -e "${YELLOW}To test stdio: mcp dev ltmc_mcp_server.py${NC}"
