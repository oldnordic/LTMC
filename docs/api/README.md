# LTMC API Reference

Complete API reference for the LTMC (Long-Term Memory and Context) MCP server with all 55 available tools.

## Quick Reference

- [MCP Protocol Integration](#mcp-protocol-integration)
- [Memory Tools](#memory-tools) (2 tools)
- [Chat Tools](#chat-tools) (4 tools)
- [Todo Tools](#todo-tools) (4 tools)
- [Context Tools](#context-tools) (12 tools)
- [Code Pattern Tools](#code-pattern-tools) (3 tools)

## MCP Protocol Integration

### Claude Code Configuration

Add LTMC to your Claude Code MCP configuration:

```json
{
  "ltmc": {
    "command": "python",
    "args": ["ltmc_mcp_server/main.py"],
    "cwd": "/path/to/ltmc-mcp-server"
  }
}
```

### Tool Access

Once configured, all 55 tools are available through Claude Code MCP interface:
- Tools are prefixed with `mcp__ltmc__`
- Example: `mcp__ltmc__store_memory`, `mcp__ltmc__retrieve_memory`
- Server runs automatically when Claude Code connects via stdio transport

### Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  },
  "id": 1
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": "..."
  },
  "error": null
}
```

## Memory Tools

### store_memory
Store content in long-term memory with vector embeddings.

**Parameters:**
- `content` (string, required): Content to store
- `file_name` (string, required): Logical filename for organization

**Example:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call", 
    "params": {
      "name": "store_memory",
      "arguments": {
        "content": "Important project insights",
        "file_name": "project_notes.md"
      }
    },
    "id": 1
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "message": "Memory stored successfully",
    "resource_id": 118,
    "chunk_count": 1
  }
}
```

### retrieve_memory
Retrieve stored content using semantic search.

**Parameters:**
- `query` (string, required): Search query
- `conversation_id` (string, required): Session identifier
- `top_k` (integer, optional): Number of results (default: 5)

**Example:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", 
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "project insights",
        "conversation_id": "session_123"
      }
    },
    "id": 2
  }'
```

## Chat Tools

### log_chat
Log chat messages for conversation history.

**Parameters:**
- `conversation_id` (string, required): Session identifier
- `role` (string, required): Message role (user/assistant/system)
- `content` (string, required): Message content
- `agent_name` (string, optional): Agent identifier
- `metadata` (object, optional): Additional metadata

### ask_with_context
Ask questions with automatic context retrieval.

**Parameters:**
- `question` (string, required): Question to ask
- `conversation_id` (string, required): Session identifier
- `context_k` (integer, optional): Context items to retrieve

### route_query
Route queries to appropriate handlers.

**Parameters:**
- `query` (string, required): Query to route
- `conversation_id` (string, required): Session identifier

### get_chats_by_tool
Retrieve chat history filtered by tool usage.

**Parameters:**
- `tool_name` (string, required): Tool to filter by
- `limit` (integer, optional): Maximum results

## Todo Tools

### add_todo
Create a new todo item.

**Parameters:**
- `title` (string, required): Todo title
- `description` (string, optional): Detailed description
- `priority` (string, optional): Priority level (high/medium/low)

**Example:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_todo", 
      "arguments": {
        "title": "Document API endpoints",
        "description": "Create comprehensive API documentation"
      }
    },
    "id": 3
  }'
```

### list_todos
List all todo items with optional filtering.

**Parameters:**
- `status` (string, optional): Filter by status (pending/completed)
- `limit` (integer, optional): Maximum results

### complete_todo
Mark a todo item as completed.

**Parameters:**
- `todo_id` (integer, required): Todo item ID

### search_todos
Search todo items by text.

**Parameters:**
- `query` (string, required): Search query
- `limit` (integer, optional): Maximum results

## Context Tools

### build_context
Build contextual information for queries.

**Parameters:**
- `query` (string, required): Query for context
- `conversation_id` (string, required): Session identifier
- `max_items` (integer, optional): Maximum context items

### retrieve_by_type
Retrieve resources by content type.

**Parameters:**
- `resource_type` (string, required): Type to filter by
- `limit` (integer, optional): Maximum results

### store_context_links
Store relationships between contexts.

**Parameters:**
- `message_id` (integer, required): Message identifier
- `chunk_ids` (array, required): Related chunk IDs

### link_resources
Create links between resources.

**Parameters:**
- `source_id` (string, required): Source resource ID
- `target_id` (string, required): Target resource ID
- `relationship_type` (string, required): Relationship type

### query_graph
Query the knowledge graph.

**Parameters:**
- `cypher_query` (string, required): Cypher query
- `parameters` (object, optional): Query parameters

### auto_link_documents
Automatically create document relationships.

**Parameters:**
- `document_ids` (array, required): Document IDs to link
- `similarity_threshold` (float, optional): Minimum similarity

## Code Pattern Tools

### log_code_attempt
Log code generation attempts for learning.

**Parameters:**
- `input_prompt` (string, required): Original prompt
- `generated_code` (string, required): Generated code
- `result` (string, required): Execution result (pass/fail)
- `language` (string, optional): Programming language

**Example:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Create async function",
        "generated_code": "async def example(): pass",
        "result": "pass",
        "language": "python"
      }
    },
    "id": 4
  }'
```

### get_code_patterns
Retrieve similar code patterns.

**Parameters:**
- `query` (string, required): Code pattern query
- `language` (string, optional): Programming language filter
- `limit` (integer, optional): Maximum results

### analyze_code_patterns
Analyze stored code patterns for insights.

**Parameters:**
- `pattern_ids` (array, optional): Specific pattern IDs
- `analysis_type` (string, optional): Analysis type

## Error Handling

All API responses include error information when operations fail:

```json
{
  "jsonrpc": "2.0", 
  "id": 1,
  "result": null,
  "error": {
    "code": -32603,
    "message": "Tool execution error: Invalid parameters"
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| -32600 | Invalid Request |
| -32601 | Method not found |
| -32602 | Invalid params |
| -32603 | Internal error |

## Rate Limiting

Currently no rate limiting is enforced. For production deployments, consider implementing rate limiting at the reverse proxy level.

## Authentication

Basic token authentication is available via environment variables:
- `ENABLE_AUTH=1`: Enable authentication
- `LTMC_API_TOKEN=your_token`: Set API token

When enabled, include token in requests:
```bash
curl -H "Authorization: Bearer your_token" http://localhost:5050/jsonrpc
```

---

For detailed tool schemas and advanced usage examples, see the [Tool Schemas](tools/) directory.