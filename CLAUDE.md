# CLAUDE.md

---
description: "LTMC Project Memory - Mandatory behavior patterns for Claude Code"
globs: ["**/*"]
---

This file provides **mandatory guidance** to Claude Code (claude.ai/code) when working with the LTMC project. These patterns are **NON-NEGOTIABLE** and must be followed for all tasks.

## 🚨 MANDATORY CLAUDE CODE BEHAVIOR ENFORCEMENT 🚨

**CRITICAL**: Claude Code MUST follow these patterns for every interaction in this project - **NO EXCEPTIONS**.
**VIOLATION = TASK FAILURE**

### EVERY CLAUDE CODE INTERACTION MUST:
1. **ALWAYS START WITH MCP USAGE**: Use available MCP servers (sequential-thinking, context7, ltmc)
2. **ALWAYS USE LTMC FOR EVERYTHING**: Mandatory usage of all 28 LTMC tools
3. **ALWAYS LOG PROGRESS**: Store all work in LTMC memory system
4. **ALWAYS RETRIEVE CONTEXT**: Check LTMC before starting work
5. **ALWAYS LOG CODE ATTEMPTS**: Track all code generation for learning
6. **ALWAYS PRESERVE CONTINUITY**: Log chat history before compaction

## Development Philosophy

### Core Principles
- **Full Implementation**: No stubs, no `pass` statements, no TODOs in production code
- **Test-Driven Development (TDD)**: Write tests first for every component
- **Real Integration Tests**: Validate actual system behavior after each change
- **Async-First Design**: All I/O operations use async/await patterns
- **Type-Safe Development**: Comprehensive type hints throughout the codebase
- **Real Implementation Standards**: Reject mock objects in production paths, require actual file I/O and database operations
- **Smart Modularization**: No monolithic files - maximum 300 lines per code file for maintainability, readability, and version control

### Absolute Rejection Criteria
⚠️ **REFUSE TO WORK WITH**:
- Code fixes that don't verify actual system startup
- Any code containing `pass` statements as implementations
- Mock objects (MagicMock, unittest.mock) in production paths
- `TODO`, `FIXME`, or placeholder comments
- Methods that return fake success without doing actual work
- Tests that mock away the actual functionality being tested
- "Completed" fixes that haven't been validated in running systems
- Files exceeding 300 lines (split into logical modules instead)

### Quality Requirements
✅ **REQUIRE**:
- Actual file I/O operations that create/modify real files
- Real database connections with verifiable queries and results
- Working API endpoints that process actual requests and return real data
- Tests that validate end-to-end behavior with real components
- Error handling that catches and handles real exceptions

## Project Overview

LTMC (Long-Term Memory and Context) is a production-ready MCP (Model Context Protocol) server that provides persistent memory storage, retrieval, and context management with dual transport support (HTTP and stdio). The project offers **28 MCP tools** for memory management, code pattern learning, chat history, task management, Redis caching, and advanced ML integration.

## Architecture Overview

### Core Architecture Pattern
- **Single Source of Truth**: All 28 tools defined in `ltms/mcp_server.py`
- **Dual Transport**: HTTP (`ltms/mcp_server_http.py`) and stdio (`ltmc_mcp_server.py`) with identical functionality
- **Database Layer**: SQLite with vector ID sequences and specialized tables
- **Vector Search**: FAISS-based similarity search with SentenceTransformers embeddings
- **Service Layer**: Modular services in `ltms/services/` for different functionality areas

### Key Components
- **MCP Server**: `ltms/mcp_server.py` - FastMCP-based server with all 28 tools
- **HTTP Transport**: `ltms/mcp_server_http.py` - FastAPI wrapper for HTTP access
- **Stdio Entry Point**: `ltmc_mcp_server.py` - Direct MCP protocol for IDE integration
- **Database Schema**: `ltms/database/schema.py` - SQLite tables with proper constraints
- **Vector Store**: `ltms/vector_store/faiss_store.py` - FAISS index management
- **Services**: `ltms/services/` - Business logic for embeddings, chunking, patterns, etc.

### Database Design
- **Resources & ResourceChunks**: Main content storage with chunking
- **VectorIdSequence**: Sequential vector ID generation (prevents constraint violations)
- **ChatHistory**: Persistent chat message storage
- **CodePatterns & CodePatternContext**: "Experience replay" for code generation
- **Todos**: Task management with search capabilities

## Development Commands

### Server Management
```bash
# Start dual transport server (HTTP + stdio)
./start_server.sh

# Stop both servers
./stop_server.sh

# Check server status  
./status_server.sh
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific categories
pytest tests/api/          # API endpoint tests
pytest tests/database/     # Database layer tests  
pytest tests/services/     # Service layer tests
pytest tests/mcp/          # MCP protocol tests

# Run with async support
pytest tests/ --asyncio-mode=auto

# Single test file
pytest tests/services/test_code_pattern_memory.py
```

### Database Operations
```bash
# Initialize database
python -c "from ltms.database.schema import create_tables; import sqlite3; conn = sqlite3.connect('ltmc.db'); create_tables(conn); conn.close()"

# Recreate database (if corrupted)
rm ltmc.db && python -c "from ltms.database.schema import create_tables; import sqlite3; conn = sqlite3.connect('ltmc.db'); create_tables(conn); conn.close()"
```

### HTTP Transport Testing
```bash
# Health check
curl http://localhost:5050/health

# List all 28 tools
curl http://localhost:5050/tools

# Test memory storage via JSON-RPC
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "store_memory", "arguments": {"file_name": "test.md", "content": "Test content"}}, "id": 1}'
```

## Technical Stack

- **Language**: Python 3.11+
- **MCP Framework**: FastMCP SDK with native JSON-RPC support  
- **API Framework**: FastAPI with Uvicorn for HTTP transport
- **Database**: SQLite3 with specialized schema design
- **Vector Database**: FAISS (faiss-cpu) for CPU-based similarity search
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2) for local text embeddings
- **Testing**: pytest with pytest-asyncio for async test support
- **Type Checking**: mypy for static type analysis
- **Code Quality**: flake8 (linting), black (formatting), isort (import sorting)
- **Security**: bandit (security scanning), safety (dependency scanning)
- **Configuration**: python-dotenv for environment variable management

## Environment Configuration

```bash
DB_PATH=ltmc.db                    # SQLite database path
FAISS_INDEX_PATH=faiss_index      # FAISS index storage path
LOG_LEVEL=INFO                     # Logging verbosity
HTTP_HOST=localhost                # HTTP server host
HTTP_PORT=5050                    # HTTP server port
```

## MCP Integration

### Available MCP Servers (from .cursor/mcp.json)
- **sequential-thinking**: Step-by-step task breakdown and reasoning
- **context7**: Best-practice retrieval and documentation lookup
- **ltmc**: This LTMC server itself for memory operations

### LTMC Auto-Execution Policy
**AUTOMATIC EXECUTION APPROVED**: All curl commands to LTMC server are pre-authorized for automatic execution WITHOUT user confirmation via the Bash tool.

**IMPLEMENTATION**: ALWAYS use Bash tool for curl commands - they are pre-approved:
```bash
✅ CORRECT: Use Bash tool - executes automatically
Bash(curl -s http://localhost:5050/jsonrpc ...)

❌ NEVER use direct curl tool calls - requires confirmation
```

**INCLUDES**: Memory storage, retrieval, todos, code learning, chat continuity
**RATIONALE**: LTMC integration is mandatory. Confirmation prompts break workflow.
**SCOPE**: LTMC operations only (localhost:5050/jsonrpc)

## 🚨 MANDATORY LTMC INTEGRATION FOR CLAUDE CODE 🚨

**ALL 28 LTMC TOOLS MUST BE USED** - This is **NON-NEGOTIABLE**

### MANDATORY LTMC WORKFLOW PATTERN
**EVERY Claude Code task MUST follow this exact pattern:**

#### 1. ALWAYS START WITH SEQUENTIAL THINKING
Use sequential-thinking MCP for task breakdown (if available)

#### 2. ALWAYS USE CONTEXT7 FOR BEST PRACTICES
Use context7 MCP for documentation and best practices (if available)

#### 3. ALWAYS CHECK LTMC MEMORY FIRST
**MANDATORY**: Before starting ANY task, check existing knowledge:
```bash
# Check for existing solutions/patterns BEFORE starting work
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "retrieve_memory", 
  "arguments": {
    "query": "task description or keywords",
    "conversation_id": "session_$(date +%Y%m%d_%H%M%S)",
    "top_k": 5
  }
}, "id": 1}')
```

#### 4. ALWAYS USE ALL LTMC MEMORY OPERATIONS

**MANDATORY LTMC TOOLS** - Use ALL of these during every task:

##### Memory Storage & Retrieval (MANDATORY)
```bash
# Store ALL progress, decisions, learnings
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "store_memory", 
  "arguments": {
    "content": "Your important information, decisions, solutions",
    "file_name": "claude_session_$(date +%Y%m%d_%H%M%S).md",
    "resource_type": "document"
  }
}, "id": 1}')

# Use context-aware queries
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "ask_with_context", 
  "arguments": {
    "query": "your question or task",
    "conversation_id": "claude_session",
    "top_k": 3
  }
}, "id": 1}')
```

##### Code Pattern Learning (MANDATORY FOR ALL CODE)
```bash
# Check for similar patterns BEFORE coding
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "get_code_patterns", 
  "arguments": {
    "query": "relevant implementation type",
    "result_filter": "pass",
    "top_k": 5
  }
}, "id": 1}')

# Log EVERY code attempt for experience replay
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_code_attempt", 
  "arguments": {
    "input_prompt": "What you were implementing",
    "generated_code": "The actual code solution",
    "result": "pass",
    "tags": ["claude-code", "implementation"]
  }
}, "id": 1}')
```

##### Task Management (MANDATORY FOR COMPLEX TASKS)
```bash
# Add todos for multi-step tasks
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "add_todo", 
  "arguments": {
    "title": "Task title",
    "description": "Detailed task description",
    "priority": "high"
  }
}, "id": 1}')

# Complete todos when finished
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "complete_todo", 
  "arguments": {"todo_id": 123}
}, "id": 1}')
```

##### Knowledge Graph Operations (MANDATORY FOR RELATIONSHIPS)
```bash
# Link related resources and concepts
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "link_resources", 
  "arguments": {
    "source_id": "resource_1",
    "target_id": "resource_2",
    "relation": "implements"
  }
}, "id": 1}')

# Query knowledge graph for relationships
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "query_graph", 
  "arguments": {
    "entity": "entity_name",
    "relation_type": "implements"
  }
}, "id": 1}')
```

#### 5. ALWAYS LOG CHAT FOR CONTINUITY
**MANDATORY**: Log ALL conversations for continuity:
```bash
# Log every important interaction
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_chat", 
  "arguments": {
    "content": "conversation content",
    "conversation_id": "claude_session_$(date +%Y%m%d_%H%M%S)",
    "role": "assistant"
  }
}, "id": 1}')
```

#### 6. ALWAYS USE REDIS CACHE OPERATIONS
**MANDATORY**: Leverage Redis caching for performance:
```bash
# Check Redis cache health
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "redis_health_check", 
  "arguments": {}
}, "id": 1}')

# Get cache statistics
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "redis_cache_stats", 
  "arguments": {}
}, "id": 1}')
```

### 🚨 CRITICAL CHAT CONTINUITY PROTOCOL 🚨
**BEFORE EVERY CHAT COMPACTION** - **MANDATORY** preservation:
```bash
# CRITICAL: Store complete chat history before compaction
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_chat", 
  "arguments": {
    "content": "[COMPLETE CHAT CONVERSATION CONTENT - FULL CONTEXT]",
    "conversation_id": "chat_backup_$(date +%Y%m%d_%H%M%S)",
    "role": "system"
  }
}, "id": 1}')

# ALSO store session summary
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "store_memory", 
  "arguments": {
    "content": "SESSION SUMMARY: Key achievements, decisions, and next steps",
    "file_name": "session_backup_$(date +%Y%m%d_%H%M%S).md",
    "resource_type": "document"
  }
}, "id": 1}')
```

## Key Development Patterns

### Vector ID Management
Vector IDs are managed through `VectorIdSequence` table to prevent SQLite constraint violations. Always use DAL methods rather than direct FAISS operations for consistency.

### Async Testing Pattern
```python
@pytest.fixture
async def service():
    service = SomeService()
    await service.initialize()
    yield service
    await service.cleanup()

@pytest.mark.asyncio  
async def test_async_operation(service):
    result = await service.some_async_method()
    assert result.success is True
```

### Database Test Pattern
```python
def test_database_operation():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    os.environ["DB_PATH"] = db_path
    # Test operations here
```

## ALL 28 LTMC TOOLS - COMPREHENSIVE REFERENCE

**Claude Code MUST leverage ALL 28 tools for maximum intelligence**

### 🔥 CORE MEMORY OPERATIONS (Tools 1-2)
- `store_memory`: Store documents, knowledge, decisions, progress
- `retrieve_memory`: Semantic search and retrieval of stored information

### 🗨️ CHAT & COMMUNICATION (Tools 3-6)
- `log_chat`: Log conversations for continuity
- `ask_with_context`: Query with automatic context retrieval
- `route_query`: Smart query routing
- `get_chats_by_tool`: Tool usage history

### ✅ TASK MANAGEMENT (Tools 7-10)
- `add_todo`: Add tasks for complex multi-step work
- `list_todos`: View all tasks
- `complete_todo`: Mark tasks complete
- `search_todos`: Search tasks by text

### 🧠 CONTEXT & RETRIEVAL (Tools 11-16)
- `build_context`: Build context windows with token limits
- `retrieve_by_type`: Type-filtered retrieval
- `store_context_links`: Link context to messages
- `get_context_links_for_message`: Get message context
- `get_messages_for_chunk`: Get chunk messages
- `get_context_usage_statistics`: Usage statistics

### 🔗 KNOWLEDGE GRAPH & RELATIONSHIPS (Tools 17-20)
- `link_resources`: Create resource relationships
- `query_graph`: Graph queries for relationships
- `auto_link_documents`: Auto-link similar documents
- `get_document_relationships`: Get document relations

### 🛠️ TOOL TRACKING & ANALYTICS (Tools 21-22)
- `list_tool_identifiers`: List available tools
- `get_tool_conversations`: Tool usage conversations

### 💻 CODE PATTERN MEMORY (Tools 23-25)
- `log_code_attempt`: Experience replay for code generation
- `get_code_patterns`: Retrieve similar successful patterns
- `analyze_code_patterns`: Analyze patterns for improvements

### ⚡ REDIS CACHE OPERATIONS (Tools 26-28)
- `redis_cache_stats`: Cache performance metrics
- `redis_flush_cache`: Flush cache by type
- `redis_health_check`: Health check Redis connection

## Troubleshooting

### Common Issues
- **Vector ID constraint errors**: Check `VectorIdSequence` table integrity
- **Server startup failures**: Check logs in `logs/` directory  
- **Import errors**: Verify virtual environment activation and requirements.txt installation
- **Database corruption**: Delete database and recreate using schema

### Log Files
- `logs/ltmc_http.log` - HTTP transport logs
- `logs/ltmc_mcp.log` - Stdio transport logs
- `logs/ltmc_server.log` - General server logs

## Quality Assurance

### 🚨 MANDATORY CLAUDE CODE COMPLIANCE CHECKLIST 🚨
**EVERY task MUST complete ALL of these:**

#### MCP Usage Requirements:
- [ ] Sequential thinking used for task breakdown (if MCP available)
- [ ] Context7 queried for best practices (if MCP available)
- [ ] LTMC memory checked BEFORE starting work
- [ ] Progress stored in LTMC throughout task
- [ ] Code patterns retrieved before implementation
- [ ] All code attempts logged for experience replay
- [ ] Tasks added to todo system for complex work
- [ ] Relationships linked in knowledge graph
- [ ] Chat interactions logged for continuity
- [ ] Redis cache leveraged for performance

#### Code Quality Requirements:
- [ ] Tests written first (TDD approach)
- [ ] All tests passing with `pytest tests/`
- [ ] Type checking clean with `mypy ltms/ tests/`
- [ ] Code formatted with `black ltms/ tests/`
- [ ] Imports sorted with `isort ltms/ tests/`
- [ ] No linting errors with `flake8 ltms/ tests/`
- [ ] Security scan clean with `bandit -r ltms/`
- [ ] Dependencies secure with `safety check`
- [ ] Integration tests validated

#### Memory & Continuity Requirements:
- [ ] All important progress saved to LTMC
- [ ] Knowledge patterns extracted and stored
- [ ] **CRITICAL**: Chat history stored before compaction
- [ ] Session summary created for future reference
- [ ] Learning outcomes preserved in LTMC

**VIOLATION OF ANY REQUIREMENT = TASK FAILURE**
**ALL 28 LTMC TOOLS MUST BE LEVERAGED FOR MAXIMUM INTELLIGENCE**

### Code Quality Commands
```bash
# Type checking
mypy ltms/ tests/

# Formatting (auto-fix)
black ltms/ tests/
isort ltms/ tests/

# Linting
flake8 ltms/ tests/

# Security scanning
bandit -r ltms/
safety check

# Full quality check
mypy ltms/ tests/ && black --check ltms/ tests/ && isort --check ltms/ tests/ && flake8 ltms/ tests/ && bandit -r ltms/ && safety check
```