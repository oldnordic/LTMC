#!/bin/bash

# LTMC Redis Service Control Script (Port 6380)
# Comprehensive Redis management for LTMC MCP Server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REDIS_PORT=6382
REDIS_CONFIG_DIR="$(pwd)/redis_config"
REDIS_CONFIG_FILE="$REDIS_CONFIG_DIR/redis_ltmc.conf"
REDIS_DATA_DIR="$(pwd)/redis_data"
REDIS_LOG_FILE="$(pwd)/logs/redis_ltmc.log"
REDIS_PID_FILE="$(pwd)/redis_ltmc.pid"
REDIS_PASSWORD="ltmc_cache_2025"

# Create directories if they don't exist
mkdir -p "$REDIS_CONFIG_DIR" "$REDIS_DATA_DIR" "$(pwd)/logs"

# Function to create Redis config
create_redis_config() {
    if [ ! -f "$REDIS_CONFIG_FILE" ]; then
        echo -e "${YELLOW}Creating Redis configuration...${NC}"
        cat > "$REDIS_CONFIG_FILE" << EOF
# LTMC Redis Configuration (Port 6380)
port $REDIS_PORT
bind 127.0.0.1
protected-mode yes
requirepass $REDIS_PASSWORD
timeout 0
tcp-keepalive 300
daemonize yes
supervised no
pidfile $REDIS_PID_FILE
loglevel notice
logfile $REDIS_LOG_FILE
databases 16
dir $REDIS_DATA_DIR
dbfilename ltmc_dump.rdb
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
maxmemory 100mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "ltmc_appendonly.aof"
appendfsync everysec
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
EOF
    fi
}

case "$1" in
    start)
        echo -e "${YELLOW}Starting LTMC Redis server on port $REDIS_PORT...${NC}"
        
        # Check if already running
        if [ -f "$REDIS_PID_FILE" ]; then
            PID=$(cat "$REDIS_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo -e "${GREEN}✓ Redis is already running (PID: $PID)${NC}"
                exit 0
            else
                echo -e "${YELLOW}Removing stale PID file${NC}"
                rm -f "$REDIS_PID_FILE"
            fi
        fi
        
        # Create Redis config if it doesn't exist
        create_redis_config
        
        # Check if redis-server is available
        if ! command -v redis-server &> /dev/null; then
            echo -e "${RED}✗ redis-server not found. Install Redis first.${NC}"
            exit 1
        fi
        
        # Start Redis with custom config
        redis-server "$REDIS_CONFIG_FILE"
        sleep 2
        
        # Verify startup
        if [ -f "$REDIS_PID_FILE" ] && ps -p $(cat "$REDIS_PID_FILE") > /dev/null 2>&1; then
            PID=$(cat "$REDIS_PID_FILE")
            echo -e "${GREEN}✓ Redis started successfully (PID: $PID)${NC}"
            echo -e "${GREEN}✓ Port: $REDIS_PORT, Password: $REDIS_PASSWORD${NC}"
            
            # Test connection
            if redis-cli -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null | grep -q "PONG"; then
                echo -e "${GREEN}✓ Connection test successful${NC}"
            else
                echo -e "${YELLOW}⚠ Started but connection test failed${NC}"
            fi
        else
            echo -e "${RED}✗ Failed to start Redis${NC}"
            exit 1
        fi
        ;;
    
    stop)
        if [ -f "$REDIS_DIR/$REDIS_PID" ] && kill -0 $(cat "$REDIS_DIR/$REDIS_PID") 2>/dev/null; then
            echo "🛑 Stopping LTMC Redis server..."
            redis-cli -h 127.0.0.1 -p $REDIS_PORT -a $REDIS_PASSWORD shutdown 2>/dev/null || true
            sleep 2
            if [ -f "$REDIS_DIR/$REDIS_PID" ]; then
                rm -f "$REDIS_DIR/$REDIS_PID"
            fi
            echo "✅ Redis server stopped"
        else
            echo "⚠️  Redis is not running"
        fi
        ;;
    
    restart)
        $0 stop
        sleep 3
        $0 start
        ;;
    
    status)
        echo -e "${BLUE}LTMC Redis Status Check (Port $REDIS_PORT)${NC}"
        
        # Check if managed by our script
        MANAGED_BY_SCRIPT=false
        if [ -f "$REDIS_PID_FILE" ]; then
            PID=$(cat "$REDIS_PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                MANAGED_BY_SCRIPT=true
                echo -e "${GREEN}✓ LTMC-managed Redis is running (PID: $PID)${NC}"
            else
                echo -e "${YELLOW}⚠ Stale LTMC Redis PID file found, cleaning up${NC}"
                rm -f "$REDIS_PID_FILE"
            fi
        fi
        
        # Check if Redis is running on the port (regardless of management)
        if redis-cli -p $REDIS_PORT ping 2>/dev/null | grep -q "PONG"; then
            if [ "$MANAGED_BY_SCRIPT" = "false" ]; then
                echo -e "${YELLOW}⚠ External Redis detected on port $REDIS_PORT (not LTMC-managed)${NC}"
            fi
            
            echo -e "${GREEN}✓ Redis connection successful${NC}"
            
            # Test with and without password
            if redis-cli -p $REDIS_PORT -a $REDIS_PASSWORD ping 2>/dev/null | grep -q "PONG"; then
                REDIS_CMD="redis-cli -p $REDIS_PORT -a $REDIS_PASSWORD"
                echo -e "${GREEN}✓ Password authentication: ENABLED${NC}"
            elif redis-cli -p $REDIS_PORT ping 2>/dev/null | grep -q "PONG"; then
                REDIS_CMD="redis-cli -p $REDIS_PORT"
                echo -e "${YELLOW}⚠ Password authentication: DISABLED${NC}"
            else
                echo -e "${RED}✗ Connection failed${NC}"
                exit 1
            fi
            
            # Get Redis info
            INFO=$($REDIS_CMD info server 2>/dev/null)
            VERSION=$(echo "$INFO" | grep "redis_version:" | cut -d: -f2 | tr -d '\r')
            UPTIME=$(echo "$INFO" | grep "uptime_in_seconds:" | cut -d: -f2 | tr -d '\r')
            
            echo -e "${BLUE}📊 Version: $VERSION${NC}"
            echo -e "${BLUE}⏱️  Uptime: ${UPTIME}s${NC}"
            
            # Get memory usage
            MEMORY=$($REDIS_CMD info memory 2>/dev/null | grep "used_memory_human:" | cut -d: -f2 | tr -d '\r')
            echo -e "${BLUE}💾 Memory: $MEMORY${NC}"
            
            # Get key count
            KEYS=$($REDIS_CMD dbsize 2>/dev/null | tr -d '\r')
            echo -e "${BLUE}🗝️  Keys: $KEYS${NC}"
            
            # Show management status
            if [ "$MANAGED_BY_SCRIPT" = "true" ]; then
                echo -e "${GREEN}✓ Status: Managed by LTMC script${NC}"
            else
                echo -e "${YELLOW}⚠ Status: External Redis (not managed by LTMC)${NC}"
                echo -e "${YELLOW}  To take management: ./redis_control.sh restart${NC}"
            fi
        else
            echo -e "${RED}✗ No Redis found on port $REDIS_PORT${NC}"
            echo -e "${YELLOW}  Start with: ./redis_control.sh start${NC}"
        fi
        ;;
    
    connect)
        echo "🔌 Connecting to LTMC Redis..."
        redis-cli -h 127.0.0.1 -p $REDIS_PORT -a $REDIS_PASSWORD
        ;;
    
    flush)
        echo "🧹 Flushing all Redis data..."
        redis-cli -h 127.0.0.1 -p $REDIS_PORT -a $REDIS_PASSWORD flushall
        echo "✅ All data cleared"
        ;;
    
    monitor)
        echo "🔍 Monitoring Redis commands (Ctrl+C to exit)..."
        redis-cli -h 127.0.0.1 -p $REDIS_PORT -a $REDIS_PASSWORD monitor
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|status|connect|flush|monitor}"
        echo ""
        echo "Commands:"
        echo "  start   - Start Redis server"
        echo "  stop    - Stop Redis server"
        echo "  restart - Restart Redis server"
        echo "  status  - Show Redis status and stats"
        echo "  connect - Connect to Redis CLI"
        echo "  flush   - Clear all cached data"
        echo "  monitor - Monitor Redis commands"
        exit 1
        ;;
esac