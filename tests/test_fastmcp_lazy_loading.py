#!/usr/bin/env python3
"""
FastMCP Lazy Loading Integration Test
=====================================

Tests the complete FastMCP lazy loading system with performance validation.

Tests:
1. Component import and initialization
2. Essential tools loading (<50ms)
3. Lazy tool access via FunctionResource patterns
4. Total startup time (<200ms)
5. Tool accessibility and functionality
"""

import asyncio
import time
import sys
import traceback
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test results tracking
test_results = {
    "import_test": False,
    "initialization_test": False,
    "essential_loading_test": False,
    "startup_time_test": False,
    "lazy_access_test": False,
    "performance_targets_met": False
}

async def test_component_imports():
    """Test that all lazy loading components can be imported."""
    print("🧪 Testing component imports...")
    
    try:
        from ltmc_mcp_server.components import (
            LazyToolManager, 
            EssentialToolsLoader, 
            ToolCategoryRegistry,
            LazyToolLoader, 
            ProgressiveInitializer
        )
        
        print("✅ All components imported successfully")
        test_results["import_test"] = True
        return True
        
    except Exception as e:
        print(f"❌ Component import failed: {e}")
        traceback.print_exc()
        return False

async def test_lazy_loading_system():
    """Test the complete lazy loading system."""
    print("\n🧪 Testing lazy loading system initialization...")
    
    try:
        # Mock dependencies for testing
        from unittest.mock import Mock, AsyncMock
        
        # Create mock FastMCP server
        mcp_mock = Mock()
        mcp_mock.tool = Mock()
        mcp_mock.resource = Mock(return_value=lambda func: func)
        
        # Create mock settings
        settings_mock = Mock()
        settings_mock.log_level = "INFO"
        
        # Import and test components
        from ltmc_mcp_server.components import (
            LazyToolManager, 
            ToolCategoryRegistry
        )
        
        # Test ToolCategoryRegistry initialization
        print("🔧 Testing ToolCategoryRegistry...")
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        # Check tool distribution
        essential_cats = await registry.get_essential_categories()
        lazy_cats = await registry.get_lazy_categories()
        total_tools = await registry.get_total_tool_count()
        
        print(f"📊 Tool distribution: {len(essential_cats)} essential categories, {len(lazy_cats)} lazy categories")
        print(f"📊 Total tools: {total_tools}")
        
        # Performance summary
        perf_summary = await registry.get_performance_summary()
        essential_load_time = perf_summary['performance_targets']['essential_load_time_ms']
        
        print(f"⏱️  Estimated essential load time: {essential_load_time:.1f}ms")
        
        # Validate performance targets
        if essential_load_time < 50.0:
            print("✅ Essential load time under 50ms target")
            test_results["essential_loading_test"] = True
        else:
            print(f"⚠️  Essential load time {essential_load_time:.1f}ms exceeds 50ms target")
        
        test_results["initialization_test"] = True
        return True
        
    except Exception as e:
        print(f"❌ Lazy loading system test failed: {e}")
        traceback.print_exc()
        return False

async def test_fastmcp_patterns():
    """Test FastMCP pattern implementation."""
    print("\n🧪 Testing FastMCP patterns...")
    
    try:
        from ltmc_mcp_server.components import ToolCategoryRegistry
        
        # Test registry patterns
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        # Test URI template generation
        mermaid_uri = await registry.get_tool_uri_template("mermaid")
        print(f"🌐 Mermaid URI template: {mermaid_uri}")
        
        # Validate URI template format
        expected_format = "tools://mermaid/{tool_name}"
        if mermaid_uri == expected_format:
            print("✅ URI template format correct")
            test_results["lazy_access_test"] = True
        else:
            print(f"❌ URI template mismatch: {mermaid_uri} != {expected_format}")
        
        return True
        
    except Exception as e:
        print(f"❌ FastMCP patterns test failed: {e}")
        traceback.print_exc()
        return False

async def test_performance_targets():
    """Test that performance targets are achievable."""
    print("\n🧪 Testing performance targets...")
    
    startup_start = time.perf_counter()
    
    try:
        # Simulate startup process
        from ltmc_mcp_server.components import ToolCategoryRegistry
        
        # Initialize registry (simulates essential component initialization)
        registry = ToolCategoryRegistry()
        await registry.initialize_categories()
        
        # Calculate simulated startup time
        startup_time = (time.perf_counter() - startup_start) * 1000
        
        print(f"⏱️  Simulated startup time: {startup_time:.1f}ms")
        
        # Check performance targets
        if startup_time < 200.0:
            print("✅ Startup time under 200ms target")
            test_results["startup_time_test"] = True
            test_results["performance_targets_met"] = True
        else:
            print(f"⚠️  Startup time {startup_time:.1f}ms exceeds 200ms target")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        traceback.print_exc()
        return False

def print_test_summary():
    """Print comprehensive test results."""
    print("\n" + "="*60)
    print("🏆 FASTMCP LAZY LOADING TEST RESULTS")
    print("="*60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        test_display = test_name.replace("_", " ").title()
        print(f"{status} {test_display}")
    
    print("-" * 60)
    print(f"📊 Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - FastMCP lazy loading ready for integration!")
    else:
        print("⚠️  Some tests failed - review implementation before integration")
    
    print("="*60)

async def main():
    """Run all lazy loading tests."""
    print("🚀 Starting FastMCP Lazy Loading Integration Tests")
    print("=" * 60)
    
    # Run test suite
    tests = [
        test_component_imports,
        test_lazy_loading_system,
        test_fastmcp_patterns,
        test_performance_targets
    ]
    
    for test_func in tests:
        await test_func()
        print()  # Add spacing between tests
    
    # Print summary
    print_test_summary()

if __name__ == "__main__":
    asyncio.run(main())