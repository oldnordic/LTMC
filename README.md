# LTMC (Long-Term Memory and Context) Multi-Agent Coordination Platform

A sophisticated, production-ready Model Context Protocol (MCP) server with advanced Redis-powered orchestration, providing persistent memory storage, retrieval, and multi-agent coordination with dual transport support (HTTP and stdio).

## 🚀 Key Features

- **Advanced Orchestration**: 6 specialized Redis-based orchestration services
- **Dual Transport Support**: HTTP and stdio transports
- **25 MCP Tools**: Comprehensive memory, chat, code pattern, and task management
- **Multi-Agent Coordination**: Full agent lifecycle and session management
- **4-Tier Memory Architecture**:
  - SQLite for temporal storage
  - FAISS vector store for semantic search
  - Redis for caching and orchestration
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

# Start dual transport server with orchestration
./start_server.sh --orchestration-mode=full

# Health and Orchestration Check
curl http://localhost:5050/orchestration/health
```

## 📊 Tool Categories

1. **Memory Tools**: Persistent storage and retrieval
2. **Chat Tools**: Conversation history management
3. **Todo Tools**: Task tracking and management
4. **Context Tools**: Semantic context retrieval
5. **Code Pattern Tools**: Machine learning-assisted code generation insights
6. **Orchestration Tools**: Multi-agent coordination and session management

## 🛡️ Development Status

- [x] Dual Transport Implementation
- [x] 25 MCP Tools
- [x] 4-Tier Memory System
- [x] Redis Orchestration Services
- [x] Multi-Agent Coordination
- [ ] Advanced Machine Learning Integration

## 🔧 Orchestration Configuration

Configure orchestration behavior using environment variables:

- `ORCHESTRATION_MODE`: Set to `basic`, `full`, `debug`, or `disabled`
- `REDIS_ENABLED`: Enable/disable Redis orchestration
- `REDIS_PORT`: Specify custom Redis port (default: 6381)

Example:
```bash
ORCHESTRATION_MODE=full REDIS_ENABLED=true ./start_server.sh
```

## 📄 License

See [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- **FastMCP**: Python SDK for MCP servers
- **FAISS**: Vector similarity search
- **SentenceTransformer**: Text embeddings
- **SQLite**: Database storage
- **Redis**: Caching and orchestration layer
- **Neo4j**: Graph database

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the logs for error details

---

**Status**: ✅ **Production Ready**

The LTMC Multi-Agent Coordination Platform is fully operational with comprehensive memory management, 25 available tools, and advanced Redis-powered orchestration to support complex multi-agent workflows.