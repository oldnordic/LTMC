# LTMC Project Tech Stack

## **🏗️ Core Architecture**

### **MCP (Model Context Protocol) Framework**
- **Primary Framework**: `mcp==1.12.3` - Official Python MCP SDK
- **Server Implementation**: `mcp.server.fastmcp.FastMCP` - FastMCP server implementation
- **Transport**: Stdio transport for MCP protocol communication
- **Protocol Version**: MCP 1.12.3 compliant

### **Async Runtime**
- **Async Framework**: `asyncio` - Python's built-in async/await support
- **HTTP Framework**: `fastapi==0.116.1` - Modern, fast web framework
- **ASGI Server**: `uvicorn==0.35.0` - Lightning-fast ASGI server
- **Async HTTP Client**: `httpx==0.28.1` - Fully featured HTTP client

---

## **🗄️ Database & Storage**

### **Primary Database**
- **SQLite**: Built-in Python database for local storage
- **Database Path**: Configurable via `db_path` setting
- **Connection Management**: Custom connection pooling and lifecycle management

### **Graph Database**
- **Neo4j**: Graph database for knowledge graph and relationships
- **Connection**: `bolt://localhost:7689` (custom port)
- **Authentication**: `neo4j` user with `ltmc_password_2025`
- **Driver**: `neo4j` Python driver (async support)

### **Vector Database**
- **FAISS**: Facebook AI Similarity Search for vector operations
- **Index Type**: In-memory and disk-based indices
- **Features**: AVX512 support, GPU support (optional)
- **Integration**: Custom FAISS service with LTMC memory system

### **Caching Layer**
- **Redis**: In-memory data structure store
- **Connection**: `localhost:6382` (custom port)
- **Authentication**: `ltmc_cache_2025` password
- **Use Cases**: Session caching, temporary data storage

---

## **🤖 Machine Learning & AI**

### **Core ML Framework**
- **PyTorch**: `torch==2.8.0` - Deep learning framework
- **CUDA Support**: Full CUDA 12.x support with optimized libraries
- **GPU Acceleration**: Optional GPU acceleration for vector operations

### **NLP & Embeddings**
- **Transformers**: `transformers==4.55.0` - Hugging Face transformers library
- **Sentence Transformers**: `sentence-transformers==5.1.0` - Semantic embeddings
- **Tokenizers**: `tokenizers==0.21.4` - Fast tokenization
- **Tiktoken**: `tiktoken==0.8.0` - OpenAI tokenizer

### **Vector Operations**
- **NumPy**: `numpy==2.3.2` - Numerical computing
- **SciPy**: `scipy==1.16.1` - Scientific computing
- **Scikit-learn**: `scikit-learn==1.7.1` - Machine learning utilities

---

## **🔧 Development & Testing**

### **Testing Framework**
- **Pytest**: `pytest==8.4.1` - Testing framework
- **Pytest-asyncio**: `pytest-asyncio==1.1.0` - Async testing support
- **Mock**: `mock==3.14.1` - Mocking and patching

### **Code Quality**
- **Type Checking**: `typing-extensions==4.14.1` - Extended type hints
- **Validation**: `pydantic==2.11.7` - Data validation
- **Settings**: `pydantic-settings==2.10.1` - Configuration management

---

## **📊 Data Processing**

### **Data Structures**
- **NetworkX**: `networkx==3.5` - Graph algorithms and data structures
- **Pandas**: Implicit dependency for data manipulation
- **JSON Schema**: `jsonschema==4.25.0` - JSON validation

### **File Handling**
- **Pathlib**: Built-in path manipulation
- **FSSpec**: `fsspec==2025.7.0` - File system interface
- **PyYAML**: `PyYAML==6.0.2` - YAML parsing

---

## **🌐 Web & API**

### **API Framework**
- **FastAPI**: Modern, fast web framework for building APIs
- **Starlette**: `starlette==0.47.2` - ASGI toolkit
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for production deployment

### **HTTP & Communication**
- **HTTPX**: Async HTTP client
- **Requests**: `requests==2.32.4` - HTTP library
- **SSE**: `sse-starlette==3.0.2` - Server-Sent Events

---

## **🔐 Security & Configuration**

### **Environment Management**
- **Python-dotenv**: `python-dotenv==1.1.1` - Environment variable loading
- **Configuration**: Centralized configuration via `LTMCSettings`
- **Secrets**: Environment-based secret management

### **Validation & Sanitization**
- **Input Validation**: Custom validation utilities
- **Content Sanitization**: User input sanitization
- **Path Security**: Secure path handling

---

## **📝 Logging & Monitoring**

### **Logging System**
- **Built-in Logging**: Python's logging module
- **Custom Formatters**: Structured logging for LTMC operations
- **Performance Tracking**: Custom performance measurement utilities

### **Monitoring**
- **Custom Metrics**: Performance and usage metrics
- **Health Checks**: Service health monitoring
- **Error Tracking**: Comprehensive error logging

---

## **🚀 Deployment & Packaging**

### **Binary Creation**
- **PyInstaller**: For creating standalone executables
- **Dependencies**: All required libraries bundled
- **Platform Support**: Linux, Windows, macOS

### **Container Support**
- **Docker**: Containerization support
- **Docker Compose**: Multi-service orchestration
- **Kubernetes**: K8s deployment manifests

---

## **📚 External Integrations**

### **AI Services**
- **Hugging Face**: `huggingface-hub==0.34.3` - Model hub integration
- **OpenAI**: Token counting and compatibility
- **Custom Models**: Local model support

### **Version Control**
- **Git Integration**: Repository information and metadata
- **File Tracking**: Change detection and versioning

---

## **⚡ Performance Features**

### **Optimization**
- **Async I/O**: Non-blocking operations throughout
- **Connection Pooling**: Database and service connection reuse
- **Caching**: Multi-layer caching strategy
- **Vectorization**: Optimized vector operations

### **Scalability**
- **Horizontal Scaling**: Multi-instance support
- **Load Balancing**: Service distribution
- **Resource Management**: Memory and CPU optimization

---

## **🔍 Development Tools**

### **IDE Support**
- **Type Hints**: Full type annotation support
- **Documentation**: Comprehensive docstrings
- **Code Generation**: Template-based code generation

### **Debugging**
- **Logging**: Detailed operation logging
- **Error Handling**: Comprehensive error management
- **Performance Profiling**: Built-in performance measurement

---

## **📋 Dependencies Summary**

### **Core Dependencies (Production)**
- `mcp==1.12.3` - MCP protocol implementation
- `fastapi==0.116.1` - Web framework
- `redis==5.2.1` - Caching layer
- `torch==2.8.0` - Machine learning
- `transformers==4.55.0` - NLP models
- `faiss` - Vector search
- `neo4j` - Graph database

### **Development Dependencies**
- `pytest==8.4.1` - Testing framework
- `pytest-asyncio==1.1.0` - Async testing
- `mock==3.14.1` - Mocking utilities

### **Optional Dependencies**
- CUDA libraries (for GPU acceleration)
- GPU-specific PyTorch builds
- Additional ML model formats

---

## **🎯 Technology Decisions**

### **Why These Choices?**
1. **MCP Protocol**: Industry standard for AI tool integration
2. **FastAPI**: Modern, fast, async-first web framework
3. **PyTorch**: Leading ML framework with excellent CUDA support
4. **FAISS**: Industry-standard vector similarity search
5. **Neo4j**: Best-in-class graph database for knowledge graphs
6. **Redis**: High-performance caching and session storage

### **Performance Considerations**
- Async-first architecture for high concurrency
- GPU acceleration for ML operations
- Optimized vector operations with FAISS
- Connection pooling for database efficiency
- Multi-layer caching strategy

### **Scalability Features**
- Stateless service design
- Horizontal scaling support
- Resource-efficient operations
- Configurable resource limits
