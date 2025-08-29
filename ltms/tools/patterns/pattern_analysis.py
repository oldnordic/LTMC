"""
Pattern analysis extension for LTMC pattern tools.
Contains the remaining complex analysis methods.

File: ltms/tools/patterns/pattern_analysis.py
Lines: ~280 (under 300 limit)
Purpose: Complex pattern analysis operations
"""

import ast
import re
from typing import Dict, Any


class PatternAnalysisExtension:
    """Extension class for complex pattern analysis operations."""
    
    @staticmethod
    async def action_summarize_code(source_code: str) -> Dict[str, Any]:
        """Summarize code structure and complexity."""
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
    
    @staticmethod
    async def action_analyze_patterns(file_path: str = None, code_content: str = None, 
                                    analysis_type: str = 'general', pattern_types: list = None) -> Dict[str, Any]:
        """Analyze code patterns and design patterns."""
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            except Exception as e:
                return {'success': False, 'error': f'Failed to read file: {str(e)}'}
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
    
    @staticmethod
    async def action_extract_comments(file_path: str = None, code_content: str = None,
                                    comment_types: list = None, include_context: bool = False) -> Dict[str, Any]:
        """Extract comments from code with optional context."""
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    code_content = f.read()
            except Exception as e:
                return {'success': False, 'error': f'Failed to read file: {str(e)}'}
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