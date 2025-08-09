# LTMC TOOL SIGNATURE MISMATCHES AND PARAMETER ISSUES INVESTIGATION

**Date**: August 9, 2025  
**Critical Issue**: 14 of 28 LTMC tools are failing due to function signature mismatches, parameter ordering issues, and missing dependencies

## EXECUTIVE SUMMARY

This investigation reveals that 50% of LTMC tools are non-functional due to systematic issues in tool definitions, parameter handling, and missing dependencies. The root causes are categorized into 5 primary failure types.

## ROOT CAUSE ANALYSIS

### 1. FAISS Dependency Missing (CRITICAL)
**File**: `ltms/vector_store/faiss_store.py:20`  
**Error**: `AttributeError: 'NoneType' object has no attribute 'IndexFlatL2'`  
**Impact**: Prevents server initialization, blocking tool registration  
**Evidence**: 
```python
# Line 20: faiss_store.py
def create_faiss_index(dimension: int) -> faiss.IndexFlatL2:  # faiss is None
```

**Fix Required**: `pip install faiss-cpu`

### 2. Parameter Signature Mismatches (HIGH PRIORITY)

#### A. ask_with_context Tool
**File**: `ltms/mcp_server.py:207`  
**Current Signature**: `ask_with_context(query: str, conversation_id: str, top_k: int = 5)`  
**Implementation Signature**: `ask_with_context(query: str, max_tokens: int = 4000, top_k: int = 5)`  
**Error**: `"'<=' not supported between instances of 'int' and 'str'"`  
**Root Cause**: Parameter `conversation_id` passed to `max_tokens` parameter

**Evidence**:
```python
# MCP Server definition (Line 207)
@mcp.tool()
def ask_with_context(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    return ask_with_context_tool(query, conversation_id, top_k)  # Wrong parameters!

# tools/ask.py implementation (Line 20)  
def ask_with_context(query: str, max_tokens: int = 4000, top_k: int = 5) -> Dict[str, Any]:
```

#### B. route_query Tool
**File**: `ltms/mcp_server.py:216`  
**Current Signature**: `route_query(query: str, source_types: List[str], top_k: int = 5)`  
**Implementation Signature**: `route_query(query: str, source_types: Optional[List[str]] = None, max_tokens: int = 4000, top_k: int = 5)`  
**Issue**: Missing `max_tokens` parameter, incorrect parameter mapping

#### C. retrieve_by_type Tool  
**File**: `ltms/mcp_server.py:234`  
**Current Signature**: `retrieve_by_type(query: str, doc_type: str, top_k: int = 5)`  
**Implementation Signature**: `retrieve_by_type(query: str, doc_type: str, top_k: int = 5)`  
**Issue**: Implementation uses `retrieve_with_metadata` with `source_filter` parameter

### 3. Function Name Suffix Inconsistencies (MEDIUM PRIORITY)

#### Context Linking Tools
All context tools have `_tool` suffix in MCP definitions but not in implementations:

**File**: `ltms/mcp_server.py:409-502`  
| MCP Tool Definition | Implementation Function | Status |
|---------------------|-------------------------|---------|
| `store_context_links_tool` | `store_context_links` | ❌ Mismatch |
| `get_context_links_for_message_tool` | `get_context_links_for_message` | ❌ Mismatch |
| `get_messages_for_chunk_tool` | `get_messages_for_chunk` | ❌ Mismatch |
| `get_context_usage_statistics_tool` | `get_context_usage_statistics` | ❌ Mismatch |

**Evidence**:
```python
# Line 410: MCP Server
@mcp.tool()
def store_context_links_tool(message_id: int, chunk_ids: List[int]) -> Dict[str, Any]:
    result = store_context_links(conn, message_id, chunk_ids)  # Function exists

# Line 24: ltms/database/context_linking.py  
def store_context_links(conn: sqlite3.Connection, message_id: int, chunk_ids: List[int]) -> Dict[str, Any]:
```

### 4. Database Schema Issues (HIGH PRIORITY)

#### Code Pattern Tools
**File**: Code pattern service calls  
**Error**: `"no such column: function_name"`  
**Evidence**: Test failure when calling `get_code_patterns`
**Root Cause**: Database schema mismatch between tool parameters and actual columns

**Investigation Needed**:
- Check `ltms/services/code_pattern_service.py` implementation
- Verify database schema in `ltms/database/schema.py`
- Confirm column names in CodePatterns table

### 5. External Dependency Issues (MEDIUM PRIORITY)

#### Neo4j Graph Tools
**Files**: `ltms/mcp_server.py:507-612` (link_resources, auto_link_documents)  
**Potential Issues**:
- Neo4j driver not installed
- Neo4j server not running  
- Connection configuration incorrect

**Evidence**: 2/4 graph tools reported as broken

## SPECIFIC TOOL FAILURE ANALYSIS

### Context Tools (0/6 Working)
1. **build_context**: Parameter signature mismatch with `build_context_window`
2. **retrieve_by_type**: Implementation uses different internal function calls
3. **store_context_links**: `_tool` suffix naming mismatch
4. **get_context_links_for_message**: `_tool` suffix naming mismatch
5. **get_messages_for_chunk**: `_tool` suffix naming mismatch  
6. **get_context_usage_statistics**: `_tool` suffix naming mismatch

### Code Pattern Tools (0/3 Working)
1. **log_code_attempt**: Database schema issues
2. **get_code_patterns**: Column name mismatch (`function_name`)
3. **analyze_code_patterns**: Schema validation failures

### Chat Tools (1/4 Working)
1. **ask_with_context**: Parameter order mismatch ❌
2. **route_query**: Parameter signature mismatch ❌
3. **get_chats_by_tool**: Working ✅
4. **log_chat**: Working ✅

### Graph Tools (2/4 Working)
1. **link_resources**: Neo4j dependency issues ❌
2. **auto_link_documents**: Neo4j dependency issues ❌
3. **query_graph**: Working ✅
4. **get_document_relationships**: Working ✅

## DETAILED FIXES REQUIRED

### Priority 1: Critical Dependencies
```bash
# Install missing FAISS dependency
pip install faiss-cpu

# Verify Neo4j dependencies
pip install neo4j
```

### Priority 2: Parameter Signature Fixes

#### Fix ask_with_context (Line 207)
```python
# Current (BROKEN)
@mcp.tool()
def ask_with_context(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    return ask_with_context_tool(query, conversation_id, top_k)

# Fixed
@mcp.tool()  
def ask_with_context(query: str, conversation_id: str, top_k: int = 5) -> Dict[str, Any]:
    # Modify implementation to accept conversation_id parameter
    return ask_with_context_tool(query, conversation_id=conversation_id, top_k=top_k)
```

#### Fix route_query (Line 216)
```python
# Current (BROKEN)
@mcp.tool()
def route_query(query: str, source_types: List[str], top_k: int = 5) -> Dict[str, Any]:
    return route_query_tool(query, source_types, top_k)

# Fixed
@mcp.tool()
def route_query(query: str, source_types: List[str], top_k: int = 5) -> Dict[str, Any]:
    return route_query_tool(query, source_types, max_tokens=4000, top_k=top_k)
```

### Priority 3: Function Name Fixes

#### Remove _tool suffixes from MCP definitions
```python
# Lines 409-502: Remove '_tool' suffix from all context functions
@mcp.tool()
def store_context_links(message_id: int, chunk_ids: List[int]) -> Dict[str, Any]:
    # Same implementation, just rename the function
```

### Priority 4: Database Schema Validation

#### Verify CodePatterns table schema
```sql
-- Check actual table structure
PRAGMA table_info(CodePatterns);

-- Expected columns based on tool usage
ALTER TABLE CodePatterns ADD COLUMN function_name TEXT;
```

## TESTING AND VALIDATION PLAN

### Phase 1: Dependency Installation
1. Install FAISS: `pip install faiss-cpu`
2. Install Neo4j driver: `pip install neo4j`
3. Verify server startup: `python server.py`

### Phase 2: Parameter Signature Fixes
1. Fix `ask_with_context` parameter mapping
2. Fix `route_query` parameter mapping  
3. Fix `retrieve_by_type` implementation calls
4. Test each fix individually via HTTP JSON-RPC

### Phase 3: Function Name Standardization
1. Remove `_tool` suffixes from context functions
2. Update all MCP tool definitions
3. Test context linking functionality

### Phase 4: Database Schema Updates
1. Examine CodePatterns table structure
2. Add missing columns if needed
3. Test code pattern tools functionality

### Phase 5: Integration Testing
1. Test all 28 tools via HTTP and stdio transports
2. Run comprehensive test suite
3. Validate tool discovery and metadata

## SUCCESS METRICS
- **Target**: 28/28 tools operational (100%)
- **Critical**: 22/28 tools operational (75%+) 
- **Minimum**: 18/28 tools operational (65%+)

## IMPLEMENTATION TIMELINE
- **Phase 1 (Dependencies)**: 30 minutes
- **Phase 2 (Signatures)**: 2 hours
- **Phase 3 (Naming)**: 1 hour  
- **Phase 4 (Database)**: 1 hour
- **Phase 5 (Testing)**: 2 hours
- **Total Estimated**: 6.5 hours

This investigation provides the complete roadmap to restore full LTMC tool functionality.