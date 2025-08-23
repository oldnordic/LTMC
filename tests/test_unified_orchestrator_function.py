#!/usr/bin/env python3
"""
Test unified_ltmc_orchestrator function existence and registration.

This test validates that the unified_ltmc_orchestrator function is properly
exported and can be called by the lazy loading system.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_unified_function_exists():
    """Test that unified_ltmc_orchestrator function exists and is callable."""
    logger.info("🔍 Testing unified_ltmc_orchestrator function existence...")
    
    try:
        # Import the unified tools module
        from ltmc_mcp_server.tools.unified.unified_tools import unified_ltmc_orchestrator, register_unified_tools
        
        # Verify function exists
        assert callable(unified_ltmc_orchestrator), "unified_ltmc_orchestrator is not callable"
        assert callable(register_unified_tools), "register_unified_tools is not callable"
        
        logger.info("✅ unified_ltmc_orchestrator function found and callable")
        
        # Check function signature
        import inspect
        sig = inspect.signature(unified_ltmc_orchestrator)
        params = list(sig.parameters.keys())
        
        expected_params = ['mcp', 'settings']
        assert params == expected_params, f"Expected params {expected_params}, got {params}"
        
        logger.info("✅ Function signature is correct: (mcp, settings)")
        
        # Verify it's in __all__
        from ltmc_mcp_server.tools.unified import unified_tools
        assert hasattr(unified_tools, '__all__'), "Module missing __all__ export list"
        assert 'unified_ltmc_orchestrator' in unified_tools.__all__, "unified_ltmc_orchestrator not in __all__"
        
        logger.info("✅ unified_ltmc_orchestrator properly exported in __all__")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False
    except AssertionError as e:
        logger.error(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_function_discovery():
    """Test that the lazy loading system can discover the function."""
    logger.info("🔍 Testing function discovery by lazy loading system...")
    
    try:
        # Simulate lazy loading discovery
        module_path = "ltmc_mcp_server.tools.unified.unified_tools"
        
        import importlib
        module = importlib.import_module(module_path)
        
        # Test getattr access (what lazy loader uses)
        func = getattr(module, 'unified_ltmc_orchestrator', None)
        assert func is not None, "getattr failed to find unified_ltmc_orchestrator"
        assert callable(func), "Found function is not callable"
        
        logger.info("✅ Function discovery via getattr successful")
        
        # Test dynamic import pattern used by lazy loader
        registration_func_name = "unified_ltmc_orchestrator"  # PyInstaller alias pattern
        register_func = getattr(module, registration_func_name, None)
        
        if not register_func:
            # Fallback to register_unified_tools
            register_func = getattr(module, "register_unified_tools", None)
        
        assert register_func is not None, f"Neither {registration_func_name} nor register_unified_tools found"
        
        logger.info("✅ Dynamic import pattern successful")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Function discovery failed: {e}")
        return False


async def test_mock_registration():
    """Test that the function can be called with mock parameters."""
    logger.info("🔍 Testing mock registration call...")
    
    try:
        from ltmc_mcp_server.tools.unified.unified_tools import unified_ltmc_orchestrator
        from ltmc_mcp_server.config.settings import LTMCSettings
        
        # Create mock MCP instance (minimal interface)
        class MockMCP:
            def __init__(self):
                self.registered_tools = []
                
            def tool(self, *args, **kwargs):
                def decorator(func):
                    self.registered_tools.append(func.__name__)
                    return func
                return decorator
        
        # Create mock settings
        settings = LTMCSettings()
        mock_mcp = MockMCP()
        
        # Call the function (should not raise exceptions)
        unified_ltmc_orchestrator(mock_mcp, settings)
        
        # Verify tool was registered
        assert len(mock_mcp.registered_tools) > 0, "No tools were registered"
        assert 'get_performance_report' in mock_mcp.registered_tools, "get_performance_report not registered"
        
        logger.info("✅ Mock registration successful")
        logger.info(f"   Registered tools: {mock_mcp.registered_tools}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Mock registration failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    logger.info("🚀 Starting unified_ltmc_orchestrator function validation tests...")
    logger.info("="*60)
    
    tests = [
        ("Function Exists", test_unified_function_exists),
        ("Function Discovery", test_function_discovery),
        ("Mock Registration", test_mock_registration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        
        results.append((test_name, result))
        if result:
            logger.info(f"✅ PASSED: {test_name}")
        else:
            logger.error(f"❌ FAILED: {test_name}")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("🎯 TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    logger.info(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - unified_ltmc_orchestrator function is working correctly")
        return True
    else:
        logger.error("💥 SOME TESTS FAILED - function issues detected")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)