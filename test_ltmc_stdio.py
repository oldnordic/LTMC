#!/usr/bin/env python3
"""Test script for LTMC MCP Server stdio transport."""

import json
import subprocess
import sys
import time
from datetime import datetime

def test_mcp_stdio():
    """Test LTMC MCP server stdio transport functionality."""
    
    print("=== LTMC MCP Server Stdio Transport Test ===")
    print(f"Test started at: {datetime.now()}")
    
    # Start the LTMC MCP server process
    print("\n1. Starting LTMC MCP server stdio transport...")
    try:
        process = subprocess.Popen(
            [sys.executable, 'ltmc_mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        print("✅ LTMC MCP server process started")
    except Exception as e:
        print(f"❌ Failed to start LTMC MCP server: {e}")
        return False
    
    def send_request(request_data):
        """Send MCP request and get response."""
        request_json = json.dumps(request_data) + '\n'
        print(f"→ Sending: {request_json.strip()}")
        
        try:
            process.stdin.write(request_json)
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                print(f"← Received: {json.dumps(response, indent=2)}")
                return response
            else:
                print("❌ No response received")
                return None
        except Exception as e:
            print(f"❌ Error during communication: {e}")
            return None
    
    try:
        # Test 1: Initialize connection
        print("\n2. Testing MCP initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "roots": {
                        "listChanged": True
                    },
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "ltmc-test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = send_request(init_request)
        if init_response and 'result' in init_response:
            print("✅ MCP initialization successful")
        else:
            print("❌ MCP initialization failed")
            return False
        
        # Test 2: List available tools
        print("\n3. Testing tools/list...")
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        tools_response = send_request(list_tools_request)
        if tools_response and 'result' in tools_response and 'tools' in tools_response['result']:
            tools = tools_response['result']['tools']
            print(f"✅ Found {len(tools)} LTMC tools")
            print("Available tools:")
            for tool in tools[:5]:  # Show first 5 tools
                print(f"  - {tool['name']}: {tool['description']}")
            if len(tools) > 5:
                print(f"  ... and {len(tools) - 5} more tools")
        else:
            print("❌ Failed to list tools")
            return False
        
        # Test 3: Test store_memory tool
        print("\n4. Testing store_memory tool...")
        store_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "store_memory",
                "arguments": {
                    "content": f"LTMC Stdio Test - Memory storage test at {datetime.now()}",
                    "file_name": f"stdio_test_{int(time.time())}.md",
                    "resource_type": "document"
                }
            }
        }
        
        store_response = send_request(store_request)
        if store_response and 'result' in store_response:
            print("✅ store_memory tool working")
        else:
            print("❌ store_memory tool failed")
            return False
        
        # Test 4: Test retrieve_memory tool
        print("\n5. Testing retrieve_memory tool...")
        retrieve_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "retrieve_memory",
                "arguments": {
                    "query": "stdio test",
                    "conversation_id": "stdio_test_session",
                    "top_k": 3
                }
            }
        }
        
        retrieve_response = send_request(retrieve_request)
        if retrieve_response and 'result' in retrieve_response:
            print("✅ retrieve_memory tool working")
        else:
            print("❌ retrieve_memory tool failed")
            return False
        
        # Test 5: Test log_chat tool
        print("\n6. Testing log_chat tool...")
        log_chat_request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "log_chat",
                "arguments": {
                    "content": "Testing LTMC stdio transport - chat logging functionality",
                    "conversation_id": f"stdio_test_{int(time.time())}",
                    "role": "system"
                }
            }
        }
        
        log_response = send_request(log_chat_request)
        if log_response and 'result' in log_response:
            print("✅ log_chat tool working")
        else:
            print("❌ log_chat tool failed")
            return False
        
        print("\n=== All stdio transport tests passed! ✅ ===")
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    finally:
        # Clean up
        print("\n7. Cleaning up...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ LTMC MCP server process terminated")
        except:
            process.kill()
            print("✅ LTMC MCP server process killed")

if __name__ == "__main__":
    success = test_mcp_stdio()
    sys.exit(0 if success else 1)