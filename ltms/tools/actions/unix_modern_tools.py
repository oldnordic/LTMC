"""
LTMC Unix Modern Tools Action Module
Modern Unix utilities including lsd, duf, tldr, delta, and fzf
"""

import subprocess
import json
from typing import Dict, Any, List


def unix_modern_tools_action(action: str, **params) -> Dict[str, Any]:
    """Modern Unix utilities with enhanced tool integration.
    
    Actions: list_modern, disk_usage, help, diff_highlight, fuzzy_select
    
    This module handles modern Unix utilities that provide enhanced functionality
    over traditional commands with better output formatting and features.
    
    Args:
        action: The modern tool action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'list_modern':
        return _handle_list_modern_action(params)
    elif action == 'disk_usage':
        return _handle_disk_usage_action(params)
    elif action == 'help':
        return _handle_help_action(params)
    elif action == 'diff_highlight':
        return _handle_diff_highlight_action(params)
    elif action == 'fuzzy_select':
        return _handle_fuzzy_select_action(params)
    else:
        return {'success': False, 'error': f'Unknown modern tools action: {action}'}


def _handle_list_modern_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle list_modern action using lsd (modern ls alternative)."""
    try:
        path = params.get('path', '.')
        
        # Use lsd for modern ls alternative
        cmd = ['lsd', '--color=never']
        
        if params.get('long_format', False):
            cmd.append('-l')
        
        if params.get('show_all', False):
            cmd.append('-a')
        
        if params.get('tree_view', False):
            cmd.append('--tree')
        
        if params.get('classify', False):
            cmd.append('-F')
        
        cmd.append(path)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return {
                'success': True,
                'files': lines,
                'path': path,
                'count': len(lines),
                'formatted_output': result.stdout,
                'tool': 'lsd'
            }
        else:
            return {'success': False, 'error': f'lsd failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix list_modern failed: {str(e)}'}


def _handle_disk_usage_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle disk_usage action using duf (modern disk usage tool)."""
    try:
        path = params.get('path')
        output_format = params.get('output_format', 'human')
        
        # Use duf for modern disk usage
        cmd = ['duf']
        
        if output_format == 'json':
            cmd.append('--json')
        
        if path:
            # Filter to show only the filesystem containing this path
            cmd.extend(['--only', path])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if output_format == 'json':
                try:
                    disk_data = json.loads(result.stdout)
                    
                    total_size = sum(int(fs.get('size', 0)) for fs in disk_data)
                    available_space = sum(int(fs.get('avail', 0)) for fs in disk_data)
                    
                    return {
                        'success': True,
                        'disk_info': disk_data,
                        'total_size': total_size,
                        'available_space': available_space,
                        'format': 'json',
                        'tool': 'duf'
                    }
                except json.JSONDecodeError:
                    return {'success': False, 'error': 'Failed to parse duf JSON output'}
            else:
                return {
                    'success': True,
                    'output': result.stdout,
                    'format': 'human',
                    'tool': 'duf'
                }
        else:
            return {'success': False, 'error': f'duf failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix disk_usage failed: {str(e)}'}


def _handle_help_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle help action using tldr for concise command help."""
    try:
        command = params.get('command')
        if not command:
            return {'success': False, 'error': 'Missing required parameter: command'}
        
        # Use tldr for concise help
        cmd = ['tldr']
        
        if params.get('update_cache', False):
            cmd.append('--update')
        
        cmd.append(command)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Parse tldr output to extract examples
            content = result.stdout
            examples = []
            
            # Extract command examples from tldr output
            lines = content.split('\n')
            current_description = None
            for line in lines:
                line_stripped = line.strip()
                # Look for description lines (usually followed by blank line and command)
                if line_stripped and not line_stripped.startswith(' ') and ':' in line_stripped and not line_stripped.startswith('git '):
                    current_description = line_stripped.rstrip(':')
                elif line.startswith('  ') and line_stripped and current_description:
                    # This is likely a command line (indented)
                    command_line = line_stripped
                    examples.append({
                        'description': current_description,
                        'command': command_line
                    })
                    current_description = None
            
            return {
                'success': True,
                'command': params.get('command'),
                'help_content': content,
                'examples': examples,
                'tool': 'tldr'
            }
        else:
            return {'success': False, 'error': f'tldr failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix help failed: {str(e)}'}


def _handle_diff_highlight_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle diff_highlight action using delta for enhanced diff visualization."""
    try:
        file1 = params.get('file1')
        file2 = params.get('file2')
        
        if not file1 or not file2:
            return {'success': False, 'error': 'Missing required parameters: file1 and file2'}
        
        # Use delta for enhanced diff highlighting
        cmd = ['delta']
        
        if params.get('side_by_side', False):
            cmd.append('--side-by-side')
        
        if params.get('line_numbers', True):
            cmd.append('--line-numbers')
        
        # Create diff and pipe to delta
        diff_cmd = ['diff', '-u', file1, file2]
        diff_result = subprocess.run(diff_cmd, capture_output=True, text=True, timeout=30)
        
        if diff_result.stdout:
            # Pipe diff output to delta
            delta_result = subprocess.run(cmd, input=diff_result.stdout, capture_output=True, text=True, timeout=30)
            
            changes_detected = diff_result.returncode != 0
            
            return {
                'success': True,
                'diff_output': delta_result.stdout if delta_result.returncode == 0 else diff_result.stdout,
                'file1': file1,
                'file2': file2,
                'changes_detected': changes_detected,
                'tool': 'delta'
            }
        else:
            return {
                'success': True,
                'diff_output': 'No differences found',
                'file1': file1,
                'file2': file2,
                'changes_detected': False,
                'tool': 'delta'
            }
            
    except Exception as e:
        return {'success': False, 'error': f'Unix diff_highlight failed: {str(e)}'}


def _handle_fuzzy_select_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle fuzzy_select action using fzf for fuzzy finding."""
    try:
        input_list = params.get('input_list', [])
        query = params.get('query', '')
        
        if not input_list:
            return {'success': False, 'error': 'Missing required parameter: input_list'}
        
        # Use fzf for fuzzy finding (non-interactive mode for testing)
        cmd = ['fzf', '--filter', query] if query else ['fzf', '--print-query']
        
        if params.get('multi_select', False):
            cmd.append('--multi')
        
        # Prepare input for fzf
        input_text = '\n'.join(input_list)
        
        result = subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=30)
        
        selected_items = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        return {
            'success': True,
            'selected_items': selected_items,
            'query': query,
            'total_items': len(input_list),
            'matches': len(selected_items),
            'tool': 'fzf'
        }
            
    except Exception as e:
        return {'success': False, 'error': f'Unix fuzzy_select failed: {str(e)}'}