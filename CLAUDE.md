# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

LTMC (Long-Term Memory and Context) is a production-ready MCP (Model Context Protocol) server that provides persistent memory storage, retrieval, and context management with dual transport support (HTTP and stdio). The project offers 22 MCP tools for memory management, code pattern learning, chat history, and task management.

## Architecture Overview

### Core Architecture Pattern
- **Single Source of Truth**: All 22 tools defined in `ltms/mcp_server.py`
- **Dual Transport**: HTTP (`ltms/mcp_server_http.py`) and stdio (`ltmc_mcp_server.py`) with identical functionality
- **Database Layer**: SQLite with vector ID sequences and specialized tables
- **Vector Search**: FAISS-based similarity search with SentenceTransformers embeddings
- **Service Layer**: Modular services in `ltms/services/` for different functionality areas

### Key Components
- **MCP Server**: `ltms/mcp_server.py` - FastMCP-based server with all 22 tools
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

# List all 22 tools
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

### Recommended MCP Usage Pattern
Every development task should follow this pattern:

#### 1. Start with Sequential Thinking
Break down complex tasks before implementation using the sequential-thinking MCP server.

#### 2. Use Context7 for Best Practices
Get relevant best practices and documentation before coding.

#### 3. Use LTMC for Memory Operations
Store all important progress and learnings via LTMC server:

```bash
# Store important information (via Bash tool - auto-executes)
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "store_memory", 
  "arguments": {
    "content": "Your important information here",
    "file_name": "descriptive_filename.md"
  }
}, "id": 1}')

# Log successful code patterns for learning (via Bash tool - auto-executes)
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_code_attempt", 
  "arguments": {
    "input_prompt": "What you were trying to implement",
    "generated_code": "The working code solution",
    "result": "pass"
  }
}, "id": 1}')
```

### Chat Continuity
**BEFORE EVERY CHAT COMPACTION** - Store complete chat history:
```bash
# MANDATORY: Store complete chat history before compaction (via Bash tool - auto-executes)
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_chat", 
  "arguments": {
    "content": "[FULL CHAT CONVERSATION CONTENT]",
    "conversation_id": "session_$(date +%Y%m%d_%H%M%S)",
    "role": "system"
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

## Tool Categories (22 Total)

### Memory & Context Tools (6)
- `store_memory`, `retrieve_memory`, `ask_with_context`, `route_query`, `build_context`, `retrieve_by_type`

### Chat & Communication Tools (5) 
- `log_chat`, `store_context_links_tool`, `get_context_links_for_message_tool`, `get_messages_for_chunk_tool`, `get_context_usage_statistics_tool`

### Code Pattern Memory Tools (3)
- `log_code_attempt`, `get_code_patterns`, `analyze_code_patterns`

### Task Management Tools (4)
- `add_todo`, `list_todos`, `complete_todo`, `search_todos`

### Graph & Relationship Tools (4)
- `link_resources`, `query_graph`, `auto_link_documents`, `get_document_relationships_tool`

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

### Pre-Commit Checklist
Before committing any code changes:
- [ ] Sequential thinking used for complex tasks (if applicable)
- [ ] Context7 queried for best practices (if applicable)  
- [ ] Tests written first (TDD approach)
- [ ] All tests passing with `pytest tests/`
- [ ] Type checking clean with `mypy ltms/ tests/`
- [ ] Code formatted with `black ltms/ tests/`
- [ ] Imports sorted with `isort ltms/ tests/`
- [ ] No linting errors with `flake8 ltms/ tests/`
- [ ] Security scan clean with `bandit -r ltms/`
- [ ] Dependencies secure with `safety check`
- [ ] Integration tests validated
- [ ] Knowledge saved to LTMC (auto-execute curl commands)
- [ ] **CRITICAL**: Store chat history if approaching compaction

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