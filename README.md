# LTMC (Long-Term Memory and Context) MCP Server

A production-ready Model Context Protocol (MCP) server for persistent memory storage, retrieval, and context management with dual transport support (HTTP and stdio).

## 🚀 Key Features

- **Dual Transport Support**: HTTP and stdio transports
- **25 MCP Tools**: Comprehensive memory, chat, code pattern, and task management
- **4-Tier Memory Architecture**:
  - SQLite for temporal storage
  - FAISS vector store for semantic search
  - Redis for caching
  - Neo4j for graph-based context linking

## 📋 Quick Links

- [📦 Installation Guide](/docs/guides/INSTALLATION.md)
- [🛠 API Reference](/docs/api/README.md)
- [🏗️ Architecture Overview](/docs/architecture/systemArchtecture.md)
- [🐛 Troubleshooting](/docs/guides/TROUBLESHOOTING.md)

## 🔧 Prerequisites

- Python 3.11+
- Redis Server (port 6381)
- Neo4j Server (bolt://localhost:7687)

## 🚀 Quick Start

```bash
# Install dependencies
poetry install

# Start dual transport server
./start_server.sh
```

## 📊 Tool Categories

1. **Memory Tools**: Persistent storage and retrieval
2. **Chat Tools**: Conversation history management
3. **Todo Tools**: Task tracking and management
4. **Context Tools**: Semantic context retrieval
5. **Code Pattern Tools**: Machine learning-assisted code generation insights

## 🛡️ Development Status

- [x] Dual Transport Implementation
- [x] 25 MCP Tools
- [x] 4-Tier Memory System
- [ ] Advanced Machine Learning Integration

## 📄 License

See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **FastMCP**: Python SDK for MCP servers
- **FAISS**: Vector similarity search
- **SentenceTransformer**: Text embeddings
- **SQLite**: Database storage
- **Redis**: Caching layer
- **Neo4j**: Graph database

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Status**: ✅ **Production Ready**

The LTMC MCP server is fully operational with comprehensive memory management and 25 available tools for all your memory and context needs.