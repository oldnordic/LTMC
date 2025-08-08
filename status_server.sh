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
LOG_FILE="$SCRIPT_DIR/logs/ltmc_mcp.log"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  LTMC MCP Server Status${NC}"
echo -e "${BLUE}================================${NC}"

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo -e "${YELLOW}PID File: $PID_FILE (PID: $PID)${NC}"
    
    # Check if process is running
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is running${NC}"
        echo -e "${YELLOW}Process Information:${NC}"
        ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
        
        # Show recent log entries
        if [ -f "$LOG_FILE" ]; then
            echo -e "${YELLOW}Recent Log Entries:${NC}"
            tail -n 10 "$LOG_FILE" | while IFS= read -r line; do
                echo -e "  $line"
            done
        else
            echo -e "${YELLOW}No log file found at $LOG_FILE${NC}"
        fi
        
        # Note about MCP server
        echo -e "${YELLOW}Note: This is an MCP server running via stdio${NC}"
        echo -e "${YELLOW}It communicates with Cursor through the MCP protocol${NC}"
        
    else
        echo -e "${RED}✗ Process is not running (stale PID file)${NC}"
        echo -e "${YELLOW}Cleaning up stale PID file...${NC}"
        rm -f "$PID_FILE"
    fi
else
    echo -e "${YELLOW}No PID file found - server is not running${NC}"
fi

echo -e "${BLUE}================================${NC}"
