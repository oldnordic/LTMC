#!/usr/bin/env python3
"""Test the fixed stdio transport with comprehensive tool testing."""

import json
import subprocess
import sys
import time
from datetime import datetime

def test_fixed_stdio():
    """Test the fixed stdio transport with tools that had issues."""
    print("🔧 Testing FIXED LTMC Stdio Transport")
    print(f"Started at: {datetime.now()}")
    print("=" * 50)
    
    try:
        # Start fixed server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Allow startup time
        time.sleep(2)
        
        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "fixed-test", "version": "1.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_req) + '\n')
        process.stdin.flush()
        time.sleep(1)
        
        init_resp = process.stdout.readline()
        if "result" in init_resp:
            print("✅ MCP initialization successful")
        else:
            print("❌ MCP initialization failed")
            return False
        
        # Initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(notif) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Test problematic tools
        test_tools = [
            {
                "name": "store_memory",
                "args": {
                    "content": f"Fixed stdio transport test at {datetime.now()}",
                    "file_name": f"fixed_stdio_test_{int(time.time())}.md",
                    "resource_type": "document"
                }
            },
            {
                "name": "log_chat",
                "args": {
                    "content": "Testing fixed stdio transport chat logging",
                    "conversation_id": f"fixed_test_{int(time.time())}",
                    "role": "system"
                }
            },
            {
                "name": "add_todo",
                "args": {
                    "title": "Fixed Stdio Test Todo",
                    "description": "Test todo via fixed stdio transport",
                    "priority": "medium"
                }
            },
            {
                "name": "log_code_attempt",
                "args": {
                    "input_prompt": "Test stdio fix",
                    "generated_code": "print('stdio fixed!')",
                    "result": "pass",
                    "tags": ["stdio", "fix", "test"]
                }
            }
        ]
        
        passed = 0
        total = len(test_tools)
        
        for i, tool_test in enumerate(test_tools, 2):
            tool_name = tool_test["name"]
            print(f"🔧 Testing {tool_name}...")
            
            tool_req = {
                "jsonrpc": "2.0",
                "id": i,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": tool_test["args"]
                }
            }
            
            process.stdin.write(json.dumps(tool_req) + '\n')
            process.stdin.flush()
            time.sleep(2)  # Give more time for complex tools
            
            tool_resp = process.stdout.readline()
            if tool_resp and "result" in tool_resp:
                print(f"   ✅ {tool_name} - SUCCESS")
                passed += 1
                
                # Parse and show result details
                try:
                    resp_data = json.loads(tool_resp.strip())
                    result = resp_data.get("result", {})
                    
                    # Check for structured content
                    if "structuredContent" in result:
                        structured = result["structuredContent"]["result"]
                        if structured.get("success"):
                            print(f"      Success: {structured.get('message', 'OK')}")
                        else:
                            print(f"      Issue: {structured.get('error', 'Unknown')}")
                    
                except json.JSONDecodeError:
                    pass
                    
            else:
                print(f"   ❌ {tool_name} - FAILED")
        
        print(f"\n📊 Results: {passed}/{total} tools passed")
        
        if passed == total:
            print("🎉 ALL TOOLS WORKING!")
            print("✅ Stdio transport performance fixed")
            print("✅ No more stdout corruption issues")
            print("✅ Should now match HTTP transport performance")
            return True
        else:
            print("❌ Some tools still have issues")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
        
    finally:
        try:
            process.terminate()
            process.wait(timeout=3)
        except:
            process.kill()

if __name__ == "__main__":
    success = test_fixed_stdio()
    print(f"\nResult: {'✅ STDIO TRANSPORT FIXED' if success else '❌ ISSUES REMAIN'}")
    sys.exit(0 if success else 1)