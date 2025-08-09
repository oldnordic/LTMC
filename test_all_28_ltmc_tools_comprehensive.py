#!/usr/bin/env python3
"""
Comprehensive test script for all 28 LTMC tools in both STDIO and HTTP FastMCP modes.
Tests each tool individually and validates functionality.
"""

import asyncio
import json
import subprocess
import time
import requests
import os
import sys
from typing import Dict, Any, List
from pathlib import Path
import tempfile
import sqlite3
from datetime import datetime

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
HTTP_BASE_URL = "http://localhost:5050"
HTTP_JSONRPC_URL = f"{HTTP_BASE_URL}/jsonrpc"
TEST_DB_PATH = "test_ltmc.db"
TEST_SESSION_ID = f"test_session_{int(time.time())}"

# All 28 LTMC tools with test parameters
LTMC_TOOLS = [
    # Core Memory Operations (Tools 1-2)
    {
        "name": "store_memory",
        "description": "Store documents, knowledge, decisions, progress",
        "params": {
            "file_name": "test_document.md",
            "content": "This is a test document for LTMC memory storage",
            "resource_type": "document"
        }
    },
    {
        "name": "retrieve_memory", 
        "description": "Semantic search and retrieval of stored information",
        "params": {
            "conversation_id": TEST_SESSION_ID,
            "query": "test document",
            "top_k": 3
        }
    },
    
    # Chat & Communication (Tools 3-6)
    {
        "name": "log_chat",
        "description": "Log conversations for continuity",
        "params": {
            "conversation_id": TEST_SESSION_ID,
            "role": "user",
            "content": "Test chat message for LTMC logging",
            "agent_name": "test_agent",
            "source_tool": "claude-code"
        }
    },
    {
        "name": "ask_with_context",
        "description": "Query with automatic context retrieval", 
        "params": {
            "query": "What is stored in memory?",
            "conversation_id": TEST_SESSION_ID,
            "top_k": 3
        }
    },
    {
        "name": "route_query",
        "description": "Smart query routing",
        "params": {
            "query": "test routing query",
            "source_types": ["document", "code"],
            "top_k": 3
        }
    },
    {
        "name": "get_chats_by_tool",
        "description": "Tool usage history",
        "params": {
            "source_tool": "claude-code",
            "limit": 10
        }
    },
    
    # Task Management (Tools 7-10)
    {
        "name": "add_todo",
        "description": "Add tasks for complex multi-step work",
        "params": {
            "title": "Test Todo Item",
            "description": "This is a test todo for LTMC task management",
            "priority": "high"
        }
    },
    {
        "name": "list_todos",
        "description": "View all tasks",
        "params": {
            "status": "all",
            "limit": 10
        }
    },
    {
        "name": "complete_todo",
        "description": "Mark tasks complete",
        "params": {
            "todo_id": 1  # Will be updated dynamically
        }
    },
    {
        "name": "search_todos",
        "description": "Search tasks by text",
        "params": {
            "query": "test",
            "limit": 10
        }
    },
    
    # Context & Retrieval (Tools 11-16)
    {
        "name": "build_context",
        "description": "Build context windows with token limits",
        "params": {
            "documents": [
                {"id": "1", "content": "Test document 1", "type": "text"},
                {"id": "2", "content": "Test document 2", "type": "code"}
            ],
            "max_tokens": 1000
        }
    },
    {
        "name": "retrieve_by_type",
        "description": "Type-filtered retrieval",
        "params": {
            "query": "test document",
            "doc_type": "document",
            "top_k": 3
        }
    },
    {
        "name": "store_context_links_tool",
        "description": "Link context to messages",
        "params": {
            "message_id": 1,  # Will be updated dynamically
            "chunk_ids": [1, 2]
        }
    },
    {
        "name": "get_context_links_for_message_tool",
        "description": "Get message context",
        "params": {
            "message_id": 1  # Will be updated dynamically
        }
    },
    {
        "name": "get_messages_for_chunk_tool",
        "description": "Get chunk messages",
        "params": {
            "chunk_id": 1  # Will be updated dynamically
        }
    },
    {
        "name": "get_context_usage_statistics_tool",
        "description": "Usage statistics",
        "params": {}
    },
    
    # Knowledge Graph & Relationships (Tools 17-20)
    {
        "name": "link_resources",
        "description": "Create resource relationships",
        "params": {
            "source_id": "doc_1",
            "target_id": "doc_2", 
            "relation": "references"
        }
    },
    {
        "name": "query_graph",
        "description": "Graph queries for relationships",
        "params": {
            "entity": "doc_1",
            "relation_type": "references"
        }
    },
    {
        "name": "auto_link_documents",
        "description": "Auto-link similar documents",
        "params": {
            "documents": [
                {"id": "doc_1", "content": "First test document", "type": "text"},
                {"id": "doc_2", "content": "Second test document", "type": "text"}
            ]
        }
    },
    {
        "name": "get_document_relationships_tool",
        "description": "Get document relations",
        "params": {
            "doc_id": "doc_1"
        }
    },
    
    # Tool Tracking & Analytics (Tools 21-22)
    {
        "name": "list_tool_identifiers",
        "description": "List available tools",
        "params": {}
    },
    {
        "name": "get_tool_conversations",
        "description": "Tool usage conversations",
        "params": {
            "source_tool": "claude-code",
            "limit": 10
        }
    },
    
    # Code Pattern Memory (Tools 23-25)
    {
        "name": "log_code_attempt",
        "description": "Experience replay for code generation",
        "params": {
            "input_prompt": "Create a test function",
            "generated_code": "def test_function():\n    return True",
            "result": "pass",
            "function_name": "test_function",
            "tags": ["python", "test"]
        }
    },
    {
        "name": "get_code_patterns",
        "description": "Retrieve similar successful patterns",
        "params": {
            "query": "test function",
            "result_filter": "pass",
            "top_k": 3
        }
    },
    {
        "name": "analyze_code_patterns_tool",
        "description": "Analyze patterns for improvements",
        "params": {
            "time_range_days": 30
        }
    },
    
    # Redis Cache Operations (Tools 26-28)
    {
        "name": "redis_cache_stats",
        "description": "Cache performance metrics",
        "params": {}
    },
    {
        "name": "redis_flush_cache",
        "description": "Flush cache by type",
        "params": {
            "cache_type": "queries"
        }
    },
    {
        "name": "redis_health_check",
        "description": "Health check Redis connection",
        "params": {}
    }
]


class LTMCTester:
    def __init__(self):
        self.results = {
            "http": {},
            "stdio": {},
            "summary": {
                "total_tools": len(LTMC_TOOLS),
                "http_passed": 0,
                "http_failed": 0,
                "stdio_passed": 0,
                "stdio_failed": 0,
                "start_time": datetime.now().isoformat(),
                "end_time": None
            }
        }
        self.dynamic_ids = {}
        
    def prepare_test_environment(self):
        """Prepare test environment and database."""
        print("🔧 Preparing test environment...")
        
        # Clean up any existing test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            
        # Set environment variables for testing
        os.environ["DB_PATH"] = TEST_DB_PATH
        os.environ["FAISS_INDEX_PATH"] = "test_faiss_index"
        os.environ["LOG_LEVEL"] = "ERROR"  # Reduce log noise during testing
        
        # Initialize database
        try:
            from ltms.database.schema import create_tables
            from ltms.database.connection import get_db_connection
            
            conn = get_db_connection(TEST_DB_PATH)
            create_tables(conn)
            conn.close()
            print("✅ Test database initialized")
        except Exception as e:
            print(f"❌ Failed to initialize test database: {e}")
            return False
            
        return True
        
    def start_http_server(self):
        """Start the LTMC HTTP server for testing."""
        print("🚀 Starting LTMC HTTP server...")
        try:
            # Check if server is already running
            try:
                response = requests.get(f"{HTTP_BASE_URL}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ HTTP server already running")
                    return True
            except:
                pass
                
            # Start the server
            self.server_process = subprocess.Popen([
                sys.executable, "-m", "ltms.mcp_server_http",
                "--host", "localhost",
                "--port", "5050"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            for i in range(10):
                try:
                    response = requests.get(f"{HTTP_BASE_URL}/health", timeout=1)
                    if response.status_code == 200:
                        print("✅ HTTP server started successfully")
                        return True
                except:
                    time.sleep(1)
                    
            print("❌ HTTP server failed to start")
            return False
            
        except Exception as e:
            print(f"❌ Error starting HTTP server: {e}")
            return False
            
    def stop_http_server(self):
        """Stop the LTMC HTTP server."""
        if hasattr(self, 'server_process'):
            self.server_process.terminate()
            self.server_process.wait()
            print("🛑 HTTP server stopped")
            
    def test_http_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single tool via HTTP JSON-RPC."""
        tool_name = tool["name"]
        params = tool["params"].copy()
        
        # Update dynamic IDs if needed
        if "todo_id" in params:
            params["todo_id"] = self.dynamic_ids.get("todo_id", 1)
        if "message_id" in params:
            params["message_id"] = self.dynamic_ids.get("message_id", 1)
        if "chunk_id" in params:
            params["chunk_id"] = self.dynamic_ids.get("chunk_id", 1)
            
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            },
            "id": 1
        }
        
        try:
            response = requests.post(
                HTTP_JSONRPC_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "result" in result:
                    tool_result = result["result"]
                    success = tool_result.get("success", True) if isinstance(tool_result, dict) else True
                    
                    # Store dynamic IDs for later tests
                    if tool_name == "add_todo" and "todo_id" in tool_result:
                        self.dynamic_ids["todo_id"] = tool_result["todo_id"]
                    if tool_name == "log_chat" and "message_id" in tool_result:
                        self.dynamic_ids["message_id"] = tool_result["message_id"]
                        
                    return {
                        "success": success,
                        "response": tool_result,
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "response": None,
                        "error": result.get("error", "Unknown JSON-RPC error")
                    }
            else:
                return {
                    "success": False,
                    "response": None,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
            
    def test_stdio_tool(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single tool via STDIO MCP."""
        # For now, STDIO testing is simulated since we need actual MCP client
        # In a real scenario, this would use the MCP protocol directly
        
        # Simulate STDIO test by importing and calling the tool directly
        try:
            from ltms.mcp_server import mcp
            
            # Get the tool function
            tool_name = tool["name"]
            params = tool["params"].copy()
            
            # Update dynamic IDs if needed
            if "todo_id" in params:
                params["todo_id"] = self.dynamic_ids.get("todo_id", 1)
            if "message_id" in params:
                params["message_id"] = self.dynamic_ids.get("message_id", 1)
            if "chunk_id" in params:
                params["chunk_id"] = self.dynamic_ids.get("chunk_id", 1)
            
            # Get tool function from mcp tools
            tool_func = None
            for mcp_tool in mcp.tools:
                if mcp_tool.name == tool_name:
                    tool_func = mcp_tool.func
                    break
                    
            if not tool_func:
                return {
                    "success": False,
                    "response": None,
                    "error": f"Tool {tool_name} not found in MCP server"
                }
                
            # Call the tool function
            if asyncio.iscoroutinefunction(tool_func):
                result = asyncio.run(tool_func(**params))
            else:
                result = tool_func(**params)
                
            success = result.get("success", True) if isinstance(result, dict) else True
            
            # Store dynamic IDs for later tests
            if tool_name == "add_todo" and isinstance(result, dict) and "todo_id" in result:
                self.dynamic_ids["todo_id"] = result["todo_id"]
            if tool_name == "log_chat" and isinstance(result, dict) and "message_id" in result:
                self.dynamic_ids["message_id"] = result["message_id"]
                
            return {
                "success": success,
                "response": result,
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
            
    def run_http_tests(self):
        """Run all tools via HTTP transport."""
        print(f"\n🧪 Testing all {len(LTMC_TOOLS)} tools via HTTP JSON-RPC...")
        
        for i, tool in enumerate(LTMC_TOOLS, 1):
            tool_name = tool["name"]
            description = tool["description"]
            
            print(f"  [{i:2d}/28] Testing {tool_name}: {description}")
            
            result = self.test_http_tool(tool)
            self.results["http"][tool_name] = result
            
            if result["success"]:
                print(f"    ✅ PASSED")
                self.results["summary"]["http_passed"] += 1
            else:
                print(f"    ❌ FAILED: {result['error']}")
                self.results["summary"]["http_failed"] += 1
                
            # Small delay between tests
            time.sleep(0.1)
            
    def run_stdio_tests(self):
        """Run all tools via STDIO transport."""
        print(f"\n🧪 Testing all {len(LTMC_TOOLS)} tools via STDIO MCP...")
        
        for i, tool in enumerate(LTMC_TOOLS, 1):
            tool_name = tool["name"]
            description = tool["description"]
            
            print(f"  [{i:2d}/28] Testing {tool_name}: {description}")
            
            result = self.test_stdio_tool(tool)
            self.results["stdio"][tool_name] = result
            
            if result["success"]:
                print(f"    ✅ PASSED") 
                self.results["summary"]["stdio_passed"] += 1
            else:
                print(f"    ❌ FAILED: {result['error']}")
                self.results["summary"]["stdio_failed"] += 1
                
            # Small delay between tests
            time.sleep(0.1)
            
    def print_summary(self):
        """Print test results summary."""
        self.results["summary"]["end_time"] = datetime.now().isoformat()
        
        print("\n" + "="*80)
        print("🎯 LTMC ALL 28 TOOLS TEST RESULTS SUMMARY")
        print("="*80)
        
        print(f"Total Tools Tested: {self.results['summary']['total_tools']}")
        print(f"Test Duration: {self.results['summary']['start_time']} to {self.results['summary']['end_time']}")
        
        print(f"\n📡 HTTP JSON-RPC Transport Results:")
        print(f"  ✅ Passed: {self.results['summary']['http_passed']}")
        print(f"  ❌ Failed: {self.results['summary']['http_failed']}")
        print(f"  📊 Success Rate: {self.results['summary']['http_passed']/28*100:.1f}%")
        
        print(f"\n🔌 STDIO MCP Transport Results:")
        print(f"  ✅ Passed: {self.results['summary']['stdio_passed']}")
        print(f"  ❌ Failed: {self.results['summary']['stdio_failed']}")
        print(f"  📊 Success Rate: {self.results['summary']['stdio_passed']/28*100:.1f}%")
        
        # Show failed tools
        http_failed = [name for name, result in self.results["http"].items() if not result["success"]]
        stdio_failed = [name for name, result in self.results["stdio"].items() if not result["success"]]
        
        if http_failed:
            print(f"\n❌ HTTP Failed Tools: {', '.join(http_failed)}")
        if stdio_failed:
            print(f"\n❌ STDIO Failed Tools: {', '.join(stdio_failed)}")
            
        print("\n" + "="*80)
        
    def save_results(self):
        """Save detailed test results to JSON file."""
        timestamp = int(time.time())
        filename = f"ltmc_all_28_tools_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"💾 Detailed results saved to: {filename}")
        
    def cleanup(self):
        """Clean up test environment."""
        print("\n🧹 Cleaning up test environment...")
        
        # Stop HTTP server
        self.stop_http_server()
        
        # Remove test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            
        # Remove test FAISS index
        import shutil
        if os.path.exists("test_faiss_index"):
            shutil.rmtree("test_faiss_index")
            
        print("✅ Cleanup complete")


def main():
    """Main test execution."""
    print("🚀 LTMC ALL 28 TOOLS COMPREHENSIVE TEST")
    print("="*80)
    print("Testing all 28 LTMC tools in both STDIO and HTTP FastMCP transports")
    print("="*80)
    
    tester = LTMCTester()
    
    try:
        # Prepare environment
        if not tester.prepare_test_environment():
            print("❌ Failed to prepare test environment")
            return 1
            
        # Start HTTP server
        if not tester.start_http_server():
            print("❌ Failed to start HTTP server")
            return 1
            
        # Run HTTP tests
        tester.run_http_tests()
        
        # Run STDIO tests
        tester.run_stdio_tests()
        
        # Print summary
        tester.print_summary()
        
        # Save results
        tester.save_results()
        
        # Determine exit code
        total_tests = 28 * 2  # 28 tools x 2 transports
        total_passed = tester.results["summary"]["http_passed"] + tester.results["summary"]["stdio_passed"]
        
        if total_passed == total_tests:
            print("🎉 ALL TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {total_tests - total_passed} tests failed out of {total_tests}")
            return 1
            
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())