#!/usr/bin/env python3
"""
Final Corrected Comprehensive LTMC Tool Validation Suite
Tests ALL 28 LTMC tools with properly researched parameter signatures.
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import time


class LTMCToolTesterFinal:
    """Final corrected comprehensive tester for all 28 LTMC tools"""
    
    def __init__(self, base_url: str = "http://localhost:5050"):
        self.base_url = base_url
        self.jsonrpc_url = f"{base_url}/jsonrpc"
        self.test_session_id = f"test_session_{int(time.time())}"
        self.results = {}
        self.errors = []
        self.test_data = {}
        
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a single LTMC tool via JSON-RPC"""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": 1
        }
        
        try:
            response = requests.post(
                self.jsonrpc_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result and result["error"]:
                self.errors.append(f"{tool_name}: {result['error']}")
                return {"success": False, "error": result["error"]}
            
            return result.get("result", {})
            
        except Exception as e:
            error_msg = f"{tool_name}: {str(e)}"
            self.errors.append(error_msg)
            return {"success": False, "error": str(e)}
    
    def test_memory_tools(self) -> Dict[str, Any]:
        """Test Memory tools (2): store_memory, retrieve_memory"""
        print("Testing Memory Tools...")
        results = {}
        
        # Test 1: store_memory
        store_result = self.call_tool("store_memory", {
            "file_name": f"test_validation_{self.test_session_id}.md",
            "content": f"Test document for comprehensive LTMC validation at {datetime.now().isoformat()}",
            "resource_type": "document"
        })
        results["store_memory"] = store_result
        
        # Test 2: retrieve_memory (note parameter order: conversation_id FIRST)
        retrieve_result = self.call_tool("retrieve_memory", {
            "conversation_id": self.test_session_id,
            "query": "comprehensive LTMC validation",
            "top_k": 3
        })
        results["retrieve_memory"] = retrieve_result
        
        return results
    
    def test_chat_tools(self) -> Dict[str, Any]:
        """Test Chat tools (4): log_chat, ask_with_context, route_query, get_chats_by_tool"""
        print("Testing Chat Tools...")
        results = {}
        
        # Test 1: log_chat (conversation_id FIRST, role SECOND)
        log_result = self.call_tool("log_chat", {
            "conversation_id": self.test_session_id,
            "role": "user",
            "content": f"Test chat message for validation at {datetime.now().isoformat()}"
        })
        results["log_chat"] = log_result
        
        # Test 2: ask_with_context
        ask_result = self.call_tool("ask_with_context", {
            "query": "What is LTMC validation testing?",
            "conversation_id": self.test_session_id,
            "top_k": 2
        })
        results["ask_with_context"] = ask_result
        
        # Test 3: route_query (keep the array format - seems to be signature issue)
        route_result = self.call_tool("route_query", {
            "query": "How do I test LTMC tools?",
            "source_types": ["memory", "documents"],
            "top_k": 2
        })
        results["route_query"] = route_result
        
        # Test 4: get_chats_by_tool (parameter is source_tool, not tool_identifier)
        chats_result = self.call_tool("get_chats_by_tool", {
            "source_tool": "log_chat",
            "limit": 5,
            "conversation_id": self.test_session_id
        })
        results["get_chats_by_tool"] = chats_result
        
        return results
    
    def test_todo_tools(self) -> Dict[str, Any]:
        """Test Todo tools (4): add_todo, list_todos, complete_todo, search_todos"""
        print("Testing Todo Tools...")
        results = {}
        
        # Test 1: add_todo
        add_result = self.call_tool("add_todo", {
            "title": f"Test Todo for Validation {self.test_session_id}",
            "description": "This is a test todo created during LTMC validation testing",
            "priority": "medium"
        })
        results["add_todo"] = add_result
        
        if add_result.get("success"):
            self.test_data["test_todo_id"] = add_result.get("todo_id")
        
        # Test 2: list_todos
        list_result = self.call_tool("list_todos", {
            "status": "all",
            "limit": 10
        })
        results["list_todos"] = list_result
        
        # Test 3: search_todos
        search_result = self.call_tool("search_todos", {
            "query": "validation testing"
        })
        results["search_todos"] = search_result
        
        # Test 4: complete_todo (if we have a test todo)
        if "test_todo_id" in self.test_data:
            complete_result = self.call_tool("complete_todo", {
                "todo_id": self.test_data["test_todo_id"]
            })
            results["complete_todo"] = complete_result
        else:
            results["complete_todo"] = {"success": False, "error": "No test todo ID available"}
        
        return results
    
    def test_context_tools(self) -> Dict[str, Any]:
        """Test Context tools (6): build_context, retrieve_by_type, store_context_links, 
        get_context_links_for_message, get_messages_for_chunk, get_context_usage_statistics"""
        print("Testing Context Tools...")
        results = {}
        
        # Test 1: build_context (may have JSON-RPC validation issues)
        build_result = self.call_tool("build_context", {
            "documents": [
                {"content": "Test document 1", "type": "document"},
                {"content": "Test document 2", "type": "document"}
            ],
            "max_tokens": 1000
        })
        results["build_context"] = build_result
        
        # Test 2: retrieve_by_type (may have JSON-RPC validation issues)
        retrieve_type_result = self.call_tool("retrieve_by_type", {
            "query": "LTMC validation testing",
            "doc_type": "document",
            "top_k": 5
        })
        results["retrieve_by_type"] = retrieve_type_result
        
        # Test 3: store_context_links (function name is store_context_links_tool, message_id as int)
        store_links_result = self.call_tool("store_context_links_tool", {
            "message_id": 123,
            "chunk_ids": [1, 2, 3]
        })
        results["store_context_links"] = store_links_result
        
        # Test 4: get_context_links_for_message (function name suffix _tool)
        get_links_result = self.call_tool("get_context_links_for_message_tool", {
            "message_id": 123
        })
        results["get_context_links_for_message"] = get_links_result
        
        # Test 5: get_messages_for_chunk (function name suffix _tool)
        get_messages_result = self.call_tool("get_messages_for_chunk_tool", {
            "chunk_id": 1
        })
        results["get_messages_for_chunk"] = get_messages_result
        
        # Test 6: get_context_usage_statistics (function name suffix _tool)
        stats_result = self.call_tool("get_context_usage_statistics_tool", {})
        results["get_context_usage_statistics"] = stats_result
        
        return results
    
    def test_graph_tools(self) -> Dict[str, Any]:
        """Test Graph tools (4): link_resources, query_graph, auto_link_documents, get_document_relationships"""
        print("Testing Graph Tools...")
        results = {}
        
        # Test 1: link_resources
        link_result = self.call_tool("link_resources", {
            "source_id": "test_resource_1",
            "target_id": "test_resource_2",
            "relation": "validates"
        })
        results["link_resources"] = link_result
        
        # Test 2: query_graph
        query_result = self.call_tool("query_graph", {
            "entity": "test_resource_1",
            "relation_type": "validates"
        })
        results["query_graph"] = query_result
        
        # Test 3: auto_link_documents (parameter is documents array, not document_id)
        auto_link_result = self.call_tool("auto_link_documents", {
            "documents": [
                {"id": "test_resource_1", "content": "Test content 1"},
                {"id": "test_resource_2", "content": "Test content 2"}
            ]
        })
        results["auto_link_documents"] = auto_link_result
        
        # Test 4: get_document_relationships (function name suffix _tool, parameter is doc_id)
        relationships_result = self.call_tool("get_document_relationships_tool", {
            "doc_id": "test_resource_1"
        })
        results["get_document_relationships"] = relationships_result
        
        return results
    
    def test_meta_tools(self) -> Dict[str, Any]:
        """Test Meta tools (2): list_tool_identifiers, get_tool_conversations"""
        print("Testing Meta Tools...")
        results = {}
        
        # Test 1: list_tool_identifiers
        list_tools_result = self.call_tool("list_tool_identifiers", {})
        results["list_tool_identifiers"] = list_tools_result
        
        # Test 2: get_tool_conversations (parameter is source_tool)
        tool_convs_result = self.call_tool("get_tool_conversations", {
            "source_tool": "store_memory",
            "limit": 5
        })
        results["get_tool_conversations"] = tool_convs_result
        
        return results
    
    def test_code_pattern_tools(self) -> Dict[str, Any]:
        """Test Code Pattern tools (3): log_code_attempt, get_code_patterns, analyze_code_patterns"""
        print("Testing Code Pattern Tools...")
        results = {}
        
        # Test 1: log_code_attempt (database schema: input_prompt, generated_code, result)
        log_code_result = self.call_tool("log_code_attempt", {
            "input_prompt": "Create a comprehensive LTMC test suite",
            "generated_code": "# Test suite code example\ndef test_ltmc_tools():\n    pass",
            "result": "pass",
            "language": "python"
        })
        results["log_code_attempt"] = log_code_result
        
        # Test 2: get_code_patterns (should work with database schema fields)
        get_patterns_result = self.call_tool("get_code_patterns", {
            "query": "LTMC test suite",
            "result_filter": "pass",
            "top_k": 3
        })
        results["get_code_patterns"] = get_patterns_result
        
        # Test 3: analyze_code_patterns (function name suffix _tool, parameters are function_name, file_name)
        analyze_result = self.call_tool("analyze_code_patterns_tool", {
            "function_name": "test_ltmc_tools"
        })
        results["analyze_code_patterns"] = analyze_result
        
        return results
    
    def test_redis_tools(self) -> Dict[str, Any]:
        """Test Redis tools (3): redis_cache_stats, redis_flush_cache, redis_health_check"""
        print("Testing Redis Tools...")
        results = {}
        
        # Test 1: redis_health_check
        health_result = self.call_tool("redis_health_check", {})
        results["redis_health_check"] = health_result
        
        # Test 2: redis_cache_stats
        stats_result = self.call_tool("redis_cache_stats", {})
        results["redis_cache_stats"] = stats_result
        
        # Test 3: redis_flush_cache (default is "all", or specific cache types)
        flush_result = self.call_tool("redis_flush_cache", {
            "cache_type": "all"
        })
        results["redis_flush_cache"] = flush_result
        
        return results
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all 28 LTMC tools"""
        print(f"Starting FINAL comprehensive LTMC tool validation at {datetime.now().isoformat()}")
        print(f"Test session ID: {self.test_session_id}")
        print("="*80)
        
        # Test all tool categories
        self.results["memory_tools"] = self.test_memory_tools()
        self.results["chat_tools"] = self.test_chat_tools() 
        self.results["todo_tools"] = self.test_todo_tools()
        self.results["context_tools"] = self.test_context_tools()
        self.results["graph_tools"] = self.test_graph_tools()
        self.results["meta_tools"] = self.test_meta_tools()
        self.results["code_pattern_tools"] = self.test_code_pattern_tools()
        self.results["redis_tools"] = self.test_redis_tools()
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("FINAL COMPREHENSIVE LTMC TOOL VALIDATION REPORT")
        print("="*80)
        
        total_tools = 28
        successful_tools = 0
        failed_tools = []
        
        for category, tools in self.results.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            for tool_name, result in tools.items():
                status = "✅ PASS" if result.get("success") else "❌ FAIL"
                print(f"  {tool_name}: {status}")
                
                if result.get("success"):
                    successful_tools += 1
                else:
                    failed_tools.append(f"{category}/{tool_name}")
                    if result.get("error"):
                        print(f"    Error: {result['error']}")
        
        print(f"\n" + "="*80)
        print("SUMMARY STATISTICS:")
        print(f"Total tools tested: {total_tools}")
        print(f"Successful tools: {successful_tools}")
        print(f"Failed tools: {len(failed_tools)}")
        print(f"Success rate: {(successful_tools/total_tools)*100:.1f}%")
        
        if failed_tools:
            print(f"\nFAILED TOOLS:")
            for tool in failed_tools:
                print(f"  - {tool}")
        
        if self.errors:
            print(f"\nERROR DETAILS:")
            for error in self.errors:
                print(f"  - {error}")
        
        # Additional analysis
        working_categories = []
        broken_categories = []
        
        for category, tools in self.results.items():
            category_success = sum(1 for result in tools.values() if result.get("success"))
            category_total = len(tools)
            category_rate = (category_success / category_total) * 100
            
            if category_rate >= 75:
                working_categories.append(f"{category}: {category_rate:.1f}%")
            else:
                broken_categories.append(f"{category}: {category_rate:.1f}%")
        
        if working_categories:
            print(f"\nWORKING CATEGORIES (≥75%):")
            for cat in working_categories:
                print(f"  - {cat}")
        
        if broken_categories:
            print(f"\nBROKEN CATEGORIES (<75%):")
            for cat in broken_categories:
                print(f"  - {cat}")
        
        report = {
            "test_session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "total_tools": total_tools,
            "successful_tools": successful_tools,
            "failed_tools": failed_tools,
            "success_rate": (successful_tools/total_tools)*100,
            "working_categories": working_categories,
            "broken_categories": broken_categories,
            "detailed_results": self.results,
            "errors": self.errors
        }
        
        return report


def main():
    """Main test execution function"""
    print("LTMC FINAL Comprehensive Tool Validation Suite")
    print("Testing ALL 28 tools with thoroughly researched parameter signatures")
    print("="*80)
    
    # Check if LTMC server is running
    try:
        response = requests.get("http://localhost:5050/health", timeout=5)
        response.raise_for_status()
        print("✅ LTMC server is running and healthy")
    except Exception as e:
        print(f"❌ LTMC server is not accessible: {e}")
        print("Please start the LTMC server with: ./start_server.sh")
        return
    
    # Initialize tester and run comprehensive test
    tester = LTMCToolTesterFinal()
    report = tester.run_comprehensive_test()
    
    # Save report to file
    report_filename = f"ltmc_final_validation_report_{int(time.time())}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📊 Detailed report saved to: {report_filename}")
    
    # Return summary for further processing
    return report


if __name__ == "__main__":
    report = main()