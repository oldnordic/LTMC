#!/usr/bin/env python3
"""
Simple Tool Registration Test
============================

Test if tools are properly registered in the FastMCP server.
"""
import sys

# Add path for imports
sys.path.insert(0, '/home/feanor/Projects/lmtc')

def test_tool_registration():
    """Test that tools are registered in the MCP server."""
    print("🧪 Testing Tool Registration...")
    
    try:
        # Import the MCP server instance
        from ltmc_mcp_server.main import mcp
        
        print(f"✅ MCP server imported: {mcp}")
        print(f"   Server name: {mcp.name}")
        
        # Access the tools directly from the FastMCP instance
        if hasattr(mcp, '_tools'):
            tools = mcp._tools
            print(f"✅ Found {len(tools)} registered tools")
            
            # List tool names
            tool_names = list(tools.keys())
            print(f"   Tool names: {tool_names[:10]}...")  # Show first 10
            
            # Check for expected tools
            expected = ['store_memory', 'retrieve_memory', 'add_todo', 'log_code_attempt']
            found = [name for name in expected if name in tool_names]
            print(f"   Expected tools found: {len(found)}/{len(expected)}")
            
            return len(tools) > 0
        else:
            print("❌ No tools attribute found on MCP server")
            return False
            
    except Exception as e:
        print(f"❌ Error testing tool registration: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_tool_access():
    """Test direct access to tool functions."""
    print("\n🧪 Testing Direct Tool Access...")
    
    try:
        from ltmc_mcp_server.main import mcp
        
        # Try to access a tool directly
        if hasattr(mcp, '_tools') and 'store_memory' in mcp._tools:
            store_tool = mcp._tools['store_memory']
            print(f"✅ store_memory tool: {store_tool}")
            print(f"   Tool type: {type(store_tool)}")
            
            # Check if it has a callable handler
            if hasattr(store_tool, 'handler'):
                print(f"   Handler: {store_tool.handler}")
                print(f"   Handler type: {type(store_tool.handler)}")
                return True
            else:
                print("❌ No handler found on tool")
                return False
        else:
            print("❌ store_memory tool not found")
            return False
            
    except Exception as e:
        print(f"❌ Error testing direct tool access: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Tool Registration Test\n")
    
    registration_success = test_tool_registration()
    access_success = test_direct_tool_access()
    
    if registration_success and access_success:
        print("\n✅ SUCCESS: Tools are properly registered!")
        print("   • Tools are accessible in the MCP server")
        print("   • Tool handlers are available")
        print("   • PyInstaller binary should have working MCP tools")
    else:
        print("\n❌ FAILURE: Tool registration issues detected")
        print("   • This explains why tools/list might be empty")
        print("   • Need to investigate FastMCP tool registration")
        
    print(f"\nRegistration: {'✅' if registration_success else '❌'}")
    print(f"Access: {'✅' if access_success else '❌'}")