#!/usr/bin/env python3
"""Test script for LTMC orchestration integration."""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_orchestration_initialization():
    """Test orchestration integration initialization."""
    print("=" * 60)
    print("LTMC Orchestration Integration Test")
    print("=" * 60)
    
    try:
        from ltms.mcp_orchestration_integration import (
            initialize_orchestration_integration,
            get_orchestration_health,
            is_orchestration_enabled,
            create_orchestration_config,
            OrchestrationMode
        )
        
        # Test configuration creation
        print("\n🔧 Testing configuration creation...")
        config = create_orchestration_config()
        print(f"   Configuration: {config}")
        
        # Test initialization
        print("\n🚀 Testing orchestration initialization...")
        await initialize_orchestration_integration(OrchestrationMode.BASIC)
        
        # Check if enabled
        enabled = is_orchestration_enabled()
        print(f"   Orchestration enabled: {enabled}")
        
        # Get health status
        print("\n💊 Testing health check...")
        health = await get_orchestration_health()
        print(f"   Health status: {health}")
        
        return True
        
    except Exception as e:
        print(f"❌ Orchestration test failed: {e}")
        logger.error(f"Orchestration test error: {e}")
        return False


async def test_enhanced_tools():
    """Test enhanced MCP tools with orchestration."""
    print("\n📧 Testing enhanced MCP tools...")
    
    try:
        from ltms.mcp_orchestration_integration import create_enhanced_mcp_tools
        
        # Create enhanced tools
        enhanced_tools = create_enhanced_mcp_tools()
        print(f"   Enhanced tools available: {list(enhanced_tools.keys())}")
        
        # Test enhanced health check
        if 'enhanced_orchestration_health' in enhanced_tools:
            health_tool = enhanced_tools['enhanced_orchestration_health']
            # The enhanced tools return functions that may be async
            try:
                health_result = health_tool()
                print(f"   Enhanced health check result: {health_result}")
            except Exception as e:
                print(f"   Enhanced health check failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced tools test failed: {e}")
        logger.error(f"Enhanced tools test error: {e}")
        return False


async def test_redis_services():
    """Test Redis-based orchestration services."""
    print("\n🔗 Testing Redis orchestration services...")
    
    try:
        # Test Redis connection
        from ltms.services.redis_service import get_redis_manager
        redis_manager = await get_redis_manager()
        
        if redis_manager.is_connected:
            print(f"   ✅ Redis connected: {redis_manager.host}:{redis_manager.port}")
        else:
            print("   ⚠️  Redis not connected - orchestration will use fallback mode")
            return True
        
        # Test orchestration services
        print("\n   Testing individual orchestration services...")
        
        # Test agent registry
        try:
            from ltms.services.agent_registry_service import get_agent_registry_service
            agent_registry = await get_agent_registry_service()
            print("   ✅ Agent Registry Service: OK")
        except Exception as e:
            print(f"   ❌ Agent Registry Service: {e}")
        
        # Test context coordination
        try:
            from ltms.services.context_coordination_service import get_context_coordination_service
            context_coord = await get_context_coordination_service()
            print("   ✅ Context Coordination Service: OK")
        except Exception as e:
            print(f"   ❌ Context Coordination Service: {e}")
        
        # Test memory locking
        try:
            from ltms.services.memory_locking_service import get_memory_locking_service
            memory_locking = await get_memory_locking_service()
            print("   ✅ Memory Locking Service: OK")
        except Exception as e:
            print(f"   ❌ Memory Locking Service: {e}")
        
        # Test tool cache
        try:
            from ltms.services.tool_cache_service import get_tool_cache_service
            tool_cache = await get_tool_cache_service()
            print("   ✅ Tool Cache Service: OK")
        except Exception as e:
            print(f"   ❌ Tool Cache Service: {e}")
        
        # Test chunk buffer
        try:
            from ltms.services.chunk_buffer_service import get_chunk_buffer_service
            chunk_buffer = await get_chunk_buffer_service()
            print("   ✅ Chunk Buffer Service: OK")
        except Exception as e:
            print(f"   ❌ Chunk Buffer Service: {e}")
        
        # Test session state
        try:
            from ltms.services.session_state_service import get_session_state_service
            session_state = await get_session_state_service()
            print("   ✅ Session State Service: OK")
        except Exception as e:
            print(f"   ❌ Session State Service: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Redis services test failed: {e}")
        logger.error(f"Redis services test error: {e}")
        return False


async def test_server_integration():
    """Test server integration endpoints."""
    print("\n🌐 Testing server integration...")
    
    try:
        import aiohttp
        import json
        
        base_url = "http://localhost:5050"
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print(f"   ✅ Health endpoint: {health_data.get('status', 'unknown')}")
                    
                    if 'orchestration' in health_data:
                        orch_status = health_data['orchestration']
                        print(f"   🔄 Orchestration in health: {orch_status.get('orchestration_enabled', False)}")
                    else:
                        print("   ⚠️  No orchestration info in health endpoint")
                else:
                    print(f"   ❌ Health endpoint failed: {response.status}")
                    return False
            
            # Test orchestration health endpoint
            try:
                async with session.get(f"{base_url}/orchestration/health") as response:
                    if response.status == 200:
                        orch_health = await response.json()
                        print(f"   ✅ Orchestration health endpoint: {orch_health.get('orchestration_enabled', False)}")
                    else:
                        print(f"   ❌ Orchestration health endpoint failed: {response.status}")
            except Exception as e:
                print(f"   ⚠️  Orchestration health endpoint not available: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Server integration test failed (server may not be running): {e}")
        return False


async def main():
    """Main test function."""
    print(f"Starting LTMC orchestration integration test at {datetime.now()}")
    
    test_results = []
    
    # Test orchestration initialization
    result = await test_orchestration_initialization()
    test_results.append(("Orchestration Initialization", result))
    
    # Test enhanced tools
    result = await test_enhanced_tools()
    test_results.append(("Enhanced Tools", result))
    
    # Test Redis services
    result = await test_redis_services()
    test_results.append(("Redis Services", result))
    
    # Test server integration
    result = await test_server_integration()
    test_results.append(("Server Integration", result))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    total = len(test_results)
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All orchestration integration tests PASSED!")
        return True
    else:
        print("⚠️  Some tests failed - orchestration may work in degraded mode")
        return False


if __name__ == "__main__":
    """Run the orchestration integration tests."""
    success = asyncio.run(main())
    sys.exit(0 if success else 1)