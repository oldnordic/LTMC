# LTMC MCP Server Implementation Plan

## Current Issues Identified

### 1. **Not Using Official MCP SDK**
- **Problem**: Our `ltms/mcp_server.py` implements raw JSON-RPC instead of using the official Python MCP SDK
- **Impact**: Missing proper protocol handling, error codes, and compatibility
- **Solution**: Install and use the official `mcp` Python package

### 2. **Incomplete Protocol Compliance**
- **Problem**: Not handling MCP initialization properly
- **Impact**: Server won't be recognized by MCP clients
- **Solution**: Implement proper `initialize` method with capabilities

### 3. **Missing Error Handling**
- **Problem**: Not using standard JSON-RPC error codes
- **Impact**: Poor error reporting to clients
- **Solution**: Use MCP SDK's built-in error handling

### 4. **Tool Schema Issues**
- **Problem**: Tool schemas not properly defined
- **Impact**: Tools may not be discoverable or usable
- **Solution**: Define proper input/output schemas using MCP SDK

## Implementation Plan

### Phase 1: Setup Official MCP SDK
1. **Install MCP Python SDK**
   ```bash
   pip install mcp
   ```

2. **Update requirements.txt**
   - Add `mcp` dependency
   - Ensure compatibility with existing dependencies

### Phase 2: Rewrite MCP Server Using SDK
1. **Create new MCP server file**
   - File: `ltms/mcp_server_proper.py`
   - Use official MCP SDK classes and decorators
   - Implement proper initialization

2. **Define Tool Schemas**
   ```python
   @tool()
   async def store_memory(
       file_name: str,
       content: str,
       resource_type: str = "document"
   ) -> Dict[str, Any]:
       """Store text content in LTMC memory."""
   
   @tool()
   async def retrieve_memory(
       conversation_id: str,
       query: str,
       top_k: int = 3
   ) -> Dict[str, Any]:
       """Retrieve relevant context from LTMC memory."""
   
   @tool()
   async def log_chat(
       conversation_id: str,
       role: str,
       content: str
   ) -> Dict[str, Any]:
       """Log a chat message in LTMC."""
   ```

3. **Implement Server Class**
   ```python
   class LTMCMCPServer(Server):
       def __init__(self):
           super().__init__()
           self.db_path = os.getenv("DB_PATH", "ltmc.db")
           self.index_path = os.getenv("FAISS_INDEX_PATH", "faiss_index")
   ```

### Phase 3: Update MCP Configuration
1. **Update `/home/feanor/.cursor/mcp.json`**
   ```json
   {
     "mcpServers": {
       "ltmc": {
         "command": "python",
         "args": ["-m", "ltms.mcp_server_proper"],
         "cwd": "/home/feanor/Projects/lmtc",
         "env": {
           "DB_PATH": "ltmc.db",
           "FAISS_INDEX_PATH": "faiss_index"
         }
       }
     }
   }
   ```

### Phase 4: Testing and Validation
1. **Install MCP Inspector Tool**
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. **Test Server Compliance**
   ```bash
   mcp-inspector python -m ltms.mcp_server_proper
   ```

3. **Test Tool Discovery**
   - Verify tools are properly listed
   - Check tool schemas are correct
   - Test tool execution

### Phase 5: Integration Testing
1. **Test with Cursor**
   - Restart Cursor to reload MCP configuration
   - Verify LTMC server shows green status
   - Test tool availability in AI assistant

2. **Test Tool Functionality**
   - Store test content in LTMC
   - Retrieve context from stored content
   - Log chat messages

## File Structure Changes

### New Files to Create
- `ltms/mcp_server_proper.py` - New MCP server using official SDK
- `tests/mcp/test_mcp_server.py` - Tests for MCP server functionality

### Files to Update
- `requirements.txt` - Add `mcp` dependency
- `/home/feanor/.cursor/mcp.json` - Update server configuration
- `README.md` - Add MCP server documentation

### Files to Remove (After Testing)
- `ltms/mcp_server.py` - Old implementation (after new one works)

## Success Criteria

### 1. **MCP Compliance**
- [ ] Server passes MCP inspector validation
- [ ] Proper initialization and capability negotiation
- [ ] Correct JSON-RPC error handling

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

## Implementation Steps

### Step 1: Install Dependencies
```bash
pip install mcp
pip freeze > requirements.txt
```

### Step 2: Create New MCP Server
- Implement using official SDK
- Add proper tool decorators
- Include error handling

### Step 3: Update Configuration
- Update MCP configuration file
- Test server startup

### Step 4: Validate Implementation
- Run MCP inspector
- Test tool discovery and execution
- Verify Cursor integration

### Step 5: Documentation
- Update README with MCP server info
- Add usage examples
- Document tool schemas

## Timeline
- **Phase 1-2**: 30 minutes (Setup and rewrite)
- **Phase 3**: 10 minutes (Configuration update)
- **Phase 4**: 20 minutes (Testing and validation)
- **Phase 5**: 15 minutes (Integration testing)

**Total Estimated Time**: 75 minutes

## Risk Mitigation

### Potential Issues
1. **SDK Compatibility**: Ensure MCP SDK works with our Python version
2. **Database Integration**: Verify our DAL works with async MCP tools
3. **Environment Variables**: Ensure proper configuration loading

### Mitigation Strategies
1. **Test in Isolation**: Test MCP server separately before integration
2. **Fallback Plan**: Keep old implementation until new one is proven
3. **Incremental Testing**: Test each tool individually

## Benefits of This Approach

### 1. **Official Compliance**
- Follows MCP specification exactly
- Compatible with all MCP clients
- Future-proof implementation

### 2. **Better Error Handling**
- Standard JSON-RPC error codes
- Clear error messages
- Proper debugging support

### 3. **Ecosystem Integration**
- Works with MCP inspector tools
- Compatible with other MCP servers
- Access to MCP community resources

### 4. **Maintainability**
- Uses official SDK (less custom code)
- Better documentation and support
- Easier to update and extend
