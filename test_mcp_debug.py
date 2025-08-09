#!/usr/bin/env python3
"""Debug MCP server tool execution issues."""

import json
import subprocess
import sys
import time

def debug_tool_execution():
    """Debug tool execution with detailed output."""
    print("=== Debugging LTMC MCP Tool Execution ===")
    
    try:
        process = subprocess.Popen(
            ["python", "/home/feanor/Projects/lmtc/ltmc_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
            cwd="/home/feanor/Projects/lmtc"
        )
        
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "debug-test", "version": "1.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\n')
        process.stdin.flush()
        time.sleep(1)
        init_response = process.stdout.readline()
        print(f"Init response: {init_response[:200]}...")
        
        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(notif) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Simple tool call with minimal args
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "redis_health_check",
                "arguments": {}
            }
        }
        
        print("Sending redis_health_check request...")
        process.stdin.write(json.dumps(tool_request) + '\n')
        process.stdin.flush()
        
        # Wait longer and read with more debugging
        print("Waiting for response...")
        time.sleep(3)
        
        # Check if process is still alive
        if process.poll() is not None:
            print("❌ Process died!")
            stderr = process.stderr.read()
            if stderr:
                print(f"Stderr: {stderr}")
            return False
        
        # Try to read response
        response = process.stdout.readline()
        print(f"Raw response: {response}")
        
        if response:
            try:
                response_data = json.loads(response.strip())
                print(f"Parsed response: {json.dumps(response_data, indent=2)[:500]}...")
                
                if "result" in response_data:
                    print("✅ Tool call successful!")
                    return True
                else:
                    print("❌ No result in response")
                    return False
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Response was: {response}")
                return False
        else:
            print("❌ No response received")
            # Check stderr for errors
            stderr = process.stderr.read()
            if stderr:
                print(f"Stderr: {stderr}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
        
    finally:
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            process.kill()

if __name__ == "__main__":
    debug_tool_execution()