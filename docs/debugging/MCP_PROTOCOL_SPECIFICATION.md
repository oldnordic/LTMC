# Official MCP Protocol Specification Research

## Protocol Overview
The Model Context Protocol (MCP) is an open protocol that standardizes how applications provide context to Large Language Models (LLMs). It functions as a "USB-C port for AI applications" enabling standardized connections between AI models and various data sources.

## Core Protocol Characteristics

### Version Management
- **Current Version**: `2025-06-18`
- **Format**: String-based identifiers in `YYYY-MM-DD` format
- **Versioning Strategy**: Date indicates last backwards-incompatible change
- **Revision States**: Draft, Current, Final

### Protocol Primitives
The MCP specification defines three core interaction primitives:

1. **Prompts**: User-controlled interactive templates
2. **Resources**: Application-controlled contextual data (similar to GET requests)
3. **Tools**: Model-controlled action functions (can have side effects)

## Technical Implementation Details

### Transport Layer Support
MCP supports multiple transport mechanisms:
- **stdio** (standard input/output) - Used by our current binary
- **Server-Sent Events (SSE)**
- **Streamable HTTP**
- **Direct ASGI server mounting**

### Message Format
- **Base Protocol**: JSON-RPC 2.0 
- **Schema Definition**: TypeScript-first with JSON Schema for wider compatibility
- **Structure**: Standard JSON-RPC request/response pattern

### Server Implementation Patterns

#### FastMCP (High-Level)
- Decorator-based server with automatic routing
- Automatic schema generation from type annotations
- Simplified development experience

#### Low-Level Server (Official SDK)
- Granular protocol control
- Manual handler registration
- Direct protocol message handling

## Critical Technical Features

### Initialization and Lifecycle
- **Version Negotiation**: During initialization between client and server
- **Capability Negotiation**: Both parties declare supported features
- **Session Management**: Single agreed version per session
- **Error Handling**: Protocol defines failure modes for version mismatch

### Schema Generation
- **Automatic Type Introspection**: From Python type annotations
- **Structured Output Validation**: For tools and responses
- **Flexible Type Support**: Pydantic models, TypedDicts, Dataclasses

### Advanced Features
- **Progress Reporting**: For long-running operations
- **OAuth Authentication**: Built-in authentication support
- **Lifespan Management**: Resource initialization and cleanup
- **Argument Completion**: Dynamic suggestion support

## Protocol Compliance Requirements

### JSON-RPC 2.0 Adherence
- **Message Structure**: Must follow JSON-RPC 2.0 specification
- **Method Identification**: Standardized method naming
- **Parameter Passing**: Structured parameter objects
- **Error Responses**: Standardized error codes and formats

### Transport Specific Requirements

#### Stdio Transport (Our Focus)
- **Message Framing**: JSON messages over stdin/stdout
- **Buffering**: Proper line-buffering for message boundaries
- **Process Communication**: Standard process stdin/stdout handling
- **Initialization**: Handshake via stdio message exchange

## FastMCP vs Official SDK Differences

### Architecture Differences
| Aspect | FastMCP | Official MCP SDK |
|--------|---------|------------------|
| **Design Philosophy** | High-level, decorator-based | Low-level, explicit control |
| **Schema Generation** | Automatic from decorators | Manual or type-based |
| **Protocol Handling** | Abstracted away | Direct JSON-RPC handling |
| **Message Format** | FastMCP-specific adaptations | Strict MCP specification compliance |
| **Initialization** | Simplified handshake | Full protocol negotiation |

### Potential Incompatibilities
1. **Message Format Variations**: FastMCP may adapt messages for ease of use
2. **Handshake Differences**: FastMCP might simplify initialization sequence  
3. **Schema Structure**: Different tool/resource definition formats
4. **Error Handling**: Varying error response formats
5. **Capability Declaration**: Different capability negotiation patterns

## Claude Code MCP Client Expectations

Based on research, Claude Code as an MCP client likely expects:

1. **Strict Protocol Compliance**: Adherence to official MCP specification
2. **Standard JSON-RPC 2.0**: Exact message format compliance
3. **Proper Initialization**: Full version and capability negotiation
4. **Standard Tool Schema**: Official MCP tool definition format
5. **Stdio Transport**: Correct stdin/stdout message handling

## Investigation Hypothesis

**Root Cause**: Our FastMCP binary uses FastMCP's adapted protocol format, while Claude Code expects strict official MCP protocol compliance. The connection fails during the initial handshake because:

1. **Version Negotiation**: FastMCP may not properly negotiate MCP version `2025-06-18`
2. **Message Format**: JSON-RPC messages don't match Claude Code's expectations
3. **Capability Declaration**: FastMCP doesn't properly declare server capabilities
4. **Tool Registration**: Schema format differs from official MCP specification

## Next Investigation Steps

1. **Compare Message Formats**: Analyze exact JSON-RPC differences between implementations
2. **Test Official SDK**: Create minimal server with official MCP Python SDK
3. **Protocol Debugging**: Log message exchanges to identify failure point
4. **Schema Analysis**: Compare tool registration formats between implementations

## Research Sources
- MCP Protocol Overview: https://modelcontextprotocol.io/introduction
- MCP Specification Repository: https://github.com/modelcontextprotocol/specification  
- Official MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Protocol Version: 2025-06-18 (Current)

---
*Research Status*: ✅ Completed - Ready for Phase 2 Testing  
*Key Finding*: FastMCP uses adapted protocol format, Claude Code expects strict MCP compliance