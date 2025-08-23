# Official MCP SDK Implementation Guide

## Official FastMCP Server Pattern (CORRECT Implementation)

Based on official MCP Python SDK documentation and examples:

### 1. Import Pattern
```python
from mcp.server.fastmcp import FastMCP  # CORRECT - Official SDK
```

### 2. Server Creation
```python
mcp = FastMCP("ServerName")  # Simple name parameter only
```

### 3. Tool Registration
```python
@mcp.tool()
def tool_name(param: type) -> return_type:
    """Tool description"""
    return result
```

### 4. Server Execution
```python
# Method 1: Simple execution
if __name__ == "__main__":
    mcp.run()  # Uses stdio transport by default

# Method 2: Async execution (for complex servers)
async def main():
    await mcp.run()

if __name__ == "__main__":
    asyncio.run(main())
```

## Official Examples from MCP SDK

### Simple Echo Server
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Echo Server")

@mcp.tool()
def echo(text: str) -> str:
    """Echo the input text"""
    return text

if __name__ == "__main__":
    mcp.run()
```

### Advanced Server with Structured Output
```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from datetime import datetime

mcp = FastMCP("Weather Service")

class WeatherData(BaseModel):
    temperature: float = Field(description="Temperature in Celsius")
    humidity: float = Field(description="Humidity percentage")
    condition: str = Field(description="Weather condition")
    location: str = Field(description="Location name")
    timestamp: datetime = Field(default_factory=datetime.now)

@mcp.tool()
def get_weather(city: str) -> WeatherData:
    """Get current weather for a city"""
    return WeatherData(
        temperature=22.5,
        humidity=65.0,
        condition="partly cloudy",
        location=city
    )

if __name__ == "__main__":
    mcp.run()
```

## Migration Requirements for LTMC Server

### Required Changes

#### 1. Import Statement Changes
```python
# WRONG (Current)
from fastmcp import FastMCP

# CORRECT (Required)
from mcp.server.fastmcp import FastMCP
```

#### 2. Server Creation Simplification
```python
# CURRENT (Complex)
mcp = FastMCP("ltmc")
# Complex initialization with settings...

# REQUIRED (Simple)
mcp = FastMCP("ltmc")
# Settings passed to individual tools, not server constructor
```

#### 3. Tool Registration Pattern (Unchanged)
```python
# This pattern works with official SDK
@mcp.tool()
async def store_memory(file_name: str, content: str, resource_type: str = "document") -> Dict[str, Any]:
    """Store content in long-term memory."""
    # Implementation remains the same
```

#### 4. Server Execution Simplification
```python
# CURRENT (Complex)
server = asyncio.run(create_server())
server.run()

# REQUIRED (Simple)
if __name__ == "__main__":
    mcp.run()  # Server handles asyncio internally
```

## Files Requiring Migration

### Core Files
1. `/ltmc_mcp_server/main.py` - Main server file
2. All files in `/ltmc_mcp_server/tools/*/` - Tool registration files
3. `/requirements.txt` - Update dependencies
4. `/ltmc.spec` - Update PyInstaller hidden imports

### Import Changes Needed
```bash
# Find all files with wrong imports
grep -r "from fastmcp import" ltmc_mcp_server/

# Replace with correct imports
# from fastmcp import FastMCP
# → from mcp.server.fastmcp import FastMCP
```

## Dependencies Update

### requirements.txt Changes
```txt
# REMOVE (jlowin's fastmcp)
fastmcp==2.10.0

# ADD (official MCP SDK - already present)
mcp>=1.12.0  # Official MCP SDK
```

## Migration Strategy

### Phase 1: Core Server Migration
1. Update main.py import statement
2. Simplify server creation and execution
3. Test basic server startup

### Phase 2: Tool Module Migration
1. Update tool imports one module at a time
2. Verify tool registration patterns work
3. Test individual tool functionality

### Phase 3: Binary Rebuild
1. Update PyInstaller specifications
2. Update hidden imports for official SDK
3. Rebuild binary with official implementation

### Phase 4: Validation
1. Test binary connection with Claude Code
2. Validate all 55 tools are accessible
3. Confirm performance is acceptable

## Expected Benefits

### Protocol Compliance
- ✅ Claude Code compatibility guaranteed
- ✅ Standard MCP JSON-RPC messages
- ✅ Proper version negotiation
- ✅ Official tool schema format

### Maintenance Improvements
- ✅ Official SDK support and updates
- ✅ Standard protocol compliance
- ✅ Better documentation and examples
- ✅ Community support

### Performance Considerations
- ⚠️ May lose some jlowin/fastmcp optimizations
- ✅ Should maintain good performance with proper async patterns
- ✅ Official SDK is well-optimized for MCP protocol

## Risk Mitigation

### Backup Strategy
- Keep current implementation in archive
- Incremental migration with rollback capability
- Test each phase before proceeding

### Compatibility Validation
- Test tool patterns work with official SDK
- Validate async patterns are preserved
- Ensure settings system integration works

---
*Implementation Status*: Ready to begin migration  
*Priority*: Replace jlowin/fastmcp with official mcp.server.fastmcp throughout codebase