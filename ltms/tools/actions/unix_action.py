"""
LTMC Unix Action Module
Unified interface for modular Unix utilities
"""

from typing import Dict, Any
from ltms.tools.actions.unix_filesystem import unix_filesystem_action
from ltms.tools.actions.unix_text_search import unix_text_search_action
from ltms.tools.actions.unix_text_syntax import unix_text_syntax_action
from ltms.tools.actions.unix_modern_tools import unix_modern_tools_action


def unix_action(action: str, **params) -> Dict[str, Any]:
    """Unix utilities with real external tool integration.
    
    Actions: ls, cat, grep, find, tree, jq, list_modern, disk_usage, help, 
             diff_highlight, fuzzy_select, parse_syntax, syntax_highlight, syntax_query
             
    This is a unified interface that delegates to the appropriate modular unix components
    based on the action type. Each module handles a specific category of operations.
    
    Args:
        action: The unix action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    # File system operations: ls, cat, tree, find
    if action in ['ls', 'cat', 'tree', 'find']:
        return unix_filesystem_action(action, **params)
    
    # Text search operations: grep
    elif action in ['grep']:
        return unix_text_search_action(action, **params)
    
    # Text syntax operations: jq, parse_syntax, syntax_highlight, syntax_query  
    elif action in ['jq', 'parse_syntax', 'syntax_highlight', 'syntax_query']:
        return unix_text_syntax_action(action, **params)
    
    # Modern tools operations: list_modern, disk_usage, help, diff_highlight, fuzzy_select
    elif action in ['list_modern', 'disk_usage', 'help', 'diff_highlight', 'fuzzy_select']:
        return unix_modern_tools_action(action, **params)
    
    else:
        return {'success': False, 'error': f'Unknown unix action: {action}'}