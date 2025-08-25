# FastMCP 2.0 Implementation Plan for LTMC Server

## Research Summary

Based on comprehensive research of FastMCP 2.0 documentation and examples, here's the correct implementation pattern:

### Key FastMCP 2.0 Principles

1. **Simple is Better**: FastMCP 2.0 motto is "in most cases, decorating a function is all you need"
2. **Default STDIO Transport**: `mcp.run()` uses stdio transport by default - no need to specify
3. **No Complex Async Setup**: Just use `mcp.run()` in main block
4. **No FastAPI/Uvicorn**: FastMCP handles transport internally
5. **Tool Registration**: Use `@mcp.tool` decorator only
6. **Lazy Loading**: Built into FastMCP - tools are loaded on demand

### Correct Server Pattern

```python
from fastmcp import FastMCP

# Create server - simple
mcp = FastMCP("ltmc")

# Load settings once at module level
from ltmc_mcp_server.config.settings import LTMCSettings
settings = LTMCSettings()

# Register tools using simple functions
@mcp.tool
def store_memory(content: str, file_name: str, resource_type: str = "document"):
    """Store content in long-term memory"""
    # Tool implementation
    pass

@mcp.tool  
def retrieve_memory(query: str, top_k: int = 5):
    """Retrieve relevant content from memory"""
    # Tool implementation
    pass

# More tool registrations...

# Simple main - no complexity
if __name__ == "__main__":
    mcp.run()  # Uses stdio by default
```

## What I Did Wrong

1. **Overcomplicated main.py**: Added async functions, database initialization, complex imports
2. **Used wrapper functions**: Instead of direct tool implementation
3. **Added FastAPI imports**: FastMCP handles transport internally
4. **Complex registration**: Used separate registration functions instead of direct decorators
5. **Database initialization**: Should be lazy, not at startup

## Correct Implementation Plan

### Phase 1: Simplify Main Server
- Remove all complex async code
- Remove database initialization from startup
- Use simple `mcp = FastMCP("ltmc")` and `mcp.run()`
- No FastAPI/Uvicorn imports

### Phase 2: Convert Tools to Direct Functions
- Convert each tool from wrapper functions to direct `@mcp.tool` decorated functions
- Move database initialization to first tool call (lazy loading)
- Remove all registration functions - use decorators directly

### Phase 3: Fix Imports
- Remove compatibility modules (config, models, services, utils)
- Use proper `ltmc_mcp_server` imports throughout
- No more import redirects

### Phase 4: Binary Building
- Use simple PyInstaller spec with FastMCP metadata
- Include only necessary modules
- Test with `mcp.run()` pattern

## Tool Implementation Pattern

Each tool should be standalone:

```python
@mcp.tool
async def store_memory(content: str, file_name: str) -> dict:
    """Store content in memory"""
    # Lazy load dependencies
    from ltmc_mcp_server.services.database_service import DatabaseService
    from ltmc_mcp_server.config.settings import LTMCSettings
    
    settings = LTMCSettings()
    db_service = DatabaseService(settings)
    
    # Implementation
    result = await db_service.store_memory(content, file_name)
    return {"success": True, "stored": file_name}
```

## Binary Building Strategy

FastMCP 2.0 with PyInstaller:
1. Simple main.py with mcp.run()
2. Include fastmcp metadata with copy_metadata
3. No complex wrapper scripts
4. Direct stdio execution

## Next Steps

1. ✅ Research complete - FastMCP 2.0 patterns understood
2. Create simplified main.py following FastMCP 2.0 pattern
3. Convert all tools to direct @mcp.tool functions
4. Remove compatibility modules and fix imports
5. Build binary with simplified approach
6. Test stdio transport functionality

## Critical Rules

- **NO FastAPI/Uvicorn imports**
- **NO complex async main functions**
- **NO wrapper functions**
- **NO database initialization at startup**
- **Use `mcp.run()` ONLY**
- **Lazy load everything in tools**