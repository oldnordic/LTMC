#!/usr/bin/env python3
"""
Manual MCP Server - PyInstaller Compatible
==========================================

Custom MCP protocol implementation that works with PyInstaller binaries.
Bypasses FastMCP stdio issues by implementing MCP protocol directly.
"""

import json
import sys
import asyncio
from typing import Dict, Any, List, Optional

class ManualMCPServer:
    """Manual MCP server implementation that works with PyInstaller."""
    
    def __init__(self, name: str):
        self.name = name
        self.tools = {}
    
    def tool(self, func_name: Optional[str] = None):
        """Decorator to register MCP tools."""
        def decorator(func):
            tool_name = func_name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP JSON-RPC request."""
        try:
            method = request.get("method", "")
            params = request.get("params", {})
            request_id = request.get("id", 1)
            
            if method == "tools/list":
                # Return list of available tools
                tool_list = []
                for tool_name, tool_func in self.tools.items():
                    tool_info = {
                        "name": tool_name,
                        "description": tool_func.__doc__ or f"Tool: {tool_name}",
                        "inputSchema": {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    }
                    tool_list.append(tool_info)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tool_list
                    }
                }
            
            elif method == "tools/call":
                # Call a specific tool
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name](**tool_args)
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result, indent=2)
                                    }
                                ]
                            }
                        }
                    except Exception as e:
                        return {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"Tool execution failed: {str(e)}"
                            }
                        }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
            
            elif method == "initialize":
                # MCP initialization
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": self.name,
                            "version": "1.0.0"
                        }
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
    
    def run(self):
        """Run the MCP server using direct stdio."""
        print(f"Manual MCP Server '{self.name}' starting...", file=sys.stderr)
        print(f"Available tools: {list(self.tools.keys())}", file=sys.stderr)
        
        try:
            while True:
                try:
                    # Read JSON-RPC request from stdin
                    line = sys.stdin.readline()
                    if not line:
                        break
                    
                    request = json.loads(line.strip())
                    
                    # Handle the request
                    response = asyncio.run(self.handle_request(request))
                    
                    # Send response to stdout
                    print(json.dumps(response), flush=True)
                
                except json.JSONDecodeError:
                    # Invalid JSON, send error response
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                
                except KeyboardInterrupt:
                    print("Server shutdown requested", file=sys.stderr)
                    break
                
                except Exception as e:
                    print(f"Server error: {e}", file=sys.stderr)
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal server error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
        
        except Exception as e:
            print(f"Fatal server error: {e}", file=sys.stderr)
            sys.exit(1)