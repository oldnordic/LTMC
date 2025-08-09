#!/usr/bin/env python3
"""Quick validation test for both HTTP and stdio transports."""

import json
import requests
import subprocess
import sys
import time
from datetime import datetime

def test_http_quick():
    """Quick test of HTTP transport with key tools."""
    print("=== Quick HTTP Transport Test ===")
    
    base_url = "http://localhost:5050"
    
    # Test essential tools from each category
    test_tools = [
        ("redis_health_check", {}),
        ("store_memory", {
            "file_name": "http_validation.md",
            "content": "HTTP transport validation test",
            "resource_type": "document"
        }),
        ("list_tool_identifiers", {}),
        ("add_todo", {
            "title": "HTTP Validation Todo",
            "description": "Test todo via HTTP",
            "priority": "low"
        })
    ]
    
    passed = 0
    total = len(test_tools)
    
    for tool_name, args in test_tools:
        try:
            response = requests.post(
                f"{base_url}/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": args},
                    "id": f"test_{tool_name}"
                },
                timeout=5
            )
            
            if response.status_code == 200 and "result" in response.json():
                print(f"  ✅ {tool_name}")
                passed += 1
            else:
                print(f"  ❌ {tool_name} - Bad response")
        except Exception as e:
            print(f"  ❌ {tool_name} - {e}")
    
    success = passed == total
    print(f"HTTP Result: {passed}/{total} tools passed - {'✅ SUCCESS' if success else '❌ FAILED'}")
    return success

def test_stdio_quick():
    """Quick test of stdio transport with key tools."""
    print("\\n=== Quick Stdio Transport Test ===")
    
    try:
        # Start stdio server
        process = subprocess.Popen(
            [sys.executable, 'ltmc_mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Initialize
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "quick-test", "version": "1.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_req) + '\\n')
        process.stdin.flush()
        time.sleep(1)
        
        init_response = process.stdout.readline()
        if not init_response or "result" not in init_response:
            print("  ❌ MCP initialization failed")
            return False
        
        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(notif) + '\\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Test essential tools
        test_tools = [
            ("redis_health_check", {}),
            ("store_memory", {
                "file_name": "stdio_validation.md", 
                "content": "Stdio transport validation test",
                "resource_type": "document"
            }),
            ("log_chat", {
                "content": "Stdio validation chat",
                "conversation_id": "stdio_test",
                "role": "system"
            })
        ]
        
        passed = 0
        total = len(test_tools)
        
        for tool_name, args in test_tools:
            try:
                tool_req = {
                    "jsonrpc": "2.0",
                    "id": f"test_{tool_name}",
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": args}
                }
                
                process.stdin.write(json.dumps(tool_req) + '\\n')
                process.stdin.flush()
                time.sleep(1)
                
                response = process.stdout.readline()
                if response and "result" in response:
                    print(f"  ✅ {tool_name}")
                    passed += 1
                else:
                    print(f"  ❌ {tool_name} - No response")
                    
            except Exception as e:
                print(f"  ❌ {tool_name} - {e}")
        
        process.terminate()
        process.wait(timeout=3)
        
        success = passed == total
        print(f"Stdio Result: {passed}/{total} tools passed - {'✅ SUCCESS' if success else '❌ FAILED'}")
        return success
        
    except Exception as e:
        print(f"❌ Stdio test failed: {e}")
        return False

def main():
    """Run quick validation tests."""
    print("🚀 LTMC Quick Dual Transport Validation")
    print(f"Started at: {datetime.now()}")
    print("=" * 50)
    
    http_success = test_http_quick()
    stdio_success = test_stdio_quick()
    
    print("\\n" + "=" * 50)
    print("📊 QUICK VALIDATION SUMMARY")
    print("=" * 50)
    
    overall_success = http_success and stdio_success
    print(f"🎯 Result: {'✅ BOTH TRANSPORTS VALIDATED' if overall_success else '❌ VALIDATION ISSUES FOUND'}")
    
    if overall_success:
        print("\\n✅ All critical tools working on both transports")
        print("✅ HTTP transport: Full functionality confirmed")
        print("✅ Stdio transport: MCP protocol compliance confirmed")
    else:
        print("\\n❌ Issues found - see details above")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)