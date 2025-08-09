# COMPREHENSIVE JSON-RPC VALIDATION ERRORS INVESTIGATION REPORT

## Executive Summary

Completed investigation of JSON-RPC validation errors in LTMC system. Identified root causes in FastMCP tool implementations causing "available but failing" tools behavior.

## Critical Findings

### 1. PRIMARY ISSUE: Return Type Validation Errors
**Location**: `/ltms/mcp_server.py` line 228
**Problem**: `build_context()` tool returns raw string instead of required `Dict[str, Any]`
```python
# BROKEN CODE (line 228):
return build_context_window(documents, max_tokens)  # Returns str

# SHOULD BE:
result = build_context_window(documents, max_tokens)
return {"success": True, "context": result}
```

**Impact**: Pydantic validation error: `Expected dict, got list/str`
**Affected Tools**: `build_context`, `retrieve_by_type`

### 2. SECONDARY ISSUE: Parameter Name Mismatches
**Pattern**: Handler functions expect different parameter names than MCP tools provide
**Examples**:
- `get_document_relationships`: expects `doc_id` but receives `document_id`/`resource_id`
- `get_chats_by_tool`: expects `source_tool` but receives `tool_identifier`/`tool_name`
- `analyze_code_patterns`: receives unexpected `tags`/`pattern_type` parameters

### 3. DATABASE SCHEMA ISSUE
**Error**: `table CodePatterns has no column named function_name`
**Location**: Code pattern logging functionality
**Impact**: Code learning features fail

## FastMCP/MCP Protocol Requirements (2025 Standard)

### JSON-RPC 2.0 Compliance
- All tools MUST return `Dict[str, Any]` structure
- Response format: `{"jsonrpc": "2.0", "id": <id>, "result": <dict>}`
- Error format: `{"jsonrpc": "2.0", "id": <id>, "error": <dict>}`

### FastMCP SDK Validation
- Auto-generates schemas from type hints and docstrings
- Uses Pydantic models for validation
- Requires structured output validation (2025-06-18 spec)
- Supports OAuth 2.1 framework and Streamable HTTP transport (2025-03-26 spec)

### Tool Definition Standards
- Type hints define input/output schemas
- `@mcp.tool()` decorator handles schema generation
- All return types must be JSON-serializable dictionaries
- Parameter names must match exactly between definitions and implementations

## Technical Architecture Analysis

### Current Architecture Issues
1. **Split Implementation**: Tools defined in `mcp_server.py` but handlers in `tools/*.py`
2. **Inconsistent Return Types**: Some tools return raw data types instead of standardized dict format
3. **Parameter Mapping**: No validation of parameter name consistency
4. **Schema Mismatch**: Database schema doesn't match code pattern tool requirements

### Resolution Strategy

#### Phase 1: Critical Return Type Fixes
1. Fix `build_context()` to return proper dict structure
2. Fix `retrieve_by_type()` to return proper dict structure
3. Validate all other tools return Dict[str, Any]

#### Phase 2: Parameter Name Alignment
1. Standardize parameter names across tool definitions and handlers
2. Update tool schemas to match handler signatures
3. Add parameter validation layer

#### Phase 3: Database Schema Updates
1. Fix CodePatterns table schema
2. Test code pattern learning functionality
3. Validate all database-dependent tools

## Impact Assessment

### Tools Currently Failing
- `build_context` - Pydantic validation error (dict expected)
- `retrieve_by_type` - Pydantic validation error (dict expected)
- `get_document_relationships` - Parameter mismatch
- `get_chats_by_tool` - Parameter mismatch
- `analyze_code_patterns` - Parameter mismatch
- `log_code_attempt` - Database schema error

### System Stability
- Core memory operations (store_memory, retrieve_memory) working correctly
- Redis caching operations functional
- Chat logging operational
- Todo management working

## Recommendations

### Immediate Actions Required
1. **Fix return types** in build_context and retrieve_by_type tools
2. **Standardize parameter names** across all tool handlers
3. **Update database schema** for code patterns
4. **Add validation layer** to catch similar issues in future

### Long-term Improvements
1. **Implement comprehensive testing** for all MCP tools
2. **Add schema validation** in development pipeline
3. **Create tool development guidelines** following FastMCP best practices
4. **Add automated validation** for parameter name consistency

## Conclusion

The "available but failing" behavior is caused by FastMCP's strict JSON-RPC validation. Tools show as available (schema generation succeeds) but fail during execution due to return type and parameter validation errors. Fixes are straightforward but require systematic attention to FastMCP/MCP protocol compliance.

## Next Steps

1. **Immediate**: Fix the two critical return type validation errors in `build_context` and `retrieve_by_type`
2. **Short-term**: Resolve parameter name mismatches across all tool handlers
3. **Medium-term**: Update database schema and implement validation layer
4. **Long-term**: Create comprehensive testing and validation framework for MCP tools

## Investigation Tools Used

- **MCP Server Analysis**: Examined `/ltms/mcp_server.py` tool definitions
- **Handler Analysis**: Investigated `/ltms/tools/*.py` handler implementations
- **Log Analysis**: Analyzed validation errors in `/logs/ltmc_http.log`
- **Protocol Research**: Studied FastMCP SDK and MCP protocol 2025 standards
- **Database Investigation**: Identified schema mismatches in code pattern tables

Investigation completed successfully with comprehensive documentation of all validation issues and resolution strategies.