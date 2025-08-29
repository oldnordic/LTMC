"""
Modern Unix utilities for LTMC MCP server.
Provides enhanced Unix utilities with modern tooling integration.

File: ltms/tools/unix/unix_actions.py  
Lines: ~290 (under 300 limit, complex functions in extension)
Purpose: Modern Unix utilities (exa, bat, ripgrep, fd, lsd, duf, fzf)
"""

import subprocess
import time
import logging
from typing import Dict, Any, List

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class UnixTools(MCPToolBase):
    """Modern Unix utilities with enhanced tooling.
    
    Provides file operations, search, and system utilities using
    modern tools: exa, bat, ripgrep, fd, lsd, duf, fzf, tree, jq.
    """
    
    def __init__(self):
        super().__init__("UnixTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid Unix actions."""
        return [
            'ls', 'cat', 'grep', 'find', 'tree', 'jq', 
            'list_modern', 'disk_usage', 'help', 'diff_highlight',
            'fuzzy_select', 'parse_syntax', 'syntax_highlight', 'syntax_query'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute Unix utility action."""
        # Unix tools don't require database connections
        
        if action == 'ls':
            return await self._action_ls(**params)
        elif action == 'cat':
            return await self._action_cat(**params)
        elif action == 'grep':
            return await self._action_grep(**params)
        elif action == 'find':
            return await self._action_find(**params)
        elif action == 'tree':
            return await self._action_tree(**params)
        elif action == 'jq':
            return await self._action_jq(**params)
        elif action == 'list_modern':
            return await self._action_list_modern(**params)
        elif action == 'disk_usage':
            return await self._action_disk_usage(**params)
        elif action == 'help':
            return await self._action_help(**params)
        elif action in ['diff_highlight', 'fuzzy_select', 'parse_syntax', 'syntax_highlight', 'syntax_query']:
            # Delegate to extension for complex operations
            from .unix_extension import UnixExtension
            return await UnixExtension.execute_extended_action(action, **params)
        else:
            return self._create_error_response(f"Unknown unix action: {action}")
    
    async def _action_ls(self, **params) -> Dict[str, Any]:
        """List files using modern exa tool with fallback to ls."""
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
                return self._create_success_response({
                    'files': lines,
                    'path': path,
                    'count': len(lines),
                    'tool': 'exa',
                    'raw_output': result.stdout
                })
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
                    return self._create_success_response({
                        'files': lines,
                        'path': path,
                        'count': len(lines),
                        'tool': 'ls (fallback)',
                        'raw_output': result.stdout
                    })
                else:
                    return self._create_error_response(f'ls failed: {result.stderr}')
                    
        except Exception as e:
            return self._create_error_response(f'Unix ls failed: {str(e)}')
    
    async def _action_cat(self, **params) -> Dict[str, Any]:
        """Display file contents using modern bat tool with fallback to cat."""
        try:
            file_path = params.get('file_path')
            if not file_path:
                return self._create_error_response('Missing required parameter: file_path')
            
            # Try bat with syntax highlighting
            cmd = ['bat', '--color=never', '--plain', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return self._create_success_response({
                    'content': result.stdout,
                    'file_path': file_path,
                    'tool': 'bat',
                    'lines': len(result.stdout.split('\n'))
                })
            else:
                # Fall back to cat
                cmd_fallback = ['cat', file_path]
                result = subprocess.run(cmd_fallback, capture_output=True, text=True)
                if result.returncode == 0:
                    return self._create_success_response({
                        'content': result.stdout,
                        'file_path': file_path,
                        'tool': 'cat (fallback)',
                        'lines': len(result.stdout.split('\n'))
                    })
                else:
                    return self._create_error_response(f'cat failed: {result.stderr}')
                    
        except Exception as e:
            return self._create_error_response(f'Unix cat failed: {str(e)}')
    
    async def _action_grep(self, **params) -> Dict[str, Any]:
        """Search patterns using modern ripgrep tool."""
        try:
            pattern = params.get('pattern')
            path = params.get('path', '.')
            if not pattern:
                return self._create_error_response('Missing required parameter: pattern')
            
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
            
            return self._create_success_response({
                'matches': matches,
                'pattern': pattern,
                'path': path,
                'count': len(matches),
                'tool': 'ripgrep',
                'raw_output': result.stdout if result.returncode == 0 else result.stderr
            })
                
        except Exception as e:
            return self._create_error_response(f'Unix grep failed: {str(e)}')
    
    async def _action_find(self, **params) -> Dict[str, Any]:
        """Find files using modern fd tool."""
        try:
            pattern = params.get('pattern')
            path = params.get('path', '.')
            if not pattern:
                return self._create_error_response('Missing required parameter: pattern')
            
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
                return self._create_success_response({
                    'files_found': files_found,
                    'pattern': pattern,
                    'search_path': path,
                    'count': len(files_found),
                    'tool': 'fd',
                    'raw_output': result.stdout
                })
            else:
                return self._create_error_response(f'fd failed: {result.stderr}')
                
        except Exception as e:
            return self._create_error_response(f'Unix find failed: {str(e)}')
    
    async def _action_tree(self, **params) -> Dict[str, Any]:
        """Display directory tree structure."""
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
                    import re
                    dir_match = re.search(r'(\d+) directories', last_line)
                    file_match = re.search(r'(\d+) files', last_line)
                    if dir_match:
                        directory_count = int(dir_match.group(1))
                    if file_match:
                        file_count = int(file_match.group(1))
                
                return self._create_success_response({
                    'tree_output': result.stdout,
                    'root_path': path,
                    'max_depth': max_depth,
                    'directory_count': directory_count,
                    'file_count': file_count,
                    'tool': 'tree'
                })
            else:
                return self._create_error_response(f'tree failed: {result.stderr}')
                
        except Exception as e:
            return self._create_error_response(f'Unix tree failed: {str(e)}')
    
    async def _action_help(self, **params) -> Dict[str, Any]:
        """Get help information for Unix tools."""
        tool_help = {
            'modern_tools': {
                'exa': 'Modern ls replacement with colors and git integration',
                'bat': 'Cat clone with syntax highlighting and git integration',  
                'ripgrep': 'Ultra-fast text search tool',
                'fd': 'Fast and user-friendly find replacement',
                'lsd': 'Modern ls with file type icons',
                'duf': 'Disk Usage/Free utility with colored output',
                'fzf': 'Fuzzy finder for interactive file selection'
            },
            'available_actions': self.get_valid_actions(),
            'examples': {
                'ls': "List files: unix_action('ls', path='/home', long=True, all=True)",
                'grep': "Search: unix_action('grep', pattern='TODO', path='.')",
                'find': "Find files: unix_action('find', pattern='*.py', type_filter='f')"
            }
        }
        
        return self._create_success_response(tool_help)


    async def _action_jq(self, **params) -> Dict[str, Any]:
        """Process JSON using jq tool."""
        try:
            query = params.get('query', '.')
            
            # Handle both direct JSON input and file input
            json_input = params.get('json_input')
            file_path = params.get('file_path')
            
            if not json_input and not file_path:
                return self._create_error_response('Missing required parameter: json_input or file_path')
            
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
                return self._create_success_response({
                    'result': result.stdout.strip(),
                    'query': query,
                    'execution_time_ms': execution_time,
                    'tool': 'jq'
                })
            else:
                return self._create_error_response(f'jq failed: {result.stderr}')
                
        except Exception as e:
            return self._create_error_response(f'Unix jq failed: {str(e)}')
    
    async def _action_list_modern(self, **params) -> Dict[str, Any]:
        """Modern ls using lsd with icons and colors."""
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
                return self._create_success_response({
                    'files': lines,
                    'path': path,
                    'count': len(lines),
                    'formatted_output': result.stdout,
                    'tool': 'lsd'
                })
            else:
                return self._create_error_response(f'lsd failed: {result.stderr}')
                
        except Exception as e:
            return self._create_error_response(f'Unix list_modern failed: {str(e)}')
    
    async def _action_disk_usage(self, **params) -> Dict[str, Any]:
        """Modern disk usage display using duf."""
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
                        import json
                        parsed_result = json.loads(result.stdout)
                        return self._create_success_response({
                            'disk_usage': parsed_result,
                            'format': 'json',
                            'tool': 'duf'
                        })
                    except json.JSONDecodeError:
                        return self._create_error_response('Failed to parse duf JSON output')
                else:
                    return self._create_success_response({
                        'disk_usage_output': result.stdout,
                        'format': 'human',
                        'tool': 'duf'
                    })
            else:
                return self._create_error_response(f'duf failed: {result.stderr}')
                
        except Exception as e:
            return self._create_error_response(f'Unix disk_usage failed: {str(e)}')


# Create global instance for backward compatibility
async def unix_action(action: str, **params) -> Dict[str, Any]:
    """Modern Unix utilities (backward compatibility).
    
    Actions: ls(exa), cat(bat), grep(ripgrep), find(fd), tree, jq, 
             list_modern(lsd), disk_usage(duf), help, diff_highlight,
             fuzzy_select(fzf), parse_syntax, syntax_highlight, syntax_query
    """
    unix_tools = UnixTools()
    return await unix_tools(action, **params)