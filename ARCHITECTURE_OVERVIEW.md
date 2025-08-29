# LTMC Architecture Overview

## System Architecture

LTMC (Long-Term Memory and Context) implements a sophisticated multi-database architecture designed for high-performance memory operations, semantic search, and intelligent context management. This document describes the current working implementation as verified in August 2025.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client Layer                         │
│              (Claude Code, MCP Inspector, etc.)                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │ MCP Protocol (stdio transport)
┌─────────────────────────▼───────────────────────────────────────┐
│                   LTMC MCP Server                               │
│                 (ltms/mcp_server.py)                           │
├─────────────────────────────────────────────────────────────────┤
│              11 Consolidated Tool Actions                       │
│   memory │ chat │ todo │ graph │ cache │ pattern │ blueprint   │
│   documentation │ sync │ config │ unix                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Unified API Layer
┌─────────────────────────▼───────────────────────────────────────┐
│                  Database Abstraction Layer                     │
│              (Atomic Synchronization Engine)                    │
└─┬─────────────┬─────────────┬─────────────┬─────────────────────┘
  │             │             │             │
┌─▼──┐     ┌───▼───┐     ┌───▼───┐     ┌───▼────┐
│SQLite│     │ FAISS │     │ Neo4j │     │ Redis  │
│Primary│     │Vector │     │ Graph │     │ Cache  │
│Store  │     │Search │     │ Rels  │     │ Layer  │
└──────┘     └───────┘     └───────┘     └────────┘
```

## Core Components

### 1. MCP Protocol Layer

**Transport**: stdio-only (NO HTTP endpoints)
- JSON-RPC over standard input/output
- Direct process communication for minimal latency
- Compatible with all MCP clients (Claude Code, MCP Inspector, etc.)

**Configuration**:
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

### 2. Tool Action Layer (11 Consolidated Tools)

**Design Pattern**: `tool_action(action: str, **params) -> Dict[str, Any]`

Each tool provides multiple related actions through a single interface:

```python
# Example: memory_action supports multiple operations
memory_action("store", file_name="doc.md", content="...")
memory_action("retrieve", query="search terms", top_k=5)
memory_action("build_context", documents=[...], max_tokens=4000)
```

**Tool Categories**:
- **Data Management**: memory_action, chat_action, todo_action
- **Relationships**: graph_action, blueprint_action
- **Analysis**: pattern_action, documentation_action, sync_action
- **System**: cache_action, config_action, unix_action

### 3. Unified Database Abstraction

**Atomic Synchronization Engine**: Ensures consistency across all databases

```python
class AtomicTransaction:
    async def execute_operation(self, operation_type, **params):
        # Phase 1: SQLite (Primary)
        sqlite_result = await self.sqlite_operation(operation_type, **params)
        
        # Phase 2: Specialized Databases
        if operation_type == "memory_store":
            faiss_result = await self.faiss_store_vector(sqlite_result.vector_id)
            neo4j_result = await self.neo4j_create_node(sqlite_result.resource_id)
            redis_result = await self.redis_cache_invalidate(operation_type)
        
        # Phase 3: Consistency Verification
        await self.verify_consistency(sqlite_result, faiss_result, neo4j_result)
        
        return unified_result
```

### 4. Database System Architecture

#### SQLite - Primary Transactional Store
**Location**: `/home/feanor/Projects/Data/ltmc.db`

**Role**: ACID-compliant primary storage
- All structured data (resources, chunks, chats, todos, patterns)
- Foreign key relationships and constraints
- Transaction coordination for multi-database operations

**Key Tables**:
```sql
Resources (id, file_name, type, created_at)
ResourceChunks (id, resource_id, chunk_text, vector_id)
ChatHistory (id, conversation_id, role, content, timestamp, source_tool)
ContextLinks (id, message_id, chunk_id)
todos (id, title, description, priority, status, created_at)
CodePatterns (id, function_name, input_prompt, generated_code, result)
```

#### FAISS - Vector Search Engine
**Location**: `/home/feanor/Projects/Data/faiss_index`

**Current Status**: 1,105 vectors loaded
**Role**: Semantic similarity search
- OpenAI embeddings (1536 dimensions)
- Flat index for exact similarity matching
- <50ms query response time

**Integration**:
```python
# Coordinated storage
sqlite_chunk_id = store_chunk_in_sqlite(text, unique_vector_id)
embedding = generate_openai_embedding(text)
faiss_index.add_vector(unique_vector_id, embedding)
```

#### Neo4j - Graph Relationships
**Connection**: `bolt://localhost:7687` (neo4j/kwe_password)

**Role**: Complex relationship modeling
- Document-to-document relationships
- Project dependencies and blueprints
- Concept and entity linking

**Graph Model**:
```cypher
// Nodes: Document, Code, Project, Concept
// Relationships: REFERENCES, IMPLEMENTS, DEPENDS_ON, RELATED_TO
CREATE (d:Document {id: "doc_123", title: "Architecture"})
CREATE (c:Code {id: "code_456", file: "main.py"})
CREATE (d)-[:IMPLEMENTS {strength: 0.8}]->(c)
```

#### Redis - High-Speed Cache
**Connection**: `localhost:6382` (password: ltmc_password_2025)

**Role**: Performance optimization
- Query result caching (5min TTL)
- Session data storage
- Frequently accessed data

**Cache Strategy**:
```python
# Multi-level caching
cache_key = f"query:{hash(query)}:{top_k}"
result = redis.get(cache_key)  # 10ms if hit
if not result:
    result = execute_database_query()  # 100-200ms
    redis.setex(cache_key, 300, json.dumps(result))
return result
```

## Data Flow Patterns

### Memory Storage Flow
```
1. Client Request → MCP Protocol → memory_action("store", ...)
2. Validate Input → Generate Unique IDs
3. SQLite Transaction:
   - Insert Resource record
   - Chunk text content
   - Insert ResourceChunk records with vector_ids
4. FAISS Operations:
   - Generate embeddings for chunks
   - Store vectors with matching vector_ids
5. Neo4j Operations:
   - Create document node
   - Auto-link related documents
6. Redis Operations:
   - Invalidate related cache entries
   - Pre-warm common query patterns
7. Return Success Response
```

### Query Execution Flow
```
1. Client Query → MCP Protocol → memory_action("retrieve", ...)
2. Cache Check (Redis) → Return if hit (10ms)
3. Query Processing:
   - Generate query embedding
   - FAISS similarity search → vector_ids
   - SQLite lookup → chunk data using vector_ids
   - Neo4j enhancement → relationship data
4. Result Ranking and Aggregation
5. Cache Store (Redis) → 5min TTL
6. Return Ranked Results
```

### Natural Language Query Flow
```
1. Client NL Query → chat_action("route_query", ...)
2. Query Classification:
   - Temporal analysis (yesterday, recent, etc.)
   - Content type detection (chat, memory, todo, etc.)
   - Intent recognition (search, create, update, etc.)
3. Route to Appropriate Databases:
   - Memory queries → SQLite + FAISS
   - Chat queries → SQLite ChatHistory
   - Task queries → SQLite todos
   - Relationship queries → Neo4j
4. Multi-database Result Aggregation
5. Semantic Ranking and Filtering
6. Return Unified Results
```

## Performance Architecture

### Response Time Targets
- **MCP Tool List**: <500ms
- **MCP Tool Call**: <2s for complex operations
- **Memory Storage**: <200ms per document
- **Semantic Search**: <100ms for 5 results
- **Cache Operations**: <10ms
- **Natural Language Queries**: <500ms end-to-end

### Optimization Strategies

**Connection Pooling**:
```python
class DatabaseManager:
    def __init__(self):
        self.sqlite_pool = SQLiteConnectionPool(min_size=2, max_size=10)
        self.redis_pool = RedisConnectionPool(min_size=5, max_size=20)
        self.neo4j_driver = Neo4jDriver(max_connection_lifetime=3600)
```

**Intelligent Caching**:
```python
# Cache key strategies
memory_queries: f"mem:{hash(query)}:{top_k}:{filters}"
chat_queries: f"chat:{conversation_id}:{tool}:{limit}"
todo_queries: f"todo:{status}:{priority}:{limit}"
graph_queries: f"graph:{entity}:{relation_type}"
```

**Batch Operations**:
```python
# FAISS batch processing
vectors_batch = []
for chunk in chunks:
    vectors_batch.append((chunk.vector_id, generate_embedding(chunk.text)))
faiss_index.add_batch(vectors_batch)  # Single operation vs multiple
```

## Scalability Design

### Horizontal Scaling Considerations

**SQLite Scaling**:
- WAL mode for concurrent reads
- Connection pooling for write optimization
- Future: SQLite replication or migration to PostgreSQL

**FAISS Scaling**:
- Index partitioning for >1M vectors
- Distributed FAISS clusters
- IVF indexes for approximate search at scale

**Neo4j Scaling**:
- Cluster deployment for high availability
- Read replicas for query distribution
- Graph partitioning strategies

**Redis Scaling**:
- Redis Cluster for large datasets
- Read replicas for query optimization
- Memory optimization with compression

### Vertical Scaling Optimizations

**Memory Management**:
```python
# Lazy loading patterns
class LazyFAISSIndex:
    def __init__(self):
        self._index = None
    
    @property
    def index(self):
        if self._index is None:
            self._index = faiss.read_index(self.index_path)
        return self._index
```

**CPU Optimization**:
- Async/await patterns for I/O operations
- Threading for CPU-intensive operations
- Process pools for parallel embeddings

## Security Architecture

### Data Protection
- Configuration file with credentials (not hardcoded)
- Database connections with authentication
- Input validation and sanitization
- Error handling without information leakage

### Access Control
```python
def validate_operation(tool_name: str, action: str, params: Dict[str, Any]):
    # Input validation
    if not isinstance(params, dict):
        raise ValidationError("Invalid parameters")
    
    # Action authorization
    allowed_actions = TOOL_ACTION_MAPPING.get(tool_name, [])
    if action not in allowed_actions:
        raise AuthorizationError(f"Action {action} not allowed for {tool_name}")
    
    return True
```

### Data Integrity
- Foreign key constraints in SQLite
- Vector ID consistency between SQLite and FAISS
- Transaction rollback on multi-database failures
- Regular consistency verification

## Monitoring and Observability

### Performance Metrics
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "database_health": {}
        }
```

### Health Checks
```python
def comprehensive_health_check():
    return {
        "sqlite": test_sqlite_connection(),
        "faiss": verify_faiss_index_health(),
        "neo4j": test_neo4j_connectivity(),
        "redis": test_redis_connectivity(),
        "overall": all_systems_healthy()
    }
```

### Error Handling
```python
def handle_database_error(operation: str, error: Exception):
    # Log error with context
    logger.error(f"Database error in {operation}: {error}")
    
    # Attempt recovery
    if isinstance(error, ConnectionError):
        attempt_reconnection()
    
    # Return user-friendly error
    return {"success": False, "error": "Database temporarily unavailable"}
```

## Configuration Management

### Environment Configuration
```json
{
    "database": {
        "db_path": "/home/feanor/Projects/Data/ltmc.db",
        "faiss_index_path": "/home/feanor/Projects/Data/faiss_index"
    },
    "redis": {
        "host": "localhost",
        "port": 6382,
        "password": "ltmc_password_2025",
        "db": 0
    },
    "neo4j": {
        "uri": "bolt://localhost:7687",
        "user": "neo4j",
        "password": "kwe_password",
        "database": "neo4j"
    },
    "performance": {
        "max_chunk_size": 1000,
        "overlap_size": 200,
        "cache_ttl": 300,
        "max_connections": 10
    }
}
```

### Runtime Configuration
```python
def load_configuration():
    config_path = "/home/feanor/Projects/ltmc/ltmc_config.json"
    with open(config_path) as f:
        config = json.load(f)
    
    # Validate configuration
    validate_config_schema(config)
    
    # Apply environment overrides
    config = apply_env_overrides(config)
    
    return config
```

## Testing Architecture

### Test Categories
1. **Unit Tests**: Individual tool actions and database operations
2. **Integration Tests**: Multi-database synchronization
3. **Performance Tests**: Response time and throughput validation
4. **End-to-End Tests**: Complete MCP client workflows

### Test Isolation
```python
class TestDatabaseManager:
    def setup_test_environment(self):
        self.test_sqlite_db = ":memory:"
        self.test_faiss_index = create_temporary_index()
        self.test_neo4j_session = create_test_session()
        self.test_redis_db = 15  # Dedicated test database
```

## Future Architecture Considerations

### Planned Enhancements
1. **Query Optimization**: Advanced FAISS index types (IVF, HNSW)
2. **Distributed Architecture**: Microservices decomposition
3. **Real-time Sync**: WebSocket support for live updates
4. **ML Integration**: Custom embedding models and ranking algorithms

### Migration Strategies
1. **Database Evolution**: Schema versioning and migration scripts
2. **Index Rebuilding**: Zero-downtime FAISS index updates
3. **Configuration Updates**: Backward-compatible config changes
4. **Client Compatibility**: MCP protocol version support

This architecture provides LTMC with enterprise-grade capabilities while maintaining simplicity through the unified MCP tool interface. The multi-database design optimizes for different access patterns while ensuring data consistency and high performance.