#!/usr/bin/env python3
"""LTMC STDIO Proxy for P1 Response Format Standardization.

P1 Implementation: Provides STDIO transport with direct JSON responses
- Accepts MCP JSON-RPC requests via STDIN
- Forwards requests to HTTP server 
- Returns unwrapped direct JSON responses via STDOUT
- Maintains protocol compliance while ensuring transport parity
"""

import sys
import json
import logging
import requests
from typing import Dict, Any
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup stderr-only logging for stdio transport compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr,
    force=True
)
logger = logging.getLogger(__name__)

class MCPStdioProxy:
    """P1 STDIO proxy that provides unwrapped JSON responses."""
    
    def __init__(self, http_server_url: str = "http://localhost:5050"):
        self.http_url = http_server_url
        self.initialized = False
        
    def unwrap_http_response(self, http_response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract direct tool result from HTTP JSON-RPC response.
        
        Args:
            http_response: HTTP server JSON-RPC response
            
        Returns:
            Direct tool result for consistent STDIO format
        """
        if "result" in http_response and http_response["result"] is not None:
            return http_response["result"]
        elif "error" in http_response and http_response["error"] is not None:
            return {
                "success": False,
                "error": http_response["error"].get("message", "Unknown error"),
                "error_code": http_response["error"].get("code", -1)
            }
        return {"success": False, "error": "Invalid response format"}
        
    def handle_request(self, request_line: str) -> Dict[str, Any]:
        """Process single MCP request and return unwrapped response.
        
        Args:
            request_line: JSON-RPC request string
            
        Returns:
            Direct JSON response (unwrapped)
        """
        try:
            request_data = json.loads(request_line.strip())
            
            # Handle initialization
            if request_data.get("method") == "initialize":
                self.initialized = True
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "experimental": {},
                        "prompts": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "tools": {"listChanged": False}
                    },
                    "serverInfo": {
                        "name": "LTMC STDIO Proxy",
                        "version": "1.0.0-p1"
                    }
                }
            
            # Handle initialized notification (no response needed)
            if request_data.get("method") == "notifications/initialized":
                return None
                
            # Forward other requests to HTTP server
            if not self.initialized:
                return {
                    "success": False,
                    "error": "Server not initialized",
                    "error_code": -32002
                }
                
            # Forward to HTTP server
            response = requests.post(
                f"{self.http_url}/jsonrpc",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                http_response = response.json()
                return self.unwrap_http_response(http_response)
            else:
                return {
                    "success": False,
                    "error": f"HTTP server error: {response.status_code}",
                    "error_code": -32603
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return {
                "success": False,
                "error": f"Invalid JSON: {str(e)}",
                "error_code": -32700
            }
        except requests.RequestException as e:
            logger.error(f"HTTP request error: {e}")
            return {
                "success": False,
                "error": f"Server connection error: {str(e)}",
                "error_code": -32603
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "success": False,
                "error": f"Internal error: {str(e)}",
                "error_code": -32603
            }
    
    def run(self):
        """Run P1 STDIO proxy server."""
        logger.info("P1: Starting LTMC STDIO Proxy with response unwrapping")
        
        try:
            # Check if HTTP server is available
            health_response = requests.get(f"{self.http_url}/health", timeout=5)
            if health_response.status_code != 200:
                raise Exception(f"HTTP server not available at {self.http_url}")
                
            logger.info(f"P1: Connected to HTTP server at {self.http_url}")
            
            # Process requests from STDIN
            for line in sys.stdin:
                if line.strip():
                    response = self.handle_request(line)
                    if response is not None:  # Skip notifications
                        print(json.dumps(response), flush=True)
                        
        except KeyboardInterrupt:
            logger.info("P1: STDIO proxy stopped by user")
        except Exception as e:
            logger.error(f"P1: STDIO proxy error: {e}")
            sys.exit(1)

def main():
    """P1 Entry point for STDIO proxy server."""
    proxy = MCPStdioProxy()
    proxy.run()

if __name__ == "__main__":
    main()