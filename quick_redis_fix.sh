#!/bin/bash
set -e

echo "🚨 EMERGENCY REDIS FIX - LTMC Team Rally!"
echo "=" * 50

# Check what Redis processes are running
echo "🔍 Checking Redis processes..."
ps aux | grep redis | grep -v grep || echo "No Redis processes found"

# Check what ports are listening
echo ""
echo "🔍 Checking Redis ports..."
netstat -tlnp 2>/dev/null | grep ':637[0-9]' || echo "No Redis ports found"

# Try to start Redis on the configured port (6380)
echo ""
echo "🚀 Starting Redis server..."
if [ -f "setup_redis.sh" ]; then
    bash setup_redis.sh
else
    echo "❌ setup_redis.sh not found"
fi

# Test connection on different ports
echo ""
echo "🔍 Testing Redis connections..."

for port in 6379 6380 6381; do
    echo "Testing port $port..."
    
    # Test with password
    if redis-cli -h localhost -p $port -a "ltmc_cache_2025" ping 2>/dev/null | grep -q "PONG"; then
        echo "✅ Redis working on port $port with password"
        echo "WORKING_PORT=$port" > /tmp/redis_working_port
        echo "WORKING_PASSWORD=ltmc_cache_2025" >> /tmp/redis_working_port
        break
    fi
    
    # Test without password
    if redis-cli -h localhost -p $port ping 2>/dev/null | grep -q "PONG"; then
        echo "✅ Redis working on port $port without password"
        echo "WORKING_PORT=$port" > /tmp/redis_working_port
        echo "WORKING_PASSWORD=" >> /tmp/redis_working_port
        break
    fi
    
    echo "❌ Port $port not responding"
done

# Check if we found a working port
if [ -f "/tmp/redis_working_port" ]; then
    source /tmp/redis_working_port
    echo ""
    echo "✅ SUCCESS: Redis is working on port $WORKING_PORT"
    
    # Update Redis service configuration
    echo "🔧 Updating Redis service configuration..."
    if [ -f "ltms/services/redis_service.py" ]; then
        # Backup original
        cp ltms/services/redis_service.py ltms/services/redis_service.py.backup
        
        # Update port
        sed -i "s/port: int = [0-9]*/port: int = $WORKING_PORT/g" ltms/services/redis_service.py
        sed -i "s/port=[0-9]*/port=$WORKING_PORT/g" ltms/services/redis_service.py
        
        # Update password if needed
        if [ ! -z "$WORKING_PASSWORD" ]; then
            sed -i "s/password=\"[^\"]*\"/password=\"$WORKING_PASSWORD\"/g" ltms/services/redis_service.py
        fi
        
        echo "✅ Redis service configuration updated to port $WORKING_PORT"
    else
        echo "❌ Redis service file not found"
    fi
    
    rm /tmp/redis_working_port
else
    echo ""
    echo "❌ FAILURE: No working Redis connection found"
    echo "🔧 Manual intervention needed:"
    echo "   1. Install Redis if not installed"
    echo "   2. Check Redis configuration"
    echo "   3. Run setup_redis.sh"
fi

echo ""
echo "🎯 Redis diagnostic complete!"