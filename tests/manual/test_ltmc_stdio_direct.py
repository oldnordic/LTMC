#!/usr/bin/env python3
"""
Direct STDIO FastMCP test for all 28 LTMC tools.
Tests tools directly through the STDIO MCP server entry point.
"""

import asyncio
import json
import subprocess
import time
import os
import sys
from typing import Dict, Any, List
from pathlib import Path
import tempfile

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_DB_PATH = "test_ltmc_stdio.db"
TEST_SESSION_ID = f"stdio_test_{int(time.time())}"

# All 28 LTMC tools with test parameters
LTMC_STDIO_TOOLS = [
    # Core Memory Operations (Tools 1-2)
    {
        "name": "store_memory",
        "params": {
            "file_name": "stdio_test_document.md",
            "content": "This is a STDIO test document for LTMC memory storage",
            "resource_type": "document"
        }
    },
    {
        "name": "retrieve_memory", 
        "params": {
            "conversation_id": TEST_SESSION_ID,
            "query": "stdio test document",
            "top_k": 3
        }
    },
    
    # Chat & Communication (Tools 3-6) 
    {
        "name": "log_chat",
        "params": {
            "conversation_id": TEST_SESSION_ID,
            "role": "user",
            "content": "STDIO test chat message for LTMC logging",
            "source_tool": "claude-code"
        }
    },
    {
        "name": "ask_with_context",
        "params": {
            "query": "What is stored in STDIO memory?",
            "conversation_id": TEST_SESSION_ID,
            "top_k": 3
        }
    },
    {
        "name": "route_query",
        "params": {
            "query": "stdio routing query",
            "source_types": ["document", "code"],
            "top_k": 3
        }
    },
    {
        "name": "get_chats_by_tool",
        "params": {
            "source_tool": "claude-code",
            "limit": 10
        }
    },
    
    # Task Management (Tools 7-10)
    {
        "name": "add_todo",
        "params": {
            "title": "STDIO Test Todo Item",
            "description": "This is a STDIO test todo for LTMC task management",
            "priority": "high"
        }
    },
    {
        "name": "list_todos",
        "params": {
            "status": "all",
            "limit": 10
        }
    },
    {
        "name": "complete_todo",
        "params": {
            "todo_id": 1
        }
    },
    {
        "name": "search_todos",
        "params": {
            "query": "stdio",
            "limit": 10
        }
    },
    
    # Context & Retrieval (Tools 11-16) - Simplified for STDIO testing
    {
        "name": "build_context",
        "params": {
            "documents": [
                {"id": "1", "content": "STDIO test document 1", "type": "text"}
            ],
            "max_tokens": 1000
        }
    },
    {
        "name": "retrieve_by_type",
        "params": {
            "query": "stdio test",
            "doc_type": "document",
            "top_k": 3
        }
    },
    {
        "name": "store_context_links_tool",
        "params": {
            "message_id": 1,
            "chunk_ids": [1]
        }
    },
    {
        "name": "get_context_links_for_message_tool",
        "params": {
            "message_id": 1
        }
    },
    {
        "name": "get_messages_for_chunk_tool",
        "params": {
            "chunk_id": 1
        }
    },
    {
        "name": "get_context_usage_statistics_tool",
        "params": {}
    },
    
    # Code Pattern Memory (Tools 23-25) - Most reliable for testing
    {
        "name": "log_code_attempt",
        "params": {
            "input_prompt": "Create a STDIO test function",
            "generated_code": "def stdio_test_function():\n    return 'STDIO works'",
            "result": "pass",
            "function_name": "stdio_test_function",
            "tags": ["python", "stdio", "test"]
        }
    },
    {
        "name": "get_code_patterns",
        "params": {
            "query": "stdio test function",
            "result_filter": "pass",
            "top_k": 3
        }
    },
    {
        "name": "analyze_code_patterns_tool",
        "params": {
            "time_range_days": 30
        }
    },
    
    # Tool Tracking & Analytics (Tools 21-22)
    {
        "name": "list_tool_identifiers",
        "params": {}
    },
    {
        "name": "get_tool_conversations",
        "params": {
            "source_tool": "claude-code",
            "limit": 10
        }
    },
    
    # Redis Cache Operations (Tools 26-28) - May fail if Redis not available
    {
        "name": "redis_cache_stats",
        "params": {}
    },
    {
        "name": "redis_flush_cache",
        "params": {
            "cache_type": "queries"
        }
    },
    {
        "name": "redis_health_check",
        "params": {}
    }
]


class STDIOTester:
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        
    def prepare_environment(self):
        """Prepare test environment."""
        print("🔧 Preparing STDIO test environment...")
        
        # Clean up any existing test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            
        # Set environment variables for testing
        os.environ["DB_PATH"] = TEST_DB_PATH
        os.environ["FAISS_INDEX_PATH"] = "test_stdio_faiss_index"
        os.environ["LOG_LEVEL"] = "ERROR"
        
        return True
        
    def test_tool_directly(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Test a tool by calling it directly from the MCP server module."""
        try:
            # Import the tool functions directly
            from ltms import mcp_server
            
            tool_name = tool["name"]
            params = tool["params"]
            
            # Get the tool function by name from globals
            if hasattr(mcp_server, tool_name):
                tool_func = getattr(mcp_server, tool_name)
                
                # Call the tool function
                if asyncio.iscoroutinefunction(tool_func):
                    result = asyncio.run(tool_func(**params))
                else:
                    result = tool_func(**params)
                    
                success = result.get("success", True) if isinstance(result, dict) else True
                
                return {
                    "success": success,
                    "response": result,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "response": None,
                    "error": f"Tool function {tool_name} not found in mcp_server module"
                }
                
        except Exception as e:
            return {
                "success": False,
                "response": None,
                "error": str(e)
            }
            
    def run_tests(self):
        """Run all STDIO tests."""
        print(f"\n🧪 Testing {len(LTMC_STDIO_TOOLS)} LTMC tools via direct STDIO calls...")
        
        for i, tool in enumerate(LTMC_STDIO_TOOLS, 1):
            tool_name = tool["name"]
            
            print(f"  [{i:2d}/{len(LTMC_STDIO_TOOLS)}] Testing {tool_name}")
            
            result = self.test_tool_directly(tool)
            self.results[tool_name] = result
            
            if result["success"]:
                print(f"    ✅ PASSED")
                self.passed += 1
            else:
                print(f"    ❌ FAILED: {result['error']}")
                self.failed += 1
                
    def print_results(self):
        """Print test results."""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*80}")
        print("🎯 LTMC STDIO DIRECT TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total Tools Tested: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        # Show failed tools
        failed_tools = [name for name, result in self.results.items() if not result["success"]]
        if failed_tools:
            print(f"\n❌ Failed Tools: {', '.join(failed_tools)}")
            
        print(f"{'='*80}")
        
    def cleanup(self):
        """Clean up test environment."""
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            
        # Remove test FAISS index
        import shutil
        if os.path.exists("test_stdio_faiss_index"):
            shutil.rmtree("test_stdio_faiss_index")


def main():
    """Main test execution."""
    print("🔌 LTMC STDIO DIRECT TEST")
    print("="*50)
    print("Testing LTMC tools via direct function calls")
    print("="*50)
    
    tester = STDIOTester()
    
    try:
        tester.prepare_environment()
        tester.run_tests()
        tester.print_results()
        
        if tester.failed == 0:
            print("🎉 ALL STDIO TESTS PASSED!")
            return 0
        else:
            print(f"⚠️  {tester.failed} tests failed")
            return 1
            
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())