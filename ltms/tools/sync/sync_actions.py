"""
Documentation synchronization tools for LTMC MCP server.
Provides documentation synchronization operations with real internal implementation.

File: ltms/tools/sync/sync_actions.py
Lines: ~290 (under 300 limit, complex functions in extension)
Purpose: Documentation sync, validation, and monitoring operations
"""

import os
import ast
import sqlite3
import logging
from typing import Dict, Any, List
from datetime import datetime, timezone

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class SyncTools(MCPToolBase):
    """Documentation synchronization tools with real internal implementation.
    
    Provides documentation synchronization, validation, drift detection,
    and monitoring operations with real file operations and AST parsing.
    """
    
    def __init__(self):
        super().__init__("SyncTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid sync actions."""
        return [
            'code', 'validate', 'drift', 'blueprint', 
            'score', 'monitor', 'status'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute documentation synchronization action."""
        # Check required database systems for some actions
        if action in ['blueprint', 'status']:
            db_check = self._check_database_availability(['sqlite'])
            if not db_check.get('success', False):
                return db_check
        
        if action == 'code':
            return await self._action_code(**params)
        elif action == 'validate':
            return await self._action_validate(**params)
        elif action == 'drift':
            return await self._action_drift(**params)
        elif action in ['blueprint', 'score', 'monitor', 'status']:
            # Delegate complex operations to extension
            from .sync_extension import SyncExtension
            return await SyncExtension.execute_extended_action(action, **params)
        else:
            return self._create_error_response(f"Unknown sync action: {action}")
    
    async def _action_code(self, **params) -> Dict[str, Any]:
        """Handle sync_documentation_with_code action with directory traversal support."""
        # Support both file_path (backward compatibility) and directory_path
        if 'file_path' not in params and 'directory_path' not in params:
            return self._create_error_response('Missing required parameter: file_path or directory_path')
        
        if 'project_id' not in params:
            return self._create_error_response('Missing required parameter: project_id')
        
        try:
            target_path = params.get('file_path') or params.get('directory_path')
            project_id = params['project_id']
            force_update = params.get('force_update', False)
            recursive = params.get('recursive', True)
            
            if not os.path.exists(target_path):
                return self._create_error_response(f'Path not found: {target_path}')
            
            start_time = datetime.now(timezone.utc)
            
            # Determine if we're processing a single file or directory
            if os.path.isfile(target_path):
                # Single file processing (backward compatibility)
                files_to_process = [target_path]
            else:
                # Directory processing with traversal
                files_to_process = self._discover_python_files(target_path, recursive)
            
            if not files_to_process:
                return self._create_error_response(f'No Python files found in: {target_path}')
            
            # Process all files
            all_results = []
            total_functions = 0
            total_classes = 0
            successful_files = 0
            failed_files = []
            
            for file_path in files_to_process:
                try:
                    file_result = await self._process_single_file(file_path, project_id)
                    if file_result['success']:
                        successful_files += 1
                        all_results.append(file_result)
                        total_functions += len(file_result['functions'])
                        total_classes += len(file_result['classes'])
                    else:
                        failed_files.append({
                            'file_path': file_path,
                            'error': file_result['error']
                        })
                except Exception as e:
                    failed_files.append({
                        'file_path': file_path,
                        'error': f'Processing failed: {str(e)}'
                    })
            
            end_time = datetime.now(timezone.utc)
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Generate comprehensive sync report
            sync_report = {
                'target_path': target_path,
                'project_id': project_id,
                'processing_mode': 'single_file' if os.path.isfile(target_path) else 'directory_traversal',
                'recursive': recursive,
                'total_files_found': len(files_to_process),
                'successful_files': successful_files,
                'failed_files_count': len(failed_files),
                'total_functions_found': total_functions,
                'total_classes_found': total_classes,
                'processing_time_ms': round(processing_time_ms, 2),
                'sync_timestamp': start_time.isoformat(),
                'force_update': force_update,
                'individual_file_results': all_results,
                'failed_files': failed_files
            }
            
            # For backward compatibility, if single file, include legacy format
            if len(all_results) == 1 and os.path.isfile(target_path):
                single_result = all_results[0]
                sync_report.update({
                    'file_path': target_path,  # Legacy field
                    'functions_found': len(single_result['functions']),  # Legacy field
                    'classes_found': len(single_result['classes']),  # Legacy field
                    'functions': single_result['functions'],  # Legacy field  
                    'classes': single_result['classes']  # Legacy field
                })
            
            success_message = f'Processed {successful_files}/{len(files_to_process)} files successfully'
            if failed_files:
                success_message += f' ({len(failed_files)} files had errors)'
            
            return self._create_success_response({
                'sync_report': sync_report,
                'message': success_message
            })
            
        except Exception as e:
            return self._create_error_response(f'Sync code failed: {str(e)}')
    
    def _discover_python_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """Discover Python files in directory with optional recursion."""
        python_files = []
        
        if recursive:
            # Recursive traversal
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.lower().endswith('.py'):
                        full_path = os.path.join(root, file)
                        python_files.append(full_path)
        else:
            # Single directory level only
            try:
                for item in os.listdir(directory_path):
                    item_path = os.path.join(directory_path, item)
                    if os.path.isfile(item_path) and item.lower().endswith('.py'):
                        python_files.append(item_path)
            except OSError:
                pass  # Handle permission errors gracefully
        
        return sorted(python_files)  # Sort for consistent ordering
    
    async def _process_single_file(self, file_path: str, project_id: str) -> Dict[str, Any]:
        """Process a single Python file with enhanced error handling."""
        try:
            # Use safe file reading with comprehensive encoding detection
            try:
                from ltms.tools.docs.documentation_extension import safe_read_file
                source_code = safe_read_file(file_path)
                if source_code is None:
                    return {
                        'success': False,
                        'error': f'Unable to read file with any encoding: {file_path}'
                    }
            except ImportError:
                # Fallback to manual encoding strategies if safe_read_file not available
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        source_code = f.read()
                except UnicodeDecodeError:
                    encodings = ['latin-1', 'cp1252', 'iso-8859-1']
                    source_code = None
                    for encoding in encodings:
                        try:
                            with open(file_path, 'r', encoding=encoding) as f:
                                source_code = f.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if source_code is None:
                        return {
                            'success': False,
                            'error': f'Unable to read file with any encoding: {file_path}'
                        }
            
            # Parse with AST
            try:
                tree = ast.parse(source_code, filename=file_path)
            except SyntaxError as e:
                return {
                    'success': False,
                    'error': f'Python syntax error in {os.path.basename(file_path)}: {str(e)}'
                }
            
            # Extract code structure
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'args': [arg.arg for arg in node.args.args],
                        'is_async': isinstance(node, ast.AsyncFunctionDef)
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'docstring': ast.get_docstring(node),
                        'methods': methods,
                        'method_count': len(methods)
                    })
            
            return {
                'success': True,
                'file_path': file_path,
                'relative_path': os.path.relpath(file_path),
                'functions': functions,
                'classes': classes,
                'lines_of_code': len(source_code.splitlines()),
                'project_id': project_id
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to process {os.path.basename(file_path)}: {str(e)}'
            }
    
    async def _action_validate(self, **params) -> Dict[str, Any]:
        """Handle validate_documentation_consistency action."""
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            
            if not os.path.exists(file_path):
                return self._create_error_response(f'File not found: {file_path}')
            
            # Read and parse source code - using safe file reading with encoding detection
            try:
                from ltms.tools.docs.documentation_extension import safe_read_file
                source_code = safe_read_file(file_path)
                if source_code is None:
                    return self._create_error_response(f'Failed to read file {file_path} - may be binary or corrupted')
            except ImportError:
                # Fallback to basic UTF-8 reading if safe_read_file not available
                with open(file_path, 'r', encoding='utf-8') as f:
                    source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Analyze documentation consistency
            total_elements = 0
            documented_elements = 0
            issues = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    total_elements += 1
                    docstring = ast.get_docstring(node)
                    
                    if docstring:
                        documented_elements += 1
                        # Check docstring quality
                        if len(docstring.strip()) < 10:
                            issues.append(f'{node.name}: Docstring too short')
                    else:
                        issues.append(f'{node.name}: Missing docstring')
            
            consistency_score = documented_elements / total_elements if total_elements > 0 else 0
            consistency_level = 'excellent' if consistency_score >= 0.9 else 'good' if consistency_score >= 0.7 else 'poor'
            
            return self._create_success_response({
                'file_path': file_path,
                'project_id': project_id,
                'consistency_score': round(consistency_score, 3),
                'consistency_level': consistency_level,
                'total_elements': total_elements,
                'documented_elements': documented_elements,
                'issues': issues,
                'validation_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            return self._create_error_response(f'Sync validate failed: {str(e)}')
    
    async def _action_drift(self, **params) -> Dict[str, Any]:
        """Handle detect_documentation_drift action."""
        required_params = ['file_path', 'project_id']
        for param in required_params:
            if param not in params:
                return self._create_error_response(f'Missing required parameter: {param}')
        
        try:
            file_path = params['file_path']
            project_id = params['project_id']
            time_threshold_hours = params.get('time_threshold_hours', 24)
            
            # Get file modification time
            if not os.path.exists(file_path):
                return self._create_error_response(f'File not found: {file_path}')
            
            file_mtime = os.path.getmtime(file_path)
            current_time = datetime.now().timestamp()
            hours_since_modified = (current_time - file_mtime) / 3600
            
            drift_detected = hours_since_modified <= time_threshold_hours
            
            # Simple drift analysis based on file modification time
            return self._create_success_response({
                'file_path': file_path,
                'project_id': project_id,
                'drift_detected': drift_detected,
                'hours_since_modified': round(hours_since_modified, 2),
                'time_threshold_hours': time_threshold_hours,
                'last_modified': datetime.fromtimestamp(file_mtime).isoformat(),
                'check_timestamp': datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            return self._create_error_response(f'Sync drift failed: {str(e)}')


# Create global instance for backward compatibility
async def sync_action(action: str, **params) -> Dict[str, Any]:
    """Documentation synchronization operations (backward compatibility).
    
    Actions: code, validate, drift, blueprint, score, monitor, status
    """
    sync_tools = SyncTools()
    return await sync_tools(action, **params)