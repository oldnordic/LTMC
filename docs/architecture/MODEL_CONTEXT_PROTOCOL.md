# LTMC Model Context Protocol (MCP) Specification

## 1. Overview

The LTMC Model Context Protocol (MCP) provides a standardized framework for multi-agent communication, coordination, and context sharing within the LTMC ecosystem. This document specifies the protocol's architecture, message formats, workflows, and error handling mechanisms.

**Protocol Version:** 1.0.0

### Key Design Principles

- **Stateless Services, Stateful Agents:** The orchestration layer is designed to be stateless, while agents maintain their own state, simplifying scalability and resilience.
- **Asynchronous Communication:** All interactions are asynchronous, enabling non-blocking operations and high performance.
- **Discoverability:** Agents can dynamically discover services, tools, and protocol versions.
- **Resilience:** The protocol includes mechanisms for handling agent failures and ensuring session integrity.

## 2. Protocol Architecture

The MCP is built upon the Redis Orchestration Layer and exposes its services to agents through a well-defined set of JSON-RPC messages.

### 2.1. Service Discovery

Upon connection, an agent's first action should be to request the service discovery information.

- **Request:**
  ```json
  {
      "jsonrpc": "2.0",
      "method": "mcp.discover",
      "id": "request-id"
  }
  ```

- **Response:**
  ```json
  {
      "jsonrpc": "2.0",
      "id": "request-id",
      "result": {
          "protocol_version": "1.0.0",
          "services": {
              "agent_registry": "/agent-registry",
              "context_coordinator": "/context-coordinator",
              "memory_locker": "/memory-locker",
              "tool_cache": "/tool-cache",
              "shared_buffer": "/shared-buffer",
              "session_manager": "/session-manager"
          }
      }
  }
  ```

### 2.2. Agent Registration and Lifecycle

Agents must register with the `AgentRegistryService` to participate in the multi-agent ecosystem.

- **Registration Request:**
  ```json
  {
      "jsonrpc": "2.0",
      "method": "agent_registry.register",
      "params": {
          "agent_id": "unique-agent-id",
          "capabilities": ["tool1", "tool2"]
      },
      "id": "request-id"
  }
  ```

- **Heartbeat:** Agents must send a heartbeat every 30 seconds to remain active.
  ```json
  {
      "jsonrpc": "2.0",
      "method": "agent_registry.heartbeat",
      "params": { "agent_id": "unique-agent-id" },
      "id": "request-id"
  }
  ```

- **Unregistration:**
  ```json
  {
      "jsonrpc": "2.0",
      "method": "agent_registry.unregister",
      "params": { "agent_id": "unique-agent-id" },
      "id": "request-id"
  }
  ```

### 2.3. Context Coordination

The `ContextCoordinationService` manages shared context for multi-agent sessions.

- **Context Propagation:** Context is propagated using a publish/subscribe model. Agents subscribe to a session's context updates.
  - **Subscription Request:**
    ```json
    {
        "jsonrpc": "2.0",
        "method": "context_coordinator.subscribe",
        "params": { "session_id": "session-id" },
        "id": "request-id"
    }
    ```
  - **Context Update Message (Pushed from server):**
    ```json
    {
        "jsonrpc": "2.0",
        "method": "context_coordinator.update",
        "params": {
            "session_id": "session-id",
            "update": { "key": "new_value" }
        }
    }
    ```

- **Conflict Resolution:** The `MemoryLockingService` is used to prevent conflicts. Before updating the context, an agent must acquire a lock on the session's context.

### 2.4. Inter-Agent Communication

Direct inter-agent communication is not part of the core MCP. Agents should communicate indirectly through the shared context. This design choice enhances scalability and simplifies the protocol.

## 3. Error Handling and Resilience

- **Agent Disconnection:** If an agent fails to send a heartbeat, the `AgentRegistryService` will mark it as "inactive". The `SessionManagerService` will then notify other agents in the session of the disconnection.
- **Error Response Format:**
  ```json
  {
      "jsonrpc": "2.0",
      "id": "request-id",
      "error": {
          "code": -32602,
          "message": "Invalid params",
          "data": { "details": "..." }
      }
  }
  ```

## 4. Agent Onboarding Workflow

1.  **Connect:** The agent establishes a connection to the LTMC server (HTTP or stdio).
2.  **Discover:** The agent calls `mcp.discover` to get the protocol version and service endpoints.
3.  **Register:** The agent calls `agent_registry.register` to join the ecosystem.
4.  **Create/Join Session:** The agent uses the `SessionManagerService` to create a new session or join an existing one.
5.  **Subscribe to Context:** The agent subscribes to the session's context updates.
6.  **Start Heartbeating:** The agent begins sending heartbeats every 30 seconds.
