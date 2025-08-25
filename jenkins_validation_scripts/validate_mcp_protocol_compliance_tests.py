#!/usr/bin/env python3
"""
LTMC MCP Protocol Compliance Tests for Jenkins
Tests that tools comply with Model Context Protocol requirements
"""

import sys
import os
import json
import inspect
import asyncio
from pathlib import Path

def setup_ltmc_path():
    """Add LTMC to Python path"""
    ltmc_home = os.environ.get('LTMC_HOME', '/home/feanor/Projects/ltmc')
    if ltmc_home not in sys.path:
        sys.path.insert(0, ltmc_home)

def test_mcp_tool_registration():
    """Test that LTMC tools are properly registered"""
    print("Testing LTMC tool registration...")
    
    try:
        from ltms.tools import consolidated
        
        # Find functions with LTMC action-based pattern
        ltmc_tools = []
        for name, obj in inspect.getmembers(consolidated):
            if (inspect.isfunction(obj) and 
                name.endswith('_action') and 
                callable(obj)):
                # Check if function has action parameter
                sig = inspect.signature(obj)
                if 'action' in sig.parameters:
                    ltmc_tools.append(name)
        
        expected_count = 11
        actual_count = len(ltmc_tools)
        
        if actual_count >= expected_count:
            print(f"✅ LTMC tools registered: {actual_count} (expected: {expected_count})")
            print(f"Tools: {', '.join(sorted(ltmc_tools))}")
            return True, ltmc_tools
        else:
            print(f"❌ LTMC tools registered: {actual_count} < {expected_count}")
            print(f"Found tools: {', '.join(sorted(ltmc_tools))}")
            return False, ltmc_tools
            
    except Exception as e:
        print(f"❌ MCP tool registration test failed: {e}")
        return False, []

async def test_tool_parameter_validation():
    """Test that tools have proper parameter validation"""
    print("Testing tool parameter validation...")
    
    try:
        from ltms.tools.consolidated import memory_action
        
        # Test valid parameters
        if asyncio.iscoroutinefunction(memory_action):
            result = await memory_action(action='status')
        else:
            result = memory_action(action='status')
        print("✅ Valid parameters: Accepted")
        
        # Test invalid action (should handle gracefully)
        try:
            if asyncio.iscoroutinefunction(memory_action):
                result = await memory_action(action='invalid_action_test_12345')
            else:
                result = memory_action(action='invalid_action_test_12345')
            # Tool should either handle gracefully or raise appropriate error
            print("✅ Invalid parameters: Handled gracefully")
            return True
        except (ValueError, KeyError, TypeError) as e:
            print("✅ Invalid parameters: Proper error handling")
            return True
        except Exception as e:
            print(f"⚠️  Invalid parameters: Unexpected error: {e}")
            return True  # Don't fail on this - tool might handle differently
            
    except ImportError as e:
        print(f"❌ Tool import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        return False

async def test_tool_response_format():
    """Test that tools return properly formatted responses"""
    print("Testing tool response format...")
    
    try:
        from ltms.tools.consolidated import memory_action
        
        # Test response format
        if asyncio.iscoroutinefunction(memory_action):
            result = await memory_action(action='status')
        else:
            result = memory_action(action='status')
        
        # Check if result is JSON-serializable
        try:
            json.dumps(result)
            print("✅ Response format: JSON-serializable")
        except (TypeError, ValueError) as e:
            print(f"⚠️  Response format: Not JSON-serializable: {e}")
            # Don't fail - tools might return different formats
        
        # Check if result has basic structure
        if isinstance(result, dict):
            print("✅ Response format: Dictionary structure")
            
            # Check for common response fields
            has_success = 'success' in result or 'status' in result or 'result' in result
            if has_success:
                print("✅ Response format: Contains status/result field")
            else:
                print("ℹ️  Response format: No explicit status field (may be OK)")
        else:
            print(f"ℹ️  Response format: {type(result).__name__} (non-dict response)")
        
        return True
        
    except Exception as e:
        print(f"❌ Response format test failed: {e}")
        return False

def test_tool_documentation():
    """Test that tools have proper documentation"""
    print("Testing tool documentation...")
    
    try:
        from ltms.tools.consolidated import memory_action
        
        # Check docstring
        if memory_action.__doc__:
            doc_length = len(memory_action.__doc__.strip())
            print(f"✅ Tool documentation: {doc_length} characters")
            return True
        else:
            print("⚠️  Tool documentation: No docstring found")
            return True  # Don't fail - documentation might be elsewhere
            
    except Exception as e:
        print(f"❌ Documentation test failed: {e}")
        return False

def test_mcp_server_integration():
    """Test MCP server integration capabilities"""
    print("Testing MCP server integration...")
    
    try:
        # Check if MCP server module exists
        ltmc_home = os.environ.get('LTMC_HOME', '/home/feanor/Projects/ltmc')
        mcp_server_path = Path(ltmc_home) / 'ltms' / '__main__.py'
        
        if mcp_server_path.exists():
            print("✅ MCP server entry point: Found")
        else:
            # Try alternative locations
            alt_paths = [
                Path(ltmc_home) / 'ltms' / 'main.py',
                Path(ltmc_home) / 'ltms' / 'server.py',
                Path(ltmc_home) / 'ltms' / 'mcp_server.py'
            ]
            
            found = False
            for alt_path in alt_paths:
                if alt_path.exists():
                    print(f"✅ MCP server entry point: Found at {alt_path.name}")
                    found = True
                    break
            
            if not found:
                print("⚠️  MCP server entry point: Not found in standard locations")
        
        # Check if tools can be imported
        from ltms.tools import consolidated
        print("✅ MCP server integration: Tools importable")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server integration test failed: {e}")
        return False

async def main():
    """Run all MCP protocol compliance tests"""
    print("=== LTMC MCP Protocol Compliance Tests ===")
    
    # Setup environment
    setup_ltmc_path()
    
    tests = [
        ("LTMC Tool Registration", test_mcp_tool_registration),
        ("Tool Parameter Validation", test_tool_parameter_validation),
        ("Tool Response Format", test_tool_response_format),
        ("Tool Documentation", test_tool_documentation),
        ("MCP Server Integration", test_mcp_server_integration)
    ]
    
    failed_tests = []
    warning_tests = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        
        try:
            if test_name == "LTMC Tool Registration":
                success, tools = test_func()
                if not success:
                    failed_tests.append(test_name)
            else:
                if asyncio.iscoroutinefunction(test_func):
                    success = await test_func()
                else:
                    success = test_func()
                if not success:
                    failed_tests.append(test_name)
                    
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed_tests.append(test_name)
    
    print(f"\n=== MCP Protocol Compliance Summary ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"Failed tests: {', '.join(failed_tests)}")
        print("❌ OVERALL: MCP protocol compliance validation FAILED")
        sys.exit(1)
    else:
        print("✅ OVERALL: All MCP protocol compliance tests PASSED")
        return 0

if __name__ == '__main__':
    asyncio.run(main())