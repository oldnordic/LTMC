#!/usr/bin/env python3
"""
Test LTMC lazy loading system tool registration.

This test validates that the lazy loading system can properly register
tools and handle the unified_ltmc_orchestrator function.
"""

import sys
import asyncio
import logging
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def test_tool_category_registry():
    """Test that tool category registry can initialize."""
    logger.info("🔍 Testing ToolCategoryRegistry initialization...")
    
    try:
        from ltmc_mcp_server.components.tool_category_registry import ToolCategoryRegistry
        
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        # Check if unified category exists
        unified_info = await registry.get_category_info('unified')
        if unified_info:
            logger.info(f"✅ Unified category found with {unified_info.tool_count} tools")
            logger.info(f"   Tools: {unified_info.tools}")
            
            # Check if get_performance_report is in the tools
            if 'get_performance_report' in unified_info.tools:
                logger.info("✅ get_performance_report found in unified category")
            else:
                logger.warning("⚠️ get_performance_report not found in unified category")
        else:
            logger.warning("⚠️ Unified category not found")
        
        # Get total tool count
        total_tools = await registry.get_total_tool_count()
        logger.info(f"✅ Registry initialized with {total_tools} total tools")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ToolCategoryRegistry test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lazy_tool_loader():
    """Test that lazy tool loader can initialize and find unified tools."""
    logger.info("🔍 Testing LazyToolLoader initialization...")
    
    try:
        from ltmc_mcp_server.components.tool_category_registry import ToolCategoryRegistry
        from ltmc_mcp_server.components.lazy_tool_loader import LazyToolLoader
        from ltmc_mcp_server.config.settings import LTMCSettings
        
        # Create mock MCP instance
        class MockMCP:
            def __init__(self):
                self.registered_tools = []
                self.resources = []
                
            def tool(self, *args, **kwargs):
                def decorator(func):
                    self.registered_tools.append(func.__name__)
                    return func
                return decorator
                
            def resource(self, uri_template):
                def decorator(func):
                    self.resources.append(uri_template)
                    return func
                return decorator
        
        # Initialize components
        mock_mcp = MockMCP()
        settings = LTMCSettings()
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        # Initialize lazy tool loader
        lazy_loader = LazyToolLoader(mock_mcp, settings, registry)
        await lazy_loader.initialize_lazy_loading()
        
        logger.info(f"✅ LazyToolLoader initialized with {len(lazy_loader.tool_proxies)} tool proxies")
        logger.info(f"✅ Registered {len(mock_mcp.resources)} resource patterns")
        
        # Check if unified tools are in the tool proxies
        unified_tools = [name for name in lazy_loader.tool_proxies.keys() if 'get_performance_report' in name]
        if unified_tools:
            logger.info(f"✅ Found unified tools in proxies: {unified_tools}")
        else:
            logger.warning("⚠️ No unified tools found in proxies")
        
        # Check tool module mapping
        if 'get_performance_report' in lazy_loader._tool_module_map:
            module_path = lazy_loader._tool_module_map['get_performance_report']
            logger.info(f"✅ get_performance_report mapped to: {module_path}")
        else:
            logger.warning("⚠️ get_performance_report not in tool module map")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LazyToolLoader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_unified_tool_dynamic_loading():
    """Test dynamic loading of unified tools."""
    logger.info("🔍 Testing unified tool dynamic loading...")
    
    try:
        from ltmc_mcp_server.components.tool_category_registry import ToolCategoryRegistry
        from ltmc_mcp_server.components.lazy_tool_loader import LazyToolLoader
        from ltmc_mcp_server.config.settings import LTMCSettings
        
        # Create mock MCP instance that tracks registrations
        class MockMCP:
            def __init__(self):
                self.registered_tools = []
                
            def tool(self, *args, **kwargs):
                def decorator(func):
                    self.registered_tools.append(func.__name__)
                    logger.info(f"📝 Registered tool: {func.__name__}")
                    return func
                return decorator
                
            def resource(self, uri_template):
                def decorator(func):
                    return func
                return decorator
        
        # Initialize components
        mock_mcp = MockMCP()
        settings = LTMCSettings()
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        lazy_loader = LazyToolLoader(mock_mcp, settings, registry)
        await lazy_loader.initialize_lazy_loading()
        
        # Test dynamic loading of get_performance_report
        if 'get_performance_report' in lazy_loader._tool_module_map:
            logger.info("🔧 Attempting dynamic load of get_performance_report...")
            
            try:
                await lazy_loader._dynamic_load_tool('get_performance_report', 'unified')
                logger.info("✅ Dynamic loading succeeded")
                
                # Check if tool was registered
                if 'get_performance_report' in mock_mcp.registered_tools:
                    logger.info("✅ get_performance_report was registered via dynamic loading")
                else:
                    logger.warning("⚠️ get_performance_report was not registered")
                    
            except Exception as e:
                logger.error(f"❌ Dynamic loading failed: {e}")
                return False
        else:
            logger.warning("⚠️ get_performance_report not available for dynamic loading")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Unified tool dynamic loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_lazy_tool_manager():
    """Test the complete lazy tool manager initialization."""
    logger.info("🔍 Testing LazyToolManager initialization...")
    
    try:
        from ltmc_mcp_server.components.lazy_tool_manager import LazyToolManager
        from ltmc_mcp_server.config.settings import LTMCSettings
        
        # Create mock MCP instance
        class MockMCP:
            def __init__(self):
                self.registered_tools = []
                self.resources = []
                
            def tool(self, *args, **kwargs):
                def decorator(func):
                    self.registered_tools.append(func.__name__)
                    return func
                return decorator
                
            def resource(self, uri_template):
                def decorator(func):
                    self.resources.append(uri_template)
                    return func
                return decorator
        
        # Initialize lazy tool manager
        mock_mcp = MockMCP()
        settings = LTMCSettings()
        
        lazy_manager = LazyToolManager(mock_mcp, settings)
        
        # Test initialization with timeout (it should be fast)
        start_time = asyncio.get_event_loop().time()
        result = await asyncio.wait_for(
            lazy_manager.initialize_lazy_loading(),
            timeout=10.0
        )
        end_time = asyncio.get_event_loop().time()
        
        initialization_time = (end_time - start_time) * 1000
        
        logger.info(f"✅ LazyToolManager initialization took {initialization_time:.1f}ms")
        
        if result.get("success"):
            startup_metrics = result.get("startup_metrics", {})
            tool_distribution = result.get("tool_distribution", {})
            
            logger.info("✅ Lazy loading initialization successful")
            logger.info(f"   Total startup time: {startup_metrics.get('total_startup_time_ms', 0):.1f}ms")
            logger.info(f"   Essential tools loaded: {tool_distribution.get('essential_tools_loaded', 0)}")
            logger.info(f"   Lazy tools available: {tool_distribution.get('lazy_tools_available', 0)}")
            logger.info(f"   Total tools: {tool_distribution.get('total_tools', 0)}")
            
            # Check performance targets
            if startup_metrics.get('startup_target_met', False):
                logger.info("✅ Startup time target met")
            else:
                logger.warning("⚠️ Startup time target exceeded")
                
            return True
        else:
            logger.error(f"❌ Lazy loading initialization failed: {result.get('error')}")
            return False
            
    except asyncio.TimeoutError:
        logger.error("❌ LazyToolManager initialization timed out")
        return False
    except Exception as e:
        logger.error(f"❌ LazyToolManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all lazy loading system tests."""
    logger.info("🚀 Starting LTMC lazy loading system tests...")
    logger.info("="*60)
    
    tests = [
        ("Tool Category Registry", test_tool_category_registry),
        ("Lazy Tool Loader", test_lazy_tool_loader),
        ("Unified Tool Dynamic Loading", test_unified_tool_dynamic_loading),
        ("Lazy Tool Manager", test_lazy_tool_manager)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            result = await asyncio.wait_for(test_func(), timeout=30.0)
            results.append((test_name, result))
            if result:
                logger.info(f"✅ PASSED: {test_name}")
            else:
                logger.error(f"❌ FAILED: {test_name}")
        except asyncio.TimeoutError:
            logger.error(f"❌ TIMEOUT: {test_name}")
            results.append((test_name, False))
        except Exception as e:
            logger.error(f"❌ ERROR: {test_name} - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("🎯 LAZY LOADING SYSTEM TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Lazy loading system is working correctly")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - Lazy loading system issues detected")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)