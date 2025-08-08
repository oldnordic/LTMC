# LTMC System Architecture

## Overview

LTMC (Long-Term Memory and Context) is a sophisticated, modular MCP (Model Context Protocol) server designed for persistent memory storage, retrieval, and context management.

## 4-Tier Memory Architecture

### 1. Temporal Storage: SQLite
- **Role**: Persistent storage of resources, chunks, and metadata
- **Key Tables**:
  - `Resources`: Main resource storage
  - `ResourceChunks`: Chunked content with vector IDs
  - `VectorIdSequence`: Sequential vector ID management
- **Characteristics**:
  - ACID-compliant
  - Low-latency read/write
  - Embedded database

### 2. Semantic Search: FAISS Vector Store
- **Role**: High-performance similarity search
- **Features**:
  - 384-dimensional embeddings
  - Nearest neighbor search
  - Supports large-scale vector comparisons
- **Use Cases**:
  - Content retrieval
  - Semantic matching
  - Context generation

### 3. Caching Layer: Redis
- **Role**: High-speed in-memory caching
- **Configuration**:
  - Port: 6381
  - Persistence mode: AOF
- **Functions**:
  - Temporary data storage
  - Session management
  - Query result caching

### 4. Graph Relationships: Neo4j
- **Role**: Complex relationship tracking
- **Features**:
  - Graph database
  - Advanced query capabilities
  - Relationship-based context linking
- **Use Cases**:
  - Document interconnections
  - Context graph generation
  - Semantic relationship analysis

## Transport Layers

### HTTP Transport
- **Server**: FastAPI at `ltms/mcp_server_http.py`
- **Port**: 5050
- **Protocol**: JSON-RPC
- **Features**:
  - RESTful endpoint
  - Comprehensive error handling
  - Middleware support

### Stdio Transport
- **Entry Point**: `ltmc_mcp_server.py`
- **Purpose**: IDE and CLI integration
- **Characteristics**:
  - Direct MCP protocol
  - Low-overhead communication
  - Identical tool set to HTTP transport

## Tool Modules (25 Total)

### 1. Memory Tools
- Persistent storage
- Retrieval with context
- Resource management

### 2. Chat Tools
- Conversation history
- Context linking
- Usage statistics

### 3. Code Pattern Tools
- Code generation tracking
- Pattern analysis
- Learning from past attempts

### 4. Todo Management
- Task tracking
- Search and filtering
- Completion tracking

### 5. Context and Relationship Tools
- Resource linking
- Graph querying
- Automatic relationship detection

## Async-First Design

### Core Principles
- All I/O operations use `async/await`
- Non-blocking architecture
- High concurrency support

### Performance Characteristics
- Minimal blocking
- Efficient resource utilization
- Scalable design

## Security and Quality Gates

### Authentication
- TBD: JWT or OAuth integration
- Per-tool access control

### Error Handling
- Comprehensive exception tracking
- Structured error responses
- Logging with context

### Quality Metrics
- 100% test coverage goal
- Comprehensive type hints
- Strict linting rules

## Integration Patterns

### MCP Server Integration
- Supports multiple AI assistants
- Standardized memory protocol
- Extensible tool framework

### Potential Extensions
- Machine learning model integration
- Advanced reasoning capabilities
- Cross-assistant memory sharing

## System Topology

```
┌───────────────────┐
│    AI Assistant   │
└────────┬──────────┘
         │
         ▼
┌─────────────────────┐
│   LTMC MCP Server   │
├─────────┬───────────┤
│ HTTP    │ Stdio     │
│ (5050)  │ Transport │
└────┬────┴───────────┘
     │
     ▼
┌─────────────────────┐
│   4-Tier Memory     │
├─────────┬───────────┤
│ SQLite  │ FAISS     │
│ Redis   │ Neo4j     │
└─────────┴───────────┘
```

## Future Roadmap

- [ ] Advanced ML integration
- [ ] Multi-agent memory sharing
- [ ] Enhanced semantic reasoning
- [ ] Distributed deployment support

## Documentation

- [Installation Guide](/docs/guides/INSTALLATION.md)
- [Troubleshooting](/docs/guides/TROUBLESHOOTING.md)
- [API Reference](/docs/api/README.md)

## Licensing

See [LICENSE](/LICENSE) for details.

## Acknowledgments

- **FastAPI**: Web framework
- **FAISS**: Vector search
- **Redis**: Caching
- **Neo4j**: Graph database
- **SQLite**: Persistent storage