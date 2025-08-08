# LTMC System Architecture

## Overview

The LTMC (Long-Term Memory and Context) Multi-Agent Coordination Platform is a sophisticated, production-ready Model Context Protocol (MCP) server with advanced Redis-powered orchestration. The system provides persistent memory storage, semantic search, multi-agent coordination, and machine learning-assisted code generation through a modern, scalable architecture.

## Architectural Principles

### Core Design Philosophy
- **Modular Architecture**: Maximum 300 lines per file for maintainability
- **Async-First Design**: All I/O operations use async/await patterns
- **Type-Safe Development**: Comprehensive type hints throughout
- **Multi-Transport Support**: HTTP and stdio protocols for diverse integration
- **Redis-Powered Orchestration**: Advanced coordination and caching layer
- **4-Tier Memory System**: Specialized storage for different data types

### Scalability Principles
- **Horizontal Scaling**: Stateless design enables multi-instance deployment
- **Caching Optimization**: Redis-based caching for performance
- **Resource Efficiency**: Intelligent memory management and pooling
- **Load Distribution**: Support for load balancers and proxy configurations

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    LTMC Multi-Agent Platform                    │
├─────────────────────────────────────────────────────────────────┤
│                      Transport Layer                           │
├──────────────────────────┬──────────────────────────────────────┤
│     HTTP Transport       │        MCP (stdio) Transport        │
│   FastAPI + Uvicorn      │      JSON-RPC over stdio            │
│   localhost:5050         │      MCP Client Integration         │
├──────────────────────────┴──────────────────────────────────────┤
│                     MCP Tool Layer (25 Tools)                  │
├───────────────────┬───────────────────┬────────────────────────┤
│   Memory Tools    │   Context Tools   │   Code Pattern Tools   │
│   • store_memory  │   • build_context │   • log_code_attempt   │
│   • retrieve_mem  │   • query_graph   │   • get_code_patterns  │
├───────────────────┼───────────────────┼────────────────────────┤
│   Chat Tools      │   Todo Tools      │   Orchestration Tools  │
│   • log_chat      │   • add_todo      │   • agent_registry     │
│   • ask_context   │   • list_todos    │   • context_coord      │
├─────────────────────────────────────────────────────────────────┤
│                  Redis Orchestration Layer                     │
├───────────────────┬────────────────────┬───────────────────────┤
│   Agent Registry  │  Context Coord     │   Memory Locking      │
│   Service         │  Service           │   Service             │
├───────────────────┼────────────────────┼───────────────────────┤
│   Orchestration   │  Tool Cache        │   Shared Buffer       │
│   Service         │  Service           │   Service             │
├───────────────────┴────────────────────┴───────────────────────┤
│               Advanced ML Integration Layer                     │
├───────────────────┬────────────────────┬───────────────────────┤
│   Learning        │  Knowledge         │   Adaptive Resource   │
│   Coordination    │  Sharing           │   Management          │
├─────────────────────────────────────────────────────────────────┤
│                    4-Tier Memory System                        │
├──────────────────┬──────────────────┬─────────────────────────┤
│     SQLite       │      Redis       │       FAISS             │
│   Temporal Data  │   Cache Layer    │   Vector Search         │
│   • Resources    │   • Sessions     │   • Embeddings          │
│   • Chunks       │   • Tool Cache   │   • Similarity          │
│   • Chat History │   • Buffers      │   • Semantic Search     │
├──────────────────┴──────────────────┴─────────────────────────┤
│                        Neo4j                                   │
│                   Knowledge Graph                              │
│                 • Document Relations                           │
│                 • Context Linking                              │
│                 • Semantic Networks                            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Transport Layer

#### HTTP Transport
- **Technology**: FastAPI + Uvicorn
- **Port**: 5050 (configurable)
- **Protocol**: JSON-RPC 2.0 over HTTP
- **Features**:
  - RESTful endpoints for health checks and tool listing
  - CORS support for web client integration
  - Async request handling
  - Comprehensive error handling

```python
# HTTP Transport Architecture
app = FastAPI(
    title="LTMC MCP HTTP Server",
    description="HTTP transport for LTMC MCP server",
    version="2.0.0"
)

@app.post("/jsonrpc")
async def handle_jsonrpc(request: JSONRPCRequest) -> JSONRPCResponse:
    # Route to appropriate tool handler
    return await tool_router.handle(request)
```

#### MCP Transport (stdio)
- **Technology**: FastMCP SDK
- **Protocol**: JSON-RPC over stdio
- **Features**:
  - Native MCP client integration (Claude Desktop, etc.)
  - Bidirectional communication
  - Tool discovery and schema validation
  - Async tool execution

```python
# MCP Transport Architecture
mcp = FastMCP("LTMC Server")

@mcp.tool()
async def store_memory(file_name: str, content: str) -> dict:
    # Tool implementation
    return await memory_service.store(file_name, content)
```

### Tool Layer Architecture

#### Modular Tool Organization
```
ltms/tools/
├── memory_tools.py      # Memory storage and retrieval
├── chat_tools.py        # Conversation management
├── todo_tools.py        # Task management
├── context_tools.py     # Semantic context and linking
├── code_pattern_tools.py # ML code pattern learning
└── orchestration_tools.py # Multi-agent coordination
```

#### Tool Registry Pattern
```python
# Tool Definition Pattern
MEMORY_TOOLS = {
    "store_memory": {
        "handler": store_memory_handler,
        "description": "Store document with vector indexing",
        "schema": {
            "type": "object",
            "properties": {
                "file_name": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["file_name", "content"]
        }
    }
}
```

### Redis Orchestration Layer

#### Service Architecture
```python
# Orchestration Services Pattern
class OrchestrationService:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.agent_registry = AgentRegistryService(redis_client)
        self.context_coordinator = ContextCoordinationService(redis_client)
        self.memory_locker = MemoryLockingService(redis_client)
        self.tool_cache = ToolCacheService(redis_client)
        self.shared_buffer = SharedChunkBufferService(redis_client)
        self.session_manager = SessionStateManagerService(redis_client)
```

#### Service Responsibilities

##### Agent Registry Service
```python
class AgentRegistryService:
    async def register_agent(self, agent_metadata: dict) -> str:
        """Register new agent with health monitoring."""
        
    async def get_active_agents(self) -> List[dict]:
        """Get all active registered agents."""
        
    async def heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat for health monitoring."""
```

##### Context Coordination Service
```python
class ContextCoordinationService:
    async def create_shared_context(self, session_id: str) -> dict:
        """Create shared context for multi-agent session."""
        
    async def propagate_context(self, context: dict) -> bool:
        """Propagate context changes to all agents."""
        
    async def get_context_for_agent(self, agent_id: str) -> dict:
        """Get relevant context for specific agent."""
```

##### Memory Locking Service
```python
class MemoryLockingService:
    async def acquire_lock(self, resource_id: str, timeout: int = 30) -> bool:
        """Acquire distributed lock for resource."""
        
    async def release_lock(self, resource_id: str) -> bool:
        """Release distributed lock."""
        
    async def with_lock(self, resource_id: str, operation: Callable):
        """Context manager for locked operations."""
```

### Advanced ML Integration Layer

#### Learning Coordination
```python
class AdvancedLearningIntegration:
    def __init__(self):
        self.learning_coordinator = LearningCoordinator()
        self.knowledge_sharing = KnowledgeSharing()
        self.adaptive_resources = AdaptiveResourceManager()
        self.performance_monitor = PerformanceMonitor()
```

#### ML Components Architecture
- **Learning Coordination**: Cross-agent learning and pattern sharing
- **Knowledge Sharing**: Distributed knowledge base updates
- **Adaptive Resource Management**: Dynamic resource allocation based on usage
- **Performance Monitoring**: ML-driven performance optimization

### 4-Tier Memory System

#### Tier 1: SQLite (Temporal Data)
```sql
-- Core Tables
CREATE TABLE resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    resource_type TEXT DEFAULT 'document',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE resource_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    vector_id INTEGER UNIQUE,
    chunk_index INTEGER NOT NULL,
    FOREIGN KEY (resource_id) REFERENCES resources(id)
);
```

#### Tier 2: Redis (Cache & Session)
```python
# Redis Data Structures
# Session State: HASH
redis.hset(f"session:{session_id}", {
    "agents": json.dumps(agent_list),
    "context": json.dumps(shared_context),
    "created_at": timestamp
})

# Tool Cache: STRING with TTL
redis.setex(f"tool_cache:{tool_hash}", 300, json.dumps(result))

# Agent Registry: SET
redis.sadd("active_agents", agent_id)
redis.setex(f"agent:{agent_id}:heartbeat", 60, timestamp)
```

#### Tier 3: FAISS (Vector Search)
```python
class FAISSVectorStore:
    def __init__(self, dimension: int = 384):
        self.index = faiss.IndexFlatIP(dimension)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    async def add_vectors(self, texts: List[str]) -> List[int]:
        embeddings = self.model.encode(texts)
        vector_ids = await self.get_next_vector_ids(len(texts))
        self.index.add(embeddings)
        return vector_ids
    
    async def search_similar(self, query: str, k: int = 10) -> List[dict]:
        query_embedding = self.model.encode([query])
        scores, indices = self.index.search(query_embedding, k)
        return self.format_results(scores, indices)
```

#### Tier 4: Neo4j (Knowledge Graph)
```cypher
// Node Structure
CREATE (d:Document {id: $doc_id, title: $title, type: $doc_type})
CREATE (c:Chunk {id: $chunk_id, content: $content, vector_id: $vector_id})
CREATE (m:Message {id: $msg_id, content: $content, timestamp: $timestamp})

// Relationship Structure
CREATE (d)-[:HAS_CHUNK]->(c)
CREATE (m)-[:REFERENCES]->(c)
CREATE (d1)-[:RELATED_TO {strength: $strength}]->(d2)
```

## Data Flow Architecture

### Memory Storage Flow
```
1. User stores document via HTTP/MCP
2. Content chunked by ChunkingService
3. Chunks vectorized by EmbeddingService  
4. Vectors stored in FAISS with sequential IDs
5. Metadata stored in SQLite
6. Relationships created in Neo4j
7. Cache updated in Redis
```

### Semantic Search Flow
```
1. User queries for information
2. Query vectorized by EmbeddingService
3. FAISS returns similar vectors
4. SQLite provides chunk metadata
5. Neo4j enhances with relationships
6. Results cached in Redis
7. Response returned to user
```

### Multi-Agent Coordination Flow
```
1. Agent registers with AgentRegistryService
2. Context created by ContextCoordinationService
3. Shared state managed by SessionStateManager
4. Memory locks handled by MemoryLockingService
5. Tool results cached by ToolCacheService
6. Buffers managed by SharedChunkBufferService
```

## Performance Characteristics

### Latency Targets
- **Tool Execution**: < 100ms for cached operations
- **Vector Search**: < 50ms for queries up to 10k vectors
- **Memory Operations**: < 200ms for storage/retrieval
- **Multi-Agent Coordination**: < 10ms for state synchronization

### Throughput Capabilities
- **Concurrent Connections**: 1000+ HTTP connections
- **Tool Executions**: 100+ per second
- **Vector Operations**: 1000+ searches per second
- **Redis Operations**: 10,000+ operations per second

### Scalability Metrics
- **Memory Growth**: Linear with document count
- **Search Performance**: Logarithmic degradation
- **Agent Coordination**: Constant time for most operations
- **Cache Efficiency**: 90%+ hit rate for tool operations

## Security Architecture

### Transport Security
- **HTTP**: TLS 1.3 support for production deployments
- **MCP**: Secure stdio communication with client validation
- **Redis**: Password authentication and connection encryption
- **Database**: SQLite file permissions and access controls

### API Security
- **Input Validation**: Comprehensive schema validation for all tools
- **Rate Limiting**: Configurable per-endpoint rate limiting
- **Error Handling**: Secure error messages without information leakage
- **Audit Logging**: Complete audit trail for all operations

## Deployment Architecture

### Single Instance Deployment
```yaml
# Docker Compose Example
version: '3.8'
services:
  ltmc:
    image: ltmc:latest
    ports:
      - "5050:5050"
    environment:
      - DB_PATH=/data/ltmc.db
      - REDIS_HOST=redis
    volumes:
      - ./data:/data
    depends_on:
      - redis
      - neo4j
  
  redis:
    image: redis:7-alpine
    ports:
      - "6381:6381"
    command: redis-server --port 6381 --requirepass ltmc_cache_2025
  
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/ltmc_graph_2025
```

### Multi-Instance Deployment
```yaml
# Kubernetes Deployment Example
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ltmc-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ltmc
  template:
    metadata:
      labels:
        app: ltmc
    spec:
      containers:
      - name: ltmc
        image: ltmc:latest
        ports:
        - containerPort: 5050
        env:
        - name: REDIS_HOST
          value: "redis-cluster"
        - name: NEO4J_URI
          value: "bolt://neo4j-cluster:7687"
```

## Monitoring and Observability

### Metrics Collection
```python
# Prometheus Metrics
REQUEST_COUNT = Counter('ltmc_requests_total', 'Total requests', ['method', 'status'])
REQUEST_DURATION = Histogram('ltmc_request_duration_seconds', 'Request duration')
ACTIVE_AGENTS = Gauge('ltmc_active_agents', 'Number of active agents')
VECTOR_INDEX_SIZE = Gauge('ltmc_vector_index_size', 'Size of vector index')
```

### Health Checks
```python
# Health Check Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "vector_store": await check_vector_store_health(),
            "neo4j": await check_neo4j_health()
        }
    }
```

### Logging Architecture
```python
# Structured Logging
logger = logging.getLogger("ltmc")
logger.info("Tool executed", extra={
    "tool_name": tool_name,
    "execution_time_ms": execution_time,
    "agent_id": agent_id,
    "session_id": session_id,
    "success": True
})
```

## Configuration Management

### Environment Variables
```bash
# Core Configuration
DB_PATH=ltmc.db
FAISS_INDEX_PATH=faiss_index
LOG_LEVEL=INFO

# Transport Configuration
HTTP_HOST=localhost
HTTP_PORT=5050

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6381
REDIS_PASSWORD=ltmc_cache_2025

# Orchestration Configuration
ORCHESTRATION_MODE=full  # basic, full, debug
REDIS_ENABLED=true
CACHE_ENABLED=true

# ML Integration Configuration
ML_INTEGRATION_ENABLED=true
ML_LEARNING_COORDINATION=true
ML_OPTIMIZATION_INTERVAL=15
```

## Next Steps

- [Deployment Guide](../guides/DEPLOYMENT.md) - Production deployment instructions
- [API Reference](../api/API_REFERENCE.md) - Complete API documentation
- [Performance Tuning](../guides/PERFORMANCE_TUNING.md) - Optimization best practices
- [Troubleshooting Guide](../guides/TROUBLESHOOTING.md) - Common issues and solutions