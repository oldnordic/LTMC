#!/bin/bash

# LTMC Standalone Redis Server Setup
# Creates a Redis server on port 6380 to avoid KWE conflicts

set -e

REDIS_PORT=6380
REDIS_DIR="redis-ltmc"
REDIS_CONF="redis-ltmc.conf"
REDIS_PID="redis-ltmc.pid"
REDIS_LOG="logs/redis-ltmc.log"

echo "🔧 Setting up standalone Redis server for LTMC on port $REDIS_PORT..."

# Create Redis directory if it doesn't exist
mkdir -p "$REDIS_DIR"
mkdir -p logs

# Generate Redis configuration
cat > "$REDIS_DIR/$REDIS_CONF" << EOF
# LTMC Standalone Redis Configuration
# Port 6380 to avoid KWE conflicts
port $REDIS_PORT
bind 127.0.0.1
timeout 0
tcp-keepalive 300

# Persistence
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump-ltmc.rdb
dir ./$REDIS_DIR

# Logging
loglevel notice
logfile $REDIS_LOG
syslog-enabled no

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security
protected-mode yes
requirepass ${REDIS_PASSWORD:-ltmc_dev_$(openssl rand -hex 8)}

# Performance
tcp-backlog 511
databases 16
EOF

# Check if Redis is installed
if ! command -v redis-server &> /dev/null; then
    echo "❌ Redis not found. Please install Redis first:"
    echo "   Ubuntu/Debian: sudo apt-get install redis-server"
    echo "   CentOS/RHEL: sudo yum install redis"
    echo "   macOS: brew install redis"
    exit 1
fi

# Check if Redis is already running on our port
if lsof -Pi :$REDIS_PORT -sTCP:LISTEN -t &> /dev/null; then
    echo "⚠️  Port $REDIS_PORT is already in use. Stopping existing Redis..."
    if [ -f "$REDIS_DIR/$REDIS_PID" ]; then
        kill $(cat "$REDIS_DIR/$REDIS_PID") 2>/dev/null || true
        rm -f "$REDIS_DIR/$REDIS_PID"
    fi
    sleep 2
fi

# Start Redis server
echo "🚀 Starting Redis server on port $REDIS_PORT..."
cd "$REDIS_DIR"
nohup redis-server "$REDIS_CONF" --daemonize yes --pidfile "$REDIS_PID" > /dev/null 2>&1

# Wait for Redis to start
sleep 2

# Test connection
if redis-cli -h 127.0.0.1 -p $REDIS_PORT -a "${REDIS_PASSWORD:-ltmc_dev_$(openssl rand -hex 8)}" ping | grep -q "PONG"; then
    echo "✅ LTMC Redis server started successfully on port $REDIS_PORT"
    echo "   Configuration: $REDIS_DIR/$REDIS_CONF"
    echo "   PID file: $REDIS_DIR/$REDIS_PID"
    echo "   Log file: $REDIS_LOG"
    echo "   Password: ${REDIS_PASSWORD:-[generated]}"
else
    echo "❌ Failed to start Redis server"
    exit 1
fi

echo "🔧 To connect: redis-cli -h 127.0.0.1 -p $REDIS_PORT -a \$REDIS_PASSWORD"
echo "🛑 To stop: redis-cli -h 127.0.0.1 -p $REDIS_PORT -a \$REDIS_PASSWORD shutdown"