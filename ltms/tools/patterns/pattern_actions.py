"""
Pattern analysis tools for LTMC MCP server.
Provides code pattern analysis with real Python AST implementation.

File: ltms/tools/patterns/pattern_actions.py
Lines: ~300 (under 300 limit)
Purpose: Code pattern analysis operations
"""

import ast
import json
import logging
import sqlite3
import time
from typing import Dict, Any, List
from datetime import datetime

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class PatternTools(MCPToolBase):
    """Pattern analysis tools with Python AST implementation.
    
    Provides code analysis, pattern extraction, and pattern logging
    functionality with real AST parsing.
    """
    
    def __init__(self):
        super().__init__("PatternTools")
        self.config = get_tool_config()
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid pattern actions."""
        return [
            'extract_functions', 'extract_classes', 'extract_comments', 
            'summarize_code', 'log_attempt', 'get_patterns', 'analyze_patterns'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute pattern analysis action."""
        # Check required database systems
        db_check = self._check_database_availability(['sqlite'])
        if not db_check.get('success', False):
            return db_check
        
        if action == 'extract_functions':
            return await self._action_extract_functions(**params)
        elif action == 'extract_classes':
            return await self._action_extract_classes(**params)
        elif action == 'extract_comments':
            return await self._action_extract_comments(**params)
        elif action == 'summarize_code':
            return await self._action_summarize_code(**params)
        elif action == 'log_attempt':
            return await self._action_log_attempt(**params)
        elif action == 'get_patterns':
            return await self._action_get_patterns(**params)
        elif action == 'analyze_patterns':
            return await self._action_analyze_patterns(**params)
        else:
            return self._create_error_response(f"Unknown pattern action: {action}")
    
    async def _action_extract_functions(self, **params) -> Dict[str, Any]:
        """Extract function definitions from source code using AST with Mind Graph tracking."""
        source_code = params.get('source_code')
        if not source_code:
            return self._create_error_response('Missing required parameter: source_code')
        
        try:
            # Track reasoning for function extraction
            reason_id = self._track_reasoning(
                reason_type="code_analysis",
                description=f"Extracting function definitions from {len(source_code)} characters of source code using Python AST",
                priority_level=2,
                confidence_score=0.9
            )
            
            tree = ast.parse(source_code)
        except SyntaxError as e:
            # Track syntax error reasoning
            error_reason_id = self._track_reasoning(
                reason_type="syntax_error",
                description=f"Syntax error encountered during AST parsing: {str(e)}",
                priority_level=1,
                confidence_score=1.0
            )
            
            # Track failed extraction change
            change_id = self._track_mind_graph_change(
                change_type="pattern_extraction_failed",
                change_summary=f"Function extraction failed due to syntax error",
                change_details=f"Error: {str(e)}"
            )
            
            if change_id and error_reason_id:
                self._link_change_to_reason(change_id, error_reason_id, "CAUSED_BY")
            
            return self._create_error_response(f'Syntax error in source code: {str(e)}')
        
        functions = []
        
        class FunctionVisitor(ast.NodeVisitor):
            """AST NodeVisitor for extracting function definitions and metadata."""
            def visit_FunctionDef(self, node):
                """Visit a function definition node and extract metadata."""
                func_info = {
                    'name': node.name,
                    'line_number': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'returns': ast.get_source_segment(source_code, node.returns) if node.returns else None,
                    'docstring': ast.get_docstring(node),
                    'decorator_list': [ast.get_source_segment(source_code, dec) for dec in node.decorator_list],
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                }
                
                # Calculate complexity
                complexity = 1
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                        complexity += 1
                func_info['complexity'] = complexity
                
                functions.append(func_info)
                self.generic_visit(node)
            
            def visit_AsyncFunctionDef(self, node):
                """Visit an async function definition node and extract metadata."""
                self.visit_FunctionDef(node)
        
        visitor = FunctionVisitor()
        visitor.visit(tree)
        
        # Track successful extraction change
        change_id = self._track_mind_graph_change(
            change_type="function_extraction",
            change_summary=f"Extracted {len(functions)} functions from source code",
            change_details=f"Functions: {[f['name'] for f in functions]}, Total complexity: {sum(f['complexity'] for f in functions)}"
        )
        
        if change_id and reason_id:
            self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
        
        result = self._create_success_response({
            'functions': functions,
            'count': len(functions),
            'tool': 'Python AST',
            'source_lines': len(source_code.split('\n')),
            'mind_graph_patterns': {
                'operation': 'extract_functions',
                'reasoning_id': reason_id,
                'change_id': change_id,
                'functions_found': len(functions)
            }
        })
        
        return result
    
    async def _action_extract_classes(self, **params) -> Dict[str, Any]:
        """Extract class definitions from source code using AST with Mind Graph tracking."""
        source_code = params.get('source_code')
        if not source_code:
            return self._create_error_response('Missing required parameter: source_code')
        
        try:
            # Track reasoning for class extraction
            reason_id = self._track_reasoning(
                reason_type="code_analysis",
                description=f"Extracting class definitions from {len(source_code)} characters of source code using Python AST",
                priority_level=2,
                confidence_score=0.9
            )
            
            tree = ast.parse(source_code)
        except SyntaxError as e:
            # Track syntax error reasoning
            error_reason_id = self._track_reasoning(
                reason_type="syntax_error",
                description=f"Syntax error encountered during AST parsing: {str(e)}",
                priority_level=1,
                confidence_score=1.0
            )
            
            # Track failed extraction change
            change_id = self._track_mind_graph_change(
                change_type="pattern_extraction_failed",
                change_summary=f"Class extraction failed due to syntax error",
                change_details=f"Error: {str(e)}"
            )
            
            if change_id and error_reason_id:
                self._link_change_to_reason(change_id, error_reason_id, "CAUSED_BY")
            
            return self._create_error_response(f'Syntax error in source code: {str(e)}')
        
        classes = []
        
        class ClassVisitor(ast.NodeVisitor):
            """AST NodeVisitor for extracting class definitions and metadata."""
            def visit_ClassDef(self, node):
                """Visit a class definition node and extract metadata."""
                methods = []
                attributes = []
                
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            'name': item.name,
                            'line_number': item.lineno,
                            'args': [arg.arg for arg in item.args.args],
                            'is_property': any(
                                isinstance(dec, ast.Name) and dec.id == 'property'
                                for dec in item.decorator_list
                            )
                        })
                    elif isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name):
                                attributes.append({
                                    'name': target.id,
                                    'line_number': item.lineno
                                })
                
                class_info = {
                    'name': node.name,
                    'line_number': node.lineno,
                    'bases': [ast.get_source_segment(source_code, base) for base in node.bases],
                    'docstring': ast.get_docstring(node),
                    'methods': methods,
                    'attributes': attributes,
                    'method_count': len(methods),
                    'attribute_count': len(attributes)
                }
                
                classes.append(class_info)
                self.generic_visit(node)
        
        visitor = ClassVisitor()
        visitor.visit(tree)
        
        # Track successful extraction change
        change_id = self._track_mind_graph_change(
            change_type="class_extraction",
            change_summary=f"Extracted {len(classes)} classes from source code",
            change_details=f"Classes: {[c['name'] for c in classes]}, Total methods: {sum(c['method_count'] for c in classes)}"
        )
        
        if change_id and reason_id:
            self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
        
        result = self._create_success_response({
            'classes': classes,
            'count': len(classes),
            'tool': 'Python AST',
            'source_lines': len(source_code.split('\n')),
            'mind_graph_patterns': {
                'operation': 'extract_classes',
                'reasoning_id': reason_id,
                'change_id': change_id,
                'classes_found': len(classes)
            }
        })
        
        return result
    
    async def _action_log_attempt(self, **params) -> Dict[str, Any]:
        """Log a pattern analysis attempt to SQLite database with Mind Graph tracking."""
        pattern_type = params.get('pattern_type')
        code_content = params.get('code_content') 
        result = params.get('result')
        
        if not pattern_type:
            return self._create_error_response('Missing required parameter: pattern_type')
        if not code_content:
            return self._create_error_response('Missing required parameter: code_content')
        if not result:
            return self._create_error_response('Missing required parameter: result')
        
        try:
            # Track reasoning for pattern attempt logging
            reason_id = self._track_reasoning(
                reason_type="pattern_logging",
                description=f"Logging pattern analysis attempt for '{pattern_type}' with result '{result}'",
                priority_level=3,
                confidence_score=0.95
            )
            
            # Optional parameters
            metadata = params.get('metadata', {})
            tags = self._ensure_list(params.get('tags', []))
            
            log_entry = {
                "action_type": "pattern_attempt",
                "pattern_type": pattern_type,
                "code_content": code_content[:500] + "..." if len(code_content) > 500 else code_content,
                "result": result,
                "metadata": metadata,
                "tags": tags,
                "timestamp": datetime.now().isoformat()
            }
            
            content = f"Pattern attempt logged: {pattern_type} - {result}\n"
            content += f"Code sample: {code_content[:200]}...\n" 
            content += f"Metadata: {metadata}"
            
            # Create pattern_attempts table if not exists
            self.db.execute_sqlite('''
                CREATE TABLE IF NOT EXISTS pattern_attempts (
                    id TEXT PRIMARY KEY,
                    pattern_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    code_content TEXT,
                    metadata TEXT,
                    tags TEXT,
                    timestamp TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            attempt_id = f"attempt_{int(time.time() * 1000)}"
            self.db.execute_sqlite('''
                INSERT INTO pattern_attempts (id, pattern_type, result, code_content, metadata, tags, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                attempt_id,
                pattern_type,
                result, 
                content,
                json.dumps(metadata),
                json.dumps(tags),
                log_entry["timestamp"]
            ))
            
            # Track the logging change
            change_id = self._track_mind_graph_change(
                change_type="pattern_log_attempt",
                change_summary=f"Logged pattern analysis attempt for '{pattern_type}'",
                change_details=f"Result: {result}, Attempt ID: {attempt_id}, Tags: {tags}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            result_data = self._create_success_response({
                'logged': True,
                'attempt_id': attempt_id,
                'pattern_type': pattern_type,
                'result': result,
                'tags': ["pattern_attempt", pattern_type] + tags,
                'mind_graph_patterns': {
                    'operation': 'log_attempt',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'attempt_logged': attempt_id
                }
            })
            
            return result_data
            
        except Exception as e:
            return self._create_error_response(f'Failed to log pattern attempt: {str(e)}')
    
    async def _action_get_patterns(self, **params) -> Dict[str, Any]:
        """Retrieve pattern analysis attempts from database with Mind Graph tracking."""
        try:
            # Track reasoning for pattern retrieval
            reason_id = self._track_reasoning(
                reason_type="pattern_retrieval",
                description=f"Retrieving pattern analysis attempts from database with filters",
                priority_level=3,
                confidence_score=0.8
            )
            
            pattern_type = params.get('pattern_type')
            tags = params.get('tags', [])
            limit = params.get('limit', 10)
            
            # Build query
            query = "SELECT * FROM pattern_attempts WHERE 1=1"
            query_params = []
            
            if pattern_type:
                query += " AND pattern_type = ?"
                query_params.append(pattern_type)
            
            if tags:
                for tag in tags:
                    query += " AND tags LIKE ?"
                    query_params.append(f'%{tag}%')
            
            query += " ORDER BY created_at DESC LIMIT ?"
            query_params.append(limit)
            
            rows = self.db.execute_sqlite(query, tuple(query_params), fetch='all')
            
            patterns = []
            for row in rows:
                pattern_data = {
                    'id': row[0],
                    'pattern_type': row[1],
                    'result': row[2],
                    'code_content': row[3],
                    'metadata': json.loads(row[4]) if row[4] else {},
                    'tags': json.loads(row[5]) if row[5] else [],
                    'timestamp': row[6],
                    'created_at': row[7]
                }
                patterns.append(pattern_data)
            
            # Track successful retrieval change
            change_id = self._track_mind_graph_change(
                change_type="pattern_retrieval",
                change_summary=f"Retrieved {len(patterns)} pattern analysis attempts",
                change_details=f"Pattern type: {pattern_type}, Tags: {tags}, Limit: {limit}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            result = self._create_success_response({
                'patterns': patterns,
                'count': len(patterns),
                'pattern_type': pattern_type,
                'tags_filter': tags,
                'limit': limit,
                'mind_graph_patterns': {
                    'operation': 'get_patterns',
                    'reasoning_id': reason_id,
                    'change_id': change_id,
                    'patterns_retrieved': len(patterns)
                }
            })
            
            return result
            
        except Exception as e:
            return self._create_error_response(f'Failed to retrieve patterns: {str(e)}')
    
    async def _action_summarize_code(self, **params) -> Dict[str, Any]:
        """Summarize code structure and complexity."""
        from .pattern_analysis import PatternAnalysisExtension
        
        source_code = params.get('source_code')
        if not source_code:
            return self._create_error_response('Missing required parameter: source_code')
        
        try:
            result = await PatternAnalysisExtension.action_summarize_code(source_code)
            if result.get('success'):
                return self._create_success_response(result)
            else:
                return result
        except Exception as e:
            return self._create_error_response(f'Summarize code failed: {str(e)}')
    
    async def _action_analyze_patterns(self, **params) -> Dict[str, Any]:
        """Analyze code patterns and design patterns."""
        from .pattern_analysis import PatternAnalysisExtension
        
        try:
            result = await PatternAnalysisExtension.action_analyze_patterns(
                file_path=params.get('file_path'),
                code_content=params.get('code_content'),
                analysis_type=params.get('analysis_type', 'general'),
                pattern_types=params.get('pattern_types', [])
            )
            if result.get('success'):
                return self._create_success_response(result)
            else:
                return result
        except Exception as e:
            return self._create_error_response(f'Analyze patterns failed: {str(e)}')
    
    async def _action_extract_comments(self, **params) -> Dict[str, Any]:
        """Extract comments from code with optional context."""
        from .pattern_analysis import PatternAnalysisExtension
        
        try:
            result = await PatternAnalysisExtension.action_extract_comments(
                file_path=params.get('file_path'),
                code_content=params.get('code_content'),
                comment_types=params.get('comment_types', []),
                include_context=params.get('include_context', False)
            )
            if result.get('success'):
                return self._create_success_response(result)
            else:
                return result
        except Exception as e:
            return self._create_error_response(f'Extract comments failed: {str(e)}')
    
    def _ensure_list(self, value):
        """Ensure value is a list for safe concatenation."""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, str):
            # Handle JSON string or comma-separated
            if value.startswith('[') and value.endswith(']'):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, ValueError, TypeError) as e:
                    logger.debug(f"Could not parse JSON value '{value}': {e}")
                    return [value]
            else:
                return [value]
        else:
            return [str(value)]


# Create global instance for backward compatibility
async def pattern_action(action: str, **params) -> Dict[str, Any]:
    """Pattern analysis operations (backward compatibility).
    
    Actions: extract_functions, extract_classes, extract_comments, 
             summarize_code, log_attempt, get_patterns, analyze_patterns
    """
    pattern_tools = PatternTools()
    return await pattern_tools(action, **params)