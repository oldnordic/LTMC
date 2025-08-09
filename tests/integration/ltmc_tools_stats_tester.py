#!/usr/bin/env python3
"""Comprehensive LTMC 28-tool tester with usage statistics display."""

import json
import requests
import time
import sys
from typing import Dict, Any, List
from datetime import datetime

BASE_URL = "http://localhost:5050/jsonrpc"

# Test cases for all 28 LTMC tools
TOOL_TESTS = [
    # Core Memory Operations (2 tools)
    {
        "name": "store_memory",
        "args": {"file_name": "test_doc.md", "content": "Test content for statistics", "resource_type": "document"},
        "category": "memory"
    },
    {
        "name": "retrieve_memory", 
        "args": {"query": "test statistics", "conversation_id": "stats_test_session", "top_k": 5},
        "category": "memory"
    },
    
    # Chat & Communication (4 tools)
    {
        "name": "log_chat",
        "args": {"content": "Testing tool statistics tracking", "conversation_id": "stats_test_session", "role": "user"},
        "category": "chat"
    },
    {
        "name": "ask_with_context",
        "args": {"query": "show tool usage stats", "conversation_id": "stats_test_session", "top_k": 3},
        "category": "chat"
    },
    {
        "name": "route_query",
        "args": {"query": "test routing for stats", "source_types": ["document"], "top_k": 5},
        "category": "chat"
    },
    {
        "name": "get_chats_by_tool",
        "args": {"source_tool": "store_memory", "limit": 10},
        "category": "chat"
    },
    
    # Task Management (4 tools)
    {
        "name": "add_todo",
        "args": {"title": "Monitor Tool Statistics", "description": "Track usage patterns", "priority": "medium"},
        "category": "todo"
    },
    {
        "name": "list_todos",
        "args": {"limit": 10},
        "category": "todo"
    },
    {
        "name": "search_todos",
        "args": {"query": "statistics", "limit": 5},
        "category": "todo"
    },
    {
        "name": "complete_todo",
        "args": {"todo_id": 1},
        "category": "todo"
    },
    
    # Context & Retrieval (6 tools)
    {
        "name": "build_context",
        "args": {"documents": [{"content": "context for statistics testing"}], "max_tokens": 1000},
        "category": "context"
    },
    {
        "name": "retrieve_by_type",
        "args": {"query": "statistics", "doc_type": "document", "top_k": 5},
        "category": "context"
    },
    {
        "name": "store_context_links",
        "args": {"message_id": "1200", "chunk_ids": [1, 2, 3]},
        "category": "context"
    },
    {
        "name": "get_context_links_for_message",
        "args": {"message_id": "1200"},
        "category": "context"
    },
    {
        "name": "get_messages_for_chunk", 
        "args": {"chunk_id": 1},
        "category": "context"
    },
    {
        "name": "get_context_usage_statistics",
        "args": {},
        "category": "context"
    },
    
    # Knowledge Graph & Relationships (4 tools)
    {
        "name": "link_resources",
        "args": {"source_id": "stats_doc1", "target_id": "stats_doc2", "relation": "analyzes"},
        "category": "knowledge_graph"
    },
    {
        "name": "query_graph",
        "args": {"entity": "stats_doc1"},
        "category": "knowledge_graph"
    },
    {
        "name": "auto_link_documents", 
        "args": {"documents": [{"id": "stats1", "content": "statistics analysis"}, {"id": "stats2", "content": "data analytics"}]},
        "category": "knowledge_graph"
    },
    {
        "name": "get_document_relationships",
        "args": {"doc_id": "stats_doc1"},
        "category": "knowledge_graph"
    },
    
    # Tool Tracking & Analytics (2 tools) 
    {
        "name": "list_tool_identifiers",
        "args": {},
        "category": "analytics"
    },
    {
        "name": "get_tool_conversations",
        "args": {"source_tool": "store_memory", "limit": 10},
        "category": "analytics"
    },
    
    # Code Pattern Memory (3 tools)
    {
        "name": "log_code_attempt",
        "args": {
            "input_prompt": "Create statistics display function",
            "generated_code": "def show_stats(): return get_tool_stats()",
            "result": "pass",
            "tags": ["statistics", "analytics"]
        },
        "category": "code_patterns"
    },
    {
        "name": "get_code_patterns",
        "args": {"query": "statistics function", "top_k": 5},
        "category": "code_patterns"
    },
    {
        "name": "analyze_code_patterns",
        "args": {"patterns": ["statistics", "analytics"]},
        "category": "code_patterns"
    },
    
    # Redis Cache Operations (3 tools)
    {
        "name": "redis_health_check",
        "args": {},
        "category": "redis"
    },
    {
        "name": "redis_cache_stats", 
        "args": {},
        "category": "redis"
    },
    {
        "name": "redis_flush_cache",
        "args": {"cache_type": "query"},
        "category": "redis"
    }
]

def test_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Test a single LTMC tool and return result."""
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

def get_tool_usage_statistics() -> Dict[str, Any]:
    """Get comprehensive tool usage statistics."""
    print("\n" + "=" * 60)
    print("📊 LTMC TOOL USAGE STATISTICS")
    print("=" * 60)
    
    stats = {}
    
    # Get Redis cache statistics
    print("\n🔥 Redis Cache Statistics:")
    cache_result = test_tool("redis_cache_stats", {})
    if cache_result["status"] == "PASS" and cache_result["result"]:
        cache_stats = cache_result["result"].get("stats", {})
        print(f"   Connected: {cache_stats.get('connected', 'Unknown')}")
        print(f"   Redis Version: {cache_stats.get('redis_version', 'Unknown')}")
        print(f"   Used Memory: {cache_stats.get('used_memory', 'Unknown')}")
        print(f"   Total Connections: {cache_stats.get('total_connections', 0)}")
        print(f"   Embedding Cache Count: {cache_stats.get('embedding_cache_count', 0)}")
        print(f"   Query Cache Count: {cache_stats.get('query_cache_count', 0)}")
        print(f"   Total Keys: {cache_stats.get('total_keys', 0)}")
        
        # Show additional cache performance stats if available
        if "hit_rate" in cache_stats:
            print(f"   Cache Hit Rate: {cache_stats.get('hit_rate', 0):.2%}")
        if "total_requests" in cache_stats:
            print(f"   Total Requests: {cache_stats.get('total_requests', 0)}")
    else:
        print("   ❌ Redis statistics unavailable")
    
    # Get tool identifiers and usage
    print("\n🔧 Tool Identifiers & Usage:")
    identifiers_result = test_tool("list_tool_identifiers", {})
    if identifiers_result["status"] == "PASS" and identifiers_result["result"]:
        id_data = identifiers_result["result"]
        tools_data = id_data.get("tools", [])
        print(f"   Active Tools: {len(tools_data)}")
        print(f"   Total Tools: {id_data.get('total_tools', 0)}")
        print(f"   Total Messages: {id_data.get('total_messages', 0)}")
        
        if tools_data:
            print("   Tool Usage Details:")
            for tool in tools_data:
                tool_id = tool.get("identifier", "unknown")
                msg_count = tool.get("message_count", 0)
                conv_count = tool.get("conversation_count", 0)
                status = tool.get("status", "unknown")
                print(f"     {tool_id}: {msg_count} messages, {conv_count} conversations, status: {status}")
    
    # Get context usage statistics
    print("\n📈 Context Usage Statistics:")
    context_result = test_tool("get_context_usage_statistics", {})
    if context_result["status"] == "PASS" and context_result["result"]:
        context_stats = context_result["result"].get("statistics", {})
        print(f"   Total Context Links: {context_stats.get('total_context_links', 0)}")
        print(f"   Total Messages: {context_stats.get('total_messages', 0)}")
        print(f"   Total Chunks: {context_stats.get('total_chunks', 0)}")
        print(f"   Avg Links per Message: {context_stats.get('avg_links_per_message', 0):.2f}")
        
        if "most_linked_chunks" in context_stats:
            print("   Most Linked Chunks:")
            for chunk in context_stats["most_linked_chunks"][:3]:
                print(f"     Chunk {chunk.get('chunk_id', 'N/A')}: {chunk.get('link_count', 0)} links")
    
    return stats

def run_comprehensive_test() -> Dict[str, Any]:
    """Run comprehensive test of all 28 LTMC tools with statistics."""
    print("🚀 Starting LTMC 28-Tool Test Suite with Statistics")
    print("=" * 70)
    
    results = []
    passed = 0
    failed = 0
    errors = 0
    category_stats = {}
    
    # Run all tool tests
    for i, test_case in enumerate(TOOL_TESTS, 1):
        tool_name = test_case["name"]
        args = test_case["args"]
        category = test_case.get("category", "unknown")
        
        print(f"[{i:2d}/28] Testing {tool_name} ({category})...", end=" ")
        
        result = test_tool(tool_name, args)
        results.append(result)
        
        # Update category stats
        if category not in category_stats:
            category_stats[category] = {"passed": 0, "failed": 0, "errors": 0}
        
        if result["status"] == "PASS":
            print("✅ PASS")
            passed += 1
            category_stats[category]["passed"] += 1
        elif result["status"] == "FAIL":
            print("❌ FAIL")
            if result.get('error'):
                print(f"      Error: {result['error']}")
            failed += 1
            category_stats[category]["failed"] += 1
        else:
            print("🔥 ERROR")
            if result.get('error'):
                print(f"      Error: {result['error']}")
            errors += 1
            category_stats[category]["errors"] += 1
        
        # Small delay between tests
        time.sleep(0.1)
    
    # Display results summary
    print("\n" + "=" * 70)
    print("📊 LTMC Tool Test Results Summary:")
    print(f"   ✅ Passed: {passed}/28 ({passed/28*100:.1f}%)")
    print(f"   ❌ Failed: {failed}/28 ({failed/28*100:.1f}%)")
    print(f"   🔥 Errors: {errors}/28 ({errors/28*100:.1f}%)")
    print(f"   🎯 Success Rate: {passed/28*100:.1f}%")
    
    # Display category breakdown
    print("\n📂 Results by Category:")
    for category, stats in category_stats.items():
        total = stats["passed"] + stats["failed"] + stats["errors"]
        success_rate = (stats["passed"] / total * 100) if total > 0 else 0
        print(f"   {category.replace('_', ' ').title()}: {stats['passed']}/{total} ({success_rate:.1f}%)")
    
    if passed == 28:
        print("\n🎉 ALL 28 TOOLS WORKING - 100% SUCCESS RATE ACHIEVED!")
        print("🔥 LTMC SYSTEM IS FULLY OPERATIONAL!")
    elif passed >= 25:
        print("\n🚀 Excellent! Nearly complete tool coverage.")
    elif passed >= 21:
        print("\n👍 Good progress! Most tools working.")
    else:
        print("\n⚠️  Significant issues remain. More work needed.")
    
    # Get and display usage statistics
    get_tool_usage_statistics()
    
    # Show this test run's tool usage
    print("\n🧪 This Test Run Statistics:")
    test_tool_calls = {}
    for test_case in TOOL_TESTS:
        tool_name = test_case["name"]
        category = test_case.get("category", "unknown")
        if category not in test_tool_calls:
            test_tool_calls[category] = []
        test_tool_calls[category].append(tool_name)
    
    for category, tools in test_tool_calls.items():
        print(f"   {category.replace('_', ' ').title()}: {len(tools)} tools called")
        for tool in tools:
            status = "✅" if any(r["tool"] == tool and r["status"] == "PASS" for r in results) else "❌"
            print(f"     {status} {tool}")
    
    return {
        "total_tools": 28,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "success_rate": passed/28*100,
        "category_breakdown": category_stats,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """Main function to run the comprehensive test suite."""
    try:
        print(f"🕐 Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check server connectivity
        try:
            response = requests.get("http://localhost:5050/health", timeout=5)
            if response.status_code != 200:
                print(f"❌ LTMC Server not responding properly (status: {response.status_code})")
                print("   Please ensure LTMC server is running on localhost:5050")
                return 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to LTMC server: {e}")
            print("   Please start the server with: ./start_server.sh")
            return 1
        
        # Run comprehensive test
        summary = run_comprehensive_test()
        
        # Save detailed results to file
        results_file = f"ltmc_tools_stats_results_{int(time.time())}.json"
        with open(results_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"\n📝 Detailed results saved to: {results_file}")
        print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Return exit code based on success rate
        if summary["success_rate"] == 100:
            return 0
        elif summary["success_rate"] >= 90:
            return 0
        else:
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        print(f"💥 Test crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())