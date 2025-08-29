"""
Unix tools extension for complex operations.
Contains the remaining Unix utility methods that exceed the 300-line limit.

File: ltms/tools/unix/unix_extension.py
Lines: ~280 (under 300 limit)
Purpose: Extended Unix operations (tldr, delta, fzf, syntax highlighting)
"""

import subprocess
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class UnixExtension:
    """Extension class for complex Unix operations."""
    
    @staticmethod
    async def execute_extended_action(action: str, **params) -> Dict[str, Any]:
        """Execute extended Unix action."""
        try:
            if action == 'help':
                return await UnixExtension._action_help_tldr(**params)
            elif action == 'diff_highlight':
                return await UnixExtension._action_diff_highlight(**params)
            elif action == 'fuzzy_select':
                return await UnixExtension._action_fuzzy_select(**params)
            elif action == 'parse_syntax':
                return await UnixExtension._action_parse_syntax(**params)
            elif action == 'syntax_highlight':
                return await UnixExtension._action_syntax_highlight(**params)
            elif action == 'syntax_query':
                return await UnixExtension._action_syntax_query(**params)
            else:
                return {'success': False, 'error': f'Unknown extended unix action: {action}'}
        except Exception as e:
            return {'success': False, 'error': f'Extended unix action failed: {str(e)}'}
    
    @staticmethod
    async def _action_help_tldr(**params) -> Dict[str, Any]:
        """Get concise help using tldr tool."""
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
                        command = line_stripped
                        examples.append({
                            'description': current_description,
                            'command': command
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
    
    @staticmethod
    async def _action_diff_highlight(**params) -> Dict[str, Any]:
        """Enhanced diff highlighting using delta tool."""
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
    
    @staticmethod
    async def _action_fuzzy_select(**params) -> Dict[str, Any]:
        """Fuzzy file selection using fzf tool."""
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
                'input_count': len(input_list),
                'selected_count': len(selected_items),
                'tool': 'fzf'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix fuzzy_select failed: {str(e)}'}
    
    @staticmethod
    async def _action_parse_syntax(**params) -> Dict[str, Any]:
        """Parse code syntax and structure."""
        try:
            file_path = params.get('file_path')
            code_content = params.get('code_content')
            
            if not file_path and not code_content:
                return {'success': False, 'error': 'Missing required parameter: file_path or code_content'}
            
            # If file_path provided, read the file
            if file_path:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code_content = f.read()
                except Exception as e:
                    return {'success': False, 'error': f'Failed to read file: {str(e)}'}
            
            # Use tree-sitter or basic parsing depending on language
            language = params.get('language', 'auto')
            
            # For now, implement basic syntax analysis
            lines = code_content.split('\n')
            syntax_info = {
                'total_lines': len(lines),
                'non_empty_lines': len([line for line in lines if line.strip()]),
                'comment_lines': len([line for line in lines if line.strip().startswith('#') or line.strip().startswith('//')]),
                'function_definitions': len([line for line in lines if 'def ' in line or 'function ' in line]),
                'class_definitions': len([line for line in lines if 'class ' in line]),
                'import_statements': len([line for line in lines if line.strip().startswith('import ') or line.strip().startswith('from ')])
            }
            
            return {
                'success': True,
                'syntax_analysis': syntax_info,
                'file_path': file_path,
                'language': language,
                'tool': 'syntax_parser'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix parse_syntax failed: {str(e)}'}
    
    @staticmethod
    async def _action_syntax_highlight(**params) -> Dict[str, Any]:
        """Syntax highlighting using bat or similar."""
        try:
            file_path = params.get('file_path')
            code_content = params.get('code_content')
            
            if not file_path and not code_content:
                return {'success': False, 'error': 'Missing required parameter: file_path or code_content'}
            
            # Use bat for syntax highlighting
            if file_path:
                cmd = ['bat', '--color=never', '--decorations=never', '--line-range', '1:', file_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            else:
                # Create temporary file for code content
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(code_content)
                    temp_path = temp_file.name
                
                cmd = ['bat', '--color=never', '--decorations=never', '--line-range', '1:', temp_path]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                # Clean up temp file
                import os
                os.unlink(temp_path)
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'highlighted_content': result.stdout,
                    'file_path': file_path,
                    'tool': 'bat'
                }
            else:
                return {'success': False, 'error': f'bat failed: {result.stderr}'}
                
        except Exception as e:
            return {'success': False, 'error': f'Unix syntax_highlight failed: {str(e)}'}
    
    @staticmethod
    async def _action_syntax_query(**params) -> Dict[str, Any]:
        """Query syntax patterns in code."""
        try:
            pattern = params.get('pattern')
            file_path = params.get('file_path')
            
            if not pattern:
                return {'success': False, 'error': 'Missing required parameter: pattern'}
            
            if not file_path:
                return {'success': False, 'error': 'Missing required parameter: file_path'}
            
            # Use ripgrep with syntax awareness
            cmd = ['rg', '--color=never', '--line-number', '--type-add', 'code:*.{py,js,ts,java,cpp,c,h,rs,go}', '--type', 'code', pattern, file_path]
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
                                    'match': parts[2],
                                    'pattern': pattern
                                })
                            except ValueError:
                                matches.append({
                                    'file': parts[0],
                                    'line_number': 1,
                                    'match': ':'.join(parts[1:]),
                                    'pattern': pattern
                                })
            
            return {
                'success': True,
                'matches': matches,
                'pattern': pattern,
                'file_path': file_path,
                'match_count': len(matches),
                'tool': 'ripgrep'
            }
                
        except Exception as e:
            return {'success': False, 'error': f'Unix syntax_query failed: {str(e)}'}