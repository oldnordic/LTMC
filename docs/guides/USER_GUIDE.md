# LTMC User Guide - Stdio MCP Protocol

## Getting Started with LTMC

Welcome to LTMC (Long-Term Memory and Context) - your intelligent memory and multi-agent coordination platform. This guide will help you get up and running quickly and make the most of LTMC's powerful features via **stdio MCP protocol**.

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

LTMC operates exclusively through **stdio MCP transport**. There are two primary ways to use LTMC:

**Option A: Via Claude Code (Recommended)**
```json
// Add to .claude/claude_desktop_config.json
{
  "mcpServers": {
    "ltmc": {
      "command": "python",
      "args": ["path/to/ltmc_stdio_wrapper.py"],
      "env": {
        "LTMC_CONFIG_PATH": "/path/to/ltmc/config"
      }
    }
  }
}
```

**Option B: Direct MCP Client Integration**
```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def setup_ltmc():
    server_params = StdioServerParameters(
        command="python",
        args=["ltmc_stdio_wrapper.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize LTMC tools
            await session.initialize()
            return session
```

### 2. Store Information

Store important information for later retrieval:

**Via MCP Tool Call:**
```python
# Using MCP tool call
result = await session.call_tool("store_memory", {
    "file_name": "meeting_notes.md",
    "content": """# Team Meeting Notes

## Project Status
- API development is 80% complete
- Frontend integration starting next week
- Database migration scheduled for Friday

## Action Items
- Review code patterns
- Update documentation
- Schedule user testing""",
    "resource_type": "document"
})
```

**Via Claude Code (Natural Language):**
```
Please store these meeting notes using LTMC:

Team Meeting Notes:
- API development is 80% complete
- Frontend integration starting next week
- Database migration scheduled for Friday

Action Items:
- Review code patterns
- Update documentation
- Schedule user testing
```

### 3. Search Your Memories

Retrieve relevant information using semantic search:

**Via MCP Tool Call:**
```python
# Search for relevant memories
results = await session.call_tool("retrieve_memory", {
    "query": "API development status and next steps",
    "conversation_id": "session_20250101",
    "top_k": 5,
    "resource_type": "document"
})

print("Found relevant memories:")
for result in results["memories"]:
    print(f"- {result['file_name']}: {result['content'][:100]}...")
```

**Via Claude Code (Natural Language):**
```
Search my LTMC memories for information about API development status
```

### 4. Chat Continuity

Maintain conversation context across sessions:

**Via MCP Tool Call:**
```python
# Log chat messages for continuity
await session.call_tool("log_chat", {
    "content": "Discussed API architecture changes and timeline adjustments",
    "conversation_id": "session_20250101",
    "role": "user",
    "metadata": {
        "topic": "api_development",
        "priority": "high"
    }
})

# Retrieve chat history
history = await session.call_tool("ask_with_context", {
    "query": "What did we discuss about the API timeline?",
    "conversation_id": "session_20250101",
    "include_history": True
})
```

### 5. Task Management

Track and manage tasks:

**Via MCP Tool Call:**
```python
# Add a new task
task = await session.call_tool("add_todo", {
    "title": "Implement user authentication API",
    "description": "Create secure JWT-based authentication endpoints with proper validation and error handling",
    "priority": "high"
})

# List pending tasks
pending_tasks = await session.call_tool("list_todos", {
    "status": "pending",
    "priority": "high",
    "limit": 10
})

# Mark task as completed
await session.call_tool("complete_todo", {
    "todo_id": task["todo_id"]
})
```

### 6. Code Pattern Learning

Learn from successful code patterns:

**Via MCP Tool Call:**
```python
# Log successful code pattern
await session.call_tool("log_code_attempt", {
    "input_prompt": "Create async database connection with error handling",
    "generated_code": """
import asyncpg
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db_connection():
    conn = None
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        yield conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise
    finally:
        if conn:
            await conn.close()
""",
    "result": "pass",
    "tags": ["python", "async", "database", "error_handling"]
})

# Retrieve similar patterns when needed
patterns = await session.call_tool("get_code_patterns", {
    "query": "async database connection with error handling",
    "result_filter": "pass",
    "top_k": 5
})
```

## Advanced Features

### Multi-Agent Coordination

LTMC provides advanced orchestration for multiple AI agents:

**Via MCP Tool Call:**
```python
# Create task blueprint for multi-agent execution
blueprint = await session.call_tool("create_task_blueprint", {
    "title": "Implement user dashboard",
    "description": "Create responsive user dashboard with real-time data",
    "estimated_duration_minutes": 240,
    "required_skills": ["frontend", "backend", "database"],
    "priority_score": 0.8,
    "tags": ["ui", "dashboard", "real-time"]
})

# Analyze task complexity
complexity = await session.call_tool("analyze_task_complexity", {
    "title": "Implement user dashboard",
    "description": "Create responsive user dashboard with real-time data",
    "required_skills": ["frontend", "backend", "database"]
})
```

### Knowledge Graphs

Build and query knowledge relationships:

**Via MCP Tool Call:**
```python
# Link related documents
await session.call_tool("link_resources", {
    "resource_1_id": "api_docs_id",
    "resource_2_id": "frontend_guide_id",
    "relationship_type": "implements",
    "metadata": {
        "connection_strength": "high",
        "created_by": "system"
    }
})

# Query document relationships
relationships = await session.call_tool("get_document_relationships", {
    "document_id": "api_docs_id",
    "include_metadata": True
})
```

### System Health Monitoring

Monitor LTMC system health:

**Via MCP Tool Call:**
```python
# Check Redis cache health
redis_health = await session.call_tool("redis_health_check")

# Get cache statistics
cache_stats = await session.call_tool("redis_cache_stats")

# Get performance metrics
performance = await session.call_tool("get_performance_report")
```

## Configuration

### Environment Variables

```bash
# Core Configuration
LTMC_DB_PATH=/path/to/ltmc.db
LTMC_VECTOR_PATH=/path/to/vector_store
REDIS_HOST=localhost
REDIS_PORT=6379
NEO4J_URI=bolt://localhost:7687

# Security
REDIS_PASSWORD=your_redis_password
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

# Performance
LTMC_CACHE_SIZE=1000
LTMC_VECTOR_DIMENSIONS=384
LTMC_SIMILARITY_THRESHOLD=0.7
```

### MCP Server Configuration

For Claude Code integration, add to your `.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ltmc": {
      "command": "python",
      "args": ["ltmc_stdio_wrapper.py"],
      "env": {
        "LTMC_DB_PATH": "/home/user/ltmc/data/ltmc.db",
        "LTMC_VECTOR_PATH": "/home/user/ltmc/data/vectors",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "NEO4J_URI": "bolt://localhost:7687",
        "LTMC_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

## Health Check and Status

Monitor your LTMC system status:

**Via MCP Tool Call:**
```python
# Get comprehensive system status
status = await session.call_tool("get_performance_report")

# Check specific components
redis_status = await session.call_tool("redis_health_check")
context_stats = await session.call_tool("get_context_usage_statistics")
```

**Via Claude Code StatusLine:**
Your Claude Code statusline will show real-time LTMC system status including:
- 🚀 LTMC Optimal (system status)
- 55 tools (available MCP tools)
- 55+v (vector count)
- redis:6382 (Redis connection)
- ML:opt (ML integration status)
- mem:ok (memory system)
- stdio (transport protocol)

## Troubleshooting

### Common Issues

**1. MCP Server Not Starting**
```bash
# Check process
pgrep -f ltmc_mcp_server

# Check logs
tail -f ltmc_server.log
```

**2. Memory/Vector Store Issues**
```python
# Reset vector store if needed
await session.call_tool("redis_clear_cache", {
    "pattern": "ltmc:vectors:*"
})
```

**3. Performance Issues**
```python
# Check system performance
performance = await session.call_tool("get_performance_report")
print(f"Status: {performance['status']}")
print(f"Memory usage: {performance['memory_usage']}")
```

## Best Practices

1. **Use Descriptive Names**: Always use meaningful file names and content descriptions
2. **Leverage Tags**: Tag your code patterns and documents for better organization
3. **Monitor Performance**: Regularly check system health via MCP tools
4. **Maintain Context**: Use conversation IDs to maintain session continuity
5. **Cache Management**: Leverage Redis caching for better performance
6. **Regular Backups**: Export important memories periodically

## Next Steps

- Explore the **[Complete 55 Tools Reference](COMPLETE_55_TOOLS_REFERENCE.md)** for detailed tool documentation
- Check out **[API Reference](../api/API_REFERENCE.md)** for comprehensive MCP tool specifications
- Review **[Troubleshooting Guide](TROUBLESHOOTING.md)** for common issues and solutions
- See **[System Architecture](../architecture/SYSTEM_ARCHITECTURE.md)** for technical details

---

**Note**: LTMC operates exclusively via stdio MCP protocol. All examples in this guide demonstrate the recommended integration patterns for maximum performance and reliability.