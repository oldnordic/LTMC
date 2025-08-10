# LTMC User Guide

## Getting Started with LTMC

Welcome to LTMC (Long-Term Memory and Context) - your intelligent memory and multi-agent coordination platform. This guide will help you get up and running quickly and make the most of LTMC's powerful features.

## What is LTMC?

LTMC is a sophisticated Model Context Protocol (MCP) server that provides:

- **Persistent Memory**: Store and retrieve documents with semantic search
- **Chat History Management**: Maintain conversation context across sessions
- **Task Management**: Track todos and project tasks
- **Code Pattern Learning**: AI-assisted code generation through experience replay
- **Multi-Agent Coordination**: Advanced orchestration for multiple AI agents
- **Knowledge Graphs**: Automatic document relationship discovery

## Quick Start

### 1. Basic Setup

After installation (see [Deployment Guide](DEPLOYMENT.md)), configure LTMC in Claude Code:

```json
{
  "ltmc": {
    "command": "python",
    "args": ["ltmc_mcp_server/main.py"],
    "cwd": "/path/to/ltmc-mcp-server"
  }
}
```

### 2. Your First Memory Storage

Store your first document:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "meeting_notes.md",
        "content": "# Team Meeting Notes\n\n## Project Status\n- API development is 80% complete\n- Frontend integration starting next week\n- Database migration scheduled for Friday\n\n## Action Items\n- Review code patterns\n- Update documentation\n- Schedule user testing"
      }
    },
    "id": 1
  }'
```

### 3. Search Your Memories

Retrieve relevant information:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "API development status",
        "top_k": 5
      }
    },
    "id": 2
  }'
```

## Core Features

### Memory Management

#### Storing Documents
LTMC automatically processes your documents:

```bash
# Store different types of content
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "python_best_practices.md",
        "content": "# Python Best Practices\n\n1. Use type hints\n2. Write docstrings\n3. Follow PEP 8\n4. Use virtual environments\n5. Write tests",
        "resource_type": "documentation"
      }
    },
    "id": 1
  }'
```

**What happens behind the scenes:**
1. Content is chunked into manageable pieces
2. Each chunk is converted to a vector embedding
3. Chunks are indexed for fast semantic search
4. Metadata is stored for filtering and organization

#### Searching with Context
Use semantic search to find relevant information:

```bash
# Search for specific topics
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "testing best practices",
        "top_k": 3
      }
    },
    "id": 2
  }'
```

### Task Management

#### Adding Tasks
Keep track of your todos:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_todo",
      "arguments": {
        "title": "Update API documentation",
        "description": "Add examples for new endpoints and update authentication section",
        "priority": 2
      }
    },
    "id": 1
  }'
```

#### Managing Tasks
List and complete your tasks:

```bash
# List pending tasks
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_todos",
      "arguments": {
        "status": "pending",
        "limit": 10
      }
    },
    "id": 2
  }'

# Complete a task
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "complete_todo",
      "arguments": {
        "todo_id": 1
      }
    },
    "id": 3
  }'
```

### Chat History Management

#### Logging Conversations
Maintain context across chat sessions:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_chat",
      "arguments": {
        "content": "User asked about implementing authentication in the API",
        "conversation_id": "project_discussion_001",
        "role": "user"
      }
    },
    "id": 1
  }'
```

#### Contextual Q&A
Ask questions with relevant context:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "ask_with_context",
      "arguments": {
        "question": "What are the best practices for API authentication?",
        "conversation_id": "project_discussion_001",
        "context_limit": 5
      }
    },
    "id": 2
  }'
```

### Code Pattern Learning

#### Learning from Code
Store successful code patterns for future reference:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Create a secure API endpoint with JWT authentication",
        "generated_code": "from fastapi import FastAPI, HTTPException, Depends\nfrom fastapi.security import HTTPBearer\nimport jwt\n\napp = FastAPI()\nsecurity = HTTPBearer()\n\ndef verify_token(token: str = Depends(security)):\n    try:\n        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[\"HS256\"])\n        return payload\n    except jwt.InvalidTokenError:\n        raise HTTPException(status_code=401, detail=\"Invalid token\")\n\n@app.get(\"/protected\")\nasync def protected_endpoint(current_user: dict = Depends(verify_token)):\n    return {\"message\": \"Hello, authenticated user!\", \"user\": current_user}",
        "result": "pass",
        "execution_time_ms": 125,
        "tags": "fastapi,jwt,authentication,security"
      }
    },
    "id": 1
  }'
```

#### Retrieving Code Patterns
Get similar successful patterns:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_code_patterns",
      "arguments": {
        "query": "FastAPI authentication JWT",
        "limit": 3
      }
    },
    "id": 2
  }'
```

## Advanced Features

### Knowledge Graph Integration

#### Linking Documents
Create relationships between documents:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "link_resources",
      "arguments": {
        "source_id": "api_docs_123",
        "target_id": "auth_guide_456",
        "relationship_type": "references"
      }
    },
    "id": 1
  }'
```

#### Auto-Linking Similar Documents
Let LTMC find relationships automatically:

```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "auto_link_documents",
      "arguments": {
        "document_id": "new_api_guide",
        "similarity_threshold": 0.8
      }
    },
    "id": 2
  }'
```

#### Querying the Knowledge Graph
Discover document relationships:

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
        "relationship_types": ["references", "implements"]
      }
    },
    "id": 3
  }'
```

### Multi-Agent Coordination

When using LTMC with multiple AI agents:

#### Agent Registration
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "register_agent",
      "arguments": {
        "agent_id": "coding_assistant",
        "agent_type": "code_generator",
        "capabilities": ["python", "fastapi", "testing"]
      }
    },
    "id": 1
  }'
```

#### Shared Context Management
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "create_shared_context",
      "arguments": {
        "session_id": "team_coding_session_001",
        "participating_agents": ["coding_assistant", "test_generator", "doc_writer"]
      }
    },
    "id": 2
  }'
```

## Integration Examples

### Python Integration

```python
import aiohttp
import asyncio
import json

class LTMCClient:
    def __init__(self, base_url="http://localhost:5050"):
        self.base_url = base_url
        
    async def call_tool(self, tool_name: str, arguments: dict):
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/jsonrpc",
                json=payload
            ) as response:
                return await response.json()

# Usage example
async def main():
    client = LTMCClient()
    
    # Store a document
    result = await client.call_tool("store_memory", {
        "file_name": "project_notes.md",
        "content": "Important project information..."
    })
    print("Stored:", result)
    
    # Search for information
    result = await client.call_tool("retrieve_memory", {
        "query": "project information",
        "top_k": 3
    })
    print("Found:", result)

# Run the example
asyncio.run(main())
```

### JavaScript Integration

```javascript
class LTMCClient {
    constructor(baseUrl = 'http://localhost:5050') {
        this.baseUrl = baseUrl;
    }
    
    async callTool(toolName, arguments) {
        const payload = {
            jsonrpc: '2.0',
            method: 'tools/call',
            params: {
                name: toolName,
                arguments: arguments
            },
            id: 1
        };
        
        const response = await fetch(`${this.baseUrl}/jsonrpc`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        return await response.json();
    }
}

// Usage example
const client = new LTMCClient();

// Store a document
client.callTool('store_memory', {
    file_name: 'meeting_notes.md',
    content: 'Meeting notes from today...'
}).then(result => {
    console.log('Stored:', result);
});

// Add a todo
client.callTool('add_todo', {
    title: 'Review API documentation',
    description: 'Check all endpoints are documented',
    priority: 2
}).then(result => {
    console.log('Todo added:', result);
});
```

### cURL Examples Collection

```bash
#!/bin/bash
# ltmc_examples.sh - Collection of useful LTMC commands

# Store project documentation
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "project_overview.md",
        "content": "# Project Overview\n\nThis project implements a REST API for user management with the following features:\n- User registration and authentication\n- Profile management\n- Role-based access control\n- Data validation and sanitization"
      }
    },
    "id": 1
  }'

# Search for authentication info
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "authentication implementation",
        "top_k": 3
      }
    },
    "id": 2
  }'

# Add development tasks
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "add_todo",
      "arguments": {
        "title": "Implement user registration endpoint",
        "description": "Create POST /users endpoint with validation",
        "priority": 3
      }
    },
    "id": 3
  }'

# Log successful code pattern
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Create user registration with password hashing",
        "generated_code": "from passlib.context import CryptContext\n\npwd_context = CryptContext(schemes=[\"bcrypt\"], deprecated=\"auto\")\n\ndef hash_password(password: str) -> str:\n    return pwd_context.hash(password)\n\ndef verify_password(plain_password: str, hashed_password: str) -> bool:\n    return pwd_context.verify(plain_password, hashed_password)",
        "result": "pass",
        "tags": "security,password,bcrypt"
      }
    },
    "id": 4
  }'
```

## Best Practices

### Memory Organization

1. **Use Descriptive Filenames**: Choose clear, searchable names
   ```
   ✓ "api_authentication_guide.md"
   ✗ "doc1.md"
   ```

2. **Tag Your Content**: Use consistent resource types
   ```
   ✓ resource_type: "documentation", "code", "meeting_notes"
   ✗ resource_type: "stuff", "things"
   ```

3. **Structure Your Content**: Well-formatted content searches better
   ```markdown
   # Clear Title
   
   ## Organized Sections
   
   - Bullet points
   - Key information
   - Actionable items
   ```

### Task Management

1. **Prioritize Effectively**:
   - Priority 3: Critical, blocking issues
   - Priority 2: Important, planned work
   - Priority 1: Nice to have, future work

2. **Write Clear Descriptions**: Include enough context for later review

3. **Use Search**: Find related tasks with `search_todos`

### Code Pattern Learning

1. **Log Both Success and Failure**: Failed attempts are valuable learning data

2. **Use Consistent Tags**: Standardize your tagging scheme
   ```
   ✓ "async,database,error-handling"
   ✗ "async stuff,db,errors"
   ```

3. **Include Performance Data**: Execution times help identify optimal patterns

### Context Management

1. **Use Conversation IDs**: Group related discussions
   ```
   "conversation_id": "feature_planning_2025_01"
   ```

2. **Build Rich Context**: Combine multiple sources for better results

3. **Monitor Usage**: Use statistics to understand your patterns

## Troubleshooting

### Common Issues

#### "Connection refused" Error
```bash
# Check if LTMC is running
curl http://localhost:5050/health

# If not running, start it
./start_server.sh
```

#### "No results found" in Search
```bash
# Check if documents are stored
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "retrieve_memory",
      "arguments": {
        "query": "",
        "top_k": 100
      }
    },
    "id": 1
  }'
```

#### Slow Search Performance
```bash
# Check system resources
curl http://localhost:5050/ml/status

# Consider adjusting search parameters
# Use more specific queries
# Reduce top_k values
```

### Getting Help

1. **Check Server Logs**:
   ```bash
   tail -f logs/ltmc_http.log
   ```

2. **Verify Configuration**:
   ```bash
   curl http://localhost:5050/orchestration/health
   ```

3. **Test Basic Functionality**:
   ```bash
   # Test storage
   curl -X POST http://localhost:5050/jsonrpc -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"store_memory","arguments":{"file_name":"test.md","content":"test"}},"id":1}'
   ```

## Next Steps

- **Advanced Usage**: See [API Reference](../api/API_REFERENCE.md) for complete tool documentation
- **Integration**: Learn about [Multi-Agent Coordination](../architecture/SYSTEM_ARCHITECTURE.md#multi-agent-coordination)
- **Performance**: Review [Performance Tuning Guide](PERFORMANCE_TUNING.md) for optimization
- **Deployment**: Scale with the [Deployment Guide](DEPLOYMENT.md)

## Community and Support

- **Documentation**: Complete guides in the `/docs` directory
- **Examples**: Additional examples in `/examples` directory
- **Issues**: Report problems and request features
- **Discussions**: Share use cases and get help

Welcome to the LTMC community! Start building smarter, more contextual applications today.