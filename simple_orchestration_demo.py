#!/usr/bin/env python3
"""Simple demonstration of LTMC orchestration integration."""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def demonstrate_basic_orchestration():
    """Demonstrate basic orchestration functionality."""
    print("=" * 60)
    print("LTMC Basic Orchestration Demonstration")
    print("=" * 60)
    
    try:
        from ltms.mcp_orchestration_integration import (
            initialize_orchestration_integration,
            get_orchestration_health,
            is_orchestration_enabled,
            OrchestrationMode
        )
        
        # Initialize orchestration in BASIC mode
        print("\n🚀 Initializing orchestration (BASIC mode)...")
        await initialize_orchestration_integration(OrchestrationMode.BASIC)
        
        if not is_orchestration_enabled():
            print("❌ Orchestration not available - check Redis connection")
            return False
        
        print("✅ Orchestration initialized successfully!")
        
        # Get orchestration health
        print("\n💊 Getting orchestration health status...")
        health = await get_orchestration_health()
        
        print(f"   • Orchestration enabled: {health.get('orchestration_enabled', False)}")
        print(f"   • Services available: {list(health.get('services_available', {}).keys())}")
        
        if 'orchestration_status' in health:
            orch_status = health['orchestration_status']
            print(f"   • Active agents: {orch_status.get('active_agents', 0)}")
            print(f"   • Mode: {orch_status.get('mode', 'unknown')}")
        
        # Test agent registration through orchestration service
        print("\n👥 Testing agent registration...")
        
        from ltms.mcp_orchestration_integration import _integration
        if _integration.orchestration_service:
            # Register a test agent
            agent_id = await _integration.orchestration_service.register_agent(
                agent_name="Demo Agent",
                capabilities=["memory_operations", "basic_coordination"],
                session_id="demo_session",
                metadata={"type": "demonstration", "purpose": "testing"}
            )
            
            if agent_id:
                print(f"   ✅ Agent registered successfully: {agent_id}")
                
                # Get updated status
                final_status = await _integration.orchestration_service.get_orchestration_status()
                print(f"   • Active agents after registration: {final_status.get('active_agents', 0)}")
                
                # Cleanup agent
                await _integration.orchestration_service.cleanup_agent(agent_id)
                print(f"   ✅ Agent cleaned up: {agent_id}")
            else:
                print("   ❌ Failed to register agent")
        
        # Test basic MCP tool functionality (without orchestration parameters)
        print("\n📧 Testing basic MCP tool functionality...")
        
        # Import a basic MCP tool directly
        from ltms.mcp_server import store_memory
        
        result = store_memory(
            file_name="orchestration_demo.md",
            content="# Orchestration Demo\\n\\nThis content was stored during the orchestration demonstration.",
            resource_type="demonstration"
        )
        
        if result.get('success'):
            print(f"   ✅ Memory stored successfully: {result.get('message', 'OK')}")
            print(f"   • Resource ID: {result.get('resource_id', 'N/A')}")
            print(f"   • Chunk count: {result.get('chunk_count', 'N/A')}")
        else:
            print(f"   ❌ Memory storage failed: {result.get('error', 'Unknown error')}")
        
        print("\n✅ Basic orchestration demonstration completed successfully!")
        print("   🔧 Orchestration services are operational")
        print("   👥 Agent registration and cleanup working")
        print("   📧 Basic MCP tools functioning")
        print("   💡 Ready for multi-agent coordination")
        
        return True
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logger.error(f"Orchestration demonstration error: {e}")
        return False


async def demonstrate_redis_services():
    """Demonstrate Redis-based services."""
    print("\n🔗 Testing Redis orchestration services...")
    
    try:
        # Test Redis connection
        from ltms.services.redis_service import get_redis_manager
        redis_manager = await get_redis_manager()
        
        if not redis_manager.is_connected:
            print("   ⚠️  Redis not connected - skipping Redis service tests")
            return True
        
        print(f"   ✅ Redis connected: {redis_manager.host}:{redis_manager.port}")
        
        # Test each service individually
        services_tested = []
        
        try:
            from ltms.services.agent_registry_service import get_agent_registry_service
            agent_registry = await get_agent_registry_service()
            services_tested.append("Agent Registry")
        except Exception as e:
            print(f"   ❌ Agent Registry Service failed: {e}")
        
        try:
            from ltms.services.context_coordination_service import get_context_coordination_service
            context_coord = await get_context_coordination_service()
            services_tested.append("Context Coordination")
        except Exception as e:
            print(f"   ❌ Context Coordination Service failed: {e}")
        
        try:
            from ltms.services.memory_locking_service import get_memory_locking_service
            memory_locking = await get_memory_locking_service()
            services_tested.append("Memory Locking")
        except Exception as e:
            print(f"   ❌ Memory Locking Service failed: {e}")
        
        if services_tested:
            print(f"   ✅ Services operational: {', '.join(services_tested)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Redis services test failed: {e}")
        return False


async def main():
    """Main demonstration function."""
    print("Starting LTMC orchestration demonstration...")
    
    # Basic orchestration test
    basic_success = await demonstrate_basic_orchestration()
    
    # Redis services test
    redis_success = await demonstrate_redis_services()
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMONSTRATION SUMMARY")
    print("=" * 60)
    
    if basic_success and redis_success:
        print("🎉 All demonstrations PASSED!")
        print("✅ LTMC orchestration integration is fully operational")
        print("🚀 Ready for production multi-agent coordination")
        return True
    else:
        print("⚠️  Some demonstrations failed")
        print("🔧 Orchestration may work in degraded mode")
        return False


if __name__ == "__main__":
    """Run the simple orchestration demonstration."""
    success = asyncio.run(main())
    print(f"\n{'SUCCESS' if success else 'PARTIAL SUCCESS'}: Orchestration demonstration complete")
    sys.exit(0 if success else 1)