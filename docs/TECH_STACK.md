# LTMC Technical Stack Documentation

## Project Overview

**LTMC (Long-Term Memory and Context)** is a sophisticated MCP (Model Context Protocol) server that provides advanced memory management, context retrieval, and multi-database orchestration capabilities for AI applications. The project implements a comprehensive tool ecosystem with action-based dispatch pattern and consolidated architecture for optimal performance.

## Core Architecture

### Language and Runtime
- **Primary Language**: Python 3.9+ (Production deployment target)
- **Development Environment**: Python 3.13 (Latest features and optimizations)
- **Execution Model**: Asynchronous/async-await patterns for high-performance I/O
- **Concurrency**: asyncio-based concurrent operations with connection pooling

### MCP Protocol Implementation
- **Protocol Version**: MCP 2024-11-05 specification compliance
- **Transport**: stdio-only communication (no HTTP endpoints)
- **SDK**: Native MCP SDK for Python MCP server development
- **Tool Architecture**: 11 consolidated tools with action-based dispatch pattern (`@mcp.tool` decorators)
- **Performance SLA**: <500ms for `tools/list`, <2s for `tools/call` operations

## Database Architecture (Multi-Tier System)

### 1. Relational Database (Primary)
- **Technology**: SQLite3 (built-in Python module)
- **Purpose**: Primary data persistence, chat history, resource metadata
- **Features**:
  - ACID compliance for data integrity
  - Foreign key constraints for referential integrity
  - Full-text search capabilities
  - Concurrent read operations with WAL mode
- **Schema**: Advanced schema with context linking, code patterns, and ML orchestration tables
- **Location**: `ltmc.db` (project root)

### 2. Vector Database
- **Technology**: FAISS (Facebook AI Similarity Search)
- **Variant**: faiss-cpu (CPU-optimized for development)
- **Purpose**: High-performance similarity search and semantic retrieval
- **Features**:
  - Real-time vector indexing
  - Cosine similarity search
  - Batch operations for efficiency
  - Memory-mapped indexes for persistence
- **Index Location**: `faiss_index` directory
- **Performance**: <25ms vector search operations

### 3. Graph Database
- **Technology**: Neo4j (optional, graceful degradation)
- **Purpose**: Document relationships and knowledge graphs
- **Features**:
  - Cypher query language
  - Graph traversal algorithms
  - Relationship modeling
  - Blueprint consistency validation
- **Connection**: Neo4j Python driver with connection pooling
- **Performance**: <20ms graph query operations

### 4. Cache Layer
- **Technology**: Redis (standalone instance)
- **Purpose**: High-speed caching and session state management
- **Features**:
  - Key-value caching with TTL
  - Pub/Sub messaging for real-time updates
  - Memory optimization with compression
  - Persistent caching with appendonly file
- **Configuration**: Custom Redis instance (port 6381, password-protected)
- **Performance**: <5ms cache operations

## Embedding and ML Pipeline

### Embedding Model
- **Primary Model**: `all-MiniLM-L6-v2` (Sentence-Transformers)
- **Purpose**: Generate high-quality text embeddings locally
- **Features**:
  - 384-dimensional embeddings
  - Local inference (no external API calls)
  - Multilingual support
  - CPU-optimized inference

### ML Orchestration Engine
- **Architecture**: Advanced ML coordination system integrated into consolidated tools
- **Components**:
  - Task routing engine with intelligent action selection
  - Continuous learning integration through pattern_action
  - Performance optimization with real-time adaptation via cache_action
  - Resource optimization based on usage patterns
- **Integration**: Native integration with all database tiers through action-based dispatch

## Development Framework

### Core Libraries
- **MCP SDK**: Official Model Context Protocol SDK with async support and automatic tool registration
- **Pydantic**: Data validation and serialization with V2 performance optimizations
- **asyncio**: Asynchronous I/O operations and concurrent execution
- **sqlite3**: Built-in relational database operations
- **sentence-transformers**: Local embedding generation
- **faiss-cpu**: CPU-optimized vector similarity search

### Configuration Management
- **Technology**: python-dotenv with environment variable loading
- **Features**:
  - Multi-environment configuration support
  - Runtime configuration validation through config_action
  - Secure credential management
  - Dynamic configuration reloading
- **Configuration Files**: `.env`, `ltmc_config.env`, project-specific configs

### Logging and Monitoring
- **Primary**: Python built-in logging module with structured logging
- **Features**:
  - Multi-level logging (DEBUG, INFO, WARNING, ERROR)
  - Structured JSON logging for production
  - Performance monitoring integration via cache_action
  - Real-time log streaming for debugging
- **Integration**: stderr logging for stdio MCP compatibility

## Quality Assurance Stack

### Testing Framework
- **Primary**: pytest with async support (`pytest-asyncio`)
- **Coverage**: pytest-cov with minimum 85% coverage requirement
- **Test Types**:
  - Unit tests (isolated component testing)
  - Integration tests (database and MCP protocol testing)
  - Performance tests (SLA compliance validation)
  - Compliance tests (mock detection and quality gates)

### Code Quality Tools
- **Formatter**: Black with line-length=88, Python 3.9+ target
- **Import Sorting**: isort with Black profile compatibility
- **Linting**: flake8 with extended ignore rules (E203, W503)
- **Type Checking**: mypy with gradual typing adoption
- **Security Scanning**: Bandit for security vulnerability detection

### Quality Gates System
- **Mock Detection**: Zero-tolerance AST and text pattern analysis
- **Performance SLA**: <15ms database, <25ms vector, <20ms graph operations
- **Test Coverage**: ≥85% code coverage requirement
- **Test Success Rate**: ≥95% success rate requirement
- **Code Quality Score**: 8.0/10 minimum quality score
- **Security Compliance**: Zero high-severity vulnerabilities

## Performance Architecture

### Performance Requirements
- **Database Operations**: <15ms response time
- **Vector Search**: <25ms similarity search
- **Graph Queries**: <20ms traversal operations
- **Cache Operations**: <5ms key-value operations
- **Memory Usage**: <500MB total consumption
- **Concurrency**: Support for multiple concurrent MCP clients

### Optimization Techniques
- **Connection Pooling**: Reuse database connections across requests
- **Lazy Loading**: On-demand loading of services and resources
- **Caching Strategy**: Multi-layer caching with Redis through cache_action
- **Batch Operations**: Bulk processing for efficiency through action-based dispatch
- **Async Operations**: Non-blocking I/O for high throughput

## Security Architecture

### Multi-Tenant Isolation
- **Project Isolation**: Secure project-based data separation
- **Path Security**: Restricted file system access with validation
- **Database Isolation**: Project-specific database prefixes and namespaces
- **Redis Namespacing**: Project-isolated cache keys

### Security Features
- **Input Validation**: Comprehensive input sanitization and validation via config_action
- **SQL Injection Prevention**: Parameterized queries and prepared statements
- **Path Traversal Protection**: Restricted file system access through unix_action
- **Credential Management**: Secure storage and rotation of database credentials

## Development Environment

### Local Development
- **Package Manager**: pip with requirements.txt
- **Virtual Environment**: venv for dependency isolation
- **Development Server**: Direct stdio MCP server execution
- **Hot Reload**: File watching for development workflow

### CI/CD Infrastructure
- **Local CI/CD**: Jenkins on raspberrypi.local (192.168.1.119:8080)
- **Quality Gates**: Automated quality validation pipeline
- **Testing Pipeline**: Multi-stage testing with real databases
- **Container Support**: Docker for isolated testing environments
- **GitHub Integration**: Automated sync after successful CI/CD validation

## Deployment Architecture

### Production Deployment
- **Execution**: Python script with stdio MCP protocol
- **Process Management**: systemd service for production deployment
- **Configuration**: Environment-based configuration management
- **Monitoring**: Performance and health monitoring integration
- **Scaling**: Multi-process deployment with shared cache layer

### Binary Distribution
- **PyInstaller**: Self-contained binary generation
- **Cross-Platform**: Linux, macOS, Windows support
- **Dependencies**: Embedded Python interpreter and libraries
- **Configuration**: External configuration file support

## Integration Points

### MCP Client Integration
- **Claude Code**: Primary MCP client for development workflows
- **VS Code**: MCP extension integration for editor support
- **Custom Clients**: MCP protocol compatibility for third-party clients

### External Service Integration
- **File System**: Direct file system access with security validation through unix_action
- **Operating System**: Native OS integration for system operations
- **Network Services**: HTTP/HTTPS client capabilities for external APIs

## Performance Monitoring

### Metrics Collection
- **Response Time Monitoring**: Operation-level performance tracking through cache_action
- **Memory Usage Tracking**: Real-time memory consumption monitoring
- **Database Performance**: Query performance and connection pool monitoring
- **Cache Hit Rates**: Redis cache efficiency metrics via cache_action

### Performance Optimization
- **Query Optimization**: Database query performance tuning
- **Index Management**: Efficient indexing strategy for fast retrieval
- **Memory Management**: Garbage collection optimization and memory pooling
- **Concurrent Processing**: Async operation optimization for throughput

## Documentation and Standards

### Technical Documentation
- **API Documentation**: Comprehensive tool and endpoint documentation via documentation_action
- **Architecture Documentation**: System design and component interaction documentation
- **Database Schema**: Complete schema documentation with relationships
- **Integration Guides**: MCP client integration and usage guides

### Development Standards
- **Code Style**: Black formatting with 88-character line length
- **Import Organization**: isort with Black compatibility
- **Type Annotations**: Gradual adoption of Python type hints
- **Error Handling**: Comprehensive exception handling and logging
- **Testing Standards**: TDD approach with comprehensive test coverage

## LTMC Tool Architecture (11 Consolidated Tools)

### Real Tool Inventory (Verified Against Codebase)

| # | Tool | File Location | Purpose |
|---|------|---------------|---------|
| 1 | `mcp__ltmc__memory_action` | `ltms/tools/consolidated.py:59` | Memory storage and retrieval with vector indexing |
| 2 | `mcp__ltmc__todo_action` | `ltms/tools/consolidated.py:307` | Task tracking and completion management |
| 3 | `mcp__ltmc__chat_action` | `ltms/tools/consolidated.py:582` | Conversation logging and conversation management |
| 4 | `mcp__ltmc__unix_action` | `ltms/tools/consolidated.py:740` | Modern Unix tools integration (exa, bat, ripgrep, fd) |
| 5 | `mcp__ltmc__pattern_action` | `ltms/tools/consolidated.py:1431` | AST-based code analysis and pattern extraction |
| 6 | `mcp__ltmc__blueprint_action` | `ltms/tools/consolidated.py:1615` | Task blueprint creation and dependency management |
| 7 | `mcp__ltmc__cache_action` | `ltms/tools/consolidated.py:2226` | Redis cache operations and performance monitoring |
| 8 | `mcp__ltmc__graph_action` | `ltms/tools/consolidated.py:2409` | Knowledge graph relationships and querying |
| 9 | `mcp__ltmc__documentation_action` | `ltms/tools/consolidated.py:2923` | API documentation and architecture diagram generation |
| 10 | `mcp__ltmc__sync_action` | `ltms/tools/consolidated.py:3324` | Code-documentation synchronization and drift detection |
| 11 | `mcp__ltmc__config_action` | `ltms/tools/consolidated.py:3738` | Configuration validation and schema management |

### Action-Based Architecture Benefits
- **Unified Interface**: All tools use consistent action parameter pattern
- **Reduced Complexity**: 80% reduction in tool count through intelligent consolidation
- **Better Organization**: Logical grouping by functionality domain
- **Easier Maintenance**: Single file to update (`ltms/tools/consolidated.py`)
- **Performance Optimization**: Centralized dispatch reduces overhead

## Future Architecture Considerations

### Scalability Planning
- **Horizontal Scaling**: Multi-instance deployment with shared state
- **Database Sharding**: Large-scale data partitioning strategies
- **Caching Strategy**: Distributed caching for multi-instance deployments through cache_action
- **Load Balancing**: Request distribution for high-availability deployments

### Technology Evolution
- **Python Version Migration**: Gradual migration to latest Python versions
- **Database Optimization**: Advanced indexing and query optimization
- **ML Pipeline Enhancement**: Advanced machine learning integration through pattern_action
- **Real-Time Processing**: Stream processing for real-time analytics via sync_action

---

## Quick Reference

### Key Directories
- **`ltms/`**: Core MCP server implementation
- **`ltms/database/`**: Database layer and schema management
- **`ltms/services/`**: Business logic and service implementations
- **`ltms/tools/`**: MCP tool implementations (consolidated architecture)
- **`config/`**: Configuration templates and examples
- **`tests/`**: Comprehensive test suite
- **`quality-gates/`**: Quality assurance and validation tools

### Key Files
- **`ltms/mcp_server.py`**: Main MCP server entry point
- **`ltms/tools/consolidated.py`**: All 11 MCP tools implementation
- **`ltms/config.py`**: Configuration management
- **`ltms/database/schema.py`**: Database schema definitions
- **`requirements.txt`**: Python dependencies
- **`.env`**: Environment configuration
- **`pytest.ini`**: Testing configuration

### Performance Targets
- **MCP Response Time**: <500ms for tool list, <2s for tool execution
- **Database Operations**: <15ms response time
- **Vector Search**: <25ms similarity search
- **Memory Usage**: <500MB total consumption
- **Test Coverage**: ≥85% code coverage
- **Test Success Rate**: ≥95% success rate

This technical stack provides a robust, scalable, and maintainable foundation for the LTMC MCP server, with comprehensive quality assurance, performance optimization, and security features. The consolidated tool architecture ensures optimal performance while maintaining simplicity and maintainability.