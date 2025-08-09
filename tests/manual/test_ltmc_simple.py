#\!/usr/bin/env python3
"""Simple test for LTMC MCP Server stdio transport tool execution."""

import json
import subprocess
import sys
import time
from datetime import datetime

def test_simple_tool():
    """Test a single tool execution with verbose debugging."""
    
    print("=== LTMC MCP Server Simple Tool Test ===")
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
        
        # Give server time to initialize
        time.sleep(2)
        
    except Exception as e:
        print(f"❌ Failed to start LTMC MCP server: {e}")
        return False
    
    def send_request_with_debug(request_data, expect_response=True):
        """Send MCP request with detailed debugging."""
        request_json = json.dumps(request_data) + '\n'
        print(f"→ Sending: {request_json.strip()}")
        
        try:
            process.stdin.write(request_json)
            process.stdin.flush()
            print("✅ Request sent successfully")
            
            if expect_response:
                # Read response with timeout
                print("⏳ Waiting for response...")
                time.sleep(1)  # Give server time to process
                
                # Check if process is still running
                if process.poll() is not None:
                    print("❌ Server process terminated unexpectedly")
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        print(f"Server stderr: {stderr_output}")
                    return None
                
                # Try to read response
                response_line = process.stdout.readline()
                if response_line:
                    response = json.loads(response_line.strip())
                    print(f"← Received: {json.dumps(response, indent=2)}")
                    return response
                else:
                    print("❌ No response received (empty line)")
                    
                    # Check for stderr output
                    stderr_output = process.stderr.read()
                    if stderr_output:
                        print(f"Server stderr: {stderr_output}")
                    
                    return None
            else:
                print("✅ Notification sent (no response expected)")
                return True
                
        except Exception as e:
            print(f"❌ Error during communication: {e}")
            # Check stderr for additional info
            try:
                stderr_output = process.stderr.read()
                if stderr_output:
                    print(f"Server stderr: {stderr_output}")
            except:
                pass
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
                    "roots": {"listChanged": True},
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "ltmc-simple-test",
                    "version": "1.0.0"
                }
            }
        }
        
        init_response = send_request_with_debug(init_request)
        if not init_response or 'result' not in init_response:
            print("❌ MCP initialization failed")
            return False
        
        print("✅ MCP initialization successful")
        
        # Test 2: Send initialized notification
        print("\n3. Sending initialized notification...")
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        send_request_with_debug(initialized_notification, expect_response=False)
        time.sleep(0.5)  # Give server time to process notification
        
        # Test 3: Simple tool call
        print("\n4. Testing simple tool call...")
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "redis_health_check",
                "arguments": {}
            }
        }
        
        tool_response = send_request_with_debug(tool_request)
        if tool_response and 'result' in tool_response:
            print("✅ Tool call successful")
            return True
        else:
            print("❌ Tool call failed")
            return False
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False
    
    finally:
        # Clean up
        print("\n5. Cleaning up...")
        try:
            process.terminate()
            process.wait(timeout=5)
            print("✅ LTMC MCP server process terminated")
        except:
            process.kill()
            print("✅ LTMC MCP server process killed")

if __name__ == "__main__":
    success = test_simple_tool()
    sys.exit(0 if success else 1)
EOF < /dev/null
