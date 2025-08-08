"""Simple test to understand FastMCP API."""

from mcp.server.fastmcp.server import FastMCP

# Create server
server = FastMCP("LTMC Server")

# Let's see what methods are available
print("FastMCP methods:")
print(dir(server))

# Let's see what the tool decorator does
print("\nTool decorator:")
print(server.tool)

# Try to understand the API
try:
    # Let's see if we can add a tool manually
    print("\nTrying to understand tool registration...")
    
    # Check if there's a different way to add tools
    if hasattr(server, 'add_tool'):
        print("Has add_tool method")
    if hasattr(server, 'tools'):
        print("Has tools attribute")
        print(server.tools)
    
    # Let's see what the server looks like
    print("\nServer object:")
    print(type(server))
    print(server)
    
except Exception as e:
    print(f"Error: {e}")
