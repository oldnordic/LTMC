#!/bin/bash

# Unified MCP Server Stop Script - FastMCP dual transport

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
HTTP_PORT="${HTTP_PORT:-5051}"

# Check if --status flag is provided
if [ "$1" = "--status" ]; then
    echo -e "${BLUE}Unified MCP Server Status:${NC}"
    
    # Check server process
    if [ -f "$PID_FILE" ]; then
        SERVER_PID=$(cat "$PID_FILE")
        if ps -p $SERVER_PID > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Unified MCP Server is running (PID: $SERVER_PID)${NC}"
            
            # Test HTTP endpoint
            if curl -s "http://localhost:$HTTP_PORT/health" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ HTTP endpoint responding at http://localhost:$HTTP_PORT${NC}"
            else
                echo -e "${YELLOW}⚠ Server running but HTTP endpoint not responding${NC}"
            fi
            
            # Show tool count if available
            TOOL_COUNT=$(curl -s "http://localhost:$HTTP_PORT/tools" 2>/dev/null | grep -o '"name"' | wc -l)
            if [ "$TOOL_COUNT" -gt 0 ]; then
                echo -e "${GREEN}✓ Tools available: $TOOL_COUNT${NC}"
            fi
            
        else
            echo -e "${RED}✗ Server PID file exists but process is not running${NC}"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}No PID file found - Unified MCP Server not running${NC}"
    fi
    
    # Check log file
    if [ -f "$LOG_FILE" ]; then
        LOG_SIZE=$(du -h "$LOG_FILE" | cut -f1)
        echo -e "${BLUE}Log file: $LOG_FILE (size: $LOG_SIZE)${NC}"
        
        # Show last few log lines if there are errors
        if grep -q "ERROR" "$LOG_FILE" 2>/dev/null; then
            echo -e "${YELLOW}Recent errors in log:${NC}"
            grep "ERROR" "$LOG_FILE" | tail -3 | sed 's/^/  /'
        fi
    fi
    
    # Check Redis connection
    echo -e "${BLUE}Checking Redis connection...${NC}"
    REDIS_PORT="${REDIS_PORT:-6382}"
    if python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='ltmc_cache_2025'); r.ping()" 2>/dev/null; then
        echo -e "${GREEN}✓ Redis connection successful (port $REDIS_PORT)${NC}"
    else
        echo -e "${YELLOW}⚠ Redis not available on port $REDIS_PORT${NC}"
    fi
    
    exit 0
fi

echo -e "${YELLOW}Stopping Unified MCP Server...${NC}"

# Function to stop server process
stop_server() {
    local pid_file="$1"
    local server_name="$2"
    
    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}No $server_name PID file found - server not running${NC}"
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
    
    # Wait for graceful shutdown (up to 15 seconds for unified server)
    for i in {1..15}; do
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
    sleep 2
    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "${GREEN}✓ $server_name stopped forcefully${NC}"
        rm -f "$pid_file"
    else
        echo -e "${RED}✗ Failed to stop $server_name${NC}"
        echo -e "${YELLOW}You may need to kill it manually: kill -9 $pid${NC}"
        return 1
    fi
}

# Stop the unified server
echo -e "${BLUE}Stopping Unified MCP Server...${NC}"
stop_server "$PID_FILE" "Unified MCP Server"

# Check if any related processes are still running
REMAINING_PROCS=$(ps aux | grep -E "(unified_mcp_server|fastmcp)" | grep -v grep | wc -l)
if [ "$REMAINING_PROCS" -gt 0 ]; then
    echo -e "${YELLOW}Found $REMAINING_PROCS remaining MCP-related processes:${NC}"
    ps aux | grep -E "(unified_mcp_server|fastmcp)" | grep -v grep | sed 's/^/  /'
    echo -e "${YELLOW}You may need to stop these manually if needed${NC}"
fi

# Check LTMC Redis service status
echo -e "${BLUE}LTMC Redis Service Status:${NC}"
REDIS_PORT="${REDIS_PORT:-6382}"
if python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='ltmc_cache_2025'); r.ping()" 2>/dev/null; then
    echo -e "${YELLOW}LTMC Redis is still running on port $REDIS_PORT${NC}"
    echo -e "${YELLOW}Note: Redis is left running as it may be used by other services${NC}"
    echo -e "${YELLOW}To stop LTMC Redis: ./redis_control.sh stop${NC}"
else
    echo -e "${GREEN}✓ LTMC Redis is not running on port $REDIS_PORT${NC}"
fi

# Show final status
if [ -f "$PID_FILE" ]; then
    echo -e "${RED}✗ Server may still be running - check manually${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Unified MCP Server stopped successfully${NC}"
    echo -e "${BLUE}To restart: ./start_unified_server.sh${NC}"
    exit 0
fi