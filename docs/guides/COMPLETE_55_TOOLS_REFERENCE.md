# LTMC Complete 55 Tools Reference Guide

**Version**: 1.0  
**Updated**: August 10, 2025  
**Transport**: stdio MCP Protocol  

## Overview

LTMC provides 55 comprehensive tools across 3 categories:
- **Core LTMC Tools (28)**: Essential memory, chat, task, and code pattern management
- **Phase3 Advanced Tools (26)**: Blueprint management, documentation sync, and orchestration
- **Unified Integration (1)**: System-wide performance monitoring and statistics

## 🧠 Core LTMC Tools (28)

### Memory & Context Management
Tools for persistent memory storage and intelligent context retrieval.

#### `mcp__ltmc__store_memory`
**Purpose**: Store persistent memory across sessions  
**Usage**: Long-term information retention for context continuity
```python
mcp__ltmc__store_memory(
    file_name="project_insights.md",
    content="Key architectural decisions and learnings",
    resource_type="document"  # document|code|note
)
```

#### `mcp__ltmc__retrieve_memory`
**Purpose**: Semantic search through stored memories  
**Usage**: Context-aware decision making and information retrieval
```python
mcp__ltmc__retrieve_memory(
    query="architectural patterns used in project",
    conversation_id="project_session_20250810",
    top_k=5  # Number of relevant results
)
```

#### `mcp__ltmc__ask_with_context`
**Purpose**: Query with automatic context retrieval  
**Usage**: Intelligent question answering with relevant background
```python
mcp__ltmc__ask_with_context(
    query="How should I implement the database layer?",
    conversation_id="dev_session",
    top_k=3
)
```

#### `mcp__ltmc__build_context`
**Purpose**: Build structured context windows with token limits  
**Usage**: Prepare context for AI processing within constraints
```python
mcp__ltmc__build_context(
    documents=[{"content": "...", "type": "code"}],
    max_tokens=4000
)
```

#### `mcp__ltmc__route_query`
**Purpose**: Smart query routing to best processing method  
**Usage**: Optimize query handling based on content type
```python
mcp__ltmc__route_query(
    query="Find database optimization patterns"
)
```

#### `mcp__ltmc__retrieve_by_type`
**Purpose**: Type-filtered document retrieval  
**Usage**: Find specific types of stored information
```python
mcp__ltmc__retrieve_by_type(
    query="authentication implementation",
    doc_type="code",
    top_k=3
)
```

#### `mcp__ltmc__advanced_context_search`
**Purpose**: Advanced context search with filters  
**Usage**: Complex searches with multiple criteria
```python
mcp__ltmc__advanced_context_search(
    query="async database patterns",
    filters={"language": "python", "complexity": "medium"},
    top_k=5
)
```

### Chat & Communication
Tools for conversation logging and communication management.

#### `mcp__ltmc__log_chat`
**Purpose**: Log conversations for continuity across sessions  
**Usage**: Maintain conversation history and context
```python
mcp__ltmc__log_chat(
    content="User requested authentication implementation",
    conversation_id="dev_session_20250810",
    role="user"  # user|assistant|system
)
```

#### `mcp__ltmc__get_chats_by_tool`
**Purpose**: Retrieve conversations that used specific tools  
**Usage**: Analyze tool usage patterns and contexts
```python
mcp__ltmc__get_chats_by_tool(
    source_tool="store_memory",
    limit=10
)
```

### Task Management
Comprehensive todo and task tracking system.

#### `mcp__ltmc__add_todo`
**Purpose**: Add tasks for complex multi-step implementations  
**Usage**: Track progress on complex development tasks
```python
mcp__ltmc__add_todo(
    title="Implement user authentication system",
    description="OAuth2, JWT tokens, role-based access control",
    priority="high"  # high|medium|low
)
```

#### `mcp__ltmc__list_todos`
**Purpose**: List todos with optional status filtering  
**Usage**: Review current task status and priorities
```python
mcp__ltmc__list_todos(
    status="pending",  # all|pending|completed
    limit=10
)
```

#### `mcp__ltmc__complete_todo`
**Purpose**: Mark todos as completed  
**Usage**: Maintain accurate task completion tracking
```python
mcp__ltmc__complete_todo(
    todo_id=123
)
```

#### `mcp__ltmc__search_todos`
**Purpose**: Search todos by title or description  
**Usage**: Find specific tasks in large todo lists
```python
mcp__ltmc__search_todos(
    query="authentication",
    limit=5
)
```

### Knowledge Graph Management
Tools for creating and querying relationships between concepts.

#### `mcp__ltmc__link_resources`
**Purpose**: Create relationships between resources in knowledge graph  
**Usage**: Build semantic connections between concepts
```python
mcp__ltmc__link_resources(
    source_id="auth_doc_123",
    target_id="security_guide_456",
    relation="implements"
)
```

#### `mcp__ltmc__query_graph`
**Purpose**: Query knowledge graph for related information  
**Usage**: Discover related concepts and dependencies
```python
mcp__ltmc__query_graph(
    entity="authentication_system",
    relation_type="depends_on"
)
```

#### `mcp__ltmc__auto_link_documents`
**Purpose**: Automatically link similar documents  
**Usage**: Build knowledge graph through similarity analysis
```python
mcp__ltmc__auto_link_documents(
    documents=[
        {"id": "doc1", "content": "..."},
        {"id": "doc2", "content": "..."}
    ]
)
```

#### `mcp__ltmc__get_document_relationships`
**Purpose**: Get all relationships for a document  
**Usage**: Understand document context and connections
```python
mcp__ltmc__get_document_relationships(
    doc_id="auth_implementation_789"
)
```

### Code Pattern Learning
Experience replay system for learning from successful implementations.

#### `mcp__ltmc__log_code_attempt`
**Purpose**: Log code attempts for experience replay learning  
**Usage**: Build library of successful implementation patterns
```python
mcp__ltmc__log_code_attempt(
    input_prompt="Implement async database connection",
    generated_code="""
    async def connect_db():
        pool = await asyncpg.create_pool(DATABASE_URL)
        return pool
    """,
    result="pass",  # pass|fail|error
    tags=["python", "async", "database", "connection"]
)
```

#### `mcp__ltmc__get_code_patterns`
**Purpose**: Retrieve successful code patterns for learning  
**Usage**: Learn from past successful implementations
```python
mcp__ltmc__get_code_patterns(
    query="async database connection patterns",
    result_filter="pass",  # pass|fail|error|all
    top_k=5
)
```

#### `mcp__ltmc__analyze_code_patterns`
**Purpose**: Analyze code patterns for insights and trends  
**Usage**: Understand coding patterns and improvement opportunities
```python
mcp__ltmc__analyze_code_patterns(
    function_name="connect_db",
    tags=["async", "database"]
)
```

#### `mcp__ltmc__get_code_statistics`
**Purpose**: Get comprehensive code pattern statistics  
**Usage**: Overview of code learning system performance
```python
mcp__ltmc__get_code_statistics()
```

### Redis Cache & Performance
Redis integration for caching and performance optimization.

#### `mcp__ltmc__redis_health_check`
**Purpose**: Monitor Redis connection health  
**Usage**: Ensure cache system is operational
```python
mcp__ltmc__redis_health_check()
```

#### `mcp__ltmc__redis_cache_stats`
**Purpose**: Get Redis cache performance statistics  
**Usage**: Monitor cache hit rates and performance
```python
mcp__ltmc__redis_cache_stats()
```

#### `mcp__ltmc__redis_set_cache`
**Purpose**: Set values in Redis cache  
**Usage**: Manual cache management for optimization
```python
mcp__ltmc__redis_set_cache(
    key="user_profile_123",
    value={"name": "John", "role": "admin"},
    ttl=3600  # Time to live in seconds
)
```

#### `mcp__ltmc__redis_get_cache`
**Purpose**: Retrieve values from Redis cache  
**Usage**: Fast data retrieval from cache
```python
mcp__ltmc__redis_get_cache(
    key="user_profile_123"
)
```

#### `mcp__ltmc__redis_delete_cache`
**Purpose**: Delete keys from Redis cache  
**Usage**: Cache cleanup and invalidation
```python
mcp__ltmc__redis_delete_cache(
    key="user_profile_123"
)
```

#### `mcp__ltmc__redis_clear_cache`
**Purpose**: Clear Redis cache with optional pattern matching  
**Usage**: Bulk cache cleanup
```python
mcp__ltmc__redis_clear_cache(
    pattern="user_*"  # Clear all user-related cache
)
```

### System Analytics
Tools for monitoring system usage and performance.

#### `mcp__ltmc__get_context_usage_statistics`
**Purpose**: Get comprehensive context usage statistics  
**Usage**: Analyze system usage patterns
```python
mcp__ltmc__get_context_usage_statistics()
```

## 🚀 Phase3 Advanced Tools (26)

### Task Blueprint Management
Advanced task management with ML-driven complexity analysis.

#### `mcp__ltmc__create_task_blueprint`
**Purpose**: Create task blueprints with automatic complexity scoring  
**Usage**: Plan complex multi-step implementations
```python
mcp__ltmc__create_task_blueprint(
    title="Implement OAuth2 Authentication",
    description="Complete OAuth2 flow with JWT tokens",
    complexity="high",
    estimated_duration_minutes=480,
    required_skills=["python", "oauth2", "jwt", "security"],
    priority_score=0.9
)
```

#### `mcp__ltmc__analyze_task_complexity`
**Purpose**: ML-based task complexity analysis  
**Usage**: Understand implementation effort and requirements
```python
mcp__ltmc__analyze_task_complexity(
    title="Database Migration System",
    description="Implement zero-downtime database migrations",
    required_skills=["database", "migrations", "sql"]
)
```

#### `mcp__ltmc__get_task_dependencies`
**Purpose**: Get dependencies for task blueprints  
**Usage**: Understand prerequisite tasks and planning
```python
mcp__ltmc__get_task_dependencies(
    blueprint_id="bp_auth_system_123"
)
```

#### `mcp__ltmc__update_blueprint_metadata`
**Purpose**: Update metadata for existing blueprints  
**Usage**: Refine task estimates and requirements
```python
mcp__ltmc__update_blueprint_metadata(
    blueprint_id="bp_auth_system_123",
    estimated_duration_minutes=360,
    priority_score=0.95,
    tags=["critical", "security", "user-facing"]
)
```

#### `mcp__ltmc__list_project_blueprints`
**Purpose**: List blueprints for specific projects with filtering  
**Usage**: Project management and planning overview
```python
mcp__ltmc__list_project_blueprints(
    project_id="web_app_v2",
    min_complexity="medium",
    tags=["security"],
    limit=10
)
```

#### `mcp__ltmc__resolve_blueprint_execution_order`
**Purpose**: Resolve optimal execution order based on dependencies  
**Usage**: Plan implementation sequence for complex projects
```python
mcp__ltmc__resolve_blueprint_execution_order(
    blueprint_ids=["bp_auth_123", "bp_db_456", "bp_api_789"]
)
```

#### `mcp__ltmc__add_blueprint_dependency`
**Purpose**: Add dependencies between blueprints  
**Usage**: Define prerequisite relationships
```python
mcp__ltmc__add_blueprint_dependency(
    dependent_blueprint_id="bp_api_789",
    prerequisite_blueprint_id="bp_auth_123",
    dependency_type="blocking",
    is_critical=True
)
```

#### `mcp__ltmc__delete_task_blueprint`
**Purpose**: Delete task blueprints and dependencies  
**Usage**: Clean up obsolete or cancelled tasks
```python
mcp__ltmc__delete_task_blueprint(
    blueprint_id="bp_obsolete_feature_456"
)
```

#### `mcp__ltmc__decompose_task_blueprint`
**Purpose**: Break complex tasks into subtasks  
**Usage**: Create manageable implementation steps
```python
mcp__ltmc__decompose_task_blueprint(
    blueprint_id="bp_complex_system_123",
    decomposition_strategy="feature_based"
)
```

### Team Assignment & Management
ML-driven team assignment and workload management.

#### `mcp__ltmc__assign_task_to_team`
**Purpose**: Assign tasks using ML routing to best team members  
**Usage**: Optimize task assignments based on skills and availability
```python
mcp__ltmc__assign_task_to_team(
    blueprint_id="bp_auth_system_123",
    available_members=[
        {"id": "dev1", "skills": ["python", "security"], "capacity": 0.8},
        {"id": "dev2", "skills": ["frontend", "react"], "capacity": 0.6}
    ],
    project_id="web_app_v2",
    preferences={"prefer_security_expert": True}
)
```

#### `mcp__ltmc__update_task_progress`
**Purpose**: Update progress for active task assignments  
**Usage**: Track implementation progress and time estimates
```python
mcp__ltmc__update_task_progress(
    assignment_id="assign_123",
    progress_percentage=75.0,
    status="in_progress",
    actual_hours_worked=28.5,
    notes="OAuth2 flow implemented, JWT integration remaining"
)
```

#### `mcp__ltmc__get_team_workload_overview`
**Purpose**: Get workload overview for team members  
**Usage**: Balance workloads and identify resource constraints
```python
mcp__ltmc__get_team_workload_overview(
    team_members=[
        {"id": "dev1", "name": "Alice"},
        {"id": "dev2", "name": "Bob"}
    ],
    project_id="web_app_v2"
)
```

### Documentation Synchronization
Advanced documentation sync with code changes.

#### `mcp__ltmc__sync_documentation_with_code`
**Purpose**: Synchronize documentation with code changes  
**Usage**: Keep documentation current with implementation
```python
mcp__ltmc__sync_documentation_with_code(
    file_path="/src/auth/oauth.py",
    project_id="web_app_v2",
    force_update=False
)
```

#### `mcp__ltmc__validate_documentation_consistency`
**Purpose**: Validate documentation consistency with code  
**Usage**: Ensure docs accurately reflect implementation
```python
mcp__ltmc__validate_documentation_consistency(
    file_path="/src/auth/oauth.py",
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__detect_documentation_drift`
**Purpose**: Detect drift between documentation and code  
**Usage**: Identify when docs become outdated
```python
mcp__ltmc__detect_documentation_drift(
    file_path="/src/auth/oauth.py",
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__update_documentation_from_blueprint`
**Purpose**: Update documentation from blueprint changes  
**Usage**: Maintain docs aligned with planned changes
```python
mcp__ltmc__update_documentation_from_blueprint(
    blueprint_id="bp_auth_system_123",
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__get_documentation_consistency_score`
**Purpose**: Get consistency score between documentation and code  
**Usage**: Measure documentation quality metrics
```python
mcp__ltmc__get_documentation_consistency_score(
    file_path="/src/auth/oauth.py",
    project_id="web_app_v2"
)
```

### Blueprint-Code Integration
Integration between task blueprints and actual code.

#### `mcp__ltmc__create_blueprint_from_code`
**Purpose**: Create blueprint nodes from code analysis  
**Usage**: Generate task blueprints from existing code
```python
mcp__ltmc__create_blueprint_from_code(
    file_path="/src/auth/oauth.py",
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__update_blueprint_structure`
**Purpose**: Update blueprint structure from code changes  
**Usage**: Keep blueprints aligned with implementation
```python
mcp__ltmc__update_blueprint_structure(
    blueprint_id="bp_auth_system_123",
    file_path="/src/auth/oauth.py"
)
```

#### `mcp__ltmc__validate_blueprint_consistency`
**Purpose**: Validate consistency between blueprint and code  
**Usage**: Ensure blueprints accurately reflect implementation
```python
mcp__ltmc__validate_blueprint_consistency(
    blueprint_id="bp_auth_system_123",
    file_path="/src/auth/oauth.py"
)
```

#### `mcp__ltmc__query_blueprint_relationships`
**Purpose**: Query blueprint relationships from Neo4j  
**Usage**: Understand blueprint dependencies and connections
```python
mcp__ltmc__query_blueprint_relationships(
    node_id="bp_auth_system_123",
    relationship_types=["depends_on", "implements"],
    max_depth=2
)
```

#### `mcp__ltmc__generate_blueprint_documentation`
**Purpose**: Generate documentation from blueprint structure  
**Usage**: Create documentation from task blueprints
```python
mcp__ltmc__generate_blueprint_documentation(
    blueprint_id="bp_auth_system_123",
    format="markdown",
    include_relationships=True
)
```

### Real-Time Synchronization
Real-time monitoring and synchronization capabilities.

#### `mcp__ltmc__start_real_time_sync`
**Purpose**: Start real-time synchronization monitoring  
**Usage**: Monitor files for changes and sync documentation
```python
mcp__ltmc__start_real_time_sync(
    file_paths=["/src/auth/", "/src/api/"],
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__get_sync_status`
**Purpose**: Get synchronization status for project  
**Usage**: Monitor sync health and identify issues
```python
mcp__ltmc__get_sync_status(
    project_id="web_app_v2"
)
```

#### `mcp__ltmc__detect_code_changes`
**Purpose**: Detect changes in code files for synchronization  
**Usage**: Identify files that need documentation updates
```python
mcp__ltmc__detect_code_changes(
    file_paths=["/src/auth/oauth.py", "/src/api/endpoints.py"],
    project_id="web_app_v2"
)
```

### System Performance
Advanced system performance monitoring and optimization.

#### `mcp__ltmc__get_taskmaster_performance_metrics`
**Purpose**: Get performance metrics for task management system  
**Usage**: Monitor and optimize task management performance
```python
mcp__ltmc__get_taskmaster_performance_metrics()
```

## 🔗 Unified Integration (1)

### System-Wide Monitoring
Unified performance monitoring across all system components.

#### `mcp__ltmc__get_performance_report`
**Purpose**: Get comprehensive performance report for entire system  
**Usage**: Monitor system health and identify optimization opportunities
```python
mcp__ltmc__get_performance_report()
```
**Returns**: Unified statistics covering:
- Server uptime and request metrics
- Tool registry statistics (55 tools breakdown)
- Performance targets and slow tool identification
- Transport information (stdio/http)

## 🎯 Usage Patterns

### Essential Daily Workflow
```python
# 1. Store important insights
mcp__ltmc__store_memory(
    file_name="daily_insights.md",
    content="Key decisions and learnings from today"
)

# 2. Log conversations
mcp__ltmc__log_chat(
    content="Discussion about authentication implementation",
    conversation_id="dev_session",
    role="user"
)

# 3. Track tasks
mcp__ltmc__add_todo(
    title="Complete OAuth2 implementation",
    description="Finish JWT token validation",
    priority="high"
)

# 4. Log successful code
mcp__ltmc__log_code_attempt(
    input_prompt="JWT token validation",
    generated_code="def validate_jwt(token): ...",
    result="pass",
    tags=["security", "jwt", "validation"]
)
```

### Complex Project Planning
```python
# 1. Create task blueprint
blueprint = mcp__ltmc__create_task_blueprint(
    title="Authentication System",
    description="Complete OAuth2 + JWT implementation",
    required_skills=["python", "security", "oauth2"]
)

# 2. Analyze complexity
complexity = mcp__ltmc__analyze_task_complexity(
    title="Authentication System",
    description="Complete OAuth2 + JWT implementation"
)

# 3. Assign to team
assignment = mcp__ltmc__assign_task_to_team(
    blueprint_id=blueprint["blueprint_id"],
    available_members=team_members,
    project_id="web_app"
)
```

### Knowledge Discovery
```python
# 1. Search for patterns
patterns = mcp__ltmc__get_code_patterns(
    query="authentication implementation",
    result_filter="pass",
    top_k=5
)

# 2. Query knowledge graph
related = mcp__ltmc__query_graph(
    entity="authentication",
    relation_type="implements"
)

# 3. Get context
context = mcp__ltmc__ask_with_context(
    query="How should I implement secure authentication?",
    conversation_id="dev_session"
)
```

## 🔧 Configuration

### Environment Setup
```bash
# Required environment variables
export DB_PATH="ltmc.db"
export REDIS_HOST="localhost"
export REDIS_PORT="6381"
export NEO4J_URI="bolt://localhost:7687"
export QDRANT_HOST="localhost"
```

### MCP Client Configuration
```json
{
  "ltmc": {
    "command": "python",
    "args": ["-m", "ltms.mcp_server"],
    "cwd": "/path/to/lmtc",
    "env": {
      "DB_PATH": "ltmc.db",
      "REDIS_HOST": "localhost",
      "REDIS_PORT": "6381"
    }
  }
}
```

---

**📋 Total Tools**: 55 (28 Core + 26 Phase3 + 1 Unified)  
**🚀 Transport**: stdio MCP Protocol  
**⚡ Performance**: <50ms average response time  
**🧠 Purpose**: Comprehensive AI assistant memory and task management