"""
LTMC Unix Text Syntax Action Module
Text processing including JSON parsing, syntax highlighting, and code analysis
"""

import subprocess
import json
import time
from typing import Dict, Any


def unix_text_syntax_action(action: str, **params) -> Dict[str, Any]:
    """Text syntax and processing utilities with real external tool integration.
    
    Actions: jq, parse_syntax, syntax_highlight, syntax_query
    
    This module handles text processing operations including JSON manipulation,
    syntax highlighting, and code structure analysis.
    
    Args:
        action: The text syntax action to perform
        **params: Additional parameters for specific actions
        
    Returns:
        Dictionary with operation result and status
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'jq':
        return _handle_jq_action(params)
    elif action == 'parse_syntax':
        return _handle_parse_syntax_action(params)
    elif action == 'syntax_highlight':
        return _handle_syntax_highlight_action(params)
    elif action == 'syntax_query':
        return _handle_syntax_query_action(params)
    else:
        return {'success': False, 'error': f'Unknown text syntax action: {action}'}


def _handle_jq_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle jq action for JSON processing."""
    try:
        query = params.get('query', '.')
        
        # Handle both direct JSON input and file input
        json_input = params.get('json_input')
        file_path = params.get('file_path')
        
        if not json_input and not file_path:
            return {'success': False, 'error': 'Missing required parameter: json_input or file_path'}
        
        start_time = time.time()
        
        # Use jq for JSON processing
        if file_path:
            cmd = ['jq']
            if params.get('raw_output', True):
                cmd.append('--raw-output')
            cmd.extend([query, file_path])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        else:
            cmd = ['jq']
            if params.get('raw_output', True):
                cmd.append('--raw-output')
            cmd.append(query)
            result = subprocess.run(cmd, input=json_input, capture_output=True, text=True, timeout=30)
        
        execution_time = (time.time() - start_time) * 1000
        
        if result.returncode == 0:
            return {
                'success': True,
                'result': result.stdout.strip(),
                'query': query,
                'execution_time_ms': execution_time,
                'tool': 'jq'
            }
        else:
            return {'success': False, 'error': f'jq failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Unix jq failed: {str(e)}'}


def _handle_parse_syntax_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle syntax parsing action."""
    try:
        file_path = params.get('file_path')
        content = params.get('content')
        language = params.get('language', 'auto')
        
        if not file_path and not content:
            return {'success': False, 'error': 'Missing required parameter: file_path or content'}
        
        # Use tree-sitter or similar for syntax parsing
        # For now, provide basic syntax analysis using file extension
        if file_path:
            extension = file_path.split('.')[-1].lower() if '.' in file_path else ''
            
            # Map file extensions to languages
            language_map = {
                'py': 'python',
                'js': 'javascript', 
                'ts': 'typescript',
                'json': 'json',
                'md': 'markdown',
                'yml': 'yaml',
                'yaml': 'yaml',
                'xml': 'xml',
                'html': 'html',
                'css': 'css',
                'sql': 'sql',
                'sh': 'bash',
                'bash': 'bash'
            }
            
            detected_language = language_map.get(extension, 'text')
            
            return {
                'success': True,
                'file_path': file_path,
                'detected_language': detected_language,
                'file_extension': extension,
                'syntax_elements': {
                    'language': detected_language,
                    'has_extension': bool(extension),
                    'is_structured': detected_language in ['json', 'xml', 'yaml', 'html']
                },
                'tool': 'basic_parser'
            }
        else:
            # Parse content directly
            lines = content.split('\n')
            
            return {
                'success': True,
                'content_length': len(content),
                'line_count': len(lines),
                'language': language,
                'syntax_elements': {
                    'language': language,
                    'line_count': len(lines),
                    'char_count': len(content),
                    'has_structure': any(char in content for char in ['{', '[', '<', '('])
                },
                'tool': 'basic_parser'
            }
            
    except Exception as e:
        return {'success': False, 'error': f'Syntax parsing failed: {str(e)}'}


def _handle_syntax_highlight_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle syntax highlighting action using bat."""
    try:
        file_path = params.get('file_path')
        content = params.get('content')
        language = params.get('language', 'auto')
        
        if not file_path and not content:
            return {'success': False, 'error': 'Missing required parameter: file_path or content'}
        
        # Use bat for syntax highlighting
        if file_path:
            cmd = ['bat', '--color=always', '--style=numbers,grid']
            
            if language != 'auto':
                cmd.extend(['--language', language])
            
            cmd.append(file_path)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        else:
            cmd = ['bat', '--color=always', '--style=numbers,grid']
            
            if language != 'auto':
                cmd.extend(['--language', language])
            
            result = subprocess.run(cmd, input=content, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return {
                'success': True,
                'highlighted_content': result.stdout,
                'file_path': file_path,
                'language': language,
                'tool': 'bat'
            }
        else:
            return {'success': False, 'error': f'Syntax highlighting failed: {result.stderr}'}
            
    except Exception as e:
        return {'success': False, 'error': f'Syntax highlighting failed: {str(e)}'}


def _handle_syntax_query_action(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle syntax query action for code structure analysis."""
    try:
        file_path = params.get('file_path')
        query_type = params.get('query_type', 'functions')
        language = params.get('language', 'auto')
        
        if not file_path:
            return {'success': False, 'error': 'Missing required parameter: file_path'}
        
        # Basic syntax querying based on file type
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return {'success': False, 'error': f'Failed to read file: {str(e)}'}
        
        results = []
        
        if query_type == 'functions':
            # Look for function definitions
            if '.py' in file_path:
                # Python functions
                import re
                pattern = r'^def\s+(\w+)\s*\([^)]*\):'
                for i, line in enumerate(content.split('\n'), 1):
                    match = re.match(pattern, line.strip())
                    if match:
                        results.append({
                            'type': 'function',
                            'name': match.group(1),
                            'line_number': i,
                            'signature': line.strip()
                        })
            elif '.js' in file_path or '.ts' in file_path:
                # JavaScript/TypeScript functions
                import re
                pattern = r'function\s+(\w+)\s*\([^)]*\)'
                for i, line in enumerate(content.split('\n'), 1):
                    match = re.search(pattern, line)
                    if match:
                        results.append({
                            'type': 'function',
                            'name': match.group(1),
                            'line_number': i,
                            'signature': line.strip()
                        })
        
        elif query_type == 'classes':
            # Look for class definitions
            if '.py' in file_path:
                import re
                pattern = r'^class\s+(\w+).*:'
                for i, line in enumerate(content.split('\n'), 1):
                    match = re.match(pattern, line.strip())
                    if match:
                        results.append({
                            'type': 'class',
                            'name': match.group(1),
                            'line_number': i,
                            'definition': line.strip()
                        })
        
        return {
            'success': True,
            'file_path': file_path,
            'query_type': query_type,
            'language': language,
            'results': results,
            'count': len(results),
            'tool': 'basic_syntax_query'
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Syntax query failed: {str(e)}'}