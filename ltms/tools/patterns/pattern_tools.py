"""
LTMC Pattern Tools - Smart Modularized Code Pattern Analysis
Extracted from consolidated.py for single responsibility and maintainability

Real Python AST implementation with FIXED log_attempt bug
NO SHORTCUTS - Production-ready pattern analysis with comprehensive error handling
"""

import ast
import json
import sqlite3
import time
import os
import sys
import warnings
from typing import Dict, Any
from datetime import datetime

# Environment setup for suppression
os.environ["PYTHONWARNINGS"] = "ignore::DeprecationWarning"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.simplefilter("ignore", DeprecationWarning)
warnings.simplefilter("ignore", FutureWarning)


def pattern_action(action: str, **params) -> Dict[str, Any]:
    """Code pattern analysis with real Python AST implementation.
    
    Actions: extract_functions, extract_classes, extract_comments, summarize_code, log_attempt, get_patterns, analyze_patterns
    """
    if not action:
        return {'success': False, 'error': 'Action parameter is required'}
    
    if action == 'extract_functions':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
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
            
            return {
                'success': True,
                'functions': functions,
                'count': len(functions),
                'tool': 'Python AST',
                'source_lines': len(source_code.split('\n'))
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Extract functions failed: {str(e)}'}
    
    elif action == 'extract_classes':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
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
            
            return {
                'success': True,
                'classes': classes,
                'count': len(classes),
                'tool': 'Python AST',
                'source_lines': len(source_code.split('\n'))
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Extract classes failed: {str(e)}'}
    
    elif action == 'summarize_code':
        try:
            source_code = params.get('source_code')
            if not source_code:
                return {'success': False, 'error': 'Missing required parameter: source_code'}
            
            try:
                tree = ast.parse(source_code)
            except SyntaxError as e:
                return {'success': False, 'error': f'Syntax error in source code: {str(e)}'}
            
            stats = {
                'functions': 0,
                'classes': 0,
                'imports': 0,
                'lines': len(source_code.split('\n')),
                'complexity': 0
            }
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    stats['functions'] += 1
                elif isinstance(node, ast.ClassDef):
                    stats['classes'] += 1
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    stats['imports'] += 1
                elif isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                    stats['complexity'] += 1
            
            summary_parts = []
            if stats['classes'] > 0:
                summary_parts.append(f"{stats['classes']} class{'es' if stats['classes'] != 1 else ''}")
            if stats['functions'] > 0:
                summary_parts.append(f"{stats['functions']} function{'s' if stats['functions'] != 1 else ''}")
            if stats['imports'] > 0:
                summary_parts.append(f"{stats['imports']} import{'s' if stats['imports'] != 1 else ''}")
            
            summary = f"Python code with {', '.join(summary_parts)} across {stats['lines']} lines"
            
            return {
                'success': True,
                'summary': summary,
                'statistics': stats,
                'tool': 'Python AST',
                'complexity_rating': 'Low' if stats['complexity'] < 5 else 'Medium' if stats['complexity'] < 15 else 'High'
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Summarize code failed: {str(e)}'}
    
    elif action == 'log_attempt':
        def _ensure_list(value):
            """Ensure value is a list for safe concatenation - BUG FIX for MCP protocol parameter handling"""
            if value is None:
                return []
            elif isinstance(value, list):
                return value
            elif isinstance(value, str):
                # Handle JSON string or comma-separated
                if value.startswith('[') and value.endswith(']'):
                    try:
                        return json.loads(value)
                    except:
                        return [value]
                else:
                    return [value]
            else:
                return [str(value)]
        
        try:
            # Required parameters
            pattern_type = params.get('pattern_type')
            code_content = params.get('code_content') 
            result = params.get('result')
            
            if not pattern_type:
                return {'success': False, 'error': 'Missing required parameter: pattern_type'}
            if not code_content:
                return {'success': False, 'error': 'Missing required parameter: code_content'}
            if not result:
                return {'success': False, 'error': 'Missing required parameter: result'}
            
            # Optional parameters with FIXED bug handling
            metadata = params.get('metadata', {})
            tags = _ensure_list(params.get('tags', []))
            
            # Use LTMC memory to store pattern attempt
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
            
            # Store in memory (sync version for compatibility)
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create pattern_attempts table if not exists
            cursor.execute('''
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
            cursor.execute('''
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
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'logged': True,
                'attempt_id': attempt_id,
                'pattern_type': pattern_type,
                'result': result,
                'tags': ["pattern_attempt", pattern_type] + tags  # FIXED: Safe concatenation
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to log pattern attempt: {str(e)}'}
    
    elif action == 'get_patterns':
        try:
            # Optional parameters
            pattern_type = params.get('pattern_type')
            tags = params.get('tags', [])
            limit = params.get('limit', 10)
            
            from ltms.config.json_config_loader import get_config
            config = get_config()
            db_path = config.get_db_path()
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
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
            
            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            patterns = []
            
            for row in rows:
                pattern_data = dict(zip(columns, row))
                # Parse JSON fields
                try:
                    pattern_data['metadata'] = json.loads(pattern_data.get('metadata', '{}'))
                    pattern_data['tags'] = json.loads(pattern_data.get('tags', '[]'))
                except:
                    pattern_data['metadata'] = {}
                    pattern_data['tags'] = []
                patterns.append(pattern_data)
            
            conn.close()
            
            return {
                'success': True,
                'patterns': patterns,
                'count': len(patterns),
                'pattern_type': pattern_type,
                'tags_filter': tags,
                'limit': limit
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to retrieve patterns: {str(e)}'}
    
    elif action == 'analyze_patterns':
        try:
            # Get code content
            file_path = params.get('file_path')
            code_content = params.get('code_content')
            analysis_type = params.get('analysis_type', 'general')
            pattern_types = params.get('pattern_types', [])
            
            if file_path:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            elif not code_content:
                return {'success': False, 'error': 'Either file_path or code_content must be provided'}
            
            analysis_results = {
                'success': True,
                'file_path': file_path,
                'analysis_type': analysis_type,
                'patterns_analyzed': pattern_types or ['all'],
                'analysis': {}
            }
            
            # Parse AST for analysis
            try:
                tree = ast.parse(code_content)
            except SyntaxError as e:
                return {'success': False, 'error': f'Failed to parse code: {str(e)}'}
            
            # Complexity analysis
            if not analysis_type or analysis_type in ['complexity', 'general']:
                complexity_data = {
                    'cyclomatic_complexity': 0,
                    'lines_of_code': len(code_content.split('\n')),
                    'function_count': 0,
                    'class_count': 0,
                    'max_nesting_level': 0
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.If, ast.For, ast.While, ast.With)):
                        complexity_data['cyclomatic_complexity'] += 1
                    elif isinstance(node, ast.FunctionDef):
                        complexity_data['function_count'] += 1
                    elif isinstance(node, ast.ClassDef):
                        complexity_data['class_count'] += 1
                
                analysis_results['analysis']['complexity'] = complexity_data
            
            # Structure analysis
            if not analysis_type or analysis_type in ['structure', 'general']:
                structure_data = {
                    'imports': [],
                    'classes': [],
                    'functions': [],
                    'global_variables': []
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            structure_data['imports'].append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            structure_data['imports'].append(f"{module}.{alias.name}")
                    elif isinstance(node, ast.ClassDef):
                        structure_data['classes'].append({
                            'name': node.name,
                            'methods': [n.name for n in node.body if isinstance(n, ast.FunctionDef)],
                            'line_number': node.lineno
                        })
                
                analysis_results['analysis']['structure'] = structure_data
            
            # Design patterns analysis
            if not analysis_type or analysis_type in ['design_patterns', 'general']:
                patterns = {
                    'singleton_pattern': '__new__' in code_content and '_instance' in code_content,
                    'factory_pattern': 'Factory' in code_content or 'factory' in code_content,
                    'decorator_pattern': False,
                    'observer_pattern': False,
                    'strategy_pattern': False
                }
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.decorator_list:
                        patterns['decorator_pattern'] = True
                    
                    if isinstance(node, ast.ClassDef):
                        methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                        if 'notify' in methods or 'subscribe' in methods:
                            patterns['observer_pattern'] = True
                        if 'execute' in methods or 'strategy' in node.name.lower():
                            patterns['strategy_pattern'] = True
                
                analysis_results['analysis']['design_patterns'] = patterns
            
            return analysis_results
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to analyze patterns: {str(e)}'}
    
    elif action == 'extract_comments':
        try:
            # Get code content
            file_path = params.get('file_path')
            code_content = params.get('code_content')
            comment_types = params.get('comment_types', [])
            include_context = params.get('include_context', False)
            
            if file_path:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            elif not code_content:
                return {'success': False, 'error': 'Either file_path or code_content must be provided'}
            
            comments = []
            
            # Extract docstrings
            if not comment_types or 'docstring' in comment_types:
                try:
                    tree = ast.parse(code_content)
                    
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                            if (node.body and isinstance(node.body[0], ast.Expr) and 
                                isinstance(node.body[0].value, ast.Constant) and 
                                isinstance(node.body[0].value.value, str)):
                                
                                docstring_node = node.body[0]
                                comments.append({
                                    'type': 'docstring',
                                    'content': docstring_node.value.value,
                                    'line_number': docstring_node.lineno,
                                    'parent_type': type(node).__name__.lower(),
                                    'parent_name': getattr(node, 'name', 'module')
                                })
                
                except SyntaxError:
                    # Fallback regex approach for docstrings
                    import re
                    docstring_pattern = r'"""([^"]*(?:"[^"]*)*?)"""'
                    matches = re.finditer(docstring_pattern, code_content, re.DOTALL)
                    
                    for i, match in enumerate(matches):
                        line_number = code_content[:match.start()].count('\n') + 1
                        comments.append({
                            'type': 'docstring',
                            'content': match.group(1),
                            'line_number': line_number,
                            'parent_type': 'unknown',
                            'parent_name': f'docstring_{i}'
                        })
            
            # Extract inline comments
            if not comment_types or 'inline' in comment_types:
                import re
                lines = code_content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    comment_match = re.search(r'#(.*)$', line)
                    if comment_match:
                        comment_pos = comment_match.start()
                        line_before_comment = line[:comment_pos]
                        
                        # Basic check for comments not inside strings
                        single_quotes = line_before_comment.count("'")
                        double_quotes = line_before_comment.count('"')
                        
                        if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                            comments.append({
                                'type': 'inline',
                                'content': comment_match.group(1).strip(),
                                'line_number': line_num,
                                'full_line': line.strip()
                            })
            
            # Extract block comments
            if not comment_types or 'block' in comment_types:
                lines = code_content.split('\n')
                current_block = []
                block_start_line = None
                
                for line_num, line in enumerate(lines, 1):
                    stripped_line = line.strip()
                    if stripped_line.startswith('#'):
                        if not current_block:
                            block_start_line = line_num
                        current_block.append(stripped_line[1:].strip())
                    else:
                        if current_block and len(current_block) > 1:  # Multi-line block
                            comments.append({
                                'type': 'block',
                                'content': '\n'.join(current_block),
                                'line_number': block_start_line,
                                'line_count': len(current_block)
                            })
                        current_block = []
                        block_start_line = None
                
                # Handle block at end of file
                if current_block and len(current_block) > 1:
                    comments.append({
                        'type': 'block',
                        'content': '\n'.join(current_block),
                        'line_number': block_start_line,
                        'line_count': len(current_block)
                    })
            
            # Add context if requested
            if include_context:
                lines = code_content.split('\n')
                
                for comment in comments:
                    line_num = comment.get('line_number', 1)
                    context_before = []
                    context_after = []
                    
                    # Get 2 lines before and after for context
                    for i in range(max(0, line_num - 3), line_num - 1):
                        if i < len(lines):
                            context_before.append(lines[i])
                    
                    for i in range(line_num, min(len(lines), line_num + 2)):
                        if i < len(lines):
                            context_after.append(lines[i])
                    
                    comment['context'] = {
                        'before': context_before,
                        'after': context_after
                    }
            
            return {
                'success': True,
                'file_path': file_path,
                'comments': comments,
                'comment_count': len(comments),
                'comment_types': comment_types or ['all'],
                'include_context': include_context
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to extract comments: {str(e)}'}
    
    else:
        return {'success': False, 'error': f'Unknown pattern action: {action}'}


# Export for import compatibility
__all__ = ['pattern_action']