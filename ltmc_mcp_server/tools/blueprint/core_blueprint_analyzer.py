"""
Core Blueprint Analyzer - Python Code Analysis Engine
====================================================

Python AST-based code analyzer for extracting functions, classes, imports, and complexity metrics.
Used by core blueprint tools for code analysis and blueprint generation.
"""

import ast
import logging
from typing import Dict, Any, List, Set, Tuple

from ltmc_mcp_server.utils.logging_utils import get_tool_logger


class PythonCodeAnalyzer(ast.NodeVisitor):
    """
    AST-based Python code analyzer for extracting functions, classes, imports, and complexity metrics.
    """
    
    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = []
        self.relationships = []
        self.current_class = None
        self.function_calls = []
    
    def visit_FunctionDef(self, node):
        """Extract function definitions with complexity analysis."""
        complexity = self._calculate_cyclomatic_complexity(node)
        function_info = {
            "type": "function",
            "name": node.name,
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "complexity": self._complexity_level(complexity),
            "complexity_score": complexity,
            "async": False,
            "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
            "args": [arg.arg for arg in node.args.args] if node.args else [],
            "returns": self._get_return_annotation(node.returns) if node.returns else None,
            "docstring": ast.get_docstring(node),
            "parent_class": self.current_class
        }
        self.functions.append(function_info)
        
        # Track function calls within this function
        old_function_calls = len(self.function_calls)
        self.generic_visit(node)
        new_calls = self.function_calls[old_function_calls:]
        
        # Create relationships for function calls
        for call_name in new_calls:
            self.relationships.append({
                "from": node.name,
                "to": call_name,
                "type": "calls"
            })
    
    def visit_AsyncFunctionDef(self, node):
        """Extract async function definitions."""
        complexity = self._calculate_cyclomatic_complexity(node)
        function_info = {
            "type": "function",
            "name": node.name,
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "complexity": self._complexity_level(complexity),
            "complexity_score": complexity,
            "async": True,
            "decorators": [self._get_decorator_name(dec) for dec in node.decorator_list],
            "args": [arg.arg for arg in node.args.args] if node.args else [],
            "returns": self._get_return_annotation(node.returns) if node.returns else None,
            "docstring": ast.get_docstring(node),
            "parent_class": self.current_class
        }
        self.functions.append(function_info)
        
        # Track function calls within this async function
        old_function_calls = len(self.function_calls)
        self.generic_visit(node)
        new_calls = self.function_calls[old_function_calls:]
        
        for call_name in new_calls:
            self.relationships.append({
                "from": node.name,
                "to": call_name,
                "type": "calls"
            })
    
    def visit_ClassDef(self, node):
        """Extract class definitions with inheritance analysis."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Extract class information
        class_info = {
            "type": "class",
            "name": node.name,
            "line_start": node.lineno,
            "line_end": node.end_lineno or node.lineno,
            "bases": [self._get_base_name(base) for base in node.bases],
            "docstring": ast.get_docstring(node),
            "methods": [],
            "attributes": []
        }
        
        # Visit class body to extract methods and attributes
        self.generic_visit(node)
        
        # Filter methods for this class
        class_methods = [f for f in self.functions if f.get("parent_class") == node.name]
        class_info["methods"] = class_methods
        
        # Calculate class complexity
        class_info["complexity_score"] = sum(m.get("complexity_score", 0) for m in class_methods)
        class_info["complexity"] = self._complexity_level(class_info["complexity_score"])
        
        self.classes.append(class_info)
        
        # Create inheritance relationships
        for base in node.bases:
            base_name = self._get_base_name(base)
            if base_name != "object":  # Skip object base class
                self.relationships.append({
                    "from": node.name,
                    "to": base_name,
                    "type": "inherits_from"
                })
        
        self.current_class = old_class
    
    def visit_Import(self, node):
        """Extract import statements."""
        for alias in node.names:
            self.imports.append({
                "type": "import",
                "module": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
    
    def visit_ImportFrom(self, node):
        """Extract from-import statements."""
        module = node.module or ""
        for alias in node.names:
            self.imports.append({
                "type": "from_import",
                "module": module,
                "name": alias.name,
                "alias": alias.asname,
                "line": node.lineno
            })
    
    def visit_Call(self, node):
        """Track function calls for relationship analysis."""
        if isinstance(node.func, ast.Name):
            self.function_calls.append(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                self.function_calls.append(f"{node.func.value.id}.{node.func.attr}")
    
    def _calculate_cyclomatic_complexity(self, node) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _complexity_level(self, complexity: int) -> str:
        """Convert complexity score to human-readable level."""
        if complexity <= 5:
            return "low"
        elif complexity <= 10:
            return "medium"
        elif complexity <= 20:
            return "high"
        else:
            return "very_high"
    
    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Call):
            if isinstance(decorator.func, ast.Name):
                return decorator.func.id
        return "unknown"
    
    def _get_base_name(self, base) -> str:
        """Extract base class name from AST node."""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return "unknown"
    
    def _get_return_annotation(self, annotation) -> str:
        """Extract return type annotation from AST node."""
        if annotation is None:
            return None
        if isinstance(annotation, ast.Name):
            return annotation.id
        elif isinstance(annotation, ast.Constant):
            return str(annotation.value)
        return "unknown"


def analyze_python_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file using AST-based analysis.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dict with analysis results including code elements and relationships
    """
    logger = get_tool_logger('blueprint_analyzer')
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Parse AST
        tree = ast.parse(content)
        
        # Analyze with visitor
        analyzer = PythonCodeAnalyzer()
        analyzer.visit(tree)
        
        # Compile results
        code_elements = analyzer.functions + analyzer.classes + analyzer.imports
        
        # Calculate summary metrics
        total_functions = len(analyzer.functions)
        total_classes = len(analyzer.classes)
        total_imports = len(analyzer.imports)
        total_relationships = len(analyzer.relationships)
        
        avg_complexity = sum(f.get("complexity_score", 0) for f in analyzer.functions)
        avg_complexity = avg_complexity / total_functions if total_functions > 0 else 0
        
        summary = {
            "file_path": file_path,
            "total_elements": len(code_elements),
            "functions": total_functions,
            "classes": total_classes,
            "imports": total_imports,
            "relationships": total_relationships,
            "average_complexity": round(avg_complexity, 2),
            "complexity_distribution": {
                "low": len([f for f in analyzer.functions if f.get("complexity") == "low"]),
                "medium": len([f for f in analyzer.functions if f.get("complexity") == "medium"]),
                "high": len([f for f in analyzer.functions if f.get("complexity") == "high"]),
                "very_high": len([f for f in analyzer.functions if f.get("complexity") == "very_high"])
            }
        }
        
        return {
            "success": True,
            "code_elements": code_elements,
            "relationships": analyzer.relationships,
            "summary": summary
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}"
        }
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in {file_path}: {e}"
        }
    except Exception as e:
        logger.error(f"Error analyzing {file_path}: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}"
        }
