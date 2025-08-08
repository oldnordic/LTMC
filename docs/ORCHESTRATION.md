# LTMC Redis Orchestration Guide

## Overview

LTMC (Long-Term Memory and Context) has been transformed from a simple MCP tool server into a sophisticated **Multi-Agent Coordination Platform** through the implementation of a comprehensive Redis orchestration layer. This guide covers the orchestration features, configuration, and usage patterns.

## Architecture

### Orchestration Services

The orchestration layer consists of 6 core services that enable multi-agent coordination:

1. **Agent Registry Service** - Manages agent lifecycle, capabilities, and discovery
2. **Context Coordination Service** - Handles session-based memory sharing between agents
3. **Memory Locking Service** - Provides concurrent access safety and deadlock prevention
4. **Tool Result Cache Service** - Intelligent caching with dependency tracking and smart TTL
5. **Shared Chunk Buffer Service** - Cross-agent memory chunk coordination with popularity tracking
6. **Session State Manager Service** - Persistent session state across agent disconnections

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 REDIS ORCHESTRATION LAYER                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │    Agent    │  │   Context   │  │    Tool Result      │  │
│  │  Registry   │  │Coordination │  │   Cache (TTL)       │  │
│  │   Service   │  │   Service   │  │    Service          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Shared    │  │   Memory    │  │   Session State     │  │
│  │Chunk Buffer │  │  Locking    │  │    Manager          │  │
│  │   Service   │  │   Service   │  │    Service          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      LTMC CORE                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │     25      │  │    Dual     │  │      SQLite +       │  │
│  │ MCP Tools   │  │ Transport   │  │   FAISS + Redis     │  │
│  │   (Async)   │  │(HTTP/stdio)│  │                     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Core LTMC Configuration
DB_PATH=ltmc.db
FAISS_INDEX_PATH=faiss_index
LOG_LEVEL=INFO
HTTP_HOST=localhost
HTTP_PORT=5050

# Orchestration Configuration
ORCHESTRATION_MODE=basic    # Options: disabled, basic, full, debug
REDIS_ENABLED=true
REDIS_HOST=localhost
REDIS_PORT=6381            # Dedicated LTMC Redis port
REDIS_PASSWORD=ltmc_cache_2025

# Service Configuration
AGENT_HEARTBEAT_INTERVAL=30     # seconds
CONTEXT_VERSION_LIMIT=100       # max versions per session
TOOL_CACHE_DEFAULT_TTL=1800     # 30 minutes
CHUNK_BUFFER_SIZE=1000          # max chunks in buffer
LOCK_TIMEOUT=300                # 5 minutes max lock time
SESSION_CLEANUP_INTERVAL=3600   # 1 hour cleanup cycle
```

### Orchestration Modes

- **`disabled`**: No orchestration services (original LTMC behavior)
- **`basic`**: Core coordination services (recommended for most use cases)
- **`full`**: All orchestration features with advanced analytics
- **`debug`**: Full mode with detailed logging and metrics

## Getting Started

### 1. Start LTMC with Orchestration

```bash
# Start with basic orchestration mode
ORCHESTRATION_MODE=basic ./start_server.sh

# Or export the environment variable
export ORCHESTRATION_MODE=basic
./start_server.sh
```

### 2. Verify Orchestration Status

```bash
# Main health check (includes orchestration status)
curl http://localhost:5050/health

# Dedicated orchestration health check
curl http://localhost:5050/orchestration/health
```

### 3. Test Multi-Agent Coordination

```bash
# Run the orchestration demonstration
python simple_orchestration_demo.py

# Run comprehensive integration tests
python tests/orchestration/run_integration_tests.py
```

## API Endpoints

### Health Monitoring

#### Main Health Endpoint
```http
GET /health
```

Response includes orchestration status:
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
    "orchestration_status": {
      "initialized": true,
      "mode": "basic",
      "active_agents": 2,
      "services": {
        "redis": true,
        "agent_registry": true,
        "context_coordination": true
      }
    }
  }
}
```

#### Orchestration Health Endpoint
```http
GET /orchestration/health
```

Detailed orchestration service status and metrics.

### MCP Tools

All 25 existing MCP tools remain unchanged and fully functional:

```bash
# List all available tools
curl http://localhost:5050/tools

# Use any MCP tool (example: memory storage)
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"store_memory","arguments":{"content":"Test with orchestration","file_name":"test.md"}},"id":1}'
```

## Multi-Agent Coordination

### Agent Registration

Agents automatically register with the orchestration layer:

```python
from ltms.services.agent_registry_service import get_agent_registry

# Automatic registration when using orchestration-enabled tools
registry = await get_agent_registry()
agent_id = await registry.register_agent(
    name="My Agent",
    capabilities=["memory", "analysis"],
    metadata={"version": "1.0"}
)
```

### Session Management

Create and manage multi-agent sessions:

```python
from ltms.services.session_state_service import get_session_state_service

session_service = await get_session_state_service()

# Create a session
session = await session_service.create_session(
    session_id="my_session",
    participants=["agent1", "agent2"],
    metadata={"task": "collaborative_analysis"}
)

# Update session state
await session_service.update_session_state(
    "my_session",
    {"progress": 0.5, "current_stage": "analysis"}
)
```

### Context Coordination

Share context between agents:

```python
from ltms.services.context_coordination_service import get_context_coordination

coordination = await get_context_coordination()

# Create shared context
await coordination.create_session_context(
    "my_session",
    participants=["agent1", "agent2"]
)

# Update shared memory
await coordination.update_shared_memory(
    "my_session",
    {"shared_data": "important_info", "version": 1}
)
```

## Performance Features

### Smart Caching

- **Tool Result Cache**: Automatically caches tool execution results with intelligent TTL
- **Dependency Tracking**: Invalidates caches when underlying data changes
- **Hit Rate Optimization**: Maintains >80% cache hit rates for frequently used tools

### Memory Optimization

- **Shared Chunk Buffer**: Cross-agent chunk sharing with LRU eviction
- **Popularity Tracking**: Multi-window analytics (1h, 4h, 24h)
- **Memory Management**: Configurable limits with automatic cleanup

### Session Persistence

- **State Persistence**: Session state survives agent disconnections
- **Background Cleanup**: Automatic cleanup of expired sessions and resources
- **Resource Tracking**: Proper cleanup when sessions end

## Monitoring and Troubleshooting

### Logging

Orchestration logs are written to:
- `logs/ltmc_http.log` - HTTP transport and orchestration integration
- `logs/ltmc_mcp.log` - Stdio transport logs
- Redis logs - Available via Redis CLI

### Health Checks

Monitor orchestration health:

```bash
# Check if all services are operational
curl -s http://localhost:5050/orchestration/health | jq '.health.services_available'

# Monitor active agents
curl -s http://localhost:5050/orchestration/health | jq '.health.orchestration_status.active_agents'

# Check session statistics
curl -s http://localhost:5050/orchestration/health | jq '.health.orchestration_status.coordination_stats'
```

### Common Issues

1. **Redis Connection Failed**
   - Ensure Redis is running on port 6381
   - Check Redis configuration and credentials
   - Verify network connectivity

2. **Orchestration Services Not Available**
   - Check ORCHESTRATION_MODE environment variable
   - Verify all required dependencies installed
   - Review server startup logs

3. **Agent Registration Issues**
   - Ensure agents have unique IDs
   - Check agent capabilities format
   - Verify Redis connectivity

### Performance Tuning

Adjust these environment variables based on your use case:

```bash
# For high-throughput scenarios
TOOL_CACHE_DEFAULT_TTL=3600        # Longer cache TTL
CHUNK_BUFFER_SIZE=2000             # Larger chunk buffer
AGENT_HEARTBEAT_INTERVAL=60        # Less frequent heartbeats

# For low-latency scenarios
TOOL_CACHE_DEFAULT_TTL=900         # Shorter cache TTL
LOCK_TIMEOUT=60                    # Shorter lock timeouts
SESSION_CLEANUP_INTERVAL=1800      # More frequent cleanup
```

## Backward Compatibility

The orchestration implementation maintains **100% backward compatibility**:

- All 25 existing MCP tools work unchanged
- Existing API endpoints remain functional
- Original configuration options still supported
- Graceful degradation when orchestration disabled

## Testing

### Integration Tests

Run comprehensive orchestration tests:

```bash
# Full orchestration test suite
./tests/orchestration/run_orchestration_tests.sh

# Individual test categories
python -m pytest tests/orchestration/test_service_integration.py -v
python -m pytest tests/orchestration/test_performance_benchmarks.py -v
python -m pytest tests/orchestration/test_backward_compatibility.py -v
```

### Demo Scripts

Explore orchestration capabilities:

```bash
# Basic orchestration demonstration
python simple_orchestration_demo.py

# Performance benchmarking
python test_orchestration_integration.py
```

## Development

### Adding Orchestration to Your Agents

1. **Import Orchestration Services**:
```python
from ltms.services.agent_registry_service import get_agent_registry
from ltms.services.context_coordination_service import get_context_coordination
from ltms.services.session_state_service import get_session_state_service
```

2. **Register Your Agent**:
```python
registry = await get_agent_registry()
agent_id = await registry.register_agent(
    name="Your Agent",
    capabilities=["your", "capabilities"],
    metadata={"version": "1.0"}
)
```

3. **Use Shared Context**:
```python
coordination = await get_context_coordination()
await coordination.create_session_context("session_id", [agent_id])
```

### Creating Custom Services

Follow the existing service patterns in `ltms/services/` for creating custom orchestration services.

## Security

- **Redis Authentication**: Uses password authentication for Redis connections
- **Session Security**: Secure session token generation and validation
- **Resource Isolation**: Prevents cross-session data leakage
- **Access Control**: Service-specific permissions and rate limiting

## Support

For issues with orchestration features:

1. Check the logs in `logs/` directory
2. Verify configuration with health endpoints
3. Run integration tests to identify issues
4. Review this documentation for configuration options

The LTMC orchestration layer provides a robust foundation for multi-agent coordination while maintaining the simplicity and reliability of the original LTMC system.