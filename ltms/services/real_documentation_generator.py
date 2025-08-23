"""
Real Documentation Generator using Python AST analysis.

This module implements actual documentation generation functionality
without any mocks, stubs, or placeholders. It uses Python's ast module
to extract docstrings and generate real markdown documentation.

Based on research of best practices for Python AST docstring extraction
and markdown generation from 2024.
"""

import ast
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


def extract_docstrings_from_file(file_path: str) -> Dict[str, Any]:
    """
    Extract docstrings from a Python file using AST analysis.
    
    Args:
        file_path: Path to the Python file to analyze
        
    Returns:
        Dict containing extracted docstring information:
        - success: bool
        - file_path: str 
        - module_docstring: str
        - functions: List[Dict] with function info and docstrings
        - classes: List[Dict] with class info and docstrings
        
    Raises:
        ValueError: If file_path is invalid
        SyntaxError: If Python file has syntax errors
    """
    if not file_path or not os.path.exists(file_path):
        raise ValueError(f"Invalid file path: {file_path}")
    
    if not file_path.endswith('.py'):
        raise ValueError(f"File must be a Python file: {file_path}")
    
    try:
        # Read and parse the Python file
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Parse into AST
        tree = ast.parse(source_code)
        
        # Extract module docstring
        module_docstring = ast.get_docstring(tree) or ""
        
        # Extract functions
        functions = []
        classes = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip methods inside classes (handled separately)
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef) and hasattr(parent, 'body'):
                        if any(child is node for child in ast.walk(parent)):
                            is_method = True
                            break
                            
                if not is_method:
                    function_info = _extract_function_info(node)
                    if function_info:
                        functions.append(function_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = _extract_class_info(node)
                if class_info:
                    classes.append(class_info)
        
        return {
            "success": True,
            "file_path": file_path,
            "module_docstring": module_docstring,
            "functions": functions,
            "classes": classes
        }
        
    except SyntaxError as e:
        return {
            "success": False,
            "error": f"Syntax error in {file_path}: {e}",
            "file_path": file_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error analyzing {file_path}: {e}",
            "file_path": file_path
        }


def _extract_function_info(func_node: ast.FunctionDef) -> Dict[str, Any]:
    """Extract information from a function AST node."""
    docstring = ast.get_docstring(func_node) or ""
    
    # Extract parameters
    parameters = []
    for arg in func_node.args.args:
        param_info = {"name": arg.arg}
        
        # Extract type annotation if present
        if arg.annotation:
            param_info["type"] = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else str(arg.annotation)
        
        parameters.append(param_info)
    
    # Extract return type
    return_type = ""
    if func_node.returns:
        return_type = ast.unparse(func_node.returns) if hasattr(ast, 'unparse') else str(func_node.returns)
    
    return {
        "name": func_node.name,
        "docstring": docstring,
        "parameters": parameters,
        "return_type": return_type,
        "is_async": isinstance(func_node, ast.AsyncFunctionDef),
        "line_number": func_node.lineno
    }


def _extract_class_info(class_node: ast.ClassDef) -> Dict[str, Any]:
    """Extract information from a class AST node."""
    docstring = ast.get_docstring(class_node) or ""
    
    # Extract methods
    methods = []
    for node in class_node.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_info = _extract_function_info(node)
            if method_info:
                methods.append(method_info)
    
    # Extract base classes
    base_classes = []
    for base in class_node.bases:
        if hasattr(ast, 'unparse'):
            base_classes.append(ast.unparse(base))
        else:
            base_classes.append(str(base))
    
    return {
        "name": class_node.name,
        "docstring": docstring,
        "methods": methods,
        "base_classes": base_classes,
        "line_number": class_node.lineno
    }


def generate_markdown_documentation(docstring_data: Dict[str, Any], project_id: str) -> str:
    """
    Generate markdown documentation from extracted docstring data.
    
    Args:
        docstring_data: Dict containing extracted docstring information
        project_id: Project identifier for the documentation
        
    Returns:
        Generated markdown documentation as string
        
    Raises:
        ValueError: If docstring_data is invalid
    """
    if not docstring_data.get("success"):
        raise ValueError("Invalid docstring data provided")
    
    markdown_lines = []
    
    # Generate header
    markdown_lines.append(f"# API Documentation for {project_id}")
    markdown_lines.append("")
    markdown_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_lines.append("")
    
    # Add module information
    file_path = docstring_data.get("file_path", "")
    if file_path:
        module_name = Path(file_path).name
        markdown_lines.append(f"## {module_name}")
        markdown_lines.append("")
        
        module_docstring = docstring_data.get("module_docstring", "")
        if module_docstring:
            markdown_lines.append(module_docstring)
            markdown_lines.append("")
    
    # Add functions
    functions = docstring_data.get("functions", [])
    if functions:
        for func in functions:
            _add_function_documentation(markdown_lines, func)
    
    # Add classes
    classes = docstring_data.get("classes", [])
    if classes:
        for cls in classes:
            _add_class_documentation(markdown_lines, cls)
    
    return "\n".join(markdown_lines)


def _add_function_documentation(markdown_lines: List[str], func_info: Dict[str, Any]):
    """Add function documentation to markdown lines."""
    func_name = func_info.get("name", "unknown")
    parameters = func_info.get("parameters", [])
    return_type = func_info.get("return_type", "")
    docstring = func_info.get("docstring", "")
    is_async = func_info.get("is_async", False)
    
    # Function signature
    async_prefix = "async " if is_async else ""
    param_strings = []
    for param in parameters:
        param_str = param["name"]
        if param.get("type"):
            param_str += f": {param['type']}"
        param_strings.append(param_str)
    
    signature = f"{async_prefix}{func_name}({', '.join(param_strings)})"
    if return_type:
        signature += f" -> {return_type}"
    
    markdown_lines.append(f"### {signature}")
    markdown_lines.append("")
    
    # Function docstring
    if docstring:
        markdown_lines.append(docstring)
        markdown_lines.append("")
    
    # Parameters section
    if parameters:
        markdown_lines.append("**Parameters:** " + ", ".join(p["name"] for p in parameters))
        markdown_lines.append("")


def _add_class_documentation(markdown_lines: List[str], class_info: Dict[str, Any]):
    """Add class documentation to markdown lines."""
    class_name = class_info.get("name", "unknown")
    docstring = class_info.get("docstring", "")
    methods = class_info.get("methods", [])
    base_classes = class_info.get("base_classes", [])
    
    # Class header
    class_signature = f"class {class_name}"
    if base_classes:
        class_signature += f"({', '.join(base_classes)})"
    
    markdown_lines.append(f"### {class_signature}")
    markdown_lines.append("")
    
    # Class docstring
    if docstring:
        markdown_lines.append(docstring)
        markdown_lines.append("")
    
    # Methods
    if methods:
        markdown_lines.append("#### Methods:")
        markdown_lines.append("")
        
        for method in methods:
            method_name = method.get("name", "unknown")
            method_params = method.get("parameters", [])
            method_docstring = method.get("docstring", "")
            
            # Method signature (simplified)
            param_names = [p["name"] for p in method_params]
            method_signature = f"{method_name}({', '.join(param_names)})"
            
            markdown_lines.append(f"##### {method_signature}")
            markdown_lines.append("")
            
            if method_docstring:
                # Take first line of docstring for brevity
                first_line = method_docstring.split('\n')[0]
                markdown_lines.append(first_line)
                markdown_lines.append("")


def write_documentation_to_file(markdown_content: str, output_file_path: str) -> Dict[str, Any]:
    """
    Write markdown documentation to a file.
    
    Args:
        markdown_content: Generated markdown content
        output_file_path: Path where to write the documentation
        
    Returns:
        Dict with operation result:
        - success: bool
        - file_path: str
        - bytes_written: int
        
    Raises:
        OSError: If file cannot be written
    """
    if not markdown_content:
        raise ValueError("Markdown content cannot be empty")
    
    if not output_file_path:
        raise ValueError("Output file path cannot be empty")
    
    try:
        # Ensure directory exists
        output_path = Path(output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Verify file was written
        if not output_path.exists():
            raise OSError(f"File was not created: {output_file_path}")
        
        bytes_written = len(markdown_content.encode('utf-8'))
        
        return {
            "success": True,
            "file_path": output_file_path,
            "bytes_written": bytes_written
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to write documentation file: {e}",
            "file_path": output_file_path
        }


def generate_documentation_from_file(
    source_file_path: str,
    output_file_path: str,
    project_id: str
) -> Dict[str, Any]:
    """
    Complete workflow: analyze Python file and generate documentation.
    
    This is the main function that combines all steps:
    1. Extract docstrings from Python file using AST
    2. Generate markdown documentation  
    3. Write documentation to output file
    
    Args:
        source_file_path: Path to Python file to document
        output_file_path: Path where to write documentation
        project_id: Project identifier for documentation header
        
    Returns:
        Dict with complete operation result:
        - success: bool
        - source_file: str
        - output_file: str  
        - functions_documented: int
        - classes_documented: int
        - bytes_written: int
        - generation_time_ms: float
    """
    start_time = time.perf_counter()
    
    try:
        # Step 1: Extract docstrings
        docstring_data = extract_docstrings_from_file(source_file_path)
        if not docstring_data["success"]:
            return {
                "success": False,
                "error": docstring_data.get("error", "Failed to extract docstrings"),
                "source_file": source_file_path
            }
        
        # Step 2: Generate markdown
        markdown_content = generate_markdown_documentation(docstring_data, project_id)
        
        # Step 3: Write to file
        write_result = write_documentation_to_file(markdown_content, output_file_path)
        if not write_result["success"]:
            return {
                "success": False,
                "error": write_result.get("error", "Failed to write documentation"),
                "source_file": source_file_path
            }
        
        # Calculate metrics
        end_time = time.perf_counter()
        generation_time_ms = (end_time - start_time) * 1000
        
        functions_count = len(docstring_data.get("functions", []))
        classes_count = len(docstring_data.get("classes", []))
        
        return {
            "success": True,
            "source_file": source_file_path,
            "output_file": output_file_path,
            "functions_documented": functions_count,
            "classes_documented": classes_count,
            "bytes_written": write_result["bytes_written"],
            "generation_time_ms": generation_time_ms
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        generation_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": False,
            "error": f"Documentation generation failed: {e}",
            "source_file": source_file_path,
            "generation_time_ms": generation_time_ms
        }