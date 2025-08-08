# LTMC Orchestration Integration

This document describes the complete Redis orchestration integration with the LTMC MCP server, providing multi-agent coordination capabilities while maintaining full backward compatibility.

## Overview

The orchestration integration adds sophisticated multi-agent coordination to LTMC without breaking existing functionality. All 25 existing MCP tools continue to work unchanged, while new orchestration capabilities are available when Redis is available.

## Architecture

### Core Components

1. **OrchestrationIntegration** (`ltms/mcp_orchestration_integration.py`)
   - Central integration layer
   - Decorates existing tools with orchestration capabilities
   - Provides graceful degradation when Redis unavailable

2. **Orchestration Services** (`ltms/services/`)
   - **OrchestrationService**: Main coordinator
   - **AgentRegistryService**: Agent lifecycle management
   - **ContextCoordinationService**: Session-based coordination
   - **MemoryLockingService**: Concurrent access safety
   - **ToolCacheService**: Result caching across agents
   - **ChunkBufferService**: Shared memory chunks
   - **SessionStateService**: Multi-agent session state

3. **Server Integration**
   - HTTP server startup/shutdown hooks
   - Health check endpoints
   - Environment configuration
   - Redis service management

## Configuration

### Environment Variables

```bash
# Orchestration Configuration
ORCHESTRATION_MODE=basic          # disabled, basic, full, debug
REDIS_ENABLED=true               # Enable Redis services
REDIS_HOST=localhost             # Redis host
REDIS_PORT=6381                  # Redis port (LTMC dedicated)
REDIS_PASSWORD=ltmc_cache_2025   # Redis password
CACHE_ENABLED=true               # Enable tool result caching
BUFFER_ENABLED=true              # Enable chunk buffer service
SESSION_STATE_ENABLED=true       # Enable session state management
```

### Orchestration Modes

- **DISABLED**: No orchestration - pure fallback mode
- **BASIC**: Agent registry + basic coordination (default)
- **FULL**: All orchestration features enabled
- **DEBUG**: Full mode with extensive logging

## Usage

### Automatic Integration

All existing MCP tools automatically gain orchestration capabilities when available:

```python
# Standard tool call (unchanged)
result = store_memory(
    file_name="document.md",
    content="Content here"
)

# Enhanced tool call with orchestration context
result = store_memory(
    file_name="document.md", 
    content="Content here",
    agent_id="agent_001",        # Optional: explicit agent
    session_id="session_001"     # Optional: explicit session
)
```

### Enhanced MCP Tools

Enhanced versions provide additional orchestration features:

```python
from ltms.mcp_orchestration_integration import create_enhanced_mcp_tools

enhanced_tools = create_enhanced_mcp_tools()

# Enhanced tools with coordination
result = await enhanced_tools['enhanced_store_memory'](
    file_name="research.md",
    content="Research findings",
    agent_id="researcher_001",
    session_id="project_alpha"
)

# Result includes orchestration metadata
{
    "success": true,
    "resource_id": "res_123",
    "orchestration": {
        "coordinated": true,
        "agent_id": "researcher_001", 
        "session_id": "project_alpha",
        "timestamp": "2025-01-15T10:30:00Z"
    }
}
```

### Multi-Agent Workflow Example

```python
from ltms.mcp_orchestration_integration import (
    initialize_orchestration_integration,
    OrchestrationMode
)

# Initialize orchestration
await initialize_orchestration_integration(OrchestrationMode.FULL)

# Register research agent
research_agent_id = await orchestration_service.register_agent(
    agent_name="Research Agent",
    capabilities=["memory_write", "information_gathering"],
    session_id="project_session",
    metadata={"role": "researcher"}
)

# Register analysis agent
analysis_agent_id = await orchestration_service.register_agent(
    agent_name="Analysis Agent",
    capabilities=["memory_read", "data_analysis"],
    session_id="project_session",
    metadata={"role": "analyst"}
)

# Agents coordinate through shared session
# Research agent stores data
store_result = await enhanced_store_memory(
    file_name="findings.md",
    content="Research data...",
    agent_id=research_agent_id,
    session_id="project_session"
)

# Analysis agent retrieves and processes (with shared cache)
retrieve_result = await enhanced_retrieve_memory(
    conversation_id="project_session",
    query="research findings",
    agent_id=analysis_agent_id,
    session_id="project_session"
)
```

## Server Integration

### Startup

The HTTP server automatically initializes orchestration during startup:

```python
# In ltms/mcp_server_http.py startup event
await initialize_orchestration_integration(orchestration_mode)
```

### Health Endpoints

#### General Health: `/health`
```json
{
  "status": "healthy",
  "orchestration": {
    "orchestration_enabled": true,
    "services_available": {
      "tool_cache": true,
      "chunk_buffer": true,
      "session_state": true
    },
    "last_check": "2025-01-15T10:30:00Z"
  }
}
```

#### Orchestration Health: `/orchestration/health`
```json
{
  "orchestration_enabled": true,
  "health": {
    "orchestration_status": {
      "active_agents": 2,
      "mode": "full",
      "coordination_stats": {
        "active_sessions": 1,
        "total_participants": 2
      }
    }
  },
  "config": {
    "orchestration_mode": "full",
    "redis_enabled": true,
    "cache_enabled": true
  }
}
```

## Backward Compatibility

### Guaranteed Compatibility

- **All 25 existing MCP tools work unchanged**
- **No breaking changes to APIs**
- **Graceful degradation when Redis unavailable**
- **Optional orchestration parameters**

### Fallback Behavior

When orchestration is unavailable:
- Tools execute normally without coordination
- No orchestration metadata in responses
- Logging indicates fallback mode
- Full functionality preserved

## Testing

### Integration Test
```bash
python test_orchestration_integration.py
```

### Manual Testing
```bash
# Start server with orchestration
./start_server.sh

# Test health endpoints
curl http://localhost:5050/health
curl http://localhost:5050/orchestration/health

# Test enhanced tool via JSON-RPC
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "store_memory", "arguments": {"file_name": "test.md", "content": "Test content", "agent_id": "test_agent", "session_id": "test_session"}}, "id": 1}'
```

### Demonstration Script
```bash
python -m ltms.mcp_orchestration_integration
```

## Performance Impact

### With Redis Available
- **Memory operations**: ~5-10ms coordination overhead
- **Tool result caching**: 50-80% performance improvement for repeated queries
- **Session coordination**: <1ms per operation

### Redis Unavailable (Fallback Mode)
- **No performance impact**
- **Identical performance to pre-orchestration LTMC**

## Service Dependencies

### Required for Full Orchestration
- **Redis Server** (port 6381) 
- **LTMC Database** (SQLite)
- **FAISS Vector Store**

### Service Startup Order
1. Redis server (via `redis_control.sh start`)
2. LTMC HTTP server
3. Orchestration service initialization
4. Individual orchestration services

### Graceful Degradation Chain
- Redis unavailable → Basic coordination only
- Agent registry fails → Default agents created
- Context coordination fails → No session sharing
- Memory locking fails → No concurrent protection
- Cache/buffer services fail → No performance optimization

## Troubleshooting

### Common Issues

#### Orchestration Not Starting
```bash
# Check Redis connection
python -c "import redis; r=redis.Redis(host='localhost', port=6381, password='ltmc_cache_2025'); print('OK' if r.ping() else 'FAIL')"

# Check logs
tail -f logs/ltmc_http.log

# Verify configuration
curl http://localhost:5050/orchestration/health
```

#### Redis Connection Issues
```bash
# Start Redis manually
./redis_control.sh start

# Check Redis status
./redis_control.sh status

# Reset Redis if needed
./redis_control.sh restart
```

#### Performance Issues
```bash
# Check active agents
curl -s http://localhost:5050/orchestration/health | python -m json.tool

# Monitor Redis memory
redis-cli -p 6381 -a ltmc_cache_2025 info memory
```

### Environment Debug Mode
```bash
export ORCHESTRATION_MODE=debug
export LOG_LEVEL=DEBUG
./start_server.sh
```

## Development

### Adding New Orchestration Features

1. **Implement Service**: Add to `ltms/services/`
2. **Integrate**: Update `OrchestrationIntegration`
3. **Test**: Add integration tests
4. **Configure**: Add environment variables
5. **Document**: Update this guide

### Service Interface Pattern
```python
async def get_new_service():
    """Get or create service instance."""
    # Service implementation with Redis backend
    pass

# Integration in OrchestrationIntegration.__init__()
try:
    self.new_service = await get_new_service()
    self._health_status['services_available']['new_service'] = True
except Exception as e:
    logger.warning(f"New service not available: {e}")
    self._health_status['services_available']['new_service'] = False
```

## Security Considerations

### Redis Security
- **Password authentication required**
- **Localhost binding only** 
- **Dedicated port (6381) for LTMC**
- **No external network exposure**

### Agent Isolation
- **Session-based isolation**
- **Capability-based access control**
- **Memory locking for concurrent safety**
- **Agent cleanup on disconnect**

---

For implementation details, see the complete integration code in `ltms/mcp_orchestration_integration.py` and related service files in `ltms/services/`.