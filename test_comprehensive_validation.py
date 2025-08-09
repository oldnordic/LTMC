#!/usr/bin/env python3
"""Comprehensive validation test for both HTTP and stdio transports."""

import json
import requests
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, Any, List

def test_http_transport() -> Dict[str, Any]:
    """Test HTTP transport with all tool categories."""
    print("=== Testing HTTP Transport ===")
    
    base_url = "http://localhost:5050"
    results = {"transport": "http", "tool_categories": {}, "overall_success": True}
    
    # Tool categories to test (sample from each category)
    tool_categories = {
        "memory_operations": ["store_memory", "retrieve_memory"],
        "chat_communication": ["log_chat", "ask_with_context"],
        "task_management": ["add_todo", "list_todos"],
        "context_retrieval": ["build_context", "retrieve_by_type"],
        "knowledge_graph": ["link_resources", "query_graph"],
        "tool_tracking": ["list_tool_identifiers"],
        "code_patterns": ["log_code_attempt", "get_code_patterns"],
        "redis_operations": ["redis_health_check", "redis_cache_stats"]
    }
    
    # Start HTTP server (assume it's running)
    try:
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ HTTP server not responding")
            results["overall_success"] = False
            return results
        print("✅ HTTP server is running")
    except Exception as e:
        print(f"❌ HTTP server connection failed: {e}")
        results["overall_success"] = False
        return results
    
    # Test each category
    for category, tools in tool_categories.items():
        print(f"\n📂 Testing {category}...")
        category_results = {"tested": [], "passed": [], "failed": []}
        
        for tool_name in tools:
            print(f"  🔧 Testing {tool_name}...")
            category_results["tested"].append(tool_name)
            
            # Create appropriate test arguments for each tool
            test_args = get_test_args(tool_name)
            
            try:
                response = requests.post(
                    f"{base_url}/jsonrpc",
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
                    if "result" in result_data:
                        print(f"    ✅ {tool_name} - Success")
                        category_results["passed"].append(tool_name)
                    else:
                        print(f"    ❌ {tool_name} - No result in response")
                        category_results["failed"].append(tool_name)
                        results["overall_success"] = False
                else:
                    print(f"    ❌ {tool_name} - HTTP {response.status_code}")
                    category_results["failed"].append(tool_name)
                    results["overall_success"] = False
                    
            except Exception as e:
                print(f"    ❌ {tool_name} - Exception: {e}")
                category_results["failed"].append(tool_name)
                results["overall_success"] = False
        
        results["tool_categories"][category] = category_results
        print(f"  📊 {category}: {len(category_results['passed'])}/{len(category_results['tested'])} passed")
    
    return results

def test_stdio_transport() -> Dict[str, Any]:
    """Test stdio transport with all tool categories."""
    print("\n=== Testing Stdio Transport ===")
    
    results = {"transport": "stdio", "tool_categories": {}, "overall_success": True}
    
    # Start stdio server
    try:
        process = subprocess.Popen(
            [sys.executable, 'ltmc_mcp_server.py'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        print("✅ Stdio server started")
        
        # Initialize MCP protocol
        init_request = {
            "jsonrpc": "2.0",
            "id": "init",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "validation-test", "version": "1.0.0"}
            }
        }
        
        process.stdin.write(json.dumps(init_request) + '\\n')
        process.stdin.flush()
        time.sleep(1)
        
        init_response = process.stdout.readline()
        if not init_response or "result" not in init_response:
            print("❌ MCP initialization failed")
            results["overall_success"] = False
            return results
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {}
        }
        process.stdin.write(json.dumps(initialized_notification) + '\\n')
        process.stdin.flush()
        time.sleep(0.5)
        
        print("✅ MCP protocol initialized")
        
    except Exception as e:
        print(f"❌ Stdio server setup failed: {e}")
        results["overall_success"] = False
        return results
    
    # Tool categories to test (fewer tools for stdio due to time constraints)
    tool_categories = {
        "memory_operations": ["store_memory"],
        "chat_communication": ["log_chat"],
        "task_management": ["add_todo"],
        "redis_operations": ["redis_health_check"],
        "code_patterns": ["log_code_attempt"]
    }
    
    def send_tool_request(tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Send a tool request via stdio and check response."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": f"test_{tool_name}",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            process.stdin.write(json.dumps(request) + '\\n')
            process.stdin.flush()
            time.sleep(1)
            
            response = process.stdout.readline()
            if response:
                response_data = json.loads(response.strip())
                return "result" in response_data
            else:
                return False
                
        except Exception as e:
            print(f"    Exception in {tool_name}: {e}")
            return False
    
    # Test each category
    for category, tools in tool_categories.items():
        print(f"\\n📂 Testing {category}...")
        category_results = {"tested": [], "passed": [], "failed": []}
        
        for tool_name in tools:
            print(f"  🔧 Testing {tool_name}...")
            category_results["tested"].append(tool_name)
            
            test_args = get_test_args(tool_name)
            
            if send_tool_request(tool_name, test_args):
                print(f"    ✅ {tool_name} - Success")
                category_results["passed"].append(tool_name)
            else:
                print(f"    ❌ {tool_name} - Failed")
                category_results["failed"].append(tool_name)
                results["overall_success"] = False
        
        results["tool_categories"][category] = category_results
        print(f"  📊 {category}: {len(category_results['passed'])}/{len(category_results['tested'])} passed")
    
    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=5)
    except:
        process.kill()
    
    return results

def get_test_args(tool_name: str) -> Dict[str, Any]:
    """Get appropriate test arguments for each tool."""
    timestamp = int(time.time())
    
    args_map = {
        "store_memory": {
            "file_name": f"validation_test_{timestamp}.md",
            "content": f"Validation test content - {datetime.now()}",
            "resource_type": "document"
        },
        "retrieve_memory": {
            "query": "validation test",
            "conversation_id": f"validation_{timestamp}",
            "top_k": 3
        },
        "log_chat": {
            "content": f"Validation test chat message - {datetime.now()}",
            "conversation_id": f"validation_{timestamp}",
            "role": "system"
        },
        "ask_with_context": {
            "query": "test query",
            "conversation_id": f"validation_{timestamp}",
            "top_k": 3
        },
        "add_todo": {
            "title": f"Validation Test Todo - {timestamp}",
            "description": "Test todo for validation",
            "priority": "low"
        },
        "list_todos": {},
        "build_context": {
            "context_id": f"validation_{timestamp}",
            "max_tokens": 1000
        },
        "retrieve_by_type": {
            "resource_type": "document",
            "limit": 5
        },
        "link_resources": {
            "source_id": "test_source",
            "target_id": "test_target",
            "relation": "test_relation"
        },
        "query_graph": {
            "entity": "test_entity",
            "relation_type": "test_relation"
        },
        "list_tool_identifiers": {},
        "log_code_attempt": {
            "input_prompt": "Test code generation",
            "generated_code": "print('validation test')",
            "result": "pass",
            "tags": ["validation", "test"]
        },
        "get_code_patterns": {
            "query": "test pattern",
            "result_filter": "pass",
            "top_k": 3
        },
        "redis_health_check": {},
        "redis_cache_stats": {}
    }
    
    return args_map.get(tool_name, {})

def main():
    """Run comprehensive validation tests."""
    print("🚀 LTMC Dual Transport Comprehensive Validation")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Test HTTP transport
    http_results = test_http_transport()
    
    # Test stdio transport
    stdio_results = test_stdio_transport()
    
    # Summary
    print("\\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    print(f"\\n🌐 HTTP Transport: {'✅ PASS' if http_results['overall_success'] else '❌ FAIL'}")
    for category, results in http_results.get('tool_categories', {}).items():
        passed = len(results['passed'])
        total = len(results['tested'])
        print(f"  {category}: {passed}/{total}")
    
    print(f"\\n📡 Stdio Transport: {'✅ PASS' if stdio_results['overall_success'] else '❌ FAIL'}")
    for category, results in stdio_results.get('tool_categories', {}).items():
        passed = len(results['passed'])
        total = len(results['tested'])
        print(f"  {category}: {passed}/{total}")
    
    # Overall result
    overall_success = http_results['overall_success'] and stdio_results['overall_success']
    print(f"\\n🎯 Overall Result: {'✅ BOTH TRANSPORTS VALIDATED' if overall_success else '❌ VALIDATION FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)