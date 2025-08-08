# LTMC MCP Server TDD Implementation Plan

## Analysis of Current Issues

Based on the error logs and MCP SDK documentation, I identified several critical problems:

### 1. **Wrong SDK Usage**
- **Problem**: Using raw JSON-RPC instead of official MCP SDK
- **Error**: `ImportError: cannot import name 'Server' from 'mcp'`
- **Solution**: Use `FastMCP` class from `mcp.server.fastmcp`

### 2. **Incorrect Server Initialization**
- **Problem**: Wrong server initialization parameters
- **Error**: `TypeError: Server.__init__() missing 1 required positional argument: 'name'`
- **Solution**: Use proper `FastMCP` initialization

### 3. **Missing Tool Definitions**
- **Problem**: Tools not properly defined with decorators
- **Error**: Tools not discoverable by MCP clients
- **Solution**: Use `@mcp.tool()` decorators

### 4. **No Tests**
- **Problem**: Jumping straight to implementation without TDD
- **Impact**: No validation of functionality
- **Solution**: Write tests first, then implement

## TDD Implementation Plan

### Phase 1: Research and Setup (COMPLETED)
- ✅ Researched official MCP SDK documentation
- ✅ Identified correct usage patterns
- ✅ Updated startup scripts

### Phase 2: Write Failing Tests (NEXT)
1. **Test MCP Server Initialization**
   - Test server can start without errors
   - Test proper tool discovery
   - Test server shutdown

2. **Test Tool Definitions**
   - Test `store_memory` tool
   - Test `retrieve_memory` tool  
   - Test `log_chat` tool

3. **Test Tool Execution**
   - Test tool calls with valid arguments
   - Test error handling for invalid arguments
   - Test integration with LTMC services

4. **Test MCP Protocol Compliance**
   - Test proper initialization response
   - Test tool listing
   - Test tool calling

### Phase 3: Implement Minimal Working Server
1. **Create Basic FastMCP Server**
   ```python
   from mcp.server.fastmcp import FastMCP
   
   mcp = FastMCP("LTMC Server")
   ```

2. **Define Tools with Decorators**
   ```python
   @mcp.tool()
   def store_memory(file_name: str, content: str, resource_type: str = "document") -> dict:
       """Store text content in LTMC memory."""
   
   @mcp.tool()
   def retrieve_memory(conversation_id: str, query: str, top_k: int = 3) -> dict:
       """Retrieve relevant context from LTMC memory."""
   
   @mcp.tool()
   def log_chat(conversation_id: str, role: str, content: str) -> dict:
       """Log a chat message in LTMC."""
   ```

3. **Add Error Handling**
   - Database connection errors
   - Invalid input validation
   - Service layer errors

### Phase 4: Integration Testing
1. **Test with MCP Inspector**
   ```bash
   npm install -g @modelcontextprotocol/inspector
   mcp-inspector python -m ltms.mcp_server
   ```

2. **Test with Cursor Integration**
   - Verify server shows green status
   - Test tool availability
   - Test tool execution

3. **Test Tool Functionality**
   - Store test content
   - Retrieve context
   - Log chat messages

## File Structure

### New Files to Create
- `tests/mcp/test_mcp_server.py` - MCP server tests
- `ltms/mcp_server.py` - New FastMCP implementation
- `tests/mcp/test_tools.py` - Tool-specific tests

### Files to Update
- `requirements.txt` - Ensure MCP SDK is included
- `/home/feanor/.cursor/mcp.json` - Update configuration
- `README.md` - Add MCP server documentation

## Implementation Steps

### Step 1: Write Failing Tests
```python
# tests/mcp/test_mcp_server.py
import pytest
import asyncio
from mcp.server.fastmcp import FastMCP

def test_mcp_server_initialization():
    """Test that MCP server can be created."""
    mcp = FastMCP("LTMC Server")
    assert mcp.name == "LTMC Server"

def test_tool_discovery():
    """Test that tools are properly discoverable."""
    # Test will fail until we implement tools
    pass

def test_tool_execution():
    """Test that tools can be executed."""
    # Test will fail until we implement tools
    pass
```

### Step 2: Implement Minimal Server
```python
# ltms/mcp_server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LTMC Server")

@mcp.tool()
def store_memory(file_name: str, content: str, resource_type: str = "document") -> dict:
    """Store text content in LTMC memory."""
    # Implementation will be added
    return {"success": True, "message": "Memory stored"}

if __name__ == "__main__":
    mcp.run()
```

### Step 3: Add Tool Implementations
- Integrate with existing LTMC services
- Add proper error handling
- Add input validation

### Step 4: Test Integration
- Test with MCP inspector
- Test with Cursor
- Test tool functionality

## Success Criteria

### 1. **MCP Compliance**
- [ ] Server passes MCP inspector validation
- [ ] Proper initialization and capability negotiation
- [ ] Correct tool discovery and execution

### 2. **Tool Functionality**
- [ ] `store_memory` tool works correctly
- [ ] `retrieve_memory` tool returns relevant context
- [ ] `log_chat` tool logs messages properly

### 3. **Cursor Integration**
- [ ] LTMC server shows green status in Cursor
- [ ] Tools are available to AI assistant
- [ ] No connection errors or timeouts

### 4. **Error Handling**
- [ ] Proper error messages for invalid inputs
- [ ] Graceful handling of database errors
- [ ] Clear error reporting to MCP clients

## Timeline
- **Step 1**: 15 minutes (Write failing tests)
- **Step 2**: 20 minutes (Implement minimal server)
- **Step 3**: 30 minutes (Add tool implementations)
- **Step 4**: 15 minutes (Integration testing)

**Total Estimated Time**: 80 minutes

## Key Differences from Previous Implementation

### 1. **Use FastMCP Instead of Raw Server**
```python
# OLD (Wrong)
from mcp.server import Server
server = Server("ltmc-server", version="1.0.0")

# NEW (Correct)
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("LTMC Server")
```

### 2. **Use Decorators for Tools**
```python
# OLD (Wrong)
async def call_tool(self, params: CallToolRequest) -> CallToolResult:
    # Manual tool handling

# NEW (Correct)
@mcp.tool()
def store_memory(file_name: str, content: str) -> dict:
    # Automatic tool registration
```

### 3. **Simple Run Method**
```python
# OLD (Complex)
async with stdio_server() as (read_stream, write_stream):
    await server.run(read_stream, write_stream, init_options)

# NEW (Simple)
if __name__ == "__main__":
    mcp.run()
```

## Benefits of This Approach

### 1. **Official SDK Compliance**
- Uses the official MCP Python SDK
- Follows MCP specification exactly
- Compatible with all MCP clients

### 2. **Simpler Implementation**
- Less boilerplate code
- Automatic tool registration
- Built-in error handling

### 3. **Better Testing**
- TDD approach ensures quality
- Tests validate each component
- Integration testing with real clients

### 4. **Future-Proof**
- Uses latest MCP SDK features
- Easy to extend with new tools
- Maintainable codebase
