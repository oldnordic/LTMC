# LTMC Tools Usage Manual
*Generated: 2025-08-23 | Status: Active Reference*

## Overview
Complete reference guide for all 11 consolidated LTMC MCP tools with exact parameters, usage examples, and return formats.

## Tool Categories

### 1. Memory Management Tools

#### `mcp__ltmc__memory_action`

**Actions Available:**
- `store` - Store documents with vector indexing
- `retrieve` - Search and retrieve stored documents  
- `build_context` - Build context from document list
- `retrieve_by_type` - Retrieve by document type

**STORE Action:**
```json
{
  "action": "store",
  "file_name": "document.txt",
  "content": "Document content here",
  "resource_type": "document", // optional, defaults to "document"
  "metadata": {} // optional
}
```
**Returns:** `{'success': True, 'doc_id': 42, 'vector_count': 860, 'message': 'Document stored'}`

**RETRIEVE Action:** ✅ **WORKING**
```json
{
  "action": "retrieve", 
  "conversation_id": "session_id",
  "query": "search terms",
  "top_k": 5 // will be converted to int automatically
}
```
**Returns:** `{'success': True, 'documents': [...], 'total_found': 0}`

**BUILD_CONTEXT Action:**
```json
{
  "action": "build_context",
  "documents": [
    {"content": "doc1 content", "title": "optional"},
    {"content": "doc2 content", "metadata": {}}
  ],
  "max_tokens": 4000 // optional, default 4000
}
```

**RETRIEVE_BY_TYPE Action:** ⚠️ **HAS BUG** (same int/str issue)
```json
{
  "action": "retrieve_by_type",
  "query": "search terms",
  "doc_type": "document", // required
  "top_k": 5
}
```

---

### 2. Task Management Tools

#### `mcp__ltmc__todo_action`

**Actions Available:**
- `add` - Add new todo
- `list` - List todos 
- `complete` - Mark todo complete
- `search` - Search todos

**LIST Action:** ✅ **WORKING**
```json
{
  "action": "list"
}
```
**Returns:** Complete todo list with status, priorities, dates

---

### 3. Communication Tools  

#### `mcp__ltmc__chat_action`

**Actions Available:**
- `log` - Log chat messages
- `get_by_tool` - Get messages by tool
- `get_tool_conversations` - Get tool conversations
- `route_query` - Route queries

**LOG Action:** ✅ **WORKING**
```json
{
  "action": "log",
  "conversation_id": "session_id", 
  "role": "user|assistant",
  "content": "message content"
}
```
**Returns:** `{'success': True, 'chat_id': 26, 'message': 'Chat logged'}`

---

### 4. System Utilities

#### `mcp__ltmc__unix_action`

**Actions Available:** ✅ **ALL WORKING**
- `ls` - List files (using exa)
- `cat` - View file content (using bat) 
- `grep` - Search content (using ripgrep)
- `find` - Find files (using fd)
- `tree` - Directory tree
- `jq` - JSON processing
- `list_modern` - Modern file listing
- `disk_usage` - Disk usage (using duf)
- `help` - Tool help
- `diff_highlight` - Highlighted diff
- `fuzzy_select` - Fuzzy selection (using fzf)

**Examples:**
```json
// List files
{"action": "ls", "path": "directory/path"}

// Search with ripgrep  
{"action": "grep", "pattern": "search_term", "path": "file_or_dir"}

// Find files
{"action": "find", "path": "search_dir", "name": "filename_pattern"}
```

---

### 5. Code Analysis Tools

#### `mcp__ltmc__pattern_action`

**Actions Available:**
- `extract_functions` - Extract function definitions
- `extract_classes` - Extract class definitions  
- `extract_comments` - Extract comments
- `summarize_code` - Summarize code structure
- `log_attempt` - Log code attempts
- `get_patterns` - Get stored patterns
- `analyze_patterns` - Analyze pattern usage

**EXTRACT_FUNCTIONS Action:** ✅ **WORKING**
```json
{
  "action": "extract_functions",
  "source_code": "def example(): pass" // required - actual code, not file_path
}
```
**Returns:** `{'success': True, 'functions': [...], 'count': 1}`

---

### 6. Project Management

#### `mcp__ltmc__blueprint_action`

**Actions Available:**
- `create` - Create project blueprint
- `analyze_complexity` - Analyze complexity
- `list_project` - List project blueprints
- `add_dependency` - Add dependencies
- `resolve_order` - Resolve execution order
- `update_metadata` - Update blueprint metadata
- `get_dependencies` - Get dependencies
- `delete` - Delete blueprint

**CREATE Action:** ✅ **WORKING** 
```json
{
  "action": "create",
  "title": "Blueprint Title", // required
  "name": "blueprint_name", // required
  "description": "Blueprint description" // required
}
```
**Returns:** `{'success': True, 'blueprint_id': 'bp_abc123', 'complexity': 'medium'}`

---

### 7. Caching & Performance

#### `mcp__ltmc__cache_action`

**Actions Available:**
- `health_check` - Check Redis health
- `stats` - Get cache statistics  
- `flush` - Flush cache
- `reset` - Reset cache

⚠️ **HAS BUG:** Config import error - `cannot import name 'config' from 'ltms.config'`

---

### 8. Graph Database

#### `mcp__ltmc__graph_action`

**Actions Available:**
- `link` - Create relationships
- `query` - Execute Cypher queries
- `auto_link` - Auto-create links
- `get_relationships` - Get entity relationships

**QUERY Action:** ✅ **WORKING**
```json
{
  "action": "query",
  "entity": "entity_name", // required
  "query": "MATCH (n) RETURN count(n)" // Cypher query
}
```
**Returns:** `{'success': True, 'relationships': [], 'count': 0}`

---

### 9. Documentation Generation

#### `mcp__ltmc__documentation_action`

**Actions Available:**
- `generate_api_docs` - Generate API documentation
- `generate_architecture_diagram` - Generate diagrams  
- `sync_documentation_with_code` - Sync docs with code
- `validate_documentation_consistency` - Validate consistency

⚠️ **PARAMETER ISSUE:** Needs `project_id` parameter (requirement unclear)

---

### 10. Documentation Synchronization  

#### `mcp__ltmc__sync_action`

**Actions Available:**
- `code` - Sync with code
- `validate` - Validate sync
- `drift` - Detect drift
- `blueprint` - Sync with blueprints
- `score` - Score consistency
- `monitor` - Monitor changes
- `status` - Get sync status

⚠️ **PARAMETER ISSUE:** Needs `project_id` parameter (requirement unclear)

---

### 11. Configuration Management

#### `mcp__ltmc__config_action`

**Actions Available:**  
- `validate_config` - Validate configuration
- `get_config_schema` - Get schema
- `export_config` - Export configuration

**VALIDATE_CONFIG Action:** ✅ **WORKING**
```json
{
  "action": "validate_config"
}
```
**Returns:** `{'success': True, 'overall_valid': True, 'validation_results': {...}}`

---

## Quick Reference Status
- ✅ **WORKING (8 tools):** memory(store,retrieve), todo, chat, unix, pattern, blueprint, graph, config
- ⚠️ **HAS BUGS (3 tools):** memory(retrieve_by_type), cache, documentation/sync
- 📋 **TOTAL:** 11 consolidated tools with 30+ actions

---

*Last Updated: 2025-08-23 | Next Update: After bug fixes*