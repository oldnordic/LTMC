"""
LTMC Unix Filesystem Action Module
File system operations with modern tools and fallbacks
"""

import subprocess
import re
from typing import Dict, Any


def unix_filesystem_action(action: str, **params) -> Dict[str, Any]:
    """File system utilities with real external tool integration.
    
    Actions: ls, cat, tree, find
    
    This module handles file system operations using modern tools like exa, bat, 
    tree, and fd with appropriate fallbacks to traditional commands.
    
    Args:
        action: The filesystem action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'ls':
        return _handle_ls_action(params)
    elif action == 'cat':
        return _handle_cat_action(params)
    elif action == 'tree':
        return _handle_tree_action(params)
    elif action == 'find':
        return _handle_find_action(params)
    else:
        return {'success': False, 'error': f'Unknown filesystem action: {action}'}


def _handle_ls_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle ls action using exa with fallback to ls."""
    try:
        path = params.get('path', '.')
        long_format = params.get('long', False)
        show_hidden = params.get('all', False)
        
        # Try modern exa first
        cmd = ['exa', '--color=never']
        if long_format:
            cmd.append('-l')
        if show_hidden:
            cmd.append('-a')
        cmd.append(path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return {
                'success': True,
                'files': lines,
                'path': path,
                'count': len(lines),
                'tool': 'exa',
                'raw_output': result.stdout
            }
        else:
            # Fall back to ls
            cmd_fallback = ['ls']
            if long_format:
                cmd_fallback.append('-l')
            if show_hidden:
                cmd_fallback.append('-a')
            cmd_fallback.append(path)
            
            result = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
                return {
                    'success': True,
                    'files': lines,
                    'path': path,
                    'count': len(lines),
                    'tool': 'ls (fallback)',
                    'raw_output': result.stdout
                }
            else:
                return {'success': False, 'error': f'ls failed: {result.stderr}'}
                
    except Exception as e:
        return {'success': False, 'error': f'Unix ls failed: {str(e)}'}


def _handle_cat_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle cat action using bat with fallback to cat."""
    try:
        file_path = params.get('file_path')
        if not file_path:
            return {'success': False, 'error': 'Missing required parameter: file_path'}
        
        # Try bat with syntax highlighting
        cmd = ['bat', '--color=never', '--plain', file_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                'success': True,
                'content': result.stdout,
                'file_path': file_path,
                'tool': 'bat',
                'lines': len(result.stdout.split('\n'))
            }
        else:
            # Fall back to cat
            cmd_fallback = ['cat', file_path]
            result = subprocess.run(cmd_fallback, capture_output=True, text=True)
            if result.returncode == 0:
                return {
                    'success': True,
                    'content': result.stdout,
                    'file_path': file_path,
                    'tool': 'cat (fallback)',
                    'lines': len(result.stdout.split('\n'))
                }
            else:
                return {'success': False, 'error': f'cat failed: {result.stderr}'}
                
    except Exception as e:
        return {'success': False, 'error': f'Unix cat failed: {str(e)}'}


def _handle_tree_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tree action for directory visualization."""
    try:
        path = params.get('path', '.')
        
        # Use tree for directory visualization
        cmd = ['tree', '--charset=ascii']
        
        max_depth = params.get('max_depth')
        if max_depth:
            cmd.extend(['-L', str(max_depth)])
        
        if params.get('show_hidden', False):
            cmd.append('-a')
        
        if params.get('directories_only', False):
            cmd.append('-d')
        
        cmd.append(path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse tree output to extract counts
            lines = result.stdout.split('\n')
            last_line = lines[-2] if len(lines) > 1 else ''
            
            directory_count = 0
            file_count = 0
            if 'directories' in last_line and 'files' in last_line:
                dir_match = re.search(r'(\d+) directories', last_line)
                file_match = re.search(r'(\d+) files', last_line)
                if dir_match:
                    directory_count = int(dir_match.group(1))
                if file_match:
                    file_count = int(file_match.group(1))
            
            return {
                'success': True,
                'tree_output': result.stdout,
                'root_path': path,
                'max_depth': max_depth,
                'directory_count': directory_count,
                'file_count': file_count,
                'tool': 'tree'
            }
        else:
            return {'success': False, 'error': f'tree failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix tree failed: {str(e)}'}


def _handle_find_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle find action using fd (fast find)."""
    try:
        pattern = params.get('pattern')
        path = params.get('path', '.')
        if not pattern:
            return {'success': False, 'error': 'Missing required parameter: pattern'}
        
        # Use fd (fast find)
        cmd = ['fd', '--color=never']
        
        # Add type filter if specified
        type_filter = params.get('type_filter')
        if type_filter == 'f':
            cmd.extend(['--type', 'f'])
        elif type_filter == 'd':
            cmd.extend(['--type', 'd'])
        
        # Add extension filter if specified
        extension = params.get('extension')
        if extension:
            cmd.extend(['--extension', extension])
        
        # Add max depth if specified
        max_depth = params.get('max_depth')
        if max_depth:
            cmd.extend(['--max-depth', str(max_depth)])
        
        # Handle glob patterns vs regex patterns
        if '*' in pattern or '?' in pattern or '[' in pattern:
            # It's a glob pattern - use --glob
            cmd.extend(['--glob', pattern, path])
        else:
            # It's a regex pattern or simple string
            cmd.extend([pattern, path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            files_found = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return {
                'success': True,
                'files_found': files_found,
                'pattern': pattern,
                'search_path': path,
                'count': len(files_found),
                'tool': 'fd',
                'raw_output': result.stdout
            }
        else:
            return {'success': False, 'error': f'fd failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix find failed: {str(e)}'}