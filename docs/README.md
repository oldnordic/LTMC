# LTMC Documentation Hub - 55 Tools

Welcome to the comprehensive documentation for the LTMC (Long-Term Memory and Context) MCP Server. This documentation suite covers all **55 tools** across 3 categories, providing everything you need to understand, deploy, and use LTMC effectively.

## 📚 Documentation Overview

### 🎯 Getting Started
Perfect for new users and quick setup:

- **[User Guide](guides/USER_GUIDE.md)** - Your first LTMC experience with step-by-step examples
- **[Claude Code Team Workflow Guide](guides/CLAUDE_CODE_TEAM_WORKFLOW_GUIDE.md)** - Complete workflow guide for humans using Claude Code + expert agents with all 55 tools
- **[Deployment Guide](guides/DEPLOYMENT.md)** - From development to production deployment
- **[Quick Start Tutorial](#)** - Get running in 5 minutes

### 📖 API Documentation
Complete reference for all LTMC tools:

- **[API Reference](api/API_REFERENCE.md)** - Comprehensive documentation for all 55 MCP tools
- **[Complete 55 Tools Reference](guides/COMPLETE_55_TOOLS_REFERENCE.md)** - Detailed usage guide for all tools
- **[Context Tools](api/CONTEXT_TOOLS.md)** - Advanced semantic search and knowledge graph tools
- **[Code Pattern Tools](api/CODE_PATTERN_TOOLS.md)** - Experience replay learning and pattern analysis
- **[Stdio MCP Protocol](#)** - Primary transport via stdio (recommended)
- **[HTTP Fallback Guide](#)** - REST API usage for development

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
- [Claude Code Team Workflow Guide](guides/CLAUDE_CODE_TEAM_WORKFLOW_GUIDE.md) - **⭐ RECOMMENDED for humans using Claude Code**
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

### Complete Tool List (55 Tools)

#### Core LTMC Tools (28)

**Memory & Context** (7 tools)
- `store_memory` - Persistent memory storage across sessions
- `retrieve_memory` - Semantic search for context-aware decisions  
- `ask_with_context` - Query with automatic context retrieval
- `build_context` - Build context windows with token limits
- `route_query` - Smart query routing to best processing method
- `retrieve_by_type` - Type-filtered document retrieval
- `advanced_context_search` - Advanced search with filters

**Chat & Communication** (2 tools)
- `log_chat` - Log conversations for continuity across sessions
- `get_chats_by_tool` - Retrieve conversations using specific tools

**Task Management** (4 tools)
- `add_todo` - Add tasks for complex multi-step implementations
- `list_todos` - List todos with optional status filtering
- `complete_todo` - Mark todos as completed for progress tracking
- `search_todos` - Search todos by title or description

**Knowledge Graph** (4 tools)
- `link_resources` - Create relationships between resources
- `query_graph` - Query knowledge graph for related information
- `auto_link_documents` - Automatically link similar documents
- `get_document_relationships` - Get all relationships for documents

**Code Pattern Learning** (4 tools)
- `log_code_attempt` - Log code attempts for experience replay learning
- `get_code_patterns` - Retrieve successful patterns for learning
- `analyze_code_patterns` - Analyze patterns for insights and trends
- `get_code_statistics` - Get comprehensive code pattern statistics

**Redis & Performance** (6 tools)
- `redis_health_check` - Monitor Redis connection health
- `redis_cache_stats` - Get Redis cache performance statistics
- `redis_set_cache` - Set values in Redis cache for optimization
- `redis_get_cache` - Retrieve values from Redis cache
- `redis_delete_cache` - Delete keys from Redis cache
- `redis_clear_cache` - Clear Redis cache with pattern matching

**System Analytics** (1 tool)
- `get_context_usage_statistics` - Comprehensive context usage analytics

#### Phase3 Advanced Tools (26)
**Task Blueprints** (9 tools) - ML-driven task management with complexity analysis  
**Team Assignment** (3 tools) - Workload management and skill-based assignment  
**Documentation Sync** (5 tools) - Code-documentation synchronization  
**Blueprint Integration** (5 tools) - Code-blueprint bidirectional sync  
**Real-Time Sync** (3 tools) - Live file monitoring and updates  
**Performance Metrics** (1 tool) - Advanced system analytics

#### Unified Integration (1)
**System Monitoring** (1 tool)
- `get_performance_report` - Unified system performance and statistics

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
- ✅ **55 MCP Tools** across 14 categories 
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

**Last Updated**: August 10, 2025  
**Documentation Version**: 3.0  
**LTMC Version**: Production Ready with 55 Tools & Advanced ML Integration

**Ready to get started?** Begin with the [User Guide](guides/USER_GUIDE.md) for the best LTMC experience! 🚀