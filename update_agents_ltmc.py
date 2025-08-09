#!/usr/bin/env python3
"""
Agent LTMC Integration Updater

Systematically updates Claude Code sub-agent configurations to add mandatory LTMC
integration requirements. Ensures all agents comply with project LTMC usage mandates.

Usage:
    python update_agents_ltmc.py [--dry-run] [--agent-type TYPE]
    
Options:
    --dry-run       Show what would be changed without modifying files
    --agent-type    Only update specific agent type (e.g., 'engineering', 'design')
"""

import os
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Agent type configurations with specific LTMC tool sets
@dataclass
class AgentConfig:
    """Configuration for agent-specific LTMC integration"""
    mandatory_tools: List[str]  # Core tools ALL agents must use
    specialized_tools: List[str]  # Agent-specific tools
    primary_focus: str  # Main domain for LTMC storage
    tags: List[str]  # Common tags for code patterns

# Agent type configurations
AGENT_CONFIGS = {
    'engineering': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_code_attempt', 
            'get_code_patterns', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'analyze_code_patterns', 'link_resources', 'query_graph',
            'redis_cache_stats', 'redis_health_check'
        ],
        primary_focus='code',
        tags=['engineering', 'development', 'implementation']
    ),
    'design': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'link_resources', 'query_graph', 'auto_link_documents',
            'get_document_relationships'
        ],
        primary_focus='document',
        tags=['design', 'ui', 'ux', 'visual']
    ),
    'marketing': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'analyze_code_patterns', 'link_resources', 'auto_link_documents',
            'get_context_usage_statistics'
        ],
        primary_focus='document',
        tags=['marketing', 'content', 'growth', 'social']
    ),
    'product': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'link_resources', 'query_graph', 'get_document_relationships',
            'search_todos', 'list_todos'
        ],
        primary_focus='document', 
        tags=['product', 'strategy', 'research', 'feedback']
    ),
    'project-management': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat', 'add_todo',
            'list_todos', 'complete_todo', 'search_todos'
        ],
        specialized_tools=[
            'link_resources', 'query_graph', 'get_context_usage_statistics',
            'get_tool_conversations'
        ],
        primary_focus='document',
        tags=['project-management', 'coordination', 'process', 'workflow']
    ),
    'studio-operations': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'redis_cache_stats', 'redis_health_check', 'redis_flush_cache',
            'get_context_usage_statistics', 'list_tool_identifiers'
        ],
        primary_focus='document',
        tags=['operations', 'infrastructure', 'monitoring', 'support']
    ),
    'testing': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_code_attempt',
            'get_code_patterns', 'log_chat', 'add_todo'
        ],
        specialized_tools=[
            'analyze_code_patterns', 'link_resources', 'get_tool_conversations',
            'list_tool_identifiers'
        ],
        primary_focus='code',
        tags=['testing', 'quality', 'automation', 'validation']
    ),
    'bonus': AgentConfig(
        mandatory_tools=[
            'store_memory', 'retrieve_memory', 'log_chat'
        ],
        specialized_tools=[
            'ask_with_context', 'route_query', 'auto_link_documents'
        ],
        primary_focus='document',
        tags=['bonus', 'creative', 'experimental']
    )
}

def get_ltmc_integration_section(agent_type: str, agent_name: str) -> str:
    """Generate the MCP requirements section for an agent"""
    config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS['bonus'])
    
    section = f"""## 🚨 MANDATORY MCP USAGE REQUIREMENTS 🚨

**EVERY {agent_name.replace('-', ' ')} task MUST follow this pattern - NO EXCEPTIONS:**

1. **ALWAYS START WITH SEQUENTIAL THINKING**: Use `@sequential-thinking` to plan {agent_type} strategies
   ```
   Use sequentialthinking tool to analyze: requirements, approach, implementation phases, success criteria
   ```

2. **ALWAYS USE CONTEXT7 FOR BEST PRACTICES**: Get relevant documentation and best practices
   ```
   Use resolve-library-id and get-library-docs for domain-specific tools and frameworks
   ```

3. **ALWAYS USE LTMC FOR EVERYTHING**: Store ALL {agent_type} patterns and insights
   ```
   MANDATORY LTMC TOOLS (via Bash tool - auto-executes):"""

    # Add mandatory tools
    for tool in config.mandatory_tools:
        section += f"\n   - {tool}: {get_tool_description(tool, agent_type)}"
    
    # Add specialized tools
    for tool in config.specialized_tools:
        section += f"\n   - {tool}: {get_tool_description(tool, agent_type)}"
    
    section += """
   ```

**VIOLATION OF MCP USAGE = IMMEDIATE TASK FAILURE**
"""
    return section

def get_tool_description(tool: str, agent_type: str) -> str:
    """Get context-appropriate description for LTMC tool"""
    descriptions = {
        'store_memory': f'Store {agent_type} patterns, decisions, successful approaches',
        'retrieve_memory': f'Get similar {agent_type} solutions BEFORE starting work',
        'log_code_attempt': f'Track EVERY implementation attempt and result',
        'get_code_patterns': f'Retrieve successful {agent_type} patterns and solutions',
        'log_chat': f'Document {agent_type} decisions, reasoning, and learnings',
        'add_todo': f'Track complex {agent_type} tasks and multi-step work',
        'analyze_code_patterns': f'Review {agent_type} patterns for optimization',
        'link_resources': f'Connect {agent_type} resources and related components',
        'query_graph': f'Explore {agent_type} dependencies and relationships',
        'redis_cache_stats': 'Monitor cache performance for optimization',
        'redis_health_check': 'Verify system connectivity and health',
        'redis_flush_cache': 'Clear cache when needed for fresh data',
        'auto_link_documents': f'Automatically link related {agent_type} documents',
        'get_document_relationships': f'Explore {agent_type} document connections',
        'get_context_usage_statistics': f'Monitor {agent_type} context usage patterns',
        'list_todos': 'View all tracked tasks and priorities',
        'complete_todo': 'Mark tasks as completed when finished',
        'search_todos': 'Find specific tasks by content or priority',
        'get_tool_conversations': f'Review {agent_type} tool usage history',
        'list_tool_identifiers': 'Discover available tools and capabilities',
        'ask_with_context': f'Query with automatic {agent_type} context retrieval',
        'route_query': f'Smart routing for {agent_type} queries'
    }
    return descriptions.get(tool, f'{agent_type.title()} tool for enhanced functionality')

def get_ltmc_commands_section(agent_type: str, agent_name: str) -> str:
    """Generate the copy-paste ready LTMC commands section"""
    config = AGENT_CONFIGS.get(agent_type, AGENT_CONFIGS['bonus'])
    
    section = f"""## 🔥 LTMC INTEGRATION COMMANDS (COPY-PASTE READY)

### {agent_type.title()} Pattern Storage & Retrieval
```bash
# Store {agent_type} patterns and successful approaches
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "store_memory", 
  "arguments": {{
    "content": "{agent_type.title()} pattern, successful approach, or key insight",
    "file_name": "{agent_name}_pattern_$(date +%Y%m%d_%H%M%S).md",
    "resource_type": "{config.primary_focus}"
  }}
}}, "id": 1}}')

# Retrieve similar {agent_type} solutions BEFORE starting
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "retrieve_memory", 
  "arguments": {{
    "query": "{agent_type} approach or solution keywords",
    "conversation_id": "{agent_name}_session",
    "top_k": 5
  }}
}}, "id": 1}}')"""

    # Add code pattern commands for code-focused agents
    if config.primary_focus == 'code':
        section += f"""

# Get successful {agent_type} code patterns
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "get_code_patterns", 
  "arguments": {{
    "query": "{agent_type} implementation approach",
    "result_filter": "pass",
    "top_k": 3,
    "tags": {config.tags}
  }}
}}, "id": 1}}')"""

    section += f"""
```

### {agent_type.title()} Work Tracking"""

    # Add code attempt tracking for code-focused agents
    if 'log_code_attempt' in config.mandatory_tools or 'log_code_attempt' in config.specialized_tools:
        section += f"""
```bash
# Log EVERY {agent_type} implementation attempt
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "log_code_attempt", 
  "arguments": {{
    "input_prompt": "What you were implementing in {agent_type}",
    "generated_code": "The actual {agent_type} implementation or solution",
    "result": "pass",
    "tags": {config.tags}
  }}
}}, "id": 1}}')"""
        
        if 'analyze_code_patterns' in config.specialized_tools:
            section += f"""

# Analyze {agent_type} patterns for optimization  
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "analyze_code_patterns", 
  "arguments": {{
    "query": "{agent_type} optimization patterns",
    "limit": 10
  }}
}}, "id": 1}}')"""
    else:
        section += """
```bash
# Document decision-making and approach reasoning
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "log_chat", 
  "arguments": {
    "content": "Decision reasoning and approach documentation",
    "conversation_id": "''' + agent_name + '''_decisions",
    "role": "assistant"
  }
}, "id": 1}')"""

    section += """
```

### Task & Resource Management
```bash
# Track complex tasks and multi-step work
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "add_todo", 
  "arguments": {
    "title": "''' + agent_type.title() + ''' task description",
    "description": "Detailed task breakdown and requirements",
    "priority": "high"
  }
}, "id": 1}')"""

    # Add resource linking for agents that use it
    if 'link_resources' in config.specialized_tools:
        section += f"""

# Link related {agent_type} resources and components
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "link_resources", 
  "arguments": {{
    "source_id": "{agent_type}_resource_1",
    "target_id": "{agent_type}_resource_2", 
    "relation": "relates_to"
  }}
}}, "id": 1}}')"""

    # Add graph queries for agents that use them
    if 'query_graph' in config.specialized_tools:
        section += f"""

# Query {agent_type} relationships and dependencies
Bash(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \\
-d '{{"jsonrpc": "2.0", "method": "tools/call", "params": {{
  "name": "query_graph", 
  "arguments": {{
    "entity": "{agent_type}_entity",
    "relation_type": "depends_on"
  }}
}}, "id": 1}}')"""

    section += """
```
"""
    return section

def has_ltmc_integration(content: str) -> bool:
    """Check if agent already has LTMC integration"""
    indicators = [
        "🚨 MANDATORY MCP USAGE REQUIREMENTS 🚨",
        "LTMC INTEGRATION COMMANDS",
        "VIOLATION OF MCP USAGE = IMMEDIATE TASK FAILURE"
    ]
    return any(indicator in content for indicator in indicators)

def has_partial_mcp(content: str) -> bool:
    """Check if agent has partial MCP usage (needs LTMC commands)"""
    return "🚨 MANDATORY MCP USAGE REQUIREMENTS 🚨" in content and "🔥 LTMC INTEGRATION COMMANDS" not in content

def extract_agent_info(file_path: Path) -> Tuple[str, str]:
    """Extract agent name and type from file path"""
    agent_name = file_path.stem
    agent_type = file_path.parent.name
    return agent_name, agent_type

def find_insertion_points(content: str) -> Tuple[int, int]:
    """Find where to insert MCP requirements and LTMC commands"""
    lines = content.split('\n')
    
    # Find insertion point for MCP requirements (after description, before responsibilities)
    mcp_insert_line = -1
    ltmc_insert_line = -1
    
    # Look for responsibility section start (various patterns)
    responsibility_patterns = [
        'Your primary responsibilities',
        'Your responsibilities', 
        'Core Responsibilities',
        '### Core Responsibilities',
        '## Core Responsibilities',
        'responsibilities:',
        'Responsibilities:',
        'Core responsibilities',
        'Primary responsibilities'
    ]
    
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        if any(pattern in line_stripped for pattern in responsibility_patterns):
            mcp_insert_line = i
            break
    
    # Fallback: look for any section that looks like responsibilities
    if mcp_insert_line == -1:
        for i, line in enumerate(lines):
            if 'responsibilities' in line.lower() or 'expertise' in line.lower():
                mcp_insert_line = i
                break
    
    # Another fallback: look after system prompt section
    if mcp_insert_line == -1:
        for i, line in enumerate(lines):
            if 'system prompt' in line.lower() or '## system prompt' in line.lower():
                # Find next meaningful section
                for j in range(i + 1, len(lines)):
                    if lines[j].strip().startswith('#') and len(lines[j].strip()) > 1:
                        mcp_insert_line = j
                        break
                break
    
    # Look for goal section (usually at the end)
    goal_patterns = [
        'Your goal is',
        'Goal:',
        '### Goal',
        '## Goal',
        'goal' 
    ]
    
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line:
            if any(pattern in line for pattern in goal_patterns if 'your' in line.lower() or line.startswith('Goal')):
                ltmc_insert_line = i
                break
    
    # Fallback: insert before last meaningful line
    if ltmc_insert_line == -1:
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip() and not lines[i].startswith('  ') and not lines[i].startswith('\t'):
                ltmc_insert_line = i + 1  # Insert after the last meaningful line
                break
    
    return mcp_insert_line, ltmc_insert_line

def update_agent_file(file_path: Path, dry_run: bool = False) -> bool:
    """Update a single agent file with LTMC integration"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        agent_name, agent_type = extract_agent_info(file_path)
        
        # Skip if already has full LTMC integration
        if has_ltmc_integration(content):
            print(f"✓ {file_path.name} already has LTMC integration")
            return False
        
        print(f"📝 Updating {file_path.name} ({agent_type}/{agent_name})")
        
        updated_content = content
        
        # Handle partial MCP (needs LTMC commands only)
        if has_partial_mcp(content):
            print(f"  Adding LTMC commands section to {agent_name}")
            mcp_insert_line, ltmc_insert_line = find_insertion_points(content)
            
            if ltmc_insert_line != -1:
                lines = content.split('\n')
                ltmc_section = get_ltmc_commands_section(agent_type, agent_name)
                lines.insert(ltmc_insert_line, ltmc_section)
                updated_content = '\n'.join(lines)
            else:
                print(f"  ⚠️ Could not find insertion point for LTMC commands in {agent_name}")
                return False
                
        else:
            # Add full LTMC integration
            print(f"  Adding full LTMC integration to {agent_name}")
            mcp_insert_line, ltmc_insert_line = find_insertion_points(content)
            
            if mcp_insert_line == -1:
                print(f"  ⚠️ Could not find insertion point for MCP requirements in {agent_name}")
                return False
            
            lines = content.split('\n')
            
            # Insert MCP requirements
            mcp_section = get_ltmc_integration_section(agent_type, agent_name)
            lines.insert(mcp_insert_line, mcp_section)
            
            # Insert LTMC commands (adjust line number for previous insertion)
            if ltmc_insert_line != -1:
                ltmc_section = get_ltmc_commands_section(agent_type, agent_name)
                # Account for lines added by MCP section
                adjusted_ltmc_line = ltmc_insert_line + len(mcp_section.split('\n'))
                lines.insert(adjusted_ltmc_line, ltmc_section)
            
            updated_content = '\n'.join(lines)
        
        # Write updated content
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print(f"  ✓ Updated {agent_name}")
        else:
            print(f"  📋 Would update {agent_name} (dry run)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error updating {file_path.name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Update Claude Code sub-agent configurations with mandatory LTMC integration"
    )
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be changed without modifying files')
    parser.add_argument('--agent-type', type=str,
                       help='Only update specific agent type (e.g., engineering, design)')
    
    args = parser.parse_args()
    
    agents_dir = Path.home() / '.claude' / 'agents'
    
    if not agents_dir.exists():
        print(f"❌ Agents directory not found: {agents_dir}")
        return 1
    
    print(f"🚀 Updating Claude Code agents with LTMC integration...")
    print(f"📂 Agents directory: {agents_dir}")
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be modified")
    
    if args.agent_type:
        print(f"🎯 Filtering for agent type: {args.agent_type}")
    
    updated_count = 0
    total_count = 0
    
    # Process each agent type directory
    for type_dir in agents_dir.iterdir():
        if not type_dir.is_dir() or type_dir.name.startswith('.'):
            continue
        
        if args.agent_type and type_dir.name != args.agent_type:
            continue
        
        print(f"\n📁 Processing {type_dir.name} agents...")
        
        for agent_file in type_dir.glob('*.md'):
            if agent_file.name == 'README.md':
                continue
            
            total_count += 1
            if update_agent_file(agent_file, args.dry_run):
                updated_count += 1
    
    print(f"\n✅ Completed: {updated_count}/{total_count} agents updated")
    
    if updated_count > 0:
        print(f"""
🎉 LTMC Integration Update Summary:
- Updated {updated_count} agent configurations
- All agents now have mandatory MCP usage requirements
- Copy-paste ready LTMC commands included
- Project compliance requirements met

🔧 Next Steps:
1. Review updated agent configurations
2. Test agent functionality with LTMC integration
3. Commit changes to preserve LTMC compliance
        """)
    
    return 0

if __name__ == '__main__':
    exit(main())