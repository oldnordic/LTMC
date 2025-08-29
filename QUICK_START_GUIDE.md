# LTMC Quick Start Guide

## What is LTMC?

LTMC (Long-Term Memory and Context) is a powerful MCP server that provides intelligent memory management, semantic search, and context-aware operations. It's designed to remember everything you work with and help you find it when you need it.

## 5-Minute Setup

### Step 1: Check Prerequisites

```bash
# Verify Python version (3.9+ required)
python --version

# Check if databases are running
redis-cli -p 6382 -a ltmc_password_2025 ping
# Should return: PONG

# Test Neo4j connection
cypher-shell -a bolt://localhost:7687 -u neo4j -p kwe_password "RETURN 'Connected' as status;"
# Should return: Connected
```

### Step 2: Start LTMC

```bash
cd /home/feanor/Projects/ltmc
python ltms/mcp_server.py
```

**Expected Output:**
```
LTMC MCP Server starting...
SQLite database: Connected (/home/feanor/Projects/Data/ltmc.db)
FAISS index: Loaded (1,105 vectors)
Neo4j: Connected (bolt://localhost:7687)
Redis: Connected (localhost:6382)
MCP Server ready on stdio transport
```

### Step 3: Connect Your MCP Client

**For Claude Code:**
Add to your MCP configuration:

```json
{
  "mcpServers": {
    "ltmc": {
      "command": "python",
      "args": ["/home/feanor/Projects/ltmc/ltms/mcp_server.py"],
      "transport": "stdio"
    }
  }
}
```

**For MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector python /home/feanor/Projects/ltmc/ltms/mcp_server.py
```

### Step 4: First Commands

**1. Check System Health**
```
Tool: cache_action
Action: health_check
```

**2. Store Your First Memory**
```
Tool: memory_action
Action: store
Parameters:
  file_name: "my_first_memory.md"
  content: "This is my first LTMC memory. It will be searchable!"
  resource_type: "document"
```

**3. Search for It**
```
Tool: memory_action
Action: retrieve
Parameters:
  query: "first memory"
  top_k: 5
```

## Essential Commands

### Memory Operations

**Store a Document:**
```
memory_action("store", 
  file_name="project_notes.md",
  content="Your content here...",
  resource_type="document")
```

**Search Your Memories:**
```
memory_action("retrieve",
  query="what I learned about databases",
  top_k=10)
```

**Ask Questions with Context:**
```
memory_action("ask_with_context",
  query="How does the authentication system work?",
  conversation_id="current_session",
  top_k=5)
```

### Task Management

**Add a Task:**
```
todo_action("add",
  title="Review documentation",
  description="Check all docs are up to date",
  priority="medium")
```

**List Tasks:**
```
todo_action("list", status="pending", limit=10)
```

**Complete a Task:**
```
todo_action("complete", todo_id=123)
```

### Natural Language Queries

**Find Past Conversations:**
```
chat_action("route_query", 
  query="yesterday's discussion about API design")
```

**Search Everything:**
```
chat_action("route_query",
  query="find anything related to error handling")
```

## Common Use Cases

### 1. Daily Development Log

**Morning Setup:**
```
# Log start of work session
chat_action("log",
  conversation_id="dev_2025_08_26",
  role="user", 
  content="Starting work on authentication module",
  source_tool="daily_log")

# Check pending tasks
todo_action("list", status="pending")
```

**During Development:**
```
# Store important findings
memory_action("store",
  file_name="auth_implementation_notes.md",
  content="Key insights about JWT implementation...",
  resource_type="document")

# Log code patterns that work
pattern_action("log_attempt",
  input_prompt="Create JWT token validation",
  generated_code="def validate_jwt(token): ...",
  result="pass")
```

**End of Day:**
```
# Add tomorrow's tasks
todo_action("add",
  title="Test authentication flow",
  description="End-to-end testing of new auth system",
  priority="high")

# Log session summary
chat_action("log",
  conversation_id="dev_2025_08_26",
  role="assistant",
  content="Completed JWT implementation, tests passing",
  source_tool="daily_log")
```

### 2. Research and Documentation

**Collect Information:**
```
# Store research findings
memory_action("store",
  file_name="oauth2_research.md", 
  content="OAuth 2.0 implementation patterns...",
  resource_type="document")

# Create relationship links
graph_action("auto_link",
  documents=[{id: "oauth2_research", type: "document"}])
```

**Generate Documentation:**
```
# Create API docs
documentation_action("generate_api_docs",
  file_path="/src/auth.py",
  project_id="main_project")

# Sync with code changes
sync_action("code",
  file_path="/src/auth.py")
```

### 3. Project Planning

**Create Project Blueprint:**
```
# Define project structure
blueprint_action("create",
  name="User Authentication System",
  description="OAuth2 + JWT implementation with Redis caching",
  complexity_score=7)

# Add dependencies
blueprint_action("add_dependency",
  project_id="auth_system", 
  dependency_id="redis_setup",
  dependency_type="requires")
```

**Track Progress:**
```
# Monitor project status
sync_action("status", project_id="auth_system")

# Get complexity analysis
blueprint_action("analyze_complexity", 
  blueprint_id="auth_system")
```

## Performance Tips

### Optimize Searches

**Use Specific Queries:**
```
# Good: Specific and targeted
memory_action("retrieve", query="JWT token validation error handling")

# Avoid: Too broad
memory_action("retrieve", query="code")
```

**Leverage Cache:**
```
# Check cache performance
cache_action("stats")

# Clear old cache if needed
cache_action("flush", pattern="old:*")
```

### Organize Content

**Use Descriptive Names:**
```
# Good: Clear and searchable
file_name="jwt_implementation_with_redis_caching.md"

# Avoid: Generic
file_name="notes.md"
```

**Set Appropriate Types:**
```
resource_type="document"  # For documentation, notes, research
resource_type="code"      # For code files, snippets
resource_type="chat"      # For conversation logs
```

## Troubleshooting

### Connection Issues

**Check Database Health:**
```
cache_action("health_check")
```

**Common Problems:**
- **Redis not responding**: Check service on port 6382 with password
- **Neo4j connection failed**: Verify bolt://localhost:7687 with neo4j/kwe_password
- **FAISS index missing**: Check /home/feanor/Projects/Data/faiss_index exists

### Performance Issues

**Slow Searches:**
```
# Check cache hit rate
cache_action("stats")

# If hit rate < 70%, consider:
# 1. Using more specific queries
# 2. Cache warming with common queries
# 3. Adjusting cache TTL settings
```

**Memory Usage:**
```
# Monitor system resources
config_action("validate_config")

# Clean up if needed
cache_action("reset")  # Clear all cache
```

### Data Issues

**Inconsistent Results:**
```
# Verify database consistency
sync_action("validate", check_consistency=true)

# Rebuild FAISS index if needed
# (Run: python rebuild_faiss_metadata.py)
```

## Next Steps

### Learn More
- Read the full [LTMC User Manual 2025](LTMC_USER_MANUAL_2025.md)
- Review [Database Architecture Guide](UNIFIED_ATOMIC_DATABASE_GUIDE.md)
- Check [Complete API Reference](ACCURATE_LTMC_API_REFERENCE.md)

### Advanced Features
- **Natural Language Queries**: Ask questions in plain English
- **Automatic Linking**: Let LTMC find relationships between your content
- **Code Pattern Learning**: Train LTMC on your coding patterns
- **Project Blueprints**: Manage complex projects with dependencies

### Integration Examples
- Use with Claude Code for enhanced development workflows
- Integrate with documentation systems for auto-sync
- Build custom workflows with the 11 consolidated tools

### Community and Support
- Check the project repository for updates
- Review test files for advanced usage examples
- Monitor performance with built-in analytics

---

**You're Ready!** LTMC is now your intelligent memory assistant. Start storing your work, and watch as it becomes easier to find and build upon your past efforts.

## Quick Reference Card

| Operation | Tool | Action | Key Parameters |
|-----------|------|--------|----------------|
| Store memory | memory_action | store | file_name, content, resource_type |
| Search memories | memory_action | retrieve | query, top_k |
| Add task | todo_action | add | title, description, priority |
| List tasks | todo_action | list | status, limit |
| Log chat | chat_action | log | conversation_id, role, content |
| Natural query | chat_action | route_query | query |
| Health check | cache_action | health_check | (none) |
| Cache stats | cache_action | stats | (none) |
| Link entities | graph_action | link | source_id, target_id, relation |
| Analyze code | pattern_action | extract_functions | file_path |
| Create blueprint | blueprint_action | create | name, description, complexity_score |

**Remember**: All tools return success/error status and detailed results. Always check the response for confirmation of operations.