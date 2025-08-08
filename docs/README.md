# LTMC Documentation Hub

Welcome to the comprehensive documentation for the LTMC (Long-Term Memory and Context) Multi-Agent Coordination Platform. This documentation suite provides everything you need to understand, deploy, and use LTMC effectively.

## 📚 Documentation Overview

### 🎯 Getting Started
Perfect for new users and quick setup:

- **[User Guide](guides/USER_GUIDE.md)** - Your first LTMC experience with step-by-step examples
- **[Deployment Guide](guides/DEPLOYMENT.md)** - From development to production deployment
- **[Quick Start Tutorial](#)** - Get running in 5 minutes

### 📖 API Documentation
Complete reference for all LTMC tools:

- **[API Reference](api/API_REFERENCE.md)** - Comprehensive documentation for all 25 MCP tools
- **[Context Tools](api/CONTEXT_TOOLS.md)** - Advanced semantic search and knowledge graph tools
- **[Code Pattern Tools](api/CODE_PATTERN_TOOLS.md)** - AI-assisted code learning and pattern analysis
- **[HTTP Transport Guide](#)** - REST API usage and examples
- **[MCP Protocol Guide](#)** - JSON-RPC over stdio documentation

### 🏗️ Architecture & System Design
Technical deep dives for developers and architects:

- **[System Architecture](architecture/SYSTEM_ARCHITECTURE.md)** - Complete technical architecture overview
- **[Redis Orchestration](redis_orchestration_architecture.md)** - Multi-agent coordination system
- **[Testing Strategy](redis_orchestration_testing_strategy.md)** - Quality assurance approach
- **[Performance Characteristics](#)** - System performance and scaling

### 🔧 Operations & Maintenance
For system administrators and DevOps:

- **[Deployment Guide](guides/DEPLOYMENT.md)** - Production deployment scenarios
- **[Performance Tuning](#)** - Optimization and scaling techniques
- **[Monitoring Guide](#)** - Observability and metrics
- **[Troubleshooting Guide](#)** - Common issues and solutions
- **[Security Guide](#)** - Security best practices and configuration

### 🤝 Development & Integration
For developers integrating with LTMC:

- **[Development Setup](#)** - Local development environment
- **[Integration Examples](#)** - Python, JavaScript, and cURL examples
- **[SDK Documentation](#)** - Client libraries and tools
- **[Contributing Guidelines](#)** - How to contribute to LTMC
- **[Code Standards](#)** - Development practices and patterns

## 🚀 Quick Navigation

### By User Type

#### 👤 End Users
Start here if you want to use LTMC for memory management and AI assistance:
- [User Guide](guides/USER_GUIDE.md)
- [Quick Start Examples](#quick-start-examples)
- [Common Use Cases](#common-use-cases)

#### 🔧 Developers
For integration and custom development:
- [API Reference](api/API_REFERENCE.md)
- [Integration Examples](#integration-examples)
- [SDK Documentation](#sdk-documentation)

#### 🏢 System Administrators
For deployment and operations:
- [Deployment Guide](guides/DEPLOYMENT.md)
- [Operations Guide](#operations-guide)
- [Security Configuration](#security-configuration)

#### 🏗️ Solution Architects
For system design and architecture decisions:
- [System Architecture](architecture/SYSTEM_ARCHITECTURE.md)
- [Performance Characteristics](#performance-characteristics)
- [Scaling Strategies](#scaling-strategies)

### By Feature

#### 🧠 Memory Management
- [Memory Tools API](api/API_REFERENCE.md#memory-tools)
- [Semantic Search Guide](#semantic-search)
- [Document Organization](#document-organization)

#### 🤝 Multi-Agent Coordination
- [Redis Orchestration](redis_orchestration_architecture.md)
- [Agent Registry](#agent-registry)
- [Context Coordination](#context-coordination)

#### 📚 Code Pattern Learning
- [Code Pattern Tools](api/CODE_PATTERN_TOOLS.md)
- [Experience Replay](#experience-replay)
- [Pattern Analysis](#pattern-analysis)

#### 🔗 Knowledge Graphs
- [Context Tools](api/CONTEXT_TOOLS.md)
- [Document Relationships](#document-relationships)
- [Auto-Linking Features](#auto-linking)

## 📊 Tool Categories Reference

### Complete Tool List (25 Tools)

#### Memory Management (2 tools)
- `store_memory` - Store documents with automatic chunking and vector indexing
- `retrieve_memory` - Semantic search across all stored content

#### Chat & Communication (4 tools)
- `log_chat` - Maintain conversation history with context linking
- `ask_with_context` - Q&A with relevant context retrieval
- `route_query` - Intelligent query routing
- `get_chats_by_tool` - Find tool-related conversations

#### Task Management (4 tools)
- `add_todo` - Create prioritized tasks
- `list_todos` - Filter and view tasks
- `complete_todo` - Mark tasks completed
- `search_todos` - Find tasks by content

#### Context & Relationships (11 tools)
- `build_context` - Create context windows
- `retrieve_by_type` - Type-filtered search
- `store_context_links` - Link messages to chunks
- `get_context_links_for_message` - Retrieve message links
- `get_messages_for_chunk` - Find chunk references
- `get_context_usage_statistics` - Usage analytics
- `link_resources` - Create explicit relationships
- `query_graph` - Search knowledge graph
- `auto_link_documents` - Automatic linking
- `get_document_relationships` - Explore connections
- `list_tool_identifiers` - Available tools
- `get_tool_conversations` - Tool usage history

#### Code Pattern Learning (3 tools)
- `log_code_attempt` - Record code generation attempts
- `get_code_patterns` - Retrieve similar patterns
- `analyze_code_patterns` - Pattern trend analysis

#### Orchestration (1+ tools)
- Multi-agent coordination and session management tools

## 🎯 Common Use Cases

### Personal Knowledge Management
- Store and search personal documents
- Maintain project notes and documentation
- Track tasks and todos
- Build knowledge graphs of related information

### Team Collaboration
- Shared memory across team members
- Conversation history maintenance
- Collaborative document linking
- Task coordination and tracking

### AI-Assisted Development
- Code pattern learning and reuse
- Documentation generation assistance
- Error pattern analysis
- Best practice identification

### Multi-Agent Systems
- Agent coordination and lifecycle management
- Shared context across multiple agents
- Distributed memory access
- Performance optimization through caching

## 🔄 Integration Patterns

### HTTP API Integration
```bash
# Example: Store and retrieve pattern
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "example.md",
        "content": "Example content"
      }
    },
    "id": 1
  }'
```

### Python SDK Integration
```python
# Example: Async client pattern
client = LTMCClient()
result = await client.call_tool("retrieve_memory", {
    "query": "search terms",
    "top_k": 5
})
```

### MCP Client Integration
```json
{
  "mcpServers": {
    "ltmc": {
      "command": "python",
      "args": ["ltmc_mcp_server.py"]
    }
  }
}
```

## 📁 Legacy Documentation Structure

The following legacy documentation is maintained for historical reference and migration purposes:

### 🏗️ Architecture (`/architecture/`)
Legacy architecture documentation:
- **[ApiSpecification.md](architecture/ApiSpecification.md)** - REST API endpoints and specifications
- **[DataBaseSchemaSQLite.md](architecture/DataBaseSchemaSQLite.md)** - Database schema and SQLite structure
- **[DataFlowDiagram.md](architecture/DataFlowDiagram.md)** - System data flow and component interactions
- **[ModularProjectStructure.md](architecture/ModularProjectStructure.md)** - Project structure and module organization
- **[systemArchtecture.md](architecture/systemArchtecture.md)** - Overall system architecture design
- **[TechStack.md](architecture/TechStack.md)** - Technology stack and dependencies

### 🔧 Implementation (`/implementation/`)
Legacy implementation plans:
- **[MCP_Implementation_Plan.md](implementation/MCP_Implementation_Plan.md)** - Model Context Protocol implementation strategy
- **[MCP_TDD_Implementation_Plan.md](implementation/MCP_TDD_Implementation_Plan.md)** - Test-Driven Development approach for MCP

### 📋 Planning (`/planning/`)
Legacy project planning:
- **[DevelopmentRoadmap.md](planning/DevelopmentRoadmap.md)** - Development timeline and milestones

### 📊 Status (`/status/`)
Legacy project status tracking:
- **[LTMC_Project_Status_Tracking.md](status/LTMC_Project_Status_Tracking.md)** - Detailed project status and TODO tracking
- **[LTMC_FINAL_STATUS_REPORT.md](status/LTMC_FINAL_STATUS_REPORT.md)** - Final project status and completion report
- **[IMPLEMENTATION_SUMMARY.md](status/IMPLEMENTATION_SUMMARY.md)** - Summary of implementation progress

### 📚 Legacy Guides (`/guides/`)
Historical development guides:
- **[LTMC_Professional_Development_Guide.md](guides/LTMC_Professional_Development_Guide.md)** - Comprehensive guide for professional development teams
- **[LTMC_Architecture_Execution_Plan.md](guides/LTMC_Architecture_Execution_Plan.md)** - Architecture execution strategy

## 📈 Performance Guidelines

### Optimization Tips
- Use appropriate `top_k` values for searches (default: 10)
- Leverage caching through Redis orchestration
- Organize documents with clear types and structure
- Monitor performance through health endpoints

### Scaling Considerations
- Horizontal scaling through multiple instances
- Redis cluster for orchestration scaling
- Neo4j clustering for knowledge graph scaling
- Load balancing for HTTP transport

## 🔐 Security Best Practices

### Transport Security
- Use HTTPS in production deployments
- Implement proper authentication mechanisms
- Configure Redis password protection
- Secure Neo4j with appropriate credentials

### Data Security
- Validate all input through schema validation
- Implement access control for sensitive operations
- Use audit logging for compliance requirements
- Regular security updates and patches

## 🐛 Troubleshooting Quick Reference

### Common Issues
1. **Connection Errors**: Check service status with health endpoints
2. **Search Issues**: Verify documents are stored and indexed
3. **Performance Problems**: Monitor Redis and vector index performance
4. **Integration Errors**: Validate JSON-RPC request format

### Debug Tools
- Health check endpoints for all services
- Log file analysis for error investigation
- Performance metrics for optimization
- Service status monitoring

## 📞 Getting Help

### Support Channels
- **Documentation**: Comprehensive guides in this repository
- **Issues**: GitHub Issues for bug reports and feature requests
- **Community**: Discussions for questions and use cases
- **Troubleshooting**: Dedicated troubleshooting guides

### Contribution
- **Code Contributions**: Follow development guidelines
- **Documentation**: Help improve and extend documentation
- **Testing**: Contribute test cases and quality improvements
- **Examples**: Share integration examples and use cases

## 📚 Additional Resources

### External Documentation
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Redis Documentation](https://redis.io/docs)
- [Neo4j Documentation](https://neo4j.com/docs)
- [FAISS Documentation](https://faiss.ai/)

### Community Resources
- Example applications and integrations
- Tutorial videos and walkthroughs
- Best practices from the community
- Performance optimization guides

---

## 📝 Documentation Status

- ✅ **User Guide** - Complete with examples and tutorials
- ✅ **API Reference** - All 25 tools documented with examples
- ✅ **Architecture Guide** - Comprehensive system design documentation
- ✅ **Deployment Guide** - Development to production deployment
- ✅ **Context Tools** - Advanced semantic search features
- ✅ **Code Pattern Tools** - AI-assisted development features
- ✅ **Redis Orchestration** - Multi-agent coordination system
- ✅ **Testing Strategy** - Quality assurance approach
- ⏳ **Performance Tuning** - Optimization techniques (planned)
- ⏳ **Monitoring Guide** - Observability setup (planned)
- ⏳ **Troubleshooting Guide** - Issue resolution (planned)

## 🚀 Project Status

**Current Status**: ✅ **PRODUCTION READY WITH COMPREHENSIVE DOCUMENTATION**

The LTMC Multi-Agent Coordination Platform is fully operational with:
- ✅ **Dual Transport** (HTTP + stdio) MCP server
- ✅ **25 MCP Tools** across 6 categories 
- ✅ **4-Tier Memory System** (SQLite + FAISS + Redis + Neo4j)
- ✅ **Redis Orchestration** with 6 specialized services
- ✅ **Advanced ML Integration** with 12 components
- ✅ **Production-Ready Architecture** with monitoring and scaling
- ✅ **Comprehensive Documentation** with user guides and API reference
- ✅ **Professional Documentation Suite** ready for enterprise use

## 🔧 Quick Usage

```bash
# Start the LTMC server with full orchestration
./start_server.sh --orchestration-mode=full

# Check comprehensive status
./status_server.sh

# Test API functionality
curl http://localhost:5050/health
curl http://localhost:5050/orchestration/health
curl http://localhost:5050/ml/status

# Stop the server
./stop_server.sh
```

---

**Last Updated**: August 8, 2025  
**Documentation Version**: 2.0  
**LTMC Version**: Production Ready with Advanced ML Integration

**Ready to get started?** Begin with the [User Guide](guides/USER_GUIDE.md) for the best LTMC experience! 🚀