#!/usr/bin/env python3
"""Verify that Redis connection fix is working."""

import asyncio
import subprocess
import sys
import redis.asyncio as aioredis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ensure_redis_running():
    """Ensure Redis is running on the correct port."""
    try:
        # First try to connect to see if it's already running
        client = aioredis.Redis(
            host="localhost",
            port=6380,
            password="ltmc_cache_2025",
            socket_connect_timeout=2
        )
        
        await client.ping()
        await client.aclose()
        print("✅ Redis is already running on port 6380")
        return True
        
    except Exception:
        print("⚠️  Redis not running, starting it...")
        
        try:
            # Run the setup script
            result = subprocess.run(
                ["bash", "setup_redis.sh"],
                capture_output=True,
                text=True,
                cwd="/home/feanor/Projects/lmtc"
            )
            
            if result.returncode == 0:
                print("✅ Redis setup script completed successfully")
                # Wait a moment for Redis to fully start
                await asyncio.sleep(3)
                return True
            else:
                print(f"❌ Redis setup failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Redis: {e}")
            return False

async def test_redis_with_services():
    """Test Redis connection with our actual services."""
    try:
        # Import and test our Redis service
        sys.path.append('/home/feanor/Projects/lmtc')
        from ltms.services.redis_service import get_redis_manager
        
        print("🔍 Testing Redis connection with our services...")
        
        manager = await get_redis_manager()
        
        if manager.is_connected:
            print("✅ Redis connection successful!")
            
            # Test basic operations
            await manager.client.set("test_connection", "success", ex=10)
            value = await manager.client.get("test_connection")
            print(f"✅ Redis operations test: {value}")
            
            return True
        else:
            print("❌ Redis connection failed in service")
            return False
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_registry():
    """Test the agent registry service that was failing."""
    try:
        sys.path.append('/home/feanor/Projects/lmtc')
        from ltms.services.agent_registry_service import get_agent_registry_service
        
        print("🔍 Testing agent registry service...")
        
        registry = await get_agent_registry_service()
        
        # Try to get active agents - this was the failing operation
        active_agents = await registry.get_active_agents()
        print(f"✅ Agent registry working! Active agents: {len(active_agents)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent registry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main verification function."""
    print("🚀 VERIFYING REDIS CONNECTION FIX")
    print("=" * 40)
    
    # Step 1: Ensure Redis is running
    if not await ensure_redis_running():
        print("❌ CRITICAL: Could not start Redis")
        return False
    
    print("\n" + "=" * 40)
    
    # Step 2: Test our Redis service
    if not await test_redis_with_services():
        print("❌ CRITICAL: Redis service connection failed")
        return False
    
    print("\n" + "=" * 40)
    
    # Step 3: Test the specific service that was failing
    if not await test_agent_registry():
        print("❌ CRITICAL: Agent registry still failing")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 SUCCESS: Redis connection fix verified!")
    print("✅ Redis is running on port 6380")
    print("✅ Redis service connects successfully") 
    print("✅ Agent registry service works")
    print("✅ No more 'Redis client not initialized' errors expected")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)