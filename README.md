# LTMC - Long-Term Memory and Context MCP Server

**Version**: 3.0  
**Status**: Production Ready  
**Tools**: 55 MCP Tools  
**Transport**: stdio MCP protocol

## 🎯 Overview

LTMC is a comprehensive Model Context Protocol (MCP) server that provides persistent memory, context management, and advanced AI coordination tools. Designed for Claude Code and expert agent teams, LTMC enables seamless knowledge retention, task management, and intelligent workflow automation.

## ✨ Key Features

- 🧠 **55 MCP Tools** across 14 categories (Core + Phase3 Advanced + Unified)
- 💾 **4-Tier Memory System** - SQLite + FAISS + Redis + Neo4j  
- 🤖 **AI Agent Coordination** - Team assignment, blueprint management, documentation sync
- 🔍 **Semantic Search** - Vector embeddings with intelligent context retrieval
- 📚 **Knowledge Graphs** - Automatic relationship building between concepts
- 🎯 **Task Management** - ML-driven complexity analysis and team assignment
- 📝 **Documentation Sync** - Real-time code-documentation consistency
- ⚡ **High Performance** - <50ms average response time with intelligent caching

## 🛠️ Tech Stack

**Core Technologies:**
- **Python 3.11+** with FastMCP SDK
- **MCP Protocol** - stdio transport for Claude Code integration
- **Vector Storage** - FAISS for semantic embeddings
- **Databases** - SQLite (primary), Redis (cache), Neo4j (graphs)
- **AI/ML** - Pattern learning, complexity analysis, team routing

**Development:**
- **Testing** - pytest with comprehensive integration tests
- **Quality** - mypy, flake8, black, bandit for security
- **Architecture** - Modular design with <300 lines per file
- **Documentation** - Complete guides for human users

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/oldnordic/ltmc-mcp-server.git
cd ltmc-mcp-server
pip install -r requirements.txt
```

### 2. Claude Code Integration
Add to your Claude Code MCP configuration:
```json
{
  "ltmc": {
    "command": "python",
    "args": ["ltmc_mcp_server/main.py"],
    "cwd": "/path/to/ltmc-mcp-server"
  }
}
```

### 3. Test Integration
Once configured, LTMC tools will be available in Claude Code:
- Use `mcp__ltmc__store_memory` to save information
- Use `mcp__ltmc__retrieve_memory` to search your knowledge
- Use `mcp__ltmc__add_todo` for task management
- Access all 55 tools through the MCP interface

## 📚 Documentation

### **For Human Users**
- 🎯 **[Claude Code Team Workflow Guide](docs/guides/CLAUDE_CODE_TEAM_WORKFLOW_GUIDE.md)** - Complete workflows for humans using Claude Code + expert agents ⭐
- 📖 **[User Guide](docs/guides/USER_GUIDE.md)** - Getting started with LTMC
- 🛠️ **[Complete 55 Tools Reference](docs/guides/COMPLETE_55_TOOLS_REFERENCE.md)** - All tools with examples

### **For Developers**
- 🔧 **[API Reference](docs/api/API_REFERENCE.md)** - Complete API documentation  
- 🏗️ **[System Architecture](docs/architecture/SYSTEM_ARCHITECTURE.md)** - Technical architecture overview
- 📋 **[Deployment Guide](docs/guides/DEPLOYMENT.md)** - Production deployment

### **Navigation Hub**
- 📚 **[Documentation Hub](docs/README.md)** - Complete documentation index with detailed guides

## 🔧 Tool Categories (55 Total)

### Core LTMC Tools (28)
- **Memory & Context** (7): Persistent storage, semantic search, context building
- **Chat & Communication** (2): Conversation logging, tool usage tracking  
- **Task Management** (4): Todo system with ML complexity analysis
- **Knowledge Graphs** (4): Relationship building, auto-linking, graph queries
- **Code Pattern Learning** (4): Experience replay, pattern analysis
- **Redis & Caching** (6): Performance optimization, cache management
- **System Analytics** (1): Usage statistics and monitoring

### Phase3 Advanced Tools (26) 
- **Task Blueprints** (9): ML-driven task planning and complexity analysis
- **Team Assignment** (3): Intelligent workload management and skill matching
- **Documentation Sync** (5): Real-time code-documentation consistency
- **Blueprint Integration** (5): Code-blueprint bidirectional synchronization  
- **Real-Time Monitoring** (3): Live file watching and change detection
- **Performance Analytics** (1): Advanced system performance metrics

### Unified Integration (1)
- **System Monitoring** (1): Comprehensive performance reporting across all components

## 🎯 Use Cases

- 🤝 **Team Collaboration** - Shared memory and context across team members
- 🧠 **Knowledge Management** - Institutional memory that never gets lost
- 📊 **Project Management** - ML-driven task planning and resource allocation  
- 🔍 **Code Learning** - Pattern recognition and experience replay
- 📝 **Documentation** - Always-current docs that sync with code changes
- 🎯 **AI Coordination** - Expert agent teams with persistent context

## 🌟 Why LTMC?

- **Never lose context** across conversations and sessions
- **Learn from experience** with code pattern replay
- **Scale your team** with AI-assisted task management
- **Maintain quality** with automated documentation sync
- **Build knowledge graphs** that connect related concepts
- **Optimize performance** with intelligent caching and monitoring

## 🤝 Contributing

Contributions welcome! Please check the documentation and submit issues or pull requests.

## 🔗 Links

- **GitHub**: [ltmc-mcp-server](https://github.com/oldnordic/ltmc-mcp-server)
- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/oldnordic/ltmc-mcp-server/issues)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.info)

---

**Ready to transform your development workflow?** Start with the [Claude Code Team Workflow Guide](docs/guides/CLAUDE_CODE_TEAM_WORKFLOW_GUIDE.md) to see how LTMC can accelerate your team's productivity! 🚀