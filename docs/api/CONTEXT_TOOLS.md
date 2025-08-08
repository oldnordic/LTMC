# LTMC Context Tools Reference

## Overview

Context Tools provide advanced semantic search, document relationship management, and knowledge graph functionality for the LTMC system. These tools enable sophisticated context management and automatic document linking.

## Context Management Tools

### build_context

Build a context window from a list of documents with token limiting.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "build_context",
      "arguments": {
        "documents": [
          {"content": "Document 1 content...", "id": "doc1"},
          {"content": "Document 2 content...", "id": "doc2"}
        ],
        "max_tokens": 4000
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `documents` (array, required): List of documents to build context from
- `max_tokens` (integer, optional): Maximum tokens for the context window (100-32000, default: 4000)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "context": "Combined context from documents...",
    "token_count": 3850,
    "documents_included": 2,
    "documents_truncated": 0
  },
  "id": 1
}
```

### retrieve_by_type

Retrieve documents filtered by type using semantic search.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_by_type",
      "arguments": {
        "query": "error handling patterns",
        "doc_type": "code",
        "top_k": 5
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Search query
- `doc_type` (string, required): Type of documents to retrieve
- `top_k` (integer, optional): Number of results to return (1-50, default: 5)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "results": [
      {
        "resource_id": 123,
        "content": "try-catch error handling code...",
        "similarity_score": 0.89,
        "resource_type": "code",
        "metadata": {
          "file_name": "error_handlers.py",
          "created_at": "2025-08-08T10:30:00Z"
        }
      }
    ],
    "total_results": 3,
    "query_type": "code"
  },
  "id": 1
}
```

## Context Linking Tools

### store_context_links

Store links between a message and document chunks for context tracking.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_context_links",
      "arguments": {
        "message_id": "msg_123",
        "chunk_ids": [456, 789, 101112]
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `message_id` (string, required): ID of the message
- `chunk_ids` (array, required): List of chunk IDs to link

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "links_created": 3,
    "message_id": "msg_123",
    "linked_chunks": [456, 789, 101112]
  },
  "id": 1
}
```

### get_context_links_for_message

Retrieve context links for a specific message.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_context_links_for_message",
      "arguments": {
        "message_id": "msg_123"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `message_id` (string, required): ID of the message to get links for

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message_id": "msg_123",
    "context_links": [
      {
        "chunk_id": 456,
        "content": "Relevant chunk content...",
        "resource_id": 789,
        "link_strength": 0.92
      }
    ],
    "total_links": 3
  },
  "id": 1
}
```

### get_messages_for_chunk

Get messages that reference a specific document chunk.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_messages_for_chunk",
      "arguments": {
        "chunk_id": 456
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `chunk_id` (integer, required): ID of the chunk to find messages for

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "chunk_id": 456,
    "messages": [
      {
        "message_id": "msg_123",
        "content": "Message content referencing this chunk...",
        "conversation_id": "session_456",
        "timestamp": "2025-08-08T10:30:00Z"
      }
    ],
    "total_messages": 2
  },
  "id": 1
}
```

## Statistics and Analysis

### get_context_usage_statistics

Get statistics about context usage patterns.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_context_usage_statistics",
      "arguments": {}
    },
    "id": 1
  }'
```

**Parameters:** None

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "statistics": {
      "total_context_links": 1250,
      "total_chunks": 890,
      "total_messages": 445,
      "average_links_per_message": 2.8,
      "most_referenced_chunks": [
        {"chunk_id": 456, "reference_count": 25},
        {"chunk_id": 789, "reference_count": 18}
      ],
      "context_usage_trends": {
        "daily_average": 45,
        "peak_usage_hour": 14
      }
    }
  },
  "id": 1
}
```

## Knowledge Graph Tools

### link_resources

Create a relationship link between two resources.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "link_resources",
      "arguments": {
        "source_id": "resource_123",
        "target_id": "resource_456",
        "relationship_type": "depends_on"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `source_id` (string, required): ID of the source resource
- `target_id` (string, required): ID of the target resource  
- `relationship_type` (string, required): Type of relationship (related_to, depends_on, etc.)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "relationship_id": "rel_789",
    "source_id": "resource_123",
    "target_id": "resource_456",
    "relationship_type": "depends_on",
    "created_at": "2025-08-08T10:30:00Z"
  },
  "id": 1
}
```

### query_graph

Query the knowledge graph for related resources.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "query_graph",
      "arguments": {
        "query": "authentication implementation",
        "relationship_types": ["depends_on", "related_to"]
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Query to search the knowledge graph
- `relationship_types` (array, optional): Filter by specific relationship types

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "query": "authentication implementation",
    "results": [
      {
        "resource_id": "resource_123",
        "content": "JWT authentication implementation...",
        "relationships": [
          {
            "target_id": "resource_456",
            "relationship_type": "depends_on",
            "strength": 0.95
          }
        ],
        "relevance_score": 0.89
      }
    ],
    "total_results": 5
  },
  "id": 1
}
```

### auto_link_documents

Automatically create links between similar documents.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "auto_link_documents",
      "arguments": {
        "document_id": "doc_123",
        "similarity_threshold": 0.8
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `document_id` (string, required): ID of the document to find links for
- `similarity_threshold` (number, optional): Minimum similarity score for linking (0.0-1.0, default: 0.8)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "document_id": "doc_123",
    "links_created": 5,
    "similar_documents": [
      {
        "document_id": "doc_456",
        "similarity_score": 0.92,
        "relationship_type": "similar_content"
      },
      {
        "document_id": "doc_789",
        "similarity_score": 0.85,
        "relationship_type": "similar_content"
      }
    ]
  },
  "id": 1
}
```

### get_document_relationships

Get all relationships for a document up to specified depth.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_document_relationships",
      "arguments": {
        "document_id": "doc_123",
        "max_depth": 2
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `document_id` (string, required): ID of the document
- `max_depth` (integer, optional): Maximum depth to traverse relationships (1-5, default: 2)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "document_id": "doc_123",
    "relationships": {
      "depth_1": [
        {
          "document_id": "doc_456",
          "relationship_type": "depends_on",
          "strength": 0.95
        }
      ],
      "depth_2": [
        {
          "document_id": "doc_789",
          "relationship_type": "related_to",
          "strength": 0.82,
          "path": ["doc_123", "doc_456", "doc_789"]
        }
      ]
    },
    "total_relationships": 8,
    "max_depth_reached": 2
  },
  "id": 1
}
```

## Tool Management

### list_tool_identifiers

List all available tool identifiers in the system.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_tool_identifiers",
      "arguments": {}
    },
    "id": 1
  }'
```

**Parameters:** None

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "tools": [
      {
        "name": "store_memory",
        "category": "memory",
        "description": "Store documents with vector indexing"
      },
      {
        "name": "log_chat",
        "category": "chat",
        "description": "Log chat messages with context"
      }
    ],
    "total_tools": 25,
    "categories": ["memory", "chat", "todo", "context", "code_pattern"]
  },
  "id": 1
}
```

### get_tool_conversations

Get conversations that involved a specific tool.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_tool_conversations",
      "arguments": {
        "tool_name": "store_memory",
        "limit": 10
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `tool_name` (string, required): Name of the tool
- `limit` (integer, optional): Maximum number of conversations to return (1-100, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "tool_name": "store_memory",
    "conversations": [
      {
        "conversation_id": "session_123",
        "usage_count": 5,
        "last_used": "2025-08-08T10:30:00Z",
        "context_summary": "User storing project documentation"
      }
    ],
    "total_conversations": 25,
    "usage_statistics": {
      "total_invocations": 150,
      "average_per_conversation": 6
    }
  },
  "id": 1
}
```

## Best Practices

### Context Building
- Use appropriate token limits based on your use case
- Include diverse documents for richer context
- Monitor token usage to avoid truncation

### Document Linking
- Set appropriate similarity thresholds for auto-linking
- Use meaningful relationship types for manual links
- Regular analysis of link patterns can reveal insights

### Knowledge Graph Queries
- Use specific relationship type filters for targeted results
- Consider traversal depth based on your analysis needs
- Combine graph queries with semantic search for best results

## Next Steps

- [Code Pattern Tools Reference](CODE_PATTERN_TOOLS.md) - ML-assisted code pattern analysis
- [API Reference](API_REFERENCE.md) - Complete API documentation
- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md) - Technical architecture overview