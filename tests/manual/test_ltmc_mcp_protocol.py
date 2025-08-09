#!/usr/bin/env python3
"""
Real MCP Protocol test for LTMC STDIO server.
Tests actual MCP JSON-RPC over STDIO transport.
"""

import asyncio
import json
import subprocess
import time
import os
import sys
from typing import Dict, Any, List
from pathlib import Path

# Test configuration
LTMC_MCP_SERVER = "./ltmc_mcp_server.py"
TEST_SESSION_ID = f"mcp_protocol_test_{int(time.time())}"

# Core tools to test MCP protocol functionality
CORE_MCP_TESTS = [
    {
        "id": 1,
        "method": "tools/list",
        "params": {}
    },
    {
        "id": 2, 
        "method": "tools/call",
        "params": {
            "name": "store_memory",
            "arguments": {
                "file_name": "mcp_protocol_test.md",
                "content": "This tests the MCP protocol over STDIO transport",
                "resource_type": "document"
            }
        }
    },
    {
        "id": 3,
        "method": "tools/call", 
        "params": {
            "name": "retrieve_memory",
            "arguments": {
                "conversation_id": TEST_SESSION_ID,
                "query": "mcp protocol test",
                "top_k": 3
            }
        }
    },
    {
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "add_todo",
            "arguments": {
                "title": "MCP Protocol Test Todo",
                "description": "Testing MCP protocol functionality",
                "priority": "high"
            }
        }
    },
    {
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "list_todos",
            "arguments": {
                "status": "all",
                "limit": 10
            }
        }
    }
]


class MCPProtocolTester:
    def __init__(self):
        self.results = {}
        self.server_process = None
        
    def prepare_environment(self):
        """Prepare MCP test environment."""
        print("🔧 Preparing MCP protocol test environment...")
        
        # Set test environment variables
        os.environ["DB_PATH"] = "mcp_test.db" 
        os.environ["FAISS_INDEX_PATH"] = "mcp_test_faiss_index"
        os.environ["LOG_LEVEL"] = "ERROR"
        
        # Clean up any existing test files
        if os.path.exists("mcp_test.db"):
            os.remove("mcp_test.db")
            
        return True
        
    def start_mcp_server(self):
        """Start the LTMC MCP server."""
        print("🚀 Starting LTMC MCP server via STDIO...")
        
        if not os.path.exists(LTMC_MCP_SERVER):
            print(f"❌ MCP server file not found: {LTMC_MCP_SERVER}")
            return False
            
        try:
            self.server_process = subprocess.Popen(
                [sys.executable, LTMC_MCP_SERVER],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0
            )
            
            print("✅ MCP server process started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start MCP server: {e}")
            return False
            
    def send_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send MCP JSON-RPC request and get response."""
        if not self.server_process:
            return {"error": "Server not running"}
            
        try:
            # Add jsonrpc version
            request["jsonrpc"] = "2.0"
            
            # Send request
            request_json = json.dumps(request) + '\n'
            self.server_process.stdin.write(request_json)
            self.server_process.stdin.flush()
            
            # Read response with timeout
            response_line = ""
            start_time = time.time()
            while time.time() - start_time < 10:  # 10 second timeout
                if self.server_process.stdout.readable():
                    char = self.server_process.stdout.read(1)
                    if char == '\n':
                        break
                    response_line += char
                else:
                    time.sleep(0.01)
                    
            if response_line.strip():
                return json.loads(response_line.strip())
            else:
                return {"error": "No response received"}
                
        except Exception as e:
            return {"error": f"MCP communication error: {str(e)}"}
            
    def test_mcp_protocol(self):
        """Test MCP protocol functionality."""
        print(f"\n🧪 Testing MCP protocol with {len(CORE_MCP_TESTS)} requests...")
        
        for i, test_request in enumerate(CORE_MCP_TESTS, 1):
            test_id = test_request["id"]
            method = test_request["method"]
            
            if method == "tools/list":
                print(f"  [{i}/5] Testing tools/list")
            else:
                tool_name = test_request["params"]["name"]
                print(f"  [{i}/5] Testing tools/call: {tool_name}")
                
            response = self.send_mcp_request(test_request)
            self.results[test_id] = response
            
            if "error" in response:
                print(f"    ❌ FAILED: {response['error']}")
            elif "result" in response:
                print(f"    ✅ PASSED")
            else:
                print(f"    ⚠️  Unexpected response format")
                
            time.sleep(0.5)  # Small delay between requests
            
    def stop_server(self):
        """Stop the MCP server."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            print("🛑 MCP server stopped")
            
    def print_results(self):
        """Print test results."""
        print(f"\n{'='*70}")
        print("🎯 MCP PROTOCOL TEST RESULTS")
        print(f"{'='*70}")
        
        passed = 0
        failed = 0
        
        for test_id, response in self.results.items():
            if "error" in response:
                failed += 1
            elif "result" in response:
                passed += 1
            else:
                failed += 1
                
        total = passed + failed
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total Requests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Show detailed results
        print(f"\n📋 Detailed Results:")
        for test_id, response in self.results.items():
            test_request = next(req for req in CORE_MCP_TESTS if req["id"] == test_id)
            method = test_request["method"]
            
            if method == "tools/list":
                desc = "List available tools"
            else:
                tool_name = test_request["params"]["name"]
                desc = f"Call {tool_name}"
                
            if "error" in response:
                print(f"  [{test_id}] {desc}: ❌ {response['error']}")
            elif "result" in response:
                print(f"  [{test_id}] {desc}: ✅ Success")
            else:
                print(f"  [{test_id}] {desc}: ⚠️  Unknown response")
                
        print(f"{'='*70}")
        
    def cleanup(self):
        """Clean up test environment."""
        print("\n🧹 Cleaning up...")
        
        # Stop server
        self.stop_server()
        
        # Clean up test files
        if os.path.exists("mcp_test.db"):
            os.remove("mcp_test.db")
            
        import shutil
        if os.path.exists("mcp_test_faiss_index"):
            try:
                if os.path.isdir("mcp_test_faiss_index"):
                    shutil.rmtree("mcp_test_faiss_index")
                else:
                    os.remove("mcp_test_faiss_index")
            except:
                pass
                
        print("✅ Cleanup complete")


def main():
    """Main test execution."""
    print("📡 LTMC MCP PROTOCOL TEST")
    print("="*50)
    print("Testing real MCP JSON-RPC over STDIO transport")
    print("="*50)
    
    tester = MCPProtocolTester()
    
    try:
        if not tester.prepare_environment():
            return 1
            
        if not tester.start_mcp_server():
            return 1
            
        tester.test_mcp_protocol()
        tester.print_results()
        
        # Check if all tests passed
        passed = sum(1 for response in tester.results.values() if "result" in response)
        total = len(tester.results)
        
        if passed == total:
            print("🎉 ALL MCP PROTOCOL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {total - passed} tests failed")
            return 1
            
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())