#!/usr/bin/env python3
"""Comprehensive test of all 28 LTMC tools for both HTTP and stdio transports."""

import json
import requests
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

def get_all_tools_http() -> List[str]:
    """Get all tool names from HTTP transport."""
    try:
        response = requests.get("http://localhost:5050/tools", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("tools", [])
    except Exception as e:
        print(f"❌ Failed to get tools from HTTP: {e}")
    return []

def test_http_transport(tools: List[str]) -> Dict[str, Any]:
    """Test all tools via HTTP transport."""
    print("🌐 Testing HTTP Transport - All 28 Tools")
    print("=" * 50)
    
    results = {"transport": "http", "tools_tested": [], "passed": [], "failed": [], "errors": {}}
    timestamp = int(time.time())
    
    for tool_name in tools:
        print(f"🔧 Testing {tool_name}...")
        results["tools_tested"].append(tool_name)
        
        # Get appropriate test arguments for each tool
        test_args = get_tool_test_args(tool_name, timestamp)
        
        try:
            response = requests.post(
                "http://localhost:5050/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": test_args
                    },
                    "id": f"test_{tool_name}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result_data = response.json()
                if "result" in result_data and not result_data.get("error"):
                    print(f"   ✅ {tool_name}")
                    results["passed"].append(tool_name)
                else:
                    print(f"   ❌ {tool_name} - Error in result")
                    results["failed"].append(tool_name)
                    results["errors"][tool_name] = result_data.get("error", "Unknown error")
            else:
                print(f"   ❌ {tool_name} - HTTP {response.status_code}")
                results["failed"].append(tool_name)
                results["errors"][tool_name] = f"HTTP {response.status_code}"
                
        except Exception as e:
            print(f"   ❌ {tool_name} - Exception: {e}")
            results["failed"].append(tool_name)
            results["errors"][tool_name] = str(e)
        
        # Small delay between requests
        time.sleep(0.1)
    
    print(f"\n📊 HTTP Results: {len(results['passed'])}/{len(results['tools_tested'])} passed")
    return results

def test_stdio_transport(tools: List[str]) -> Dict[str, Any]:
    """Test all tools via stdio transport."""
    print("\n📡 Testing Stdio Transport - All 28 Tools")
    print("=" * 50)
    
    results = {"transport": "stdio", "tools_tested": [], "passed": [], "failed": [], "errors": {}}
    timestamp = int(time.time())
    
    try:
        # Start stdio server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Initialize MCP protocol
        init_req = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "comprehensive-test", "version": "1.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_req) + '\n')
        process.stdin.flush()
        time.sleep(1)
        
        init_response = process.stdout.readline()
        if not init_response or "result" not in init_response:
            print("❌ MCP initialization failed")
            return results
        
        # Send initialized notification
        notif = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(notif) + '\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        # Test each tool
        for i, tool_name in enumerate(tools, 1):
            print(f"🔧 Testing {tool_name}...")
            results["tools_tested"].append(tool_name)
            
            test_args = get_tool_test_args(tool_name, timestamp)
            
            tool_req = {
                "jsonrpc": "2.0",
                "id": f"test_{i}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": test_args
                }
            }
            
            try:
                process.stdin.write(json.dumps(tool_req) + '\n')
                process.stdin.flush()
                time.sleep(1)  # Wait for response
                
                response = process.stdout.readline()
                if response and "result" in response:
                    resp_data = json.loads(response.strip())
                    if not resp_data.get("error"):
                        print(f"   ✅ {tool_name}")
                        results["passed"].append(tool_name)
                    else:
                        print(f"   ❌ {tool_name} - Error in result")
                        results["failed"].append(tool_name)
                        results["errors"][tool_name] = resp_data.get("error", "Unknown error")
                else:
                    print(f"   ❌ {tool_name} - No response")
                    results["failed"].append(tool_name)
                    results["errors"][tool_name] = "No response"
                    
            except Exception as e:
                print(f"   ❌ {tool_name} - Exception: {e}")
                results["failed"].append(tool_name)
                results["errors"][tool_name] = str(e)
        
        # Cleanup
        process.terminate()
        process.wait(timeout=3)
        
    except Exception as e:
        print(f"❌ Stdio transport setup failed: {e}")
        results["errors"]["setup"] = str(e)
    
    print(f"\n📊 Stdio Results: {len(results['passed'])}/{len(results['tools_tested'])} passed")
    return results

def get_tool_test_args(tool_name: str, timestamp: int) -> Dict[str, Any]:
    """Get appropriate test arguments for each tool."""
    
    args_map = {
        # Memory operations
        "store_memory": {
            "content": f"Comprehensive test {tool_name} - {timestamp}",
            "file_name": f"test_{tool_name}_{timestamp}.md",
            "resource_type": "document"
        },
        "retrieve_memory": {
            "query": f"test {tool_name}",
            "conversation_id": f"test_{timestamp}",
            "top_k": 3
        },
        
        # Chat operations
        "log_chat": {
            "content": f"Test {tool_name} message",
            "conversation_id": f"test_{timestamp}",
            "role": "system"
        },
        "ask_with_context": {
            "query": f"test {tool_name} query",
            "conversation_id": f"test_{timestamp}",
            "top_k": 3
        },
        "route_query": {
            "query": f"test {tool_name} routing",
            "conversation_id": f"test_{timestamp}"
        },
        "get_chats_by_tool": {
            "source_tool": "test_tool",
            "limit": 5
        },
        
        # Todo operations
        "add_todo": {
            "title": f"Test {tool_name} - {timestamp}",
            "description": f"Test todo for {tool_name}",
            "priority": "low"
        },
        "list_todos": {},
        "complete_todo": {"todo_id": 1},  # May fail if no todos exist, that's ok
        "search_todos": {"query": "test"},
        
        # Context operations
        "build_context": {
            "context_id": f"test_{tool_name}_{timestamp}",
            "max_tokens": 1000
        },
        "retrieve_by_type": {
            "resource_type": "document",
            "limit": 5
        },
        "store_context_links": {
            "message_id": f"msg_{timestamp}",
            "chunk_ids": ["chunk_1"]
        },
        "get_context_links_for_message": {
            "message_id": f"msg_{timestamp}"
        },
        "get_messages_for_chunk": {
            "chunk_id": f"chunk_{timestamp}"
        },
        "get_context_usage_statistics": {},
        
        # Knowledge graph operations
        "link_resources": {
            "source_id": f"source_{timestamp}",
            "target_id": f"target_{timestamp}",
            "relation": "test_relation"
        },
        "query_graph": {
            "entity": f"test_entity_{timestamp}",
            "relation_type": "test_relation"
        },
        "auto_link_documents": {
            "document_id": f"doc_{timestamp}",
            "similarity_threshold": 0.7
        },
        "get_document_relationships": {
            "document_id": f"doc_{timestamp}"
        },
        
        # Tool tracking
        "list_tool_identifiers": {},
        "get_tool_conversations": {
            "source_tool": "test_tool",
            "limit": 10
        },
        
        # Code patterns
        "log_code_attempt": {
            "input_prompt": f"Test {tool_name}",
            "generated_code": f"print('test_{tool_name}')",
            "result": "pass",
            "tags": ["test", tool_name]
        },
        "get_code_patterns": {
            "query": f"test {tool_name}",
            "result_filter": "pass",
            "top_k": 3
        },
        "analyze_code_patterns": {
            "tags": ["test"],
            "limit": 5
        },
        
        # Redis operations
        "redis_cache_stats": {},
        "redis_flush_cache": {"cache_type": "queries"},  # Use safer cache type
        "redis_health_check": {}
    }
    
    return args_map.get(tool_name, {})

def main():
    """Run comprehensive test of all 28 tools."""
    print("🚀 LTMC Comprehensive Tool Testing - All 28 Tools")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Get tool list from HTTP
    tools = get_all_tools_http()
    if not tools:
        print("❌ Failed to get tool list from HTTP transport")
        return False
    
    print(f"📋 Found {len(tools)} tools to test:")
    for i, tool in enumerate(tools, 1):
        print(f"   {i:2d}. {tool}")
    
    # Test HTTP transport
    http_results = test_http_transport(tools)
    
    # Test stdio transport
    stdio_results = test_stdio_transport(tools)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    print(f"\n🌐 HTTP Transport:")
    print(f"   Tested: {len(http_results['tools_tested'])}/28 tools")
    print(f"   Passed: {len(http_results['passed'])}/28 tools")
    print(f"   Failed: {len(http_results['failed'])}/28 tools")
    
    print(f"\n📡 Stdio Transport:")
    print(f"   Tested: {len(stdio_results['tools_tested'])}/28 tools")
    print(f"   Passed: {len(stdio_results['passed'])}/28 tools")
    print(f"   Failed: {len(stdio_results['failed'])}/28 tools")
    
    # Show any failures
    if http_results['failed']:
        print(f"\n❌ HTTP Failures:")
        for tool in http_results['failed']:
            error = http_results['errors'].get(tool, 'Unknown')
            print(f"   - {tool}: {error}")
    
    if stdio_results['failed']:
        print(f"\n❌ Stdio Failures:")
        for tool in stdio_results['failed']:
            error = stdio_results['errors'].get(tool, 'Unknown')
            print(f"   - {tool}: {error}")
    
    # Final status
    http_success = len(http_results['passed']) == 28
    stdio_success = len(stdio_results['passed']) == 28
    overall_success = http_success and stdio_success
    
    print(f"\n🎯 Final Results:")
    http_status = "✅ 28/28 PASS" if http_success else f"❌ {len(http_results['passed'])}/28 PASS"
    stdio_status = "✅ 28/28 PASS" if stdio_success else f"❌ {len(stdio_results['passed'])}/28 PASS"
    overall_status = "✅ ALL TOOLS WORKING" if overall_success else "❌ ISSUES FOUND"
    
    print(f"   HTTP Transport: {http_status}")
    print(f"   Stdio Transport: {stdio_status}")
    print(f"   Overall: {overall_status}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)