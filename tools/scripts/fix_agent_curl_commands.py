#!/usr/bin/env python3
"""
Fix Agent Curl Commands - Replace HTTP endpoints with MCP tools

This script specifically finds and replaces curl commands in agent files
that are trying to call non-existent HTTP endpoints, replacing them with
proper MCP tool call instructions.
"""

import os
import re
from pathlib import Path

def fix_curl_commands_in_file(file_path: Path) -> bool:
    """Fix curl commands in a single agent file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file has curl commands to fix
        if 'curl -s http://localhost:5050/jsonrpc' not in content:
            return False
        
        print(f"🔧 Fixing curl commands in {file_path.name}")
        
        # Replace store_memory curl command
        store_memory_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "store_memory".*?\'\)'
        store_memory_replacement = '''Use mcp__ltmc__store_memory with parameters:
- content: "Pattern, successful approach, or key insight"  
- file_name: "pattern_YYYYMMDD_HHMMSS.md"
- resource_type: "document" or "code"'''
        
        # Replace retrieve_memory curl command  
        retrieve_memory_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "retrieve_memory".*?\'\)'
        retrieve_memory_replacement = '''Use mcp__ltmc__retrieve_memory with parameters:
- query: "search keywords for similar solutions"
- conversation_id: "session_name"
- top_k: 5'''

        # Replace log_code_attempt curl command
        log_code_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "log_code_attempt".*?\'\)'
        log_code_replacement = '''Use mcp__ltmc__log_code_attempt with parameters:
- input_prompt: "What you were implementing"
- generated_code: "The actual implementation code"
- result: "pass" or "fail"'''

        # Replace get_code_patterns curl command
        get_patterns_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "get_code_patterns".*?\'\)'
        get_patterns_replacement = '''Use mcp__ltmc__get_code_patterns with parameters:
- query: "implementation approach keywords"
- result_filter: "pass"
- top_k: 3'''

        # Replace analyze_code_patterns curl command
        analyze_patterns_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "analyze_code_patterns".*?\'\)'
        analyze_patterns_replacement = '''Use mcp__ltmc__analyze_code_patterns with parameters:
- query: "optimization patterns keywords"
- limit: 10'''

        # Replace add_todo curl command
        add_todo_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "add_todo".*?\'\)'
        add_todo_replacement = '''Use mcp__ltmc__add_todo with parameters:
- title: "Task description"
- description: "Detailed task breakdown and requirements"
- priority: "high", "medium", or "low"'''

        # Replace link_resources curl command
        link_resources_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "link_resources".*?\'\)'
        link_resources_replacement = '''Use mcp__ltmc__link_resources with parameters:
- source_id: "resource_1"
- target_id: "resource_2"
- relation: "relates_to"'''

        # Replace log_chat curl command
        log_chat_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "log_chat".*?\'\)'
        log_chat_replacement = '''Use mcp__ltmc__log_chat with parameters:
- content: "Decision reasoning and approach documentation"
- conversation_id: "session_decisions"
- role: "assistant"'''

        # Replace query_graph curl command  
        query_graph_pattern = r'Bash\(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\\n-d \'.*?"name": "query_graph".*?\'\)'
        query_graph_replacement = '''Use mcp__ltmc__query_graph with parameters:
- entity: "entity_name"
- relation_type: "depends_on" or other relation type'''

        # Apply all replacements
        original_content = content
        
        # Use DOTALL flag to handle multi-line patterns
        content = re.sub(store_memory_pattern, store_memory_replacement, content, flags=re.DOTALL)
        content = re.sub(retrieve_memory_pattern, retrieve_memory_replacement, content, flags=re.DOTALL)
        content = re.sub(log_code_pattern, log_code_replacement, content, flags=re.DOTALL)
        content = re.sub(get_patterns_pattern, get_patterns_replacement, content, flags=re.DOTALL)
        content = re.sub(analyze_patterns_pattern, analyze_patterns_replacement, content, flags=re.DOTALL)
        content = re.sub(add_todo_pattern, add_todo_replacement, content, flags=re.DOTALL)
        content = re.sub(link_resources_pattern, link_resources_replacement, content, flags=re.DOTALL)
        content = re.sub(log_chat_pattern, log_chat_replacement, content, flags=re.DOTALL)
        content = re.sub(query_graph_pattern, query_graph_replacement, content, flags=re.DOTALL)
        
        # Check if any changes were made
        if content == original_content:
            print(f"  ⚠️ No curl patterns matched in {file_path.name}")
            return False
        
        # Write the updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✅ Fixed curl commands in {file_path.name}")
        return True
        
    except Exception as e:
        print(f"  ❌ Error fixing {file_path.name}: {e}")
        return False

def main():
    """Main function to fix curl commands in all agent files"""
    agents_dir = Path.home() / '.claude' / 'agents'
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return 1
    
    print("🔧 Fixing curl commands in all agent files...")
    print(f"📂 Agents directory: {agents_dir}")
    
    fixed_count = 0
    total_files = 0
    
    # Process all agent files
    for agent_file in agents_dir.rglob('*.md'):
        if agent_file.name == 'README.md':
            continue
        
        total_files += 1
        if fix_curl_commands_in_file(agent_file):
            fixed_count += 1
    
    print(f"\n✅ Completed: Fixed curl commands in {fixed_count}/{total_files} agent files")
    
    if fixed_count > 0:
        print(f"""
🎉 Agent Curl Command Fix Summary:
- Fixed {fixed_count} agent files
- All curl HTTP endpoints replaced with MCP tool calls
- Agents can now properly use LTMC MCP tools via stdio protocol

🔧 Changes Made:
- Replaced 'Bash(curl...)' with 'Use mcp__ltmc__tool_name'
- Simplified parameter format for clarity
- Removed non-existent HTTP endpoint references
        """)
    
    return 0

if __name__ == '__main__':
    exit(main())