#!/usr/bin/env python3
"""Debug script to test Redis connection and identify issues."""

import asyncio
import redis.asyncio as aioredis
import logging
import subprocess
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_redis_connection(host="localhost", port=6381, password="ltmc_cache_2025"):
    """Test Redis connection with detailed diagnostics."""
    print(f"🔍 Testing Redis connection to {host}:{port}")
    
    try:
        # Test basic connection
        client = aioredis.Redis(
            host=host,
            port=port,
            password=password,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test ping
        response = await client.ping()
        print(f"✅ Redis PING successful: {response}")
        
        # Test basic operations
        await client.set("test_key", "test_value", ex=10)
        value = await client.get("test_key")
        print(f"✅ Redis SET/GET test: {value}")
        
        # Get server info
        info = await client.info()
        print(f"✅ Redis server version: {info.get('redis_version', 'unknown')}")
        print(f"✅ Connected clients: {info.get('connected_clients', 0)}")
        print(f"✅ Used memory: {info.get('used_memory_human', 'unknown')}")
        
        await client.aclose()
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

async def test_different_ports():
    """Test connection on different ports."""
    ports = [6379, 6380, 6381]
    password = "ltmc_cache_2025"
    
    for port in ports:
        print(f"\n🔍 Testing port {port}...")
        success = await test_redis_connection(port=port, password=password)
        if success:
            print(f"✅ Found working Redis on port {port}")
            return port
        else:
            # Try without password
            print(f"🔍 Trying port {port} without password...")
            try:
                client = aioredis.Redis(host="localhost", port=port, socket_connect_timeout=2)
                response = await client.ping()
                print(f"✅ Redis PING successful on port {port} without password: {response}")
                await client.aclose()
                return port
            except Exception as e:
                print(f"❌ Port {port} failed even without password: {e}")
    
    return None

def check_redis_processes():
    """Check for running Redis processes."""
    try:
        result = subprocess.run(['ps', 'aux', '|', 'grep', 'redis'], 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print("🔍 Running Redis processes:")
            print(result.stdout)
        else:
            print("❌ No Redis processes found")
            
        # Check ports
        result = subprocess.run(['netstat', '-tlnp', '|', 'grep', '6379\\|6380\\|6381'], 
                              shell=True, capture_output=True, text=True)
        if result.stdout:
            print("🔍 Redis ports in use:")
            print(result.stdout)
        else:
            print("❌ No Redis ports found listening")
            
    except Exception as e:
        print(f"❌ Failed to check processes: {e}")

async def main():
    """Main diagnostic function."""
    print("🚀 LTMC Redis Connection Diagnostics")
    print("=" * 50)
    
    # Check for running processes
    check_redis_processes()
    
    print("\n" + "=" * 50)
    print("🔍 Testing Redis connections...")
    
    # Test different ports
    working_port = await test_different_ports()
    
    if working_port:
        print(f"\n✅ SUCCESS: Redis is working on port {working_port}")
        print(f"🔧 Update redis_service.py to use port {working_port}")
    else:
        print("\n❌ FAILURE: No working Redis connection found")
        print("🔧 Need to start Redis server first")
        print("   Run: ./setup_redis.sh")

if __name__ == "__main__":
    asyncio.run(main())