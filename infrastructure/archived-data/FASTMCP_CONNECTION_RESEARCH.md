# FastMCP Connection Research

## Overview
FastMCP is a Python library that provides a simplified way to build MCP (Model Context Protocol) servers with multiple transport options and flexible client-server architecture.

## Transport Protocols

### 1. STDIO (Default - Our Current Binary Type)
- **Best for**: Local tools and command-line scripts
- **Implementation**: Simplest approach with minimal configuration
- **Usage**: Default when no transport is specified
- **Connection**: Uses standard input/output for MCP communication

### 2. Streamable HTTP
- **Best for**: Web deployments and remote access
- **Configuration**: `mcp.run(transport="http", host="127.0.0.1", port=8000, path="/mcp")`
- **Features**: Configurable host, port, and path parameters

### 3. Server-Sent Events (SSE)
- **Best for**: Compatibility with existing SSE clients
- **Configuration**: `mcp.run(transport="sse", host="127.0.0.1", port=8000)`
- **Features**: Real-time streaming capabilities

## Client Connection Architecture

### Multi-Server Support
- FastMCP supports connecting to multiple servers through a unified client
- Can use standard MCP configuration format
- Enables access to tools and resources across different servers

### Connection Methods
- **Direct Instance**: For in-memory testing via direct server instance connection
- **Standard MCP Config**: Uses established MCP configuration patterns
- **Automatic Detection**: Transport protocol auto-detection capabilities

## Key Technical Features

### Connection Capabilities
- Automatic transport detection and negotiation
- Flexible server and client configuration options
- Support for both local and remote server interactions
- Efficient testing mechanisms for development

### Developer Experience
- Emphasizes "Pythonic" approach to building MCP servers
- Focus on simplicity and ease of implementation
- Reduced boilerplate code compared to raw MCP implementations

## Potential Issues for Binary Implementation

### STDIO Transport Considerations
Since our binary uses STDIO transport (default), potential connection issues could be:

1. **Input/Output Handling**: Improper stdin/stdout management in binary
2. **JSON-RPC Protocol**: FastMCP's JSON-RPC implementation vs. direct protocol
3. **Process Communication**: Binary process communication with MCP clients
4. **Buffer Management**: Stdin/stdout buffering in binary execution context

### Debugging Approach
1. Test FastMCP STDIO transport in development environment
2. Compare binary stdio behavior vs. direct Python execution
3. Verify JSON-RPC message format compliance
4. Check process communication and buffering issues

## Official MCP Python SDK Research

### Key Architecture Components
- **Official MCP Implementation**: Standard protocol for LLM context provision
- **Multiple Transports**: stdio, SSE, and Streamable HTTP support
- **Protocol Compliance**: Robust message and lifecycle event handling
- **Type Safety**: Automatic schema generation and type validation

### Core MCP Concepts
1. **Resources**: Data endpoints (similar to GET requests)
2. **Tools**: Action-enabling functions with side effects allowed
3. **Prompts**: Reusable interaction templates

### Server Implementation Pattern
```python
from fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

### Structured Output Support
- Pydantic models
- TypedDicts  
- Dataclasses
- Dictionaries
- Primitive types
- Generic types

### Unique Features vs FastMCP
- **Automatic Schema Generation**: Built-in type introspection
- **Progress Reporting**: For long-running tasks
- **Flexible Context Injection**: Advanced context management
- **Official Protocol Compliance**: Guaranteed MCP standard adherence

### Potential Binary Connection Issues

#### FastMCP vs Official SDK Differences
1. **Protocol Implementation**: FastMCP may have different JSON-RPC handling
2. **Stdio Transport**: Official SDK might have stricter stdio requirements
3. **Schema Generation**: Different approaches to tool schema creation
4. **Message Lifecycle**: Varying handling of MCP protocol events

#### Binary-Specific Issues
1. **Import Path Resolution**: Binary may not resolve MCP modules correctly
2. **Stdio Buffering**: Different buffering behavior in binary vs. Python
3. **Protocol Handshake**: MCP initialization sequence differences
4. **Schema Registration**: Tool registration timing and format issues

## Claude Code MCP Client Requirements

### Transport Protocol Expectations
Claude Code (the MCP client) supports three transport types:

1. **Stdio Servers (Our Current Binary Type)**
   - Run as local processes on the machine
   - Ideal for tools needing direct system access
   - Command format: `claude mcp add <name> <command> [args...]`

2. **Remote SSE (Server-Sent Events)**
   - Real-time streaming connections
   - Command: `claude mcp add --transport sse <name> <url>`

3. **Remote HTTP Servers**
   - Standard request/response patterns
   - Command: `claude mcp add --transport http <name> <url>`

### Claude Code Configuration System
- **Three Scopes**: local, project, and user configuration
- **Environment Variables**: Supports expansion in configuration
- **OAuth 2.0**: Authentication support for remote servers
- **Management Commands**: `claude mcp list`, `claude mcp get`, `claude mcp remove`
- **Security**: "/mcp command for authentication, secure token storage

### Critical Discovery: Protocol Compatibility Issue

**THE PROBLEM**: Claude Code expects **standard MCP protocol compliance** for stdio servers, but our binary uses FastMCP which may have different:

1. **Message Format**: Claude Code expects specific JSON-RPC structure
2. **Handshake Protocol**: Standard MCP initialization sequence
3. **Tool Schema**: Official MCP tool definition format
4. **Stdio Communication**: Exact stdin/stdout message exchange pattern

### Why Our FastMCP Binary Fails to Connect

Claude Code is the MCP client trying to communicate with our FastMCP binary via stdio transport. The connection fails because:

1. **Protocol Mismatch**: FastMCP != Standard MCP protocol that Claude Code expects
2. **Message Format**: Claude Code sends standard MCP messages, FastMCP responds in different format
3. **Handshake Failure**: Initial connection negotiation doesn't match Claude Code's expectations
4. **Tool Registration**: Schema format differences prevent proper tool discovery

### Next Debugging Steps
1. Test if our binary works with official MCP Python SDK instead of FastMCP
2. Compare FastMCP message format vs. standard MCP protocol
3. Check if Claude Code has specific stdio transport requirements
4. Verify JSON-RPC message structure compatibility

## Research Sources
- FastMCP: https://github.com/jlowin/fastmcp
- Official MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Claude Code MCP Docs: https://docs.anthropic.com/en/docs/claude-code/mcp
- **Critical**: Claude Code is the MCP client - protocol compatibility is the issue