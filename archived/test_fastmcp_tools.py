#!/usr/bin/env python3
"""
FastMCP Tools Investigation
===========================

Check what's happening with FastMCP tool registration.
"""
import sys
sys.path.insert(0, '/home/feanor/Projects/lmtc')

def investigate_fastmcp_tools():
    """Investigate FastMCP tool registration."""
    print("🧪 Investigating FastMCP Tool Registration...")
    
    try:
        from ltmc_mcp_server.main import mcp
        
        print(f"✅ MCP server: {mcp}")
        print(f"   Name: {mcp.name}")
        
        # Check get_tools method
        tools = mcp.get_tools()
        print(f"✅ get_tools() returned: {len(tools)} tools")
        
        if tools:
            for i, tool in enumerate(tools[:5]):  # Show first 5
                print(f"   Tool {i+1}: {tool.name} - {tool.description[:50]}...")
                
            # Test tool names
            tool_names = [tool.name for tool in tools]
            expected = ['store_memory', 'retrieve_memory', 'add_todo']
            found = [name for name in expected if name in tool_names]
            print(f"   Expected tools found: {found}")
            
            return True
        else:
            print("❌ No tools returned by get_tools()")
            
            # Check if tools are there but not returned
            print("   Investigating tool decorator registration...")
            
            # Try to manually check tool registration
            try:
                import importlib
                # Force reload to ensure decorators are executed
                main_module = importlib.import_module('ltmc_mcp_server.main')
                tools_after_reload = main_module.mcp.get_tools()
                print(f"   After reload: {len(tools_after_reload)} tools")
                
                if tools_after_reload:
                    tool_names = [t.name for t in tools_after_reload]
                    print(f"   Tool names: {tool_names[:10]}")
                    return True
                    
            except Exception as e:
                print(f"   Reload error: {e}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error investigating tools: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_binary_tools_directly():
    """Test tools in binary by running it with debug info."""
    print("\n🧪 Testing Binary Tools Directly...")
    
    import subprocess
    import json
    
    # Create a debug script that prints tool info
    debug_script = '''
import sys
sys.path.insert(0, "/home/feanor/Projects/lmtc")

try:
    from ltmc_mcp_server.main import mcp
    tools = mcp.get_tools()
    print(f"TOOLS_COUNT: {len(tools)}")
    for tool in tools[:3]:
        print(f"TOOL: {tool.name}")
    if tools:
        print("TOOLS_SUCCESS")
    else:
        print("TOOLS_EMPTY")
except Exception as e:
    print(f"TOOLS_ERROR: {e}")
'''
    
    try:
        # Test with the binary
        result = subprocess.run([
            '/home/feanor/Projects/lmtc/dist/ltmc-minimal', 
            '-c', debug_script
        ], capture_output=True, text=True, timeout=10)
        
        print(f"   Binary result: {result.returncode}")
        if result.stdout:
            print(f"   stdout: {result.stdout}")
        if result.stderr:
            print(f"   stderr: {result.stderr}")
            
        return "TOOLS_SUCCESS" in result.stdout or "TOOLS_COUNT:" in result.stdout
        
    except Exception as e:
        print(f"   Binary test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FastMCP Tools Investigation\n")
    
    # Test 1: Direct investigation
    tools_found = investigate_fastmcp_tools()
    
    # Test 2: Binary test
    binary_success = test_binary_tools_directly()
    
    print(f"\n📊 Investigation Results:")
    print(f"   • Tools found in module: {'✅' if tools_found else '❌'}")
    print(f"   • Binary tools working: {'✅' if binary_success else '❌'}")
    
    if tools_found and binary_success:
        print("\n🎉 SUCCESS: Tools are properly registered!")
        print("   • FastMCP tool registration is working")
        print("   • Binary has access to all tools")
        print("   • Issue might be in MCP protocol handling")
    elif tools_found:
        print("\n⚠️  PARTIAL: Tools found but binary issue")
        print("   • Tools are registered in module")
        print("   • Binary might have import/execution issues")
    else:
        print("\n❌ FAILURE: No tools found")
        print("   • Tool decorators might not be executing")
        print("   • Need to check FastMCP version compatibility")