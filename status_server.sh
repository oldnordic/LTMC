#!/bin/bash

# LTMC MCP Server Status Script

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
HTTP_PORT="${HTTP_PORT:-5050}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LTMC MCP Server Status (Dual Transport)${NC}"
echo -e "${BLUE}========================================${NC}"

# Check Redis connection  
echo -e "${BLUE}LTMC Redis Service Status:${NC}"
if python -c "import redis; r=redis.Redis(host='localhost', port=6382, decode_responses=True); r.ping()" 2>/dev/null; then
    echo -e "${GREEN}✓ LTMC Redis is running on port 6382${NC}"
else
    echo -e "${YELLOW}⚠ LTMC Redis not available on port 6382${NC}"
    echo -e "${YELLOW}  Start with: ./redis_control.sh start${NC}"
fi
echo

# Check HTTP Server
echo -e "${BLUE}HTTP Transport Server Status:${NC}"
if [ -f "$HTTP_PID_FILE" ]; then
    HTTP_PID=$(cat "$HTTP_PID_FILE")
    echo -e "${YELLOW}HTTP PID File: $HTTP_PID_FILE (PID: $HTTP_PID)${NC}"
    
    if ps -p $HTTP_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ HTTP server is running${NC}"
        echo -e "${YELLOW}HTTP Process Information:${NC}"
        ps -p $HTTP_PID -o pid,ppid,cmd,etime,pcpu,pmem
        echo -e "${GREEN}✓ Endpoint: http://localhost:$HTTP_PORT${NC}"
        echo -e "${GREEN}✓ Health Check: http://localhost:$HTTP_PORT/health${NC}"
        
        # Test HTTP endpoint
        if curl -s "http://localhost:$HTTP_PORT/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ HTTP endpoint is responding${NC}"
        else
            echo -e "${YELLOW}⚠ HTTP endpoint not responding${NC}"
        fi
        
        if [ -f "$HTTP_LOG_FILE" ]; then
            echo -e "${YELLOW}Recent HTTP Log Entries:${NC}"
            tail -n 5 "$HTTP_LOG_FILE" | while IFS= read -r line; do
                echo -e "  $line"
            done
        fi
    else
        echo -e "${RED}✗ HTTP process is not running (stale PID file)${NC}"
        rm -f "$HTTP_PID_FILE"
    fi
else
    echo -e "${YELLOW}No HTTP PID file found - HTTP server not running${NC}"
fi
echo

# Check Stdio Server
echo -e "${BLUE}Stdio Transport Server Status:${NC}"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}Stdio PID File: $PID_FILE (PID: $PID)${NC}"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Stdio server is running${NC}"
        echo -e "${YELLOW}Stdio Process Information:${NC}"
        ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
        
        if [ -f "$LOG_FILE" ]; then
            echo -e "${YELLOW}Recent Stdio Log Entries:${NC}"
            tail -n 5 "$LOG_FILE" | while IFS= read -r line; do
                echo -e "  $line"
            done
        fi
        
        echo -e "${YELLOW}Note: Stdio server communicates with MCP clients${NC}"
    else
        echo -e "${RED}✗ Stdio process is not running (stale PID file)${NC}"
        rm -f "$PID_FILE"
    fi
else
    echo -e "${YELLOW}No Stdio PID file found - stdio server not running${NC}"
fi

echo -e "${BLUE}================================${NC}"
