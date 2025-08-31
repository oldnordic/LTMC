"""
LTMC Tool Registry
Centralized registry for all consolidated MCP tools following python-mcp-sdk patterns
"""

from typing import Dict, Any, Callable


def get_consolidated_tools() -> Dict[str, Dict[str, Any]]:
    """Get the complete registry of consolidated LTMC tools.
    
    This registry follows python-mcp-sdk best practices with proper schemas,
    descriptions, and handler functions for all 11 consolidated tools.
    
    Returns:
        Dictionary mapping tool names to their definitions
    """
    
    # Import all modular tool functions
    from ltms.tools.monitoring.cache_actions import cache_action
    from ltms.tools.graph.graph_actions import graph_action
    from ltms.tools.unix.unix_actions import unix_action
    from ltms.tools.memory.memory_actions import memory_action
    from ltms.tools.todos.todo_actions import todo_action
    from ltms.tools.memory.chat_actions import chat_action
    from ltms.tools.patterns.pattern_actions import pattern_action
    from ltms.tools.blueprints.blueprint_actions import blueprint_action
    from ltms.tools.docs.documentation_actions import documentation_action
    from ltms.tools.sync.sync_actions import sync_action
    from ltms.tools.config.config_actions import config_action
    from ltms.tools.coordination.coordination_actions import coordination_action
    from ltms.tools.sprints.sprint_actions import sprint_action
    
    # Import Sequential MCP tools
    from ltms.integrations.sequential_thinking import get_sequential_mcp_tools
    
    # Get base consolidated tools
    base_tools = {
        "memory_action": {
            "handler": memory_action,
            "description": "Memory operations with real SQLite+FAISS implementation: store, retrieve, build_context",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store", "retrieve", "build_context", "retrieve_by_type", "ask_with_context"],
                        "description": "Memory action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "todo_action": {
            "handler": todo_action,
            "description": "Todo operations with real SQLite implementation: add, list, complete, search",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "list", "complete", "search"],
                        "description": "Todo action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "chat_action": {
            "handler": chat_action,
            "description": "Chat operations with real SQLite implementation: log, get_by_tool, get_tool_conversations, route_query",
            "schema": {
                "type": "object", 
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["log", "get_by_tool", "get_tool_conversations", "route_query"],
                        "description": "Chat action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "unix_action": {
            "handler": unix_action,
            "description": "Unix utilities with real external tool integration: ls(exa), cat(bat), grep(ripgrep), find(fd), tree, jq, lsd, duf, tldr, delta, fzf",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ls", "cat", "grep", "find", "tree", "jq", "list_modern", "disk_usage", "help", "diff_highlight", "fuzzy_select", "parse_syntax", "syntax_highlight", "syntax_query"],
                        "description": "Unix action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "pattern_action": {
            "handler": pattern_action,
            "description": "Code pattern analysis with real Python AST implementation: extract_functions, extract_classes, summarize_code",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["extract_functions", "extract_classes", "extract_comments", "summarize_code", "log_attempt", "get_patterns", "analyze_patterns"],
                        "description": "Pattern analysis action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "blueprint_action": {
            "handler": blueprint_action,
            "description": "Blueprint management with real SQLite+Neo4j implementation: create, analyze_complexity, list_project, add_dependency, resolve_order, update_metadata, get_dependencies, delete",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create", "analyze_complexity", "list_project", "add_dependency", "resolve_order", "update_metadata", "get_dependencies", "delete"],
                        "description": "Blueprint action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "cache_action": {
            "handler": cache_action,
            "description": "Cache operations with real Redis implementation: health_check, stats, flush, reset",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["health_check", "stats", "flush", "reset"],
                        "description": "Cache action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "graph_action": {
            "handler": graph_action,
            "description": "Knowledge graph operations with real Neo4j implementation: link, query, auto_link, get_relationships",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["link", "query", "auto_link", "get_relationships", "stats"],
                        "description": "Graph action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "documentation_action": {
            "handler": documentation_action,
            "description": "Documentation operations with real internal implementation: generate_api_docs, generate_architecture_diagram, sync_documentation_with_code, validate_documentation_consistency",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["generate_api_docs", "generate_architecture_diagram", "sync_documentation_with_code", "validate_documentation_consistency"],
                        "description": "Documentation action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "sync_action": {
            "handler": sync_action,
            "description": "Documentation synchronization with real internal implementation: code, validate, drift, blueprint, score, monitor, status",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["code", "validate", "drift", "blueprint", "score", "monitor", "status"],
                        "description": "Sync action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "config_action": {
            "handler": config_action,
            "description": "Configuration management with real internal implementation: validate_config, get_config_schema, export_config",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["validate_config", "get_config_schema", "export_config"],
                        "description": "Config action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "coordination_action": {
            "handler": coordination_action,
            "description": "Agent coordination with external file-based state: store_analysis, retrieve_handoff, update_status, list_pending, create_workflow",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["store_analysis", "retrieve_handoff", "update_status", "list_pending", "create_workflow", "store_handoff", "get_workflow_state", "log_coordination_activity"],
                        "description": "Coordination action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        },
        
        "sprint_action": {
            "handler": sprint_action,
            "description": "Professional sprint management with LTMC integration: projects, sprints, stories, tasks, coordination",
            "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_project", "list_projects", "create_sprint", "list_sprints", "start_sprint", "complete_sprint", "create_story", "list_stories", "assign_story", "create_task", "complete_task", "get_sprint_dashboard", "create_sprint_workflow", "link_coordination", "transition_workflow_state", "get_workflow_state", "list_workflow_types"],
                        "description": "Sprint management action to perform"
                    }
                },
                "required": ["action"],
                "additionalProperties": True
            }
        }
    }
    
    # Add Sequential MCP tools to the registry
    sequential_tools = get_sequential_mcp_tools()
    base_tools.update(sequential_tools)
    
    return base_tools


# Legacy alias for backward compatibility
CONSOLIDATED_TOOLS = get_consolidated_tools()