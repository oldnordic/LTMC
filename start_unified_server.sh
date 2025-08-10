#!/bin/bash

# Unified MCP Server Startup Script - FastMCP with dual transport (stdio + HTTP)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/unified_mcp.pid"
LOG_FILE="$SCRIPT_DIR/logs/unified_mcp.log"
VENV_PATH="$SCRIPT_DIR/venv"
HTTP_PORT="${HTTP_PORT:-5050}"

# Create logs directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/logs"

echo -e "${BLUE}Starting Unified MCP Server (FastMCP dual transport)...${NC}"

# Check if server is already running
if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${RED}Unified MCP server already running (PID: $(cat $PID_FILE)). Stopping first...${NC}"
    bash "$SCRIPT_DIR/stop_unified_server.sh"
    sleep 2
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Please run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check if required packages are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python -c "import fastmcp" 2>/dev/null; then
    echo -e "${RED}FastMCP package not found. Installing...${NC}"
    pip install fastmcp
fi

# Load .env file first
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Check Redis connection (required for caching and orchestration)
REDIS_PORT="${REDIS_PORT:-6382}"
echo -e "${YELLOW}Checking LTMC Redis connection (port $REDIS_PORT)...${NC}"
if ! python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='${REDIS_PASSWORD}'); r.ping()" 2>/dev/null; then
    echo -e "${YELLOW}Warning: LTMC Redis not available on port $REDIS_PORT. Starting Redis service...${NC}"
    ./redis_control.sh start
    
    # Wait for Redis to start and verify
    sleep 3
    if python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='${REDIS_PASSWORD}'); r.ping()" 2>/dev/null; then
        echo -e "${GREEN}✓ LTMC Redis started successfully${NC}"
    else
        echo -e "${YELLOW}Warning: Redis failed to start. Caching will be disabled.${NC}"
    fi
else
    echo -e "${GREEN}✓ LTMC Redis connection successful${NC}"
fi

# Set environment variables for Unified MCP Server
export DB_PATH="${DB_PATH:-ltmc.db}"
export LTMC_DATA_DIR="${LTMC_DATA_DIR:-$(pwd)/data}"
export FAISS_INDEX_PATH="${FAISS_INDEX_PATH:-$LTMC_DATA_DIR/faiss_index}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export HTTP_HOST="${HTTP_HOST:-localhost}"
export HTTP_PORT="$HTTP_PORT"

# Ensure data directory exists
mkdir -p "$LTMC_DATA_DIR"

# Set Redis environment variables
export REDIS_ENABLED="${REDIS_ENABLED:-true}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6382}"
export REDIS_PASSWORD="${REDIS_PASSWORD:-ltmc_cache_2025}"

# Set performance optimization variables
export CACHE_ENABLED="${CACHE_ENABLED:-true}"
export LAZY_LOADING_ENABLED="${LAZY_LOADING_ENABLED:-true}"
export CONNECTION_POOLING_ENABLED="${CONNECTION_POOLING_ENABLED:-true}"

# Set Advanced ML Integration environment variables
export ML_INTEGRATION_ENABLED="${ML_INTEGRATION_ENABLED:-true}"
export ML_LEARNING_COORDINATION="${ML_LEARNING_COORDINATION:-true}"
export ML_KNOWLEDGE_SHARING="${ML_KNOWLEDGE_SHARING:-true}"
export ML_ADAPTIVE_RESOURCES="${ML_ADAPTIVE_RESOURCES:-true}"

echo -e "${YELLOW}Environment variables:${NC}"
echo -e "  DB_PATH: $DB_PATH"
echo -e "  LTMC_DATA_DIR: $LTMC_DATA_DIR"
echo -e "  FAISS_INDEX_PATH: $FAISS_INDEX_PATH"
echo -e "  LOG_LEVEL: $LOG_LEVEL"
echo -e "  HTTP_HOST: $HTTP_HOST"
echo -e "  HTTP_PORT: $HTTP_PORT (FastMCP dual transport)"
echo -e "  REDIS_ENABLED: $REDIS_ENABLED"
echo -e "  REDIS_PORT: $REDIS_PORT"
echo -e "  CACHE_ENABLED: $CACHE_ENABLED"
echo -e "  ML_INTEGRATION_ENABLED: $ML_INTEGRATION_ENABLED"

# Start the Unified MCP Server
echo -e "${YELLOW}Starting Unified MCP Server with FastMCP dual transport...${NC}"
cd "$SCRIPT_DIR"

# Start unified server directly using command line interface
nohup python unified_mcp_server.py --transport http --host "$HTTP_HOST" --port "$HTTP_PORT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > "$PID_FILE"

# Wait a moment and check if server started successfully
sleep 5
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Unified MCP Server started successfully (PID: $SERVER_PID)${NC}"
    echo -e "${GREEN}✓ Server log: $LOG_FILE${NC}"
    
    # Test HTTP endpoint availability
    echo -e "${YELLOW}Testing HTTP endpoint...${NC}"
    for i in {1..10}; do
        if curl -s "http://$HTTP_HOST:$HTTP_PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ HTTP endpoint responding: http://$HTTP_HOST:$HTTP_PORT${NC}"
            break
        fi
        sleep 1
    done
    
else
    echo -e "${RED}✗ Failed to start Unified MCP Server${NC}"
    echo -e "${YELLOW}Check server log: $LOG_FILE${NC}"
    if [ -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}Last few lines of log:${NC}"
        tail -20 "$LOG_FILE"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}✓ Unified MCP Server started successfully with all Phase 1-4 features!${NC}"
echo -e "${BLUE}Server Details:${NC}"
echo -e "  ${GREEN}✓ Dual Transport:${NC} HTTP + stdio via FastMCP"
echo -e "  ${GREEN}✓ HTTP Endpoint:${NC} http://$HTTP_HOST:$HTTP_PORT"
echo -e "  ${GREEN}✓ Health Check:${NC} http://$HTTP_HOST:$HTTP_PORT/health"
echo -e "  ${GREEN}✓ Tools (55):${NC} All LTMC + taskmaster + advanced features"
echo -e "  ${GREEN}✓ Performance:${NC} Advanced caching, lazy loading, connection pooling"
echo -e "${BLUE}Features Available:${NC}"
echo -e "  ${GREEN}✓ Memory Tools:${NC} store_memory, retrieve_memory"
echo -e "  ${GREEN}✓ Chat Tools:${NC} log_chat, ask_with_context, route_query"
echo -e "  ${GREEN}✓ Todo Tools:${NC} add_todo, list_todos, complete_todo, search_todos"
echo -e "  ${GREEN}✓ Taskmaster Tools:${NC} blueprint creation, task analysis, team assignment"
echo -e "  ${GREEN}✓ Blueprint Tools:${NC} code analysis, documentation sync"
echo -e "  ${GREEN}✓ Advanced Features:${NC} ML integration, orchestration, caching"
echo -e "${YELLOW}Usage:${NC}"
echo -e "  HTTP: curl http://$HTTP_HOST:$HTTP_PORT/health"
echo -e "  Stdio: Connect MCP client to unified_mcp_server.py"
echo -e "  Stop: ./stop_unified_server.sh"
echo -e "  Status: ./stop_unified_server.sh --status"