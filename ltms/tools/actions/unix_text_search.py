"""
LTMC Unix Text Search Action Module
Text search operations using ripgrep and similar tools
"""

import subprocess
from typing import Dict, Any


def unix_text_search_action(action: str, **params) -> Dict[str, Any]:
    """Text search utilities with real external tool integration.
    
    Actions: grep
    
    This module handles text search operations using tools like ripgrep
    for fast and efficient pattern matching in files.
    
    Args:
        action: The text search action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'grep':
        return _handle_grep_action(params)
    else:
        return {'success': False, 'error': f'Unknown text search action: {action}'}


def _handle_grep_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle grep action using ripgrep."""
    try:
        pattern = params.get('pattern')
        path = params.get('path', '.')
        if not pattern:
            return {'success': False, 'error': 'Missing required parameter: pattern'}
        
        # Use ripgrep
        cmd = ['rg', '--color=never', '--line-number', pattern, path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        matches = []
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        try:
                            matches.append({
                                'file': parts[0],
                                'line_number': int(parts[1]),
                                'content': parts[2]
                            })
                        except ValueError:
                            # If line number parsing fails, treat as simple match
                            matches.append({
                                'file': parts[0],
                                'line_number': 1,
                                'content': ':'.join(parts[1:])
                            })
        
        return {
            'success': True,
            'matches': matches,
            'pattern': pattern,
            'path': path,
            'count': len(matches),
            'tool': 'ripgrep',
            'raw_output': result.stdout if result.returncode == 0 else result.stderr
        }
            
    except Exception as e:
        return {'success': False, 'error': f'Unix grep failed: {str(e)}'}