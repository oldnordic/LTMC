#!/usr/bin/env python3
"""Comprehensive test of all 52 LTMC tools via stdio MCP transport only."""

import json
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Any

def test_stdio_transport() -> Dict[str, Any]:
    """Test all 52 tools via stdio MCP transport."""
    print("📡 Testing Stdio MCP Transport - All 52 Tools")
    print("=" * 50)
    
    results = {"transport": "stdio", "tools_tested": [], "passed": [], "failed": [], "errors": {}}
    timestamp = int(time.time())
    
    # Expected 52 tools (current consolidated architecture)
    expected_tools = [
        # Memory & Context (7 tools)
        "store_memory", "retrieve_memory", "ask_with_context", "route_query", 
        "build_context", "retrieve_by_type", "log_chat",
        
        # Todo Management (4 tools)
        "add_todo", "list_todos", "complete_todo", "search_todos",
        
        # Context Linking (4 tools)
        "store_context_links", "get_context_links_for_message", 
        "get_messages_for_chunk", "get_context_usage_statistics",
        
        # Neo4j Graph (4 tools)
        "link_resources", "query_graph", "auto_link_documents", "get_document_relationships",
        
        # Code Patterns (3 tools)
        "log_code_attempt", "get_code_patterns", "analyze_code_patterns",
        
        # Chat Analysis (3 tools)
        "get_chats_by_tool", "list_tool_identifiers", "get_tool_conversations",
        
        # Redis Operations (3 tools)
        "redis_cache_stats", "redis_flush_cache", "redis_health_check",
        
        # Documentation Sync (18 tools)
        "sync_documentation_with_code", "validate_documentation_consistency", 
        "detect_documentation_drift", "update_documentation_from_blueprint",
        "get_documentation_consistency_score", "start_real_time_documentation_sync",
        "get_documentation_sync_status", "generate_api_docs", "generate_architecture_diagram",
        "generate_progress_report", "update_documentation", "generate_advanced_documentation",
        "create_documentation_template", "maintain_documentation_integrity",
        "commit_documentation_changes", "generate_documentation_changelog",
        "validate_template_syntax", "check_neo4j_health",
        
        # Security & Projects (6 tools)
        "create_task_blueprint", "analyze_task_complexity", "get_task_dependencies",
        "update_blueprint_metadata", "list_project_blueprints", "resolve_blueprint_execution_order"
    ]
    
    try:
        # Start stdio server
        process = subprocess.Popen(
            ["python", "ltms/mcp_server.py"],
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
        for i, tool_name in enumerate(expected_tools, 1):
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
            "query": f"test {tool_name} routing"
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
            "documents": [],
            "max_tokens": 1000
        },
        "retrieve_by_type": {
            "query": "test",
            "doc_type": "document",
            "top_k": 5
        },
        "store_context_links": {
            "message_id": f"msg_{timestamp}",
            "chunk_ids": [1]
        },
        "get_context_links_for_message": {
            "message_id": f"msg_{timestamp}"
        },
        "get_messages_for_chunk": {
            "chunk_id": 1
        },
        "get_context_usage_statistics": {},
        
        # Knowledge graph operations
        "link_resources": {
            "source_id": f"source_{timestamp}",
            "target_id": f"target_{timestamp}",
            "relation": "test_relation"
        },
        "query_graph": {
            "entity": f"test_entity_{timestamp}"
        },
        "auto_link_documents": {
            "similarity_threshold": 0.7
        },
        "get_document_relationships": {
            "doc_id": f"doc_{timestamp}"
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
            "result": "pass"
        },
        "get_code_patterns": {
            "query": f"test {tool_name}",
            "result_filter": "pass",
            "top_k": 3
        },
        "analyze_code_patterns": {},
        
        # Redis operations
        "redis_cache_stats": {},
        "redis_flush_cache": {"cache_type": "queries"},
        "redis_health_check": {},
        
        # Documentation sync operations
        "sync_documentation_with_code": {
            "file_path": "test.py",
            "project_id": "test_project"
        },
        "validate_documentation_consistency": {
            "file_path": "test.py",
            "project_id": "test_project"
        },
        "detect_documentation_drift": {
            "file_path": "test.py",
            "project_id": "test_project"
        },
        "check_neo4j_health": {},
        
        # Task blueprint operations
        "create_task_blueprint": {
            "title": f"Test task {timestamp}",
            "description": "Test task description"
        },
        "analyze_task_complexity": {
            "title": "Test task",
            "description": "Test description"
        }
    }
    
    return args_map.get(tool_name, {})

def main():
    """Run comprehensive test of all 52 tools."""
    print("🚀 LTMC Comprehensive Tool Testing - All 52 Tools (stdio MCP only)")
    print(f"Started at: {datetime.now()}")
    print("=" * 60)
    
    # Test stdio transport (only transport available)
    stdio_results = test_stdio_transport()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    print(f"\n📡 Stdio MCP Transport:")
    print(f"   Tested: {len(stdio_results['tools_tested'])}/52 tools")
    print(f"   Passed: {len(stdio_results['passed'])}/52 tools")
    print(f"   Failed: {len(stdio_results['failed'])}/52 tools")
    
    # Show any failures
    if stdio_results['failed']:
        print(f"\n❌ Stdio Failures:")
        for tool in stdio_results['failed']:
            error = stdio_results['errors'].get(tool, 'Unknown')
            print(f"   - {tool}: {error}")
    
    # Final status
    stdio_success = len(stdio_results['passed']) == 52
    
    print(f"\n🎯 Final Results:")
    stdio_status = "✅ 52/52 PASS" if stdio_success else f"❌ {len(stdio_results['passed'])}/52 PASS"
    overall_status = "✅ ALL TOOLS WORKING" if stdio_success else "❌ ISSUES FOUND"
    
    print(f"   Stdio MCP Transport: {stdio_status}")
    print(f"   Overall: {overall_status}")
    
    return stdio_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)