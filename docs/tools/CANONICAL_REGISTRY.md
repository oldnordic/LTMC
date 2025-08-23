# LTMC Canonical Tools Registry

**Generated**: August 22, 2025  
**Status**: ✅ All 24 canonical tools active  
**Format**: group:operation naming convention

## Registry Overview

The LTMC canonical tools registry implements a clean `group:operation` naming convention for all MCP tools, providing consistent interfaces and improved organization.

## Tool Groups Summary

| Group | Tools | Status | Description |
|-------|-------|---------|-------------|
| memory | 5 | ✅ Active | Core memory storage and retrieval |
| chat | 3 | ✅ Active | Conversation logging and analysis |
| todo | 4 | ✅ Active | Task management and tracking |
| blueprint | 5 | ✅ Active | Advanced project planning |
| pattern | 7 | ✅ Active | Code analysis and LangExtract |

## Complete Tool Reference

### Memory Group (5 tools)
Core memory management and context operations.

#### `memory:store`
**Description**: Store memory/doc/code/blueprint  
**Sample Call**: `memory:store(file_name="doc.md", content="...", resource_type="document")`  
**Parameters**:
- `file_name` (string, required): Name of the file/document to store
- `content` (string, required): Content to store  
- `resource_type` (string, optional): Type of resource (document, code, note, blueprint, etc.)

#### `memory:retrieve`
**Description**: Semantic search for memory  
**Sample Call**: `memory:retrieve(query="foo", conversation_id="session1")`  
**Parameters**:
- `query` (string, required): Search query to find relevant memories
- `conversation_id` (string, optional): Conversation ID to scope the search
- `top_k` (integer, optional): Number of results to return (default: 10)

#### `memory:build_context` 
**Description**: Build context window  
**Sample Call**: `memory:build_context(documents=[...], max_tokens=4000)`  
**Parameters**:
- `documents` (array, required): List of documents to build context from
- `max_tokens` (integer, optional): Maximum tokens for the context window (default: 4000)
- `topic` (string, optional): Optional topic focus for context building

#### `memory:list`
**Description**: List all resources by type  
**Sample Call**: `memory:list(resource_type="blueprint")`  
**Parameters**:
- `resource_type` (string, required): Type of resources to list
- `query` (string, optional): Optional query filter
- `top_k` (integer, optional): Number of results to return (default: 10)

#### `memory:ask_with_context`
**Description**: Query with context expansion  
**Sample Call**: `memory:ask_with_context(query="bar", conversation_id="session1")`  
**Parameters**:
- `query` (string, required): Question to ask with context
- `conversation_id` (string, optional): Conversation ID for context scoping
- `top_k` (integer, optional): Maximum number of context items to retrieve (default: 5)

### Chat Group (3 tools)
Conversation logging and communication management.

#### `chat:log`
**Description**: Log a chat/conversation  
**Sample Call**: `chat:log(content="...", conversation_id=1, role="user")`  
**Parameters**:
- `content` (string, required): The chat message content to log
- `conversation_id` (string, required): Unique identifier for the conversation
- `role` (string, optional): Role of the message sender (user, assistant, system)
- `agent_name` (string, optional): Name of the agent if applicable
- `metadata` (object, optional): Optional metadata dictionary
- `source_tool` (string, optional): Tool that generated this message

#### `chat:get_by_tool`
**Description**: Retrieve chats for a tool/topic  
**Sample Call**: `chat:get_by_tool(tool="memory")`  
**Parameters**:
- `tool` (string, required): Name of the source tool to search for in chat history
- `limit` (integer, optional): Maximum number of chat messages to return (default: 10)

#### `chat:get_tool_conversations`
**Description**: Get all conversations for a tool  
**Sample Call**: `chat:get_tool_conversations(tool="pattern")`  
**Parameters**:
- `tool` (string, required): Name of the source tool
- `limit` (integer, optional): Maximum number of conversations to return (default: 50)

### Todo Group (4 tools)
Task management and tracking system.

#### `todo:add`
**Description**: Add a new todo/task  
**Sample Call**: `todo:add(title="DoX", description="...", priority="high")`  
**Parameters**:
- `title` (string, required): Title of the todo item
- `description` (string, optional): Detailed description of the task
- `priority` (string, optional): Priority level (low, medium, high)

#### `todo:list`
**Description**: List/search todos  
**Sample Call**: `todo:list(status="pending")`  
**Parameters**:
- `status` (string, optional): Filter by status (all, pending, completed)
- `limit` (integer, optional): Maximum number of todos to return (default: 10)

#### `todo:complete`
**Description**: Mark todo as complete  
**Sample Call**: `todo:complete(todo_id=1)`  
**Parameters**:
- `todo_id` (integer, required): ID of the todo item to complete

#### `todo:search`
**Description**: Search todos by text  
**Sample Call**: `todo:search(query="API")`  
**Parameters**:
- `query` (string, required): Search query to find matching todos
- `limit` (integer, optional): Maximum number of todos to return (default: 10)

### Blueprint Group (5 tools)
Advanced task management with ML-driven complexity analysis.

#### `blueprint:create`
**Description**: Create a task blueprint  
**Sample Call**: `blueprint:create(title="x", description="y", project_id="p1")`  
**Parameters**:
- `title` (string, required): Blueprint title
- `description` (string, required): Detailed description
- `complexity` (string, optional): Explicit complexity level (TRIVIAL, SIMPLE, MODERATE, COMPLEX, CRITICAL)
- `estimated_duration_minutes` (integer, optional): Estimated duration in minutes (default: 60)
- `required_skills` (array, optional): List of required skills
- `priority_score` (number, optional): Priority score (0.0 to 1.0, default: 0.5)
- `project_id` (string, optional): Project identifier for isolation
- `tags` (array, optional): List of tags for categorization
- `resource_requirements` (object, optional): Resource requirements dictionary

#### `blueprint:analyze_complexity`
**Description**: Analyze blueprint/task complexity  
**Sample Call**: `blueprint:analyze_complexity(title="Task", description="...", required_skills=["python"])`  
**Parameters**:
- `title` (string, required): Task title
- `description` (string, required): Task description  
- `required_skills` (array, optional): List of required skills

#### `blueprint:decompose`
**Description**: Decompose blueprint into subtasks  
**Sample Call**: `blueprint:decompose(blueprint_id="bp1")`  
**Parameters**:
- `blueprint_id` (string, required): Blueprint identifier
- `decomposition_strategy` (string, optional): Strategy for decomposition (default: "feature_based")

#### `blueprint:link`
**Description**: Link blueprints by dependency  
**Sample Call**: `blueprint:link(source_id="bp1", target_id="bp2")`  
**Parameters**:
- `source_id` (string, required): Blueprint that must be completed first
- `target_id` (string, required): Blueprint that depends on prerequisite
- `dependency_type` (string, optional): Type of dependency (blocking, soft, resource)
- `is_critical` (boolean, optional): Whether this is a critical dependency

#### `blueprint:list`
**Description**: List blueprints for project  
**Sample Call**: `blueprint:list(project_id="p1")`  
**Parameters**:
- `project_id` (string, required): Project identifier
- `min_complexity` (string, optional): Minimum complexity level
- `max_complexity` (string, optional): Maximum complexity level
- `tags` (array, optional): Filter by tags
- `limit` (integer, optional): Maximum number of results
- `offset` (integer, optional): Number of results to skip

### Pattern Group (7 tools)
Code pattern analysis and LangExtract integration.

#### `pattern:log_attempt`
**Description**: Log code attempt/experience  
**Sample Call**: `pattern:log_attempt(input="...", generated_code="...", result="pass")`  
**Parameters**:
- `input_prompt` (string, required): The prompt or description of what code was being generated
- `generated_code` (string, required): The code that was generated
- `result` (string, required): Result of the attempt (pass, fail, partial)
- `error_message` (string, optional): Error message if the attempt failed
- `execution_time_ms` (integer, optional): Execution time in milliseconds
- `file_name` (string, optional): Name of the file where code was generated
- `function_name` (string, optional): Name of the function being implemented
- `module_name` (string, optional): Name of the module or package
- `tags` (array, optional): List of tags for categorization

#### `pattern:get_patterns`
**Description**: Retrieve code patterns/solutions  
**Sample Call**: `pattern:get_patterns(query="jwt", result_filter="pass")`  
**Parameters**:
- `query` (string, required): Query describing the type of code pattern needed
- `result_filter` (string, optional): Filter by result type (pass, fail, partial)
- `top_k` (integer, optional): Maximum number of patterns to return (default: 5)
- `file_name` (string, optional): Filter by file name
- `function_name` (string, optional): Filter by function name
- `module_name` (string, optional): Filter by module name

#### `pattern:analyze`
**Description**: Analyze code pattern usage  
**Sample Call**: `pattern:analyze(patterns=["auth"], time_range_days=30)`  
**Parameters**:
- `patterns` (array, optional): Specific patterns to analyze
- `time_range_days` (integer, optional): Number of days to analyze (default: 30)
- `file_name` (string, optional): Filter analysis by file name
- `function_name` (string, optional): Filter analysis by function name
- `module_name` (string, optional): Filter analysis by module name

#### `pattern:extract_functions`
**Description**: Extract function definitions (LangExtract)  
**Sample Call**: `pattern:extract_functions(source_code="def foo(): pass", language="python")`  
**Parameters**:
- `source_code` (string, required): Source code content to analyze
- `file_path` (string, optional): Optional file path for context and language detection
- `language` (string, optional): Programming language (auto, python, javascript)
- `extract_docstrings` (boolean, optional): Whether to extract and parse docstrings (default: true)
- `include_private` (boolean, optional): Whether to include private/internal functions (default: false)
- `complexity_analysis` (boolean, optional): Whether to calculate complexity metrics (default: true)

#### `pattern:extract_classes`
**Description**: Extract class definitions (LangExtract)  
**Sample Call**: `pattern:extract_classes(source_code="class Foo: pass", language="python")`  
**Parameters**:
- `source_code` (string, required): Source code content to analyze
- `file_path` (string, optional): Optional file path for context and language detection
- `language` (string, optional): Programming language (auto, python, javascript)
- `analyze_inheritance` (boolean, optional): Whether to analyze inheritance hierarchies (default: true)
- `extract_relationships` (boolean, optional): Whether to analyze class relationships (default: true)
- `include_private` (boolean, optional): Whether to include private/internal classes (default: false)

#### `pattern:summarize`
**Description**: Summarize code using AST/LLM (LangExtract)  
**Sample Call**: `pattern:summarize(source_code="...", summary_length="detailed")`  
**Parameters**:
- `source_code` (string, required): Source code content to summarize
- `file_path` (string, optional): Optional file path for context and language detection
- `language` (string, optional): Programming language (auto, python, javascript)
- `summary_length` (string, optional): Length of natural language summary (brief, medium, detailed)
- `include_complexity` (boolean, optional): Whether to include complexity analysis (default: true)
- `include_todos` (boolean, optional): Whether to include TODO/FIXME analysis (default: true)

#### `pattern:extract_comments`
**Description**: Extract comments/docstrings (LangExtract)  
**Sample Call**: `pattern:extract_comments(source_code="# comment\ndef foo(): pass")`  
**Parameters**:
- `source_code` (string, required): Source code content to analyze
- `file_path` (string, optional): Optional file path for context and language detection
- `language` (string, optional): Programming language (auto, python, javascript)
- `include_docstrings` (boolean, optional): Whether to extract and parse docstrings (default: true)
- `include_todos` (boolean, optional): Whether to extract TODO/FIXME/NOTE comments (default: true)
- `extract_metadata` (boolean, optional): Whether to include processing metadata (default: true)

## Usage Patterns

### Essential Workflow
```python
# 1. Store insights
memory:store(file_name="insights.md", content="Key findings")

# 2. Log conversations  
chat:log(content="User asked about X", conversation_id="session1")

# 3. Track tasks
todo:add(title="Implement feature", priority="high")

# 4. Log successful patterns
pattern:log_attempt(input="JWT validation", generated_code="...", result="pass")
```

### Advanced Project Planning
```python
# 1. Create blueprint
blueprint:create(title="Auth System", description="OAuth2 + JWT", project_id="app")

# 2. Analyze complexity
blueprint:analyze_complexity(title="Auth System", description="OAuth2 + JWT")

# 3. Extract code patterns
pattern:extract_functions(source_code=code, language="python")
```

## Registry Health
- ✅ All 24 tools active and validated
- ✅ Real database connections (no mocks)  
- ✅ Full MCP protocol compliance
- ✅ Development branch compatible

## Next Steps
Ready for Unix tool integration and production deployment.