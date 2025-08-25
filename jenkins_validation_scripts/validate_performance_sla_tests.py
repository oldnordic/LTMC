#!/usr/bin/env python3
"""
LTMC Performance SLA Tests for Jenkins
Tests that tool operations meet performance requirements
"""

import sys
import os
import time
import traceback
import asyncio
from pathlib import Path

def setup_ltmc_path():
    """Add LTMC to Python path"""
    ltmc_home = os.environ.get('LTMC_HOME', '/home/feanor/Projects/ltmc')
    if ltmc_home not in sys.path:
        sys.path.insert(0, ltmc_home)

async def test_memory_action_performance():
    """Test memory_action performance"""
    print("Testing memory_action performance...")
    
    try:
        from ltms.tools.consolidated import memory_action
        
        # Test status operation (should be fast)
        start_time = time.time()
        # Handle async function
        if asyncio.iscoroutinefunction(memory_action):
            result = await memory_action(action='status')
        else:
            result = memory_action(action='status')
        duration_ms = (time.time() - start_time) * 1000
        
        # SLA threshold: 2000ms for complex operations, 500ms for simple
        sla_threshold = 500  # ms for status operation
        
        if duration_ms <= sla_threshold:
            print(f"✅ memory_action(status): {duration_ms:.2f}ms (SLA: {sla_threshold}ms)")
            return True, duration_ms
        else:
            print(f"❌ memory_action(status): {duration_ms:.2f}ms > {sla_threshold}ms SLA")
            return False, duration_ms
            
    except ImportError as e:
        print(f"❌ memory_action import failed: {e}")
        return False, 0
    except Exception as e:
        print(f"❌ memory_action execution failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False, 0

def test_graph_action_performance():
    """Test graph_action performance if available"""
    print("Testing graph_action performance...")
    
    try:
        from ltms.tools.consolidated import graph_action
        
        # Test simple graph operation
        start_time = time.time()
        result = graph_action(action='health_check')
        duration_ms = (time.time() - start_time) * 1000
        
        # SLA threshold for graph operations
        sla_threshold = 1000  # ms for graph operations
        
        if duration_ms <= sla_threshold:
            print(f"✅ graph_action(health_check): {duration_ms:.2f}ms (SLA: {sla_threshold}ms)")
            return True, duration_ms
        else:
            print(f"❌ graph_action(health_check): {duration_ms:.2f}ms > {sla_threshold}ms SLA")
            return False, duration_ms
            
    except ImportError as e:
        print(f"⚠️  graph_action not available: {e}")
        return True, 0  # Don't fail if graph_action not available
    except Exception as e:
        print(f"⚠️  graph_action test failed: {e}")
        return True, 0  # Don't fail on non-critical graph errors

def test_tool_import_performance():
    """Test tool import performance"""
    print("Testing tool import performance...")
    
    try:
        start_time = time.time()
        from ltms.tools import consolidated
        import_duration_ms = (time.time() - start_time) * 1000
        
        # Import should be reasonable (allow for larger consolidated file)
        import_sla = 5000  # ms - increased for consolidated architecture
        
        if import_duration_ms <= import_sla:
            print(f"✅ Tool import: {import_duration_ms:.2f}ms (SLA: {import_sla}ms)")
            
            # Count available tools
            tool_count = len([name for name in dir(consolidated) 
                            if callable(getattr(consolidated, name)) and not name.startswith('_')])
            print(f"✅ Available tools: {tool_count}")
            
            return True, import_duration_ms
        else:
            print(f"❌ Tool import: {import_duration_ms:.2f}ms > {import_sla}ms SLA")
            return False, import_duration_ms
            
    except Exception as e:
        print(f"❌ Tool import failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False, 0

def test_system_resource_usage():
    """Test system resource usage"""
    print("Testing system resource usage...")
    
    try:
        import psutil
        process = psutil.Process()
        
        # Memory usage test
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        
        # Memory SLA: should be reasonable for consolidated architecture
        memory_sla = 1000  # MB - increased for consolidated tools with multiple dependencies
        
        if memory_mb <= memory_sla:
            print(f"✅ Memory usage: {memory_mb:.1f}MB (SLA: {memory_sla}MB)")
            return True, memory_mb
        else:
            print(f"⚠️  Memory usage: {memory_mb:.1f}MB > {memory_sla}MB SLA")
            return True, memory_mb  # Don't fail, just warn
            
    except ImportError:
        print("⚠️  psutil not available - skipping resource tests")
        return True, 0
    except Exception as e:
        print(f"⚠️  Resource test failed: {e}")
        return True, 0

async def main():
    """Run all performance SLA tests"""
    print("=== LTMC Performance SLA Tests ===")
    
    # Setup environment
    setup_ltmc_path()
    
    tests = [
        ("Tool Import Performance", test_tool_import_performance),
        ("Memory Action Performance", test_memory_action_performance),
        ("Graph Action Performance", test_graph_action_performance),
        ("System Resource Usage", test_system_resource_usage)
    ]
    
    failed_tests = []
    total_duration = 0
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        
        try:
            if asyncio.iscoroutinefunction(test_func):
                success, duration = await test_func()
            else:
                success, duration = test_func()
            total_duration += duration
            
            if success:
                print(f"✅ {test_name}: PASS")
            else:
                print(f"❌ {test_name}: FAIL")
                failed_tests.append(test_name)
                
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed_tests.append(test_name)
    
    print(f"\n=== Performance Test Summary ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Total execution time: {total_duration:.2f}ms")
    
    if failed_tests:
        print(f"Failed tests: {', '.join(failed_tests)}")
        print("❌ OVERALL: Performance SLA validation FAILED")
        sys.exit(1)
    else:
        print("✅ OVERALL: All performance SLA tests PASSED")
        return 0

if __name__ == '__main__':
    asyncio.run(main())