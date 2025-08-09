#!/usr/bin/env python3
"""Script to fix Redis connection issues by identifying and correcting the port configuration."""

import os
import subprocess
import asyncio
import redis.asyncio as aioredis

async def find_working_redis_port():
    """Find which port has a working Redis instance."""
    ports_to_try = [6379, 6380, 6381]
    passwords = ["ltmc_cache_2025", None]
    
    for port in ports_to_try:
        for password in passwords:
            try:
                client = aioredis.Redis(
                    host="localhost",
                    port=port,
                    password=password,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                
                response = await client.ping()
                await client.aclose()
                
                print(f"✅ Found working Redis on port {port} with {'password' if password else 'no password'}")
                return port, password
                
            except Exception:
                continue
    
    return None, None

def update_redis_service_port(port, password):
    """Update the Redis service configuration with the correct port."""
    redis_service_path = "ltms/services/redis_service.py"
    
    if not os.path.exists(redis_service_path):
        print(f"❌ Redis service file not found: {redis_service_path}")
        return False
    
    # Read current content
    with open(redis_service_path, 'r') as f:
        content = f.read()
    
    # Update port in the default initialization
    import re
    
    # Update the default port in __init__
    content = re.sub(
        r'port: int = \d+',
        f'port: int = {port}',
        content
    )
    
    # Update the port in get_redis_manager function
    content = re.sub(
        r'port=\d+',
        f'port={port}',
        content
    )
    
    # Update password if needed
    if password:
        content = re.sub(
            r'password="[^"]*"',
            f'password="{password}"',
            content
        )
    
    # Write updated content
    with open(redis_service_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated Redis service to use port {port}")
    return True

def start_redis_if_needed():
    """Start Redis if it's not running."""
    try:
        # Check if setup script exists
        if os.path.exists("setup_redis.sh"):
            print("🚀 Starting Redis server...")
            result = subprocess.run(["bash", "setup_redis.sh"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Redis server started successfully")
                return True
            else:
                print(f"❌ Failed to start Redis: {result.stderr}")
                return False
        else:
            print("❌ setup_redis.sh not found")
            return False
    except Exception as e:
        print(f"❌ Error starting Redis: {e}")
        return False

async def main():
    """Main function to fix Redis connection."""
    print("🔧 LTMC Redis Connection Fix")
    print("=" * 40)
    
    # First, try to find existing Redis
    port, password = await find_working_redis_port()
    
    if not port:
        print("⚠️  No working Redis found, attempting to start...")
        if start_redis_if_needed():
            # Try again after starting
            await asyncio.sleep(2)
            port, password = await find_working_redis_port()
    
    if port:
        print(f"✅ Redis is working on port {port}")
        
        # Update the service configuration
        if update_redis_service_port(port, password):
            print("✅ Redis service configuration updated")
            print("🎯 Redis connection issues should be resolved")
        else:
            print("❌ Failed to update service configuration")
    else:
        print("❌ Could not establish Redis connection")
        print("🔧 Manual steps needed:")
        print("   1. Install Redis: sudo apt-get install redis-server")
        print("   2. Run setup: ./setup_redis.sh")
        print("   3. Run this script again")

if __name__ == "__main__":
    asyncio.run(main())