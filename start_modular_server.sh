#!/bin/bash

# LTMC Modular FastMCP Server Startup Script
# ==========================================
# 
# Starts the new modular FastMCP architecture with 55+ tools
# 11 tool modules, all under 300 lines, FastMCP 2.0 compliance
# Automatic stdio/HTTP transport handling via mcp.run()

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/ltmc_modular.pid"
LOG_FILE="$SCRIPT_DIR/logs/ltmc_modular.log"
VENV_PATH="$SCRIPT_DIR/venv"
SERVER_SCRIPT="ltmc_mcp_server/main.py"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

echo -e "${BLUE}🚀 Starting LTMC Modular FastMCP Server...${NC}"
echo -e "${BLUE}Architecture: 11 modules, 55+ tools, FastMCP 2.0${NC}"

# Check if server is already running
if [ -f "$PID_FILE" ] && ps -p $(cat "$PID_FILE") > /dev/null 2>&1; then
    echo -e "${RED}Server already running (PID: $(cat $PID_FILE)). Stopping first...${NC}"
    bash "$SCRIPT_DIR/stop_modular_server.sh"
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

# Check if server script exists
if [ ! -f "$SERVER_SCRIPT" ]; then
    echo -e "${RED}Server script not found: $SERVER_SCRIPT${NC}"
    echo -e "${YELLOW}Please ensure the modular server is properly set up${NC}"
    exit 1
fi

# Check required dependencies
echo -e "${YELLOW}Checking MCP SDK dependencies...${NC}"
if ! python -c "from mcp.server.fastmcp import FastMCP" 2>/dev/null; then
    echo -e "${RED}Official MCP SDK not found. Installing...${NC}"
    pip install mcp
fi

if ! python -c "import aiosqlite, redis, neo4j, faiss" 2>/dev/null; then
    echo -e "${RED}Database dependencies missing. Installing...${NC}"
    pip install aiosqlite redis neo4j-driver faiss-cpu
fi

# Load .env file
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Check database connections
echo -e "${YELLOW}Checking database connections...${NC}"

# SQLite check
export DB_PATH="${DB_PATH:-ltmc.db}"
export LTMC_DATA_DIR="${LTMC_DATA_DIR:-$(pwd)/data}"
mkdir -p "$LTMC_DATA_DIR"
echo -e "${GREEN}✓ SQLite: $DB_PATH${NC}"

# Redis check
REDIS_PORT="${REDIS_PORT:-6382}"
REDIS_PASSWORD="${REDIS_PASSWORD:-ltmc_cache_2025}"
if python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='$REDIS_PASSWORD'); r.ping()" 2>/dev/null; then
    echo -e "${GREEN}✓ Redis: localhost:$REDIS_PORT${NC}"
else
    echo -e "${YELLOW}⚠ Redis not available. Starting Redis service...${NC}"
    if [ -f ./redis_control.sh ]; then
        ./redis_control.sh start
        sleep 2
        if python -c "import redis; r=redis.Redis(host='localhost', port=$REDIS_PORT, decode_responses=True, password='$REDIS_PASSWORD'); r.ping()" 2>/dev/null; then
            echo -e "${GREEN}✓ Redis started successfully${NC}"
        else
            echo -e "${YELLOW}⚠ Redis start failed. Some features may be limited.${NC}"
        fi
    fi
fi

# Neo4j check
NEO4J_URI="${NEO4J_URI:-bolt://localhost:7687}"
NEO4J_USER="${NEO4J_USER:-neo4j}"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-kwe_password}"
if python -c "from neo4j import GraphDatabase; driver=GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USER', '$NEO4J_PASSWORD')); driver.verify_connectivity(); driver.close()" 2>/dev/null; then
    echo -e "${GREEN}✓ Neo4j: $NEO4J_URI${NC}"
else
    echo -e "${YELLOW}⚠ Neo4j not available. Graph features will be limited.${NC}"
fi

# FAISS check
export FAISS_INDEX_PATH="${FAISS_INDEX_PATH:-$LTMC_DATA_DIR/faiss_index}"
echo -e "${GREEN}✓ FAISS index: $FAISS_INDEX_PATH${NC}"

# Set environment variables
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export REDIS_ENABLED="${REDIS_ENABLED:-true}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="$REDIS_PORT" 
export REDIS_PASSWORD="$REDIS_PASSWORD"

echo -e "${YELLOW}Configuration summary:${NC}"
echo -e "  DB_PATH: $DB_PATH"
echo -e "  LTMC_DATA_DIR: $LTMC_DATA_DIR"
echo -e "  FAISS_INDEX_PATH: $FAISS_INDEX_PATH"
echo -e "  LOG_LEVEL: $LOG_LEVEL"
echo -e "  REDIS_HOST: $REDIS_HOST:$REDIS_PORT"
echo -e "  NEO4J_URI: $NEO4J_URI"

# Start the modular FastMCP server
echo -e "${YELLOW}Starting modular FastMCP server...${NC}"
cd "$SCRIPT_DIR"

# Run server in background mode for process management
nohup python "$SERVER_SCRIPT" > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo $SERVER_PID > "$PID_FILE"

# Wait and check if server started successfully
sleep 5
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Modular FastMCP server started successfully!${NC}"
    echo -e "${GREEN}   PID: $SERVER_PID${NC}"
    echo -e "${GREEN}   Log: $LOG_FILE${NC}"
    
    # Show server capabilities
    echo -e "${BLUE}📋 Server Architecture:${NC}"
    echo -e "   🔧 Tool Modules: 11 (all ≤300 lines)"
    echo -e "   🛠 Total Tools: 55+"
    echo -e "   📡 Transport: Automatic (stdio/HTTP)"
    echo -e "   🏗 Framework: Official FastMCP 2.0"
    echo -e "   📊 Database: 4-tier (SQLite, Redis, Neo4j, FAISS)"
    
    echo -e "${BLUE}🔧 Tool Categories:${NC}"
    echo -e "   📝 Memory: store_memory, retrieve_memory"
    echo -e "   💬 Chat: log_chat, ask_with_context"
    echo -e "   ✅ Todo: add_todo, complete_todo, list_todos, search_todos"
    echo -e "   🔗 Context: build_context, link_resources, query_graph"
    echo -e "   📊 Patterns: log_code_attempt, get_code_patterns, analyze_patterns"
    echo -e "   🗄 Redis: cache operations, health_check, stats"
    echo -e "   🤖 Advanced: ML integration, context usage"
    echo -e "   📋 Taskmaster: task blueprints, dependencies, analysis"
    echo -e "   🏗 Blueprint: Neo4j blueprints, documentation generation"
    echo -e "   📚 Documentation: sync, validation, drift detection"
    echo -e "   🔧 Unified: performance reporting, system health"
    
    echo -e "${BLUE}🎯 Usage:${NC}"
    echo -e "   📡 MCP Inspector: mcp dev $SERVER_SCRIPT"
    echo -e "   🔧 Cursor IDE: Configure MCP server in settings"
    echo -e "   📊 Status: ./stop_modular_server.sh --status"
    echo -e "   🛑 Stop: ./stop_modular_server.sh"
    
else
    echo -e "${RED}❌ Failed to start modular FastMCP server${NC}"
    echo -e "${YELLOW}Check log file: $LOG_FILE${NC}"
    if [ -f "$LOG_FILE" ]; then
        echo -e "${YELLOW}Last 20 lines:${NC}"
        tail -20 "$LOG_FILE"
    fi
    rm -f "$PID_FILE"
    exit 1
fi

echo -e "${GREEN}🎉 LTMC Modular FastMCP Server is ready!${NC}"