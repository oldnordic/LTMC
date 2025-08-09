#!/usr/bin/env python3
"""Simple debugging test for LTMC stdio transport."""

import json
import subprocess
import sys
import time

def test_simple():
    """Test basic MCP functionality."""
    
    print("=== Simple LTMC MCP Test ===")
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, 'ltmc_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )
    
    try:
        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            }
        }
        
        print("Sending init...")
        process.stdin.write(json.dumps(init_req) + '\n')
        process.stdin.flush()
        
        # Wait and read response
        time.sleep(2)
        response = process.stdout.readline()
        print(f"Init response: {response}")
        
        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        
        print("Sending notification...")
        process.stdin.write(json.dumps(notif) + '\n')
        process.stdin.flush()
        time.sleep(1)
        
        # Test simple tool call - using redis_health_check (no dependencies)
        tool_req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "redis_health_check",
                "arguments": {}
            }
        }
        
        print("Sending tool call...")
        process.stdin.write(json.dumps(tool_req) + '\n')
        process.stdin.flush()
        
        # Wait and read tool response
        time.sleep(3)
        tool_response = process.stdout.readline()
        print(f"Tool response: {tool_response}")
        
        if tool_response:
            print("✅ Tool call got response")
        else:
            print("❌ No tool response")
            
            # Check if process died
            if process.poll() is not None:
                stderr = process.stderr.read()
                print(f"Process died. Stderr: {stderr}")
        
    finally:
        process.terminate()
        process.wait()
        
if __name__ == "__main__":
    test_simple()