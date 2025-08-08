# LTMC API Reference

## Overview

The LTMC (Long-Term Memory and Context) MCP Server provides 25+ tools for memory management, chat history, task tracking, code patterns, and multi-agent orchestration. This document provides comprehensive API reference for all available tools.

## Transport Protocols

LTMC supports dual transport protocols:

- **HTTP Transport**: REST API available at `http://localhost:5050`
- **MCP Protocol**: JSON-RPC over stdio for MCP clients

## Authentication

Currently, LTMC operates in development mode without authentication. For production deployments, implement appropriate authentication mechanisms.

## Tool Categories

1. [Memory Tools](#memory-tools) - Persistent storage and retrieval
2. [Chat Tools](#chat-tools) - Conversation history management  
3. [Todo Tools](#todo-tools) - Task tracking and management
4. [Context Tools](#context-tools) - Semantic context retrieval
5. [Code Pattern Tools](#code-pattern-tools) - ML-assisted code insights
6. [Orchestration Tools](#orchestration-tools) - Multi-agent coordination

## Memory Tools

### store_memory

Store a document or memory in LTMC with automatic chunking and vector indexing.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "project_notes.md",
        "content": "Important project information...",
        "resource_type": "document"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `file_name` (string, required): Name of the file/document to store
- `content` (string, required): Content to store
- `resource_type` (string, optional): Type of resource (document, code, note, etc.) - default: "document"

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "resource_id": 123,
    "chunks_created": 3,
    "vector_ids": [1, 2, 3],
    "message": "Memory stored successfully"
  },
  "id": 1
}
```

### retrieve_memory

Retrieve relevant documents/memories using semantic search.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "project implementation details",
        "conversation_id": "session_123",
        "top_k": 10
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Search query to find relevant memories
- `conversation_id` (string, optional): Optional conversation ID to scope the search
- `top_k` (integer, optional): Number of results to return (1-100, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "results": [
      {
        "resource_id": 123,
        "chunk_id": 456,
        "content": "Relevant content snippet...",
        "similarity_score": 0.85,
        "metadata": {
          "file_name": "project_notes.md",
          "resource_type": "document",
          "created_at": "2025-08-08T10:30:00Z"
        }
      }
    ],
    "total_results": 5
  },
  "id": 1
}
```

## Chat Tools

### log_chat

Log a chat message with automatic context linking and relationship building.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_chat",
      "arguments": {
        "content": "User asked about API implementation",
        "conversation_id": "session_123",
        "role": "user"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `content` (string, required): The chat message content to log
- `conversation_id` (string, required): Unique identifier for the conversation
- `role` (string, optional): Role of the message sender - enum: ["user", "assistant", "system"] - default: "user"

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "chat_id": 789,
    "context_links": 3,
    "message": "Chat message logged successfully"
  },
  "id": 1
}
```

### ask_with_context

Ask a question with relevant context retrieved from memory.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ask_with_context",
      "arguments": {
        "question": "How do I implement error handling?",
        "conversation_id": "session_123",
        "context_limit": 10
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `question` (string, required): The question to ask
- `conversation_id` (string, optional): Optional conversation ID for context scoping
- `context_limit` (integer, optional): Maximum number of context items to retrieve (1-50, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "question": "How do I implement error handling?",
    "context": [
      {
        "content": "Error handling best practices...",
        "source": "error_handling.md",
        "relevance": 0.92
      }
    ],
    "suggested_response": "Based on the context, error handling should follow these patterns..."
  },
  "id": 1
}
```

### route_query

Route a query to the most appropriate context or processing method.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "route_query",
      "arguments": {
        "query": "What are the best practices for async programming?",
        "conversation_id": "session_123"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Query to route and process
- `conversation_id` (string, optional): Optional conversation ID for context

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "route": "context_search",
    "confidence": 0.88,
    "results": "Query processed through context search with relevant results..."
  },
  "id": 1
}
```

## Todo Tools

### add_todo

Add a new todo item to the task management system.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_todo",
      "arguments": {
        "title": "Implement API authentication",
        "description": "Add JWT-based authentication to the HTTP transport",
        "priority": 3
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `title` (string, required): Title of the todo item
- `description` (string, optional): Detailed description of the task - default: ""
- `priority` (integer, optional): Priority level (1=low, 2=medium, 3=high) - default: 1

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "todo_id": 456,
    "title": "Implement API authentication",
    "priority": 3,
    "status": "pending",
    "created_at": "2025-08-08T10:30:00Z"
  },
  "id": 1
}
```

### list_todos

List todo items with optional status filtering.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_todos",
      "arguments": {
        "status": "pending",
        "limit": 20
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `status` (string, optional): Filter by status - enum: ["all", "pending", "completed"] - default: "all"
- `limit` (integer, optional): Maximum number of todos to return (1-100, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "todos": [
      {
        "todo_id": 456,
        "title": "Implement API authentication",
        "description": "Add JWT-based authentication to the HTTP transport",
        "priority": 3,
        "status": "pending",
        "created_at": "2025-08-08T10:30:00Z"
      }
    ],
    "total_count": 15,
    "filtered_count": 12
  },
  "id": 1
}
```

### complete_todo

Mark a specific todo item as completed.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "complete_todo",
      "arguments": {
        "todo_id": 456
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `todo_id` (integer, required): ID of the todo item to complete

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "todo_id": 456,
    "status": "completed",
    "completed_at": "2025-08-08T11:45:00Z"
  },
  "id": 1
}
```

### search_todos

Search todo items by title or description using text search.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_todos",
      "arguments": {
        "query": "authentication",
        "limit": 10
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Search query to find matching todos
- `limit` (integer, optional): Maximum number of results to return (1-100, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "results": [
      {
        "todo_id": 456,
        "title": "Implement API authentication",
        "description": "Add JWT-based authentication to the HTTP transport",
        "priority": 3,
        "status": "pending",
        "relevance_score": 0.95
      }
    ],
    "total_results": 3
  },
  "id": 1
}
```

## Error Handling

All API responses follow the JSON-RPC 2.0 specification. Errors are returned in the following format:

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Missing required parameter 'file_name'"
    }
  },
  "id": 1
}
```

### Common Error Codes

- `-32700`: Parse error (Invalid JSON)
- `-32600`: Invalid Request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000` to `-32099`: Server-defined errors

## Rate Limiting

Currently, no rate limiting is implemented. For production deployments, implement appropriate rate limiting based on your requirements.

## Examples

### Complete Workflow Example

```bash
# 1. Store some memory
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "api_design.md",
        "content": "REST API best practices: Use proper HTTP methods, implement proper error handling, use JSON for data exchange..."
      }
    },
    "id": 1
  }'

# 2. Add a related todo
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_todo",
      "arguments": {
        "title": "Review API design document",
        "description": "Review the stored API design best practices",
        "priority": 2
      }
    },
    "id": 2
  }'

# 3. Search for related information
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "API best practices error handling"
      }
    },
    "id": 3
  }'
```

## Next Steps

- [Context Tools Reference](CONTEXT_TOOLS.md) - Advanced context and semantic search tools
- [Code Pattern Tools Reference](CODE_PATTERN_TOOLS.md) - ML-assisted code pattern analysis
- [Orchestration Tools Reference](ORCHESTRATION_TOOLS.md) - Multi-agent coordination tools
- [HTTP Transport Guide](HTTP_TRANSPORT.md) - Complete HTTP API documentation
- [MCP Protocol Guide](MCP_PROTOCOL.md) - JSON-RPC over stdio documentation