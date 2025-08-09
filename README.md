# LTMC - Long-Term Memory and Context

[![Production Ready](https://img.shields.io/badge/Status-Production%20Ready-green.svg)](https://github.com/your-repo/lmtc) [![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org) [![MCP](https://img.shields.io/badge/Protocol-MCP-purple.svg)](https://modelcontextprotocol.io)

**A production-ready Model Context Protocol (MCP) server providing persistent memory, semantic search, and intelligent context management for AI assistants.**

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd lmtc
pip install -r requirements.txt

# Start services
./setup_redis.sh
./start_server.sh

# Test the server
curl http://localhost:5050/health
```

**✅ Server running at `http://localhost:5050`**

## 🎯 What is LTMC?

LTMC transforms AI interactions by providing:

- **🧠 Persistent Memory** - Store and retrieve context across sessions
- **🔍 Semantic Search** - Find relevant information using AI-powered similarity
- **📊 Code Pattern Learning** - AI learns from successful code examples  
- **🔗 Knowledge Graphs** - Automatic relationship discovery between concepts
- **⚡ High Performance** - Redis caching with <50ms response times

## 🛠️ Core Features

| Feature | Description |
|---------|-------------|
| **28 MCP Tools** | Complete toolkit for memory, tasks, chat, and code patterns |
| **Dual Transport** | HTTP REST API + native MCP protocol support |
| **Vector Search** | FAISS-powered semantic similarity search |
| **Redis Orchestration** | High-performance caching and coordination |
| **Production Ready** | Docker support, monitoring, and scaling |

## 📖 Documentation

- **[User Guide](docs/guides/USER_GUIDE.md)** - Complete getting started guide
- **[API Reference](docs/api/API_REFERENCE.md)** - All 28 tools documented  
- **[Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)** - Technical deep dive
- **[Deployment](docs/guides/DEPLOYMENT.md)** - Production deployment guide

## 🔧 Architecture

```
┌─────────────────────────────────────────┐
│           LTMC MCP Server               │
├─────────────────────────────────────────┤
│  HTTP API  ←→  MCP Protocol (stdio)    │
├─────────────────────────────────────────┤
│          28 MCP Tools Layer            │  
├─────────────────────────────────────────┤
│     SQLite + FAISS + Redis + Neo4j     │
└─────────────────────────────────────────┘
```

## 📊 Tool Categories

- **Memory & Search** - `store_memory`, `retrieve_memory`, `ask_with_context`
- **Chat History** - `log_chat`, `route_query`, `get_chats_by_tool`  
- **Task Management** - `add_todo`, `list_todos`, `complete_todo`, `search_todos`
- **Knowledge Graph** - `link_resources`, `query_graph`, `auto_link_documents`
- **Code Patterns** - `log_code_attempt`, `get_code_patterns`, `analyze_code_patterns`
- **Cache & Performance** - Redis integration with statistics and health monitoring

## 🔌 Integration

### MCP Configuration
Add to your MCP client configuration:

```json
{
  "ltmc": {
    "command": "python",
    "args": ["ltmc_mcp_server.py"],
    "env": {"DB_PATH": "ltmc.db"}
  }
}
```

### HTTP API Usage
```bash
# Store memory
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "store_memory", "arguments": {"file_name": "note.md", "content": "Important information"}}, "id": 1}'

# Search memory  
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "retrieve_memory", "arguments": {"query": "important", "top_k": 5}}, "id": 2}'
```

## 🚀 Production Deployment

### Docker
```bash
docker build -t ltmc .
docker run -p 5050:5050 ltmc
```

### Environment Variables
```bash
DB_PATH=ltmc.db                    # Database file path
REDIS_HOST=localhost               # Redis host
REDIS_PORT=6381                   # Redis port  
LOG_LEVEL=INFO                    # Logging level
```

## 🧪 Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Check specific functionality
python tests/manual/test_ltmc_simple.py
```

## 📁 Project Structure

```
lmtc/
├── ltms/                  # Core LTMC system
├── docs/                  # Documentation
├── tests/                 # Test suites
├── config/                # Configuration files
├── tools/scripts/         # Utility scripts
└── archive/              # Historical results
```

## 🤝 Contributing

1. **Issues & Bugs**: [GitHub Issues](../../issues)
2. **Development**: See [Architecture Guide](docs/architecture/SYSTEM_ARCHITECTURE.md)  
3. **Testing**: See [Testing Guide](docs/testing/)

## 📋 Status

- ✅ **28 MCP Tools** - Complete and tested
- ✅ **Production Ready** - Docker, monitoring, scaling
- ✅ **High Performance** - Redis caching, vector search
- ✅ **Comprehensive Docs** - User guides and API reference

---

**Ready to enhance your AI workflows with persistent memory?** [Get started now!](docs/guides/USER_GUIDE.md) 🚀