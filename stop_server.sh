#!/bin/bash

# LTMC MCP Server Stop Script - Dual Transport (Stdio + HTTP)

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

# Check if --status flag is provided
if [ "$1" = "--status" ]; then
    echo -e "${BLUE}LTMC MCP Server Status:${NC}"
    
    # Check stdio server
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Stdio transport server is running (PID: $PID)${NC}"
            echo -e "${BLUE}  Entry point: ltmc_mcp_server.py${NC}"
        else
            echo -e "${RED}✗ Stdio server PID file exists but process is not running${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}No stdio PID file found - stdio server not running${NC}"
    fi
    
    # Check HTTP server
    if [ -f "$HTTP_PID_FILE" ]; then
        HTTP_PID=$(cat "$HTTP_PID_FILE")
        if ps -p $HTTP_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ HTTP transport server is running (PID: $HTTP_PID)${NC}"
        else
            echo -e "${RED}✗ HTTP server PID file exists but process is not running${NC}"
            rm -f "$HTTP_PID_FILE"
        fi
    else
        echo -e "${YELLOW}No HTTP PID file found - HTTP server not running${NC}"
    fi
    
    exit 0
fi

echo -e "${YELLOW}Stopping LTMC MCP Server (Dual Transport)...${NC}"

# Function to stop a server process
stop_server() {
    local pid_file="$1"
    local server_name="$2"
    
    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}No $server_name PID file found${NC}"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "${YELLOW}$server_name process $pid is not running. Removing stale PID file.${NC}"
        rm -f "$pid_file"
        return 0
    fi
    
    echo -e "${YELLOW}Found running $server_name process (PID: $pid)${NC}"
    
    # Try graceful shutdown first
    echo -e "${YELLOW}Sending SIGTERM to $server_name process $pid...${NC}"
    kill -TERM $pid
    
    # Wait for graceful shutdown (up to 10 seconds)
    for i in {1..10}; do
        if ! ps -p $pid > /dev/null 2>&1; then
            echo -e "${GREEN}✓ $server_name stopped gracefully${NC}"
            rm -f "$pid_file"
            return 0
        fi
        sleep 1
    done
    
    # Force kill if still running
    echo -e "${YELLOW}$server_name did not stop gracefully. Force killing...${NC}"
    kill -KILL $pid
    
    # Wait a moment and check
    sleep 1
    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $server_name stopped forcefully${NC}"
        rm -f "$pid_file"
    else
        echo -e "${RED}✗ Failed to stop $server_name${NC}"
        echo -e "${YELLOW}You may need to kill it manually: kill -9 $pid${NC}"
        return 1
    fi
}

# Stop HTTP server first
echo -e "${BLUE}Stopping HTTP transport server...${NC}"
stop_server "$HTTP_PID_FILE" "HTTP transport server"

# Stop stdio server
echo -e "${BLUE}Stopping stdio transport server...${NC}"
stop_server "$PID_FILE" "stdio transport server"

# Check LTMC Redis service status
echo -e "${BLUE}LTMC Redis Service Status:${NC}"
if python -c "import redis; r=redis.Redis(host='localhost', port=6381, decode_responses=True, password='ltmc_cache_2025'); r.ping()" 2>/dev/null; then
    echo -e "${YELLOW}LTMC Redis is still running on port 6381${NC}"
    echo -e "${YELLOW}Note: Redis is left running as it may be used by other services${NC}"
    echo -e "${YELLOW}To stop LTMC Redis: ./redis_control.sh stop${NC}"
else
    echo -e "${GREEN}✓ LTMC Redis is not running on port 6381${NC}"
fi

echo -e "${GREEN}✓ LTMC MCP Server stopped successfully${NC}"
