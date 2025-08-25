"""
LTMC Tech Stack Pattern Detector - AST Pattern Recognition

AST visitor for detecting MCP patterns in Python code.
Smart modularized component for pattern analysis.

Performance SLA: <500ms operations
No mocks, stubs, or placeholders - production ready only.
"""

import ast
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger(__name__)


class MCPPatternVisitor(ast.NodeVisitor):
    """AST visitor for detecting MCP patterns in Python code"""
    
    def __init__(self):
        self.patterns = []
    
    def visit_FunctionDef(self, node):
        """Detect MCP tool decorators on functions"""
        # Check for @mcp.tool decorator or @Tool decorator
        for decorator in node.decorator_list:
            if (isinstance(decorator, ast.Attribute) and
                isinstance(decorator.value, ast.Name) and
                decorator.value.id == 'mcp' and
                decorator.attr == 'tool'):
                
                self.patterns.append({
                    'type': 'mcp_tool_decorator',
                    'line': node.lineno,
                    'function_name': node.name,
                    'valid': True,
                    'details': {
                        'decorator': '@mcp.tool',
                        'has_docstring': ast.get_docstring(node) is not None,
                        'has_return_annotation': node.returns is not None
                    }
                })
            elif (isinstance(decorator, ast.Call) and
                  hasattr(decorator.func, 'id') and
                  decorator.func.id == 'Tool'):
                
                self.patterns.append({
                    'type': 'tool_decorator',
                    'line': node.lineno,
                    'function_name': node.name,
                    'valid': True,
                    'details': {
                        'decorator': '@Tool()',
                        'has_docstring': ast.get_docstring(node) is not None,
                        'has_return_annotation': node.returns is not None
                    }
                })
            elif (isinstance(decorator, ast.Name) and
                  decorator.id == 'Tool'):
                
                self.patterns.append({
                    'type': 'tool_decorator',
                    'line': node.lineno,
                    'function_name': node.name,
                    'valid': True,
                    'details': {
                        'decorator': '@Tool',
                        'has_docstring': ast.get_docstring(node) is not None,
                        'has_return_annotation': node.returns is not None
                    }
                })
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Detect MCP server creation patterns"""
        # Check for server creation patterns
        if (isinstance(node.func, ast.Attribute) and
            hasattr(node.func, 'attr') and
            node.func.attr in ['Server', 'stdio_server']):
            
            self.patterns.append({
                'type': 'mcp_server_creation',
                'line': node.lineno,
                'valid': True,
                'details': {'pattern': f'{node.func.attr}() instantiation'}
            })
        
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Detect direct MCP imports"""
        for alias in node.names:
            if alias.name.startswith('mcp'):
                self.patterns.append({
                    'type': 'mcp_import',
                    'line': node.lineno,
                    'module': alias.name,
                    'valid': True,
                    'details': {'import_type': 'direct'}
                })
        
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Detect MCP from imports"""
        if node.module and 'mcp' in node.module:
            for alias in node.names:
                self.patterns.append({
                    'type': 'mcp_from_import',
                    'line': node.lineno,
                    'module': node.module,
                    'name': alias.name,
                    'valid': True,
                    'details': {'import_type': 'from_import'}
                })
        
        self.generic_visit(node)