"""LTMC Client Utilities for P1 MCP Protocol Handling.

P1 Implementation: Client Library Enhancement
- Provides utilities for handling both HTTP and STDIO transports
- Automatic MCP protocol unwrapping for consistent client experience  
- Transport-agnostic client interface with format normalization
"""

import json
import requests
import subprocess
from typing import Dict, Any, Optional, Union, Literal
from pathlib import Path


class MCPClientError(Exception):
    """Exception raised for MCP client errors."""
    pass


class LTMCClient:
    """P1 Enhanced LTMC client with dual transport support."""
    
    def __init__(
        self,
        transport: Literal["http", "stdio"] = "http",
        http_url: str = "http://localhost:5050",
        stdio_server_path: Optional[str] = None
    ):
        """Initialize LTMC client with P1 transport support.
        
        Args:
            transport: Transport type ("http" or "stdio")
            http_url: URL for HTTP transport
            stdio_server_path: Path to STDIO server executable
        """
        self.transport = transport
        self.http_url = http_url
        self.stdio_server_path = stdio_server_path or "ltmc_stdio_proxy.py"
        self.request_id = 0
        self.initialized = False
        
        if transport == "stdio":
            self._start_stdio_server()
            self._initialize_stdio()
    
    def _get_next_id(self) -> int:
        """Get next request ID."""
        self.request_id += 1
        return self.request_id
    
    def _start_stdio_server(self):
        """Start STDIO server process."""
        try:
            server_path = Path(__file__).parent / self.stdio_server_path
            self.stdio_process = subprocess.Popen(
                ["python3", str(server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
        except Exception as e:
            raise MCPClientError(f"Failed to start STDIO server: {e}")
    
    def _initialize_stdio(self):
        """Initialize STDIO server with MCP protocol."""
        try:
            # Send initialization request
            init_request = {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "ltmc-client-p1", "version": "1.0.0"}
                },
                "id": self._get_next_id()
            }
            
            self.stdio_process.stdin.write(json.dumps(init_request) + "\n")
            self.stdio_process.stdin.flush()
            
            # Read initialization response
            response_line = self.stdio_process.stdout.readline()
            if response_line:
                response_data = json.loads(response_line.strip())
                if "protocolVersion" in response_data:
                    # Send initialized notification
                    initialized_notification = {
                        "jsonrpc": "2.0",
                        "method": "notifications/initialized", 
                        "params": {}
                    }
                    self.stdio_process.stdin.write(json.dumps(initialized_notification) + "\n")
                    self.stdio_process.stdin.flush()
                    self.initialized = True
                else:
                    raise MCPClientError(f"Invalid initialization response: {response_data}")
            else:
                raise MCPClientError("No initialization response received")
                
        except Exception as e:
            raise MCPClientError(f"STDIO initialization failed: {e}")
    
    def _send_http_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via HTTP transport with P1 unwrapping.
        
        Args:
            method: MCP method name
            params: Method parameters
            
        Returns:
            Unwrapped direct JSON response
        """
        try:
            request_data = {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": self._get_next_id()
            }
            
            response = requests.post(
                f"{self.http_url}/jsonrpc",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # P1: Unwrap HTTP JSON-RPC response
                if "result" in response_data:
                    return response_data["result"]
                elif "error" in response_data:
                    raise MCPClientError(f"Server error: {response_data['error']}")
                else:
                    raise MCPClientError("Invalid response format")
            else:
                raise MCPClientError(f"HTTP error: {response.status_code}")
                
        except requests.RequestException as e:
            raise MCPClientError(f"HTTP request failed: {e}")
    
    def _send_stdio_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via STDIO transport (already unwrapped).
        
        Args:
            method: MCP method name
            params: Method parameters
            
        Returns:
            Direct JSON response (P1 format)
        """
        if not self.initialized:
            raise MCPClientError("STDIO client not initialized")
            
        try:
            request_data = {
                "jsonrpc": "2.0", 
                "method": method,
                "params": params,
                "id": self._get_next_id()
            }
            
            self.stdio_process.stdin.write(json.dumps(request_data) + "\n")
            self.stdio_process.stdin.flush()
            
            response_line = self.stdio_process.stdout.readline()
            if response_line:
                # P1: STDIO proxy already returns unwrapped format
                return json.loads(response_line.strip())
            else:
                raise MCPClientError("No response received from STDIO server")
                
        except Exception as e:
            raise MCPClientError(f"STDIO request failed: {e}")
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """P1 Transport-agnostic tool calling with consistent response format.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            
        Returns:
            Direct JSON tool result (consistent across transports)
        """
        params = {"name": tool_name, "arguments": arguments}
        
        if self.transport == "http":
            return self._send_http_request("tools/call", params)
        elif self.transport == "stdio":
            return self._send_stdio_request("tools/call", params)
        else:
            raise MCPClientError(f"Unsupported transport: {self.transport}")
    
    # Convenience methods for common LTMC operations
    
    def store_memory(self, content: str, file_name: str, resource_type: str = "document") -> Dict[str, Any]:
        """Store content in LTMC memory."""
        return self.call_tool("store_memory", {
            "content": content,
            "file_name": file_name, 
            "resource_type": resource_type
        })
    
    def retrieve_memory(self, query: str, conversation_id: str, top_k: int = 3) -> Dict[str, Any]:
        """Retrieve content from LTMC memory."""
        return self.call_tool("retrieve_memory", {
            "query": query,
            "conversation_id": conversation_id,
            "top_k": top_k
        })
    
    def log_chat(self, content: str, conversation_id: str, role: str = "user") -> Dict[str, Any]:
        """Log chat message to LTMC."""
        return self.call_tool("log_chat", {
            "content": content,
            "conversation_id": conversation_id,
            "role": role
        })
    
    def add_todo(self, title: str, description: str, priority: str = "medium") -> Dict[str, Any]:
        """Add todo item to LTMC."""
        return self.call_tool("add_todo", {
            "title": title,
            "description": description,
            "priority": priority
        })
    
    def get_code_patterns(self, query: str, result_filter: str = None, top_k: int = 5) -> Dict[str, Any]:
        """Get code patterns from LTMC."""
        return self.call_tool("get_code_patterns", {
            "query": query,
            "result_filter": result_filter,
            "top_k": top_k
        })
    
    def close(self):
        """Clean up client resources."""
        if hasattr(self, 'stdio_process'):
            self.stdio_process.terminate()
            self.stdio_process.wait()


def create_client(transport: Literal["http", "stdio"] = "http", **kwargs) -> LTMCClient:
    """P1 Factory function for creating LTMC clients.
    
    Args:
        transport: Transport type ("http" or "stdio")
        **kwargs: Additional client configuration
        
    Returns:
        Configured LTMC client with P1 enhancements
    """
    return LTMCClient(transport=transport, **kwargs)


# P1 Legacy support functions for existing code
def unwrap_mcp_response(response: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """P1 Utility to unwrap MCP JSON-RPC responses to direct format.
    
    Args:
        response: MCP response (dict or JSON string)
        
    Returns:
        Unwrapped direct JSON result
    """
    if isinstance(response, str):
        response = json.loads(response)
    
    if isinstance(response, dict):
        if "jsonrpc" in response and "result" in response:
            return response["result"]
        elif "error" in response:
            return {
                "success": False,
                "error": response["error"].get("message", "Unknown error"),
                "error_code": response["error"].get("code", -1)
            }
    
    return response


def normalize_response_format(response: Dict[str, Any]) -> Dict[str, Any]:
    """P1 Normalize response format for consistent client experience.
    
    Args:
        response: Response from any transport
        
    Returns:
        Normalized response format
    """
    # Already normalized if contains success field or standard tool result
    if "success" in response or "message" in response or "resource_id" in response:
        return response
    
    # Try to unwrap if it looks like MCP format
    return unwrap_mcp_response(response)