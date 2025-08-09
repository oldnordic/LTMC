#!/usr/bin/env python3
"""Comprehensive test suite for all 28 LTMC tools."""

import json
import requests
import time
from typing import Dict, Any, List

BASE_URL = "http://localhost:5050/jsonrpc"

# Test cases for all 28 LTMC tools
TOOL_TESTS = [
    # Core Memory Operations (2 tools)
    {
        "name": "store_memory",
        "args": {"file_name": "test_doc.md", "content": "Test content", "resource_type": "document"}
    },
    {
        "name": "retrieve_memory", 
        "args": {"query": "test", "conversation_id": "test_session", "top_k": 5}
    },
    
    # Chat & Communication (4 tools)
    {
        "name": "log_chat",
        "args": {"content": "Test chat message", "conversation_id": "test_session", "role": "user"}
    },
    {
        "name": "ask_with_context",
        "args": {"query": "test query", "conversation_id": "test_session", "top_k": 3}
    },
    {
        "name": "route_query",
        "args": {"query": "test routing", "source_types": ["document"], "top_k": 5}
    },
    {
        "name": "get_chats_by_tool",
        "args": {"source_tool": "store_memory", "limit": 10}
    },
    
    # Task Management (4 tools)
    {
        "name": "add_todo",
        "args": {"title": "Test Task", "description": "Test description", "priority": "medium"}
    },
    {
        "name": "list_todos",
        "args": {"limit": 10}
    },
    {
        "name": "search_todos",
        "args": {"query": "test", "limit": 5}
    },
    {
        "name": "complete_todo",
        "args": {"todo_id": 1}  # This might fail if no todos exist, that's expected
    },
    
    # Context & Retrieval (6 tools)
    {
        "name": "build_context",
        "args": {"documents": [{"content": "test document"}], "max_tokens": 1000}
    },
    {
        "name": "retrieve_by_type",
        "args": {"query": "test", "doc_type": "document", "top_k": 5}
    },
    {
        "name": "store_context_links",
        "args": {"message_id": "1199", "chunk_ids": [1, 2, 3]}
    },
    {
        "name": "get_context_links_for_message",
        "args": {"message_id": "1199"}
    },
    {
        "name": "get_messages_for_chunk", 
        "args": {"chunk_id": 1}
    },
    {
        "name": "get_context_usage_statistics",
        "args": {}
    },
    
    # Knowledge Graph & Relationships (4 tools) - Now Working!
    {
        "name": "link_resources",
        "args": {"source_id": "test_doc1", "target_id": "test_doc2", "relation": "relates_to"}
    },
    {
        "name": "query_graph",
        "args": {"entity": "test_doc1"}
    },
    {
        "name": "auto_link_documents", 
        "args": {"documents": [{"id": "auto1", "content": "python tutorial"}, {"id": "auto2", "content": "python guide"}]}
    },
    {
        "name": "get_document_relationships",
        "args": {"doc_id": "test_doc1"}
    },
    
    # Tool Tracking & Analytics (2 tools)
    {
        "name": "list_tool_identifiers",
        "args": {}
    },
    {
        "name": "get_tool_conversations",
        "args": {"source_tool": "store_memory", "limit": 10}
    },
    
    # Code Pattern Memory (3 tools)
    {
        "name": "log_code_attempt",
        "args": {
            "input_prompt": "Create a function",
            "generated_code": "def test(): return True",
            "result": "pass",
            "tags": ["test", "function"]
        }
    },
    {
        "name": "get_code_patterns",
        "args": {"query": "function", "top_k": 5}
    },
    {
        "name": "analyze_code_patterns",
        "args": {"patterns": ["function", "class"]}
    },
    
    # Redis Cache Operations (3 tools)
    {
        "name": "redis_health_check",
        "args": {}
    },
    {
        "name": "redis_cache_stats", 
        "args": {}
    },
    {
        "name": "redis_flush_cache",
        "args": {"cache_type": "all"}
    }
]

def test_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single LTMC tool."""
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": args
        },
        "id": 1
    }
    
    try:
        response = requests.post(BASE_URL, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        if "result" in result:
            success = result["result"].get("success", True) if isinstance(result["result"], dict) else True
            return {
                "tool": tool_name,
                "status": "PASS" if success else "FAIL", 
                "result": result["result"],
                "error": None
            }
        elif "error" in result:
            return {
                "tool": tool_name,
                "status": "FAIL",
                "result": None,
                "error": result["error"]
            }
        else:
            return {
                "tool": tool_name,
                "status": "UNKNOWN",
                "result": result,
                "error": "Unexpected response format"
            }
            
    except Exception as e:
        return {
            "tool": tool_name,
            "status": "ERROR",
            "result": None,
            "error": str(e)
        }

def run_comprehensive_test() -> Dict[str, Any]:
    """Run comprehensive test of all 28 LTMC tools."""
    print("🚀 Starting comprehensive LTMC 28-tool test suite...")
    print("=" * 60)
    
    results = []
    passed = 0
    failed = 0
    errors = 0
    
    for i, test_case in enumerate(TOOL_TESTS, 1):
        tool_name = test_case["name"]
        args = test_case["args"]
        
        print(f"[{i:2d}/28] Testing {tool_name}...", end=" ")
        
        result = test_tool(tool_name, args)
        results.append(result)
        
        if result["status"] == "PASS":
            print("✅ PASS")
            passed += 1
        elif result["status"] == "FAIL":
            print("❌ FAIL")
            print(f"      Error: {result.get('error', 'Unknown failure')}")
            failed += 1
        else:
            print("🔥 ERROR")
            print(f"      Error: {result.get('error', 'Unknown error')}")
            errors += 1
        
        # Small delay between tests
        time.sleep(0.1)
    
    print("=" * 60)
    print("📊 LTMC Tool Test Results Summary:")
    print(f"   ✅ Passed: {passed}/28 ({passed/28*100:.1f}%)")
    print(f"   ❌ Failed: {failed}/28 ({failed/28*100:.1f}%)")
    print(f"   🔥 Errors: {errors}/28 ({errors/28*100:.1f}%)")
    print(f"   🎯 Success Rate: {passed/28*100:.1f}%")
    
    if passed == 28:
        print("🎉 ALL 28 TOOLS WORKING - 100% SUCCESS RATE ACHIEVED!")
    elif passed >= 25:
        print("🚀 Excellent! Nearly complete tool coverage.")
    elif passed >= 21:
        print("👍 Good progress! Most tools working.")
    else:
        print("⚠️  Significant issues remain. More work needed.")
    
    return {
        "total_tools": 28,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "success_rate": passed/28*100,
        "results": results
    }

if __name__ == "__main__":
    summary = run_comprehensive_test()
    
    # Save detailed results to file
    with open("ltmc_tool_test_results.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📝 Detailed results saved to: ltmc_tool_test_results.json")