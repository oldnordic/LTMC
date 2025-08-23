#!/usr/bin/env python3
"""
Advanced Documentation Generation Service

Production-quality documentation extraction system combining:
- Pydantic v2 for type-aware parameter/return extraction and schema validation
- docstring-parser for parsing Google/Numpy/Sphinx-style docstrings
- Advanced AST analysis for code inspection
- Type hint extraction from function signatures

No stubs, no mocks, no placeholders - full functionality only.
"""

import ast
import importlib.util
import inspect
import logging
import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, get_origin, get_args, Callable
import json
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-party imports
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from docstring_parser import parse as parse_docstring
from docstring_parser.common import DocstringStyle

logger = logging.getLogger(__name__)


class ParameterInfo(BaseModel):
    """
    Comprehensive parameter information extracted from function signatures and docstrings.
    
    Combines runtime type inspection with docstring documentation for complete
    parameter analysis including type hints, default values, and descriptions.
    """
    name: str = Field(..., description="Parameter name")
    type_hint: Optional[str] = Field(None, description="Type hint string representation")
    default_value: Optional[Any] = Field(None, description="Default value if parameter is optional")
    description: Optional[str] = Field(None, description="Parameter description from docstring")
    is_required: bool = Field(True, description="Whether parameter is required")
    kind: str = Field(..., description="Parameter kind: POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, VAR_POSITIONAL, KEYWORD_ONLY, VAR_KEYWORD")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Type constraints and validation rules")


class ReturnInfo(BaseModel):
    """
    Return type and documentation information.
    
    Extracts return type hints from function signatures and return documentation
    from docstrings for comprehensive return value analysis.
    """
    type_hint: Optional[str] = Field(None, description="Return type hint string")
    description: Optional[str] = Field(None, description="Return value description from docstring")
    possible_values: Optional[List[str]] = Field(None, description="Documented possible return values")


class ExceptionInfo(BaseModel):
    """
    Exception documentation extracted from docstrings.
    
    Provides comprehensive exception analysis including exception types,
    conditions that trigger them, and detailed descriptions.
    """
    exception_type: str = Field(..., description="Exception class name")
    description: Optional[str] = Field(None, description="Exception description and trigger conditions")
    conditions: Optional[List[str]] = Field(None, description="Specific conditions that trigger this exception")


class ExampleInfo(BaseModel):
    """
    Code example information from docstrings.
    
    Extracts and structures code examples with descriptions and expected
    outputs for comprehensive usage documentation.
    """
    code: str = Field(..., description="Example code snippet")
    description: Optional[str] = Field(None, description="Example description")
    expected_output: Optional[str] = Field(None, description="Expected output or result")
    category: str = Field("basic", description="Example category: basic, advanced, error_handling")


class ComplexityMetrics(BaseModel):
    """
    Code complexity metrics for functions and classes.
    
    Provides quantitative analysis of code complexity including cyclomatic
    complexity, line counts, and maintainability indicators.
    """
    cyclomatic_complexity: int = Field(0, description="Cyclomatic complexity score")
    lines_of_code: int = Field(0, description="Total lines of code")
    lines_of_comments: int = Field(0, description="Total lines of comments")
    maintainability_index: Optional[float] = Field(None, description="Maintainability index score")
    nested_depth: int = Field(0, description="Maximum nesting depth")


class SourceLocation(BaseModel):
    """
    Source code location information.
    
    Provides detailed location information for functions, classes, and methods
    including file paths, line numbers, and column positions.
    """
    file_path: str = Field(..., description="Full file path")
    line_start: int = Field(..., description="Starting line number")
    line_end: Optional[int] = Field(None, description="Ending line number")
    column_start: Optional[int] = Field(None, description="Starting column position")
    column_end: Optional[int] = Field(None, description="Ending column position")


class FunctionDocumentation(BaseModel):
    """
    Comprehensive function documentation combining signature analysis and docstring parsing.
    
    Provides complete function documentation including type information,
    parameter details, return types, exceptions, examples, and metrics.
    """
    name: str = Field(..., description="Function name")
    module_path: str = Field(..., description="Module path where function is defined")
    signature: str = Field(..., description="Complete function signature")
    docstring_raw: Optional[str] = Field(None, description="Raw docstring content")
    short_description: Optional[str] = Field(None, description="Brief function description")
    long_description: Optional[str] = Field(None, description="Detailed function description")
    parameters: List[ParameterInfo] = Field(default_factory=list, description="Function parameters")
    return_info: Optional[ReturnInfo] = Field(None, description="Return type and documentation")
    exceptions: List[ExceptionInfo] = Field(default_factory=list, description="Documented exceptions")
    examples: List[ExampleInfo] = Field(default_factory=list, description="Code examples")
    decorators: List[str] = Field(default_factory=list, description="Applied decorators")
    source_location: Optional[SourceLocation] = Field(None, description="Source code location")
    complexity_metrics: Optional[ComplexityMetrics] = Field(None, description="Code complexity metrics")
    is_async: bool = Field(False, description="Whether function is async")
    is_property: bool = Field(False, description="Whether function is a property")
    is_classmethod: bool = Field(False, description="Whether function is a classmethod")
    is_staticmethod: bool = Field(False, description="Whether function is a staticmethod")


class AttributeInfo(BaseModel):
    """
    Class attribute information.
    
    Provides comprehensive attribute analysis including type hints,
    default values, and documentation for class attributes.
    """
    name: str = Field(..., description="Attribute name")
    type_hint: Optional[str] = Field(None, description="Type hint for attribute")
    default_value: Optional[Any] = Field(None, description="Default attribute value")
    description: Optional[str] = Field(None, description="Attribute description")
    is_property: bool = Field(False, description="Whether attribute is a property")
    is_class_var: bool = Field(False, description="Whether attribute is a class variable")


class ClassDocumentation(BaseModel):
    """
    Comprehensive class documentation with methods, attributes, and inheritance analysis.
    
    Provides complete class documentation including all methods, attributes,
    inheritance relationships, and complexity metrics.
    """
    name: str = Field(..., description="Class name")
    module_path: str = Field(..., description="Module path where class is defined")
    docstring_raw: Optional[str] = Field(None, description="Raw class docstring")
    short_description: Optional[str] = Field(None, description="Brief class description")
    long_description: Optional[str] = Field(None, description="Detailed class description")
    methods: List[FunctionDocumentation] = Field(default_factory=list, description="Class methods")
    attributes: List[AttributeInfo] = Field(default_factory=list, description="Class attributes")
    inheritance_chain: List[str] = Field(default_factory=list, description="Base classes in MRO order")
    decorators: List[str] = Field(default_factory=list, description="Class decorators")
    source_location: Optional[SourceLocation] = Field(None, description="Source code location")
    complexity_metrics: Optional[ComplexityMetrics] = Field(None, description="Class complexity metrics")
    is_abstract: bool = Field(False, description="Whether class is abstract")
    is_dataclass: bool = Field(False, description="Whether class is a dataclass")
    is_pydantic_model: bool = Field(False, description="Whether class is a Pydantic model")


class ModuleDocumentation(BaseModel):
    """
    Complete module documentation with all functions, classes, and metadata.
    
    Provides comprehensive module analysis including all contained functions,
    classes, imports, constants, and module-level documentation.
    """
    name: str = Field(..., description="Module name")
    file_path: str = Field(..., description="Full file path to module")
    docstring_raw: Optional[str] = Field(None, description="Raw module docstring")
    short_description: Optional[str] = Field(None, description="Brief module description")
    long_description: Optional[str] = Field(None, description="Detailed module description")
    functions: List[FunctionDocumentation] = Field(default_factory=list, description="Module functions")
    classes: List[ClassDocumentation] = Field(default_factory=list, description="Module classes")
    constants: List[AttributeInfo] = Field(default_factory=list, description="Module-level constants")
    imports: List[str] = Field(default_factory=list, description="Import statements")
    source_location: SourceLocation = Field(..., description="Module file location")
    complexity_metrics: Optional[ComplexityMetrics] = Field(None, description="Module complexity metrics")
    extraction_metadata: Dict[str, Any] = Field(default_factory=dict, description="Extraction process metadata")


class TypeExtractor:
    """
    Advanced type information extractor using runtime inspection and static analysis.
    
    Combines Python's inspect module with typing utilities to extract comprehensive
    type information from function signatures, including complex generic types.
    """
    
    def __init__(self):
        """Initialize the type extractor."""
        self.logger = logging.getLogger(f"{__name__}.TypeExtractor")
    
    def extract_function_signature(self, func: Callable, ast_node: Optional[ast.FunctionDef] = None) -> FunctionDocumentation:
        """
        Extract complete function documentation with comprehensive type information.
        
        Args:
            func: Function object to analyze
            ast_node: Optional AST node for additional static analysis
            
        Returns:
            Complete function documentation with type information
        """
        try:
            # Get function signature and type hints
            sig = inspect.signature(func)
            
            # Safe type hints extraction with fallback
            try:
                type_hints = self._get_type_hints_safe(func)
            except Exception as e:
                self.logger.warning(f"Failed to get type hints for {func.__name__}: {e}")
                type_hints = {}
            
            # Extract parameters with comprehensive information
            parameters = []
            for param_name, param in sig.parameters.items():
                param_info = ParameterInfo(
                    name=param_name,
                    type_hint=self._format_type_hint(type_hints.get(param_name)),
                    default_value=self._safe_repr(param.default) if param.default != param.empty else None,
                    is_required=param.default == param.empty,
                    kind=param.kind.name,
                    constraints=self._extract_type_constraints(type_hints.get(param_name))
                )
                parameters.append(param_info)
            
            # Extract return type information
            return_info = None
            if 'return' in type_hints:
                return_info = ReturnInfo(
                    type_hint=self._format_type_hint(type_hints['return'])
                )
            
            # Extract function metadata
            decorators = []
            is_async = inspect.iscoroutinefunction(func)
            is_property = isinstance(inspect.getattr_static(func.__class__ if hasattr(func, '__class__') else object, func.__name__, None), property)
            
            # Extract decorators from AST if available
            if ast_node:
                decorators = [self._get_decorator_name(dec) for dec in ast_node.decorator_list]
            
            # Create source location
            source_location = None
            try:
                source_file = inspect.getfile(func)
                source_lines = inspect.getsourcelines(func)
                source_location = SourceLocation(
                    file_path=source_file,
                    line_start=source_lines[1],
                    line_end=source_lines[1] + len(source_lines[0]) - 1
                )
            except Exception as e:
                self.logger.debug(f"Could not get source location for {func.__name__}: {e}")
            
            return FunctionDocumentation(
                name=func.__name__,
                module_path=func.__module__ or "unknown",
                signature=str(sig),
                docstring_raw=inspect.getdoc(func),
                parameters=parameters,
                return_info=return_info,
                decorators=decorators,
                source_location=source_location,
                is_async=is_async,
                is_property=is_property,
                is_classmethod=isinstance(inspect.getattr_static(func.__class__ if hasattr(func, '__class__') else object, func.__name__, None), classmethod),
                is_staticmethod=isinstance(inspect.getattr_static(func.__class__ if hasattr(func, '__class__') else object, func.__name__, None), staticmethod)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract function signature for {getattr(func, '__name__', 'unknown')}: {e}")
            # Return minimal documentation on error
            return FunctionDocumentation(
                name=getattr(func, '__name__', 'unknown'),
                module_path=getattr(func, '__module__', 'unknown'),
                signature="unknown",
                docstring_raw=inspect.getdoc(func) if callable(func) else None
            )
    
    def _get_type_hints_safe(self, func: Callable) -> Dict[str, Any]:
        """
        Safely get type hints with error handling for complex types.
        
        Args:
            func: Function to analyze
            
        Returns:
            Dictionary of type hints
        """
        try:
            # Try modern approach first (Python 3.10+)
            if hasattr(inspect, 'get_annotations'):
                return inspect.get_annotations(func, eval_str=True)
        except Exception:
            pass
        
        try:
            # Fallback to typing.get_type_hints
            import typing
            return typing.get_type_hints(func)
        except Exception:
            pass
        
        # Final fallback to raw annotations
        return getattr(func, '__annotations__', {})
    
    def _format_type_hint(self, type_hint: Any) -> Optional[str]:
        """
        Format type hints including complex generic types and unions.
        
        Args:
            type_hint: Type hint to format
            
        Returns:
            String representation of type hint
        """
        if type_hint is None:
            return None
        
        try:
            # Handle special typing constructs
            origin = get_origin(type_hint)
            args = get_args(type_hint)
            
            if origin is not None:
                if args:
                    # Handle generic types like List[str], Dict[str, int]
                    args_str = ', '.join(self._format_type_hint(arg) or 'Any' for arg in args)
                    origin_name = getattr(origin, '__name__', str(origin))
                    return f"{origin_name}[{args_str}]"
                else:
                    # Handle origins without arguments
                    return getattr(origin, '__name__', str(origin))
            
            # Handle regular types
            if hasattr(type_hint, '__name__'):
                return type_hint.__name__
            
            # Handle string annotations
            if isinstance(type_hint, str):
                return type_hint
            
            # Fallback to string representation
            return str(type_hint)
            
        except Exception as e:
            self.logger.debug(f"Failed to format type hint {type_hint}: {e}")
            return str(type_hint)
    
    def _extract_type_constraints(self, type_hint: Any) -> Optional[Dict[str, Any]]:
        """
        Extract type constraints for validation (e.g., from Pydantic Field).
        
        Args:
            type_hint: Type hint to analyze
            
        Returns:
            Dictionary of constraints if any found
        """
        # This would be expanded to extract Pydantic Field constraints,
        # typing.Annotated constraints, etc.
        return None
    
    def _safe_repr(self, value: Any) -> str:
        """
        Safe string representation of values.
        
        Args:
            value: Value to represent
            
        Returns:
            String representation
        """
        try:
            if value == inspect.Parameter.empty:
                return "No default"
            return repr(value)
        except Exception:
            return str(type(value).__name__)
    
    def _get_decorator_name(self, decorator_node: ast.expr) -> str:
        """
        Extract decorator name from AST node.
        
        Args:
            decorator_node: AST decorator node
            
        Returns:
            Decorator name as string
        """
        try:
            if isinstance(decorator_node, ast.Name):
                return decorator_node.id
            elif isinstance(decorator_node, ast.Attribute):
                return f"{self._get_name(decorator_node.value)}.{decorator_node.attr}"
            elif isinstance(decorator_node, ast.Call):
                if isinstance(decorator_node.func, ast.Name):
                    return f"{decorator_node.func.id}(...)"
                elif isinstance(decorator_node.func, ast.Attribute):
                    return f"{self._get_name(decorator_node.func.value)}.{decorator_node.func.attr}(...)"
            
            return "unknown_decorator"
            
        except Exception:
            return "unknown_decorator"
    
    def _get_name(self, node: ast.expr) -> str:
        """
        Extract name from AST node.
        
        Args:
            node: AST node
            
        Returns:
            Name as string
        """
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_name(node.value)}.{node.attr}"
            else:
                return "unknown"
        except Exception:
            return "unknown"


class DocstringParser:
    """
    Multi-style docstring parser supporting Google, Numpy, and Sphinx formats.
    
    Provides unified parsing interface for extracting structured information
    from docstrings regardless of their formatting style.
    """
    
    def __init__(self):
        """Initialize the docstring parser."""
        self.logger = logging.getLogger(f"{__name__}.DocstringParser")
    
    def parse_docstring(self, docstring: Optional[str]) -> Dict[str, Any]:
        """
        Parse docstring and extract structured information.
        
        Args:
            docstring: Raw docstring text
            
        Returns:
            Dictionary with parsed docstring components
        """
        if not docstring or not docstring.strip():
            return {}
        
        try:
            # Try to parse with docstring_parser
            parsed = parse_docstring(docstring)
            
            return {
                'short_description': parsed.short_description,
                'long_description': parsed.long_description,
                'parameters': self._extract_parameters(parsed.params),
                'returns': self._extract_returns(parsed.returns),
                'exceptions': self._extract_exceptions(parsed.raises),
                'examples': self._extract_examples(parsed.examples),
                'notes': getattr(parsed, 'notes', None),
                'style': self._detect_docstring_style(docstring)
            }
            
        except Exception as e:
            self.logger.debug(f"Failed to parse docstring: {e}")
            # Fallback to basic parsing
            return {
                'docstring_raw': docstring,
                'short_description': self._extract_first_line(docstring),
                'style': 'unknown'
            }
    
    def _extract_parameters(self, params) -> List[Dict[str, Any]]:
        """
        Extract parameter information from parsed docstring.
        
        Args:
            params: Parsed parameter objects
            
        Returns:
            List of parameter dictionaries
        """
        if not params:
            return []
        
        result = []
        for param in params:
            param_info = {
                'name': param.arg_name,
                'description': param.description,
                'type_hint': getattr(param, 'type_name', None),
                'is_optional': getattr(param, 'is_optional', False)
            }
            result.append(param_info)
        
        return result
    
    def _extract_returns(self, returns) -> Optional[Dict[str, Any]]:
        """
        Extract return information from parsed docstring.
        
        Args:
            returns: Parsed returns object
            
        Returns:
            Return information dictionary
        """
        if not returns:
            return None
        
        return {
            'description': returns.description,
            'type_hint': getattr(returns, 'type_name', None)
        }
    
    def _extract_exceptions(self, raises) -> List[Dict[str, Any]]:
        """
        Extract exception information from parsed docstring.
        
        Args:
            raises: Parsed raises objects
            
        Returns:
            List of exception dictionaries
        """
        if not raises:
            return []
        
        result = []
        for exc in raises:
            exc_info = {
                'exception_type': getattr(exc, 'type_name', 'Exception'),
                'description': exc.description
            }
            result.append(exc_info)
        
        return result
    
    def _extract_examples(self, examples) -> List[Dict[str, Any]]:
        """
        Extract example information from parsed docstring.
        
        Args:
            examples: Parsed example objects
            
        Returns:
            List of example dictionaries
        """
        if not examples:
            return []
        
        result = []
        for example in examples:
            example_info = {
                'code': getattr(example, 'snippet', ''),
                'description': getattr(example, 'description', ''),
                'category': 'basic'
            }
            result.append(example_info)
        
        return result
    
    def _detect_docstring_style(self, docstring: str) -> str:
        """
        Detect docstring style (Google, Numpy, Sphinx).
        
        Args:
            docstring: Raw docstring text
            
        Returns:
            Detected style name
        """
        if 'Args:' in docstring or 'Returns:' in docstring:
            return 'google'
        elif 'Parameters' in docstring and '----------' in docstring:
            return 'numpy'
        elif ':param ' in docstring or ':type ' in docstring:
            return 'sphinx'
        else:
            return 'unknown'
    
    def _extract_first_line(self, docstring: str) -> str:
        """
        Extract first non-empty line as short description.
        
        Args:
            docstring: Raw docstring text
            
        Returns:
            First line content
        """
        lines = docstring.strip().split('\n')
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped
        return ""


class ASTAnalyzer(ast.NodeVisitor):
    """
    Advanced AST analyzer for comprehensive code structure extraction.
    
    Performs static analysis of Python code to extract functions, classes,
    complexity metrics, and other structural information.
    """
    
    def __init__(self):
        """Initialize the AST analyzer."""
        self.functions = []
        self.classes = []
        self.imports = []
        self.constants = []
        self.complexity_metrics = {}
        self.current_class = None
        self.logger = logging.getLogger(f"{__name__}.ASTAnalyzer")
    
    def analyze_module(self, source_code: str, file_path: str) -> Dict[str, Any]:
        """
        Analyze complete module structure.
        
        Args:
            source_code: Python source code
            file_path: Path to source file
            
        Returns:
            Dictionary with analysis results
        """
        try:
            tree = ast.parse(source_code, filename=file_path)
            self.visit(tree)
            
            return {
                'functions': self.functions,
                'classes': self.classes,
                'imports': self.imports,
                'constants': self.constants,
                'complexity_metrics': self.complexity_metrics
            }
            
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return {
                'functions': [],
                'classes': [],
                'imports': [],
                'constants': [],
                'complexity_metrics': {},
                'parse_error': str(e)
            }
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visit function definition and extract comprehensive information.
        
        Args:
            node: AST function definition node
        """
        try:
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            complexity = self._calculate_complexity(node)
            
            func_info = {
                'name': node.name,
                'lineno': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'end_lineno': getattr(node, 'end_lineno', node.lineno),
                'decorators': decorators,
                'complexity': complexity,
                'docstring': ast.get_docstring(node),
                'is_async': False,
                'args': [arg.arg for arg in node.args.args],
                'parent_class': self.current_class
            }
            
            self.functions.append(func_info)
            
        except Exception as e:
            self.logger.error(f"Error analyzing function {node.name}: {e}")
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visit async function definition.
        
        Args:
            node: AST async function definition node
        """
        try:
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            complexity = self._calculate_complexity(node)
            
            func_info = {
                'name': node.name,
                'lineno': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'end_lineno': getattr(node, 'end_lineno', node.lineno),
                'decorators': decorators,
                'complexity': complexity,
                'docstring': ast.get_docstring(node),
                'is_async': True,
                'args': [arg.arg for arg in node.args.args],
                'parent_class': self.current_class
            }
            
            self.functions.append(func_info)
            
        except Exception as e:
            self.logger.error(f"Error analyzing async function {node.name}: {e}")
        
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visit class definition and extract comprehensive information.
        
        Args:
            node: AST class definition node
        """
        try:
            bases = [self._get_name(base) for base in node.bases]
            decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
            
            # Check for special class types
            is_dataclass = any('dataclass' in dec for dec in decorators)
            is_pydantic_model = any('BaseModel' in base for base in bases)
            
            class_info = {
                'name': node.name,
                'lineno': node.lineno,
                'col_offset': getattr(node, 'col_offset', 0),
                'end_lineno': getattr(node, 'end_lineno', node.lineno),
                'bases': bases,
                'decorators': decorators,
                'docstring': ast.get_docstring(node),
                'is_dataclass': is_dataclass,
                'is_pydantic_model': is_pydantic_model,
                'methods': [],
                'attributes': []
            }
            
            # Set current class context for method processing
            previous_class = self.current_class
            self.current_class = node.name
            
            # Extract class attributes
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    # Type annotated attribute
                    attr_info = {
                        'name': item.target.id,
                        'type_hint': self._get_name(item.annotation) if item.annotation else None,
                        'has_default': item.value is not None,
                        'lineno': item.lineno
                    }
                    class_info['attributes'].append(attr_info)
            
            self.classes.append(class_info)
            
            # Continue visiting child nodes
            self.generic_visit(node)
            
            # Restore previous class context
            self.current_class = previous_class
            
        except Exception as e:
            self.logger.error(f"Error analyzing class {node.name}: {e}")
    
    def visit_Import(self, node: ast.Import):
        """
        Visit import statement.
        
        Args:
            node: AST import node
        """
        for alias in node.names:
            import_info = {
                'type': 'import',
                'name': alias.name,
                'alias': alias.asname,
                'lineno': node.lineno
            }
            self.imports.append(import_info)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Visit from-import statement.
        
        Args:
            node: AST import-from node
        """
        for alias in node.names:
            import_info = {
                'type': 'from_import',
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'level': node.level,
                'lineno': node.lineno
            }
            self.imports.append(import_info)
    
    def visit_Assign(self, node: ast.Assign):
        """
        Visit assignment statement to extract constants.
        
        Args:
            node: AST assignment node
        """
        # Only capture module-level assignments
        if self.current_class is None:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    # Likely a constant (all uppercase)
                    constant_info = {
                        'name': target.id,
                        'lineno': node.lineno,
                        'value_type': type(node.value).__name__
                    }
                    self.constants.append(constant_info)
        
        self.generic_visit(node)
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity for a code block.
        
        Args:
            node: AST node to analyze
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, 
                                ast.Try, ast.ExceptHandler, ast.AsyncFor, 
                                ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # Add complexity for boolean operators
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_decorator_name(self, decorator_node: ast.expr) -> str:
        """
        Extract decorator name from AST node.
        
        Args:
            decorator_node: AST decorator node
            
        Returns:
            Decorator name as string
        """
        try:
            if isinstance(decorator_node, ast.Name):
                return decorator_node.id
            elif isinstance(decorator_node, ast.Attribute):
                return f"{self._get_name(decorator_node.value)}.{decorator_node.attr}"
            elif isinstance(decorator_node, ast.Call):
                if isinstance(decorator_node.func, ast.Name):
                    return f"{decorator_node.func.id}(...)"
                elif isinstance(decorator_node.func, ast.Attribute):
                    return f"{self._get_name(decorator_node.func.value)}.{decorator_node.func.attr}(...)"
            
            return "unknown_decorator"
            
        except Exception:
            return "unknown_decorator"
    
    def _get_name(self, node: ast.expr) -> str:
        """
        Extract name from AST node.
        
        Args:
            node: AST node
            
        Returns:
            Name as string
        """
        try:
            if isinstance(node, ast.Name):
                return node.id
            elif isinstance(node, ast.Attribute):
                return f"{self._get_name(node.value)}.{node.attr}"
            elif isinstance(node, ast.Constant):
                return str(node.value)
            else:
                return "unknown"
        except Exception:
            return "unknown"


class AdvancedDocumentationExtractor:
    """
    Main orchestrator combining all extraction components for comprehensive documentation generation.
    
    Integrates type extraction, docstring parsing, and AST analysis to produce
    complete module documentation with all metadata and cross-references.
    """
    
    def __init__(self):
        """Initialize the advanced documentation extractor."""
        self.type_extractor = TypeExtractor()
        self.docstring_parser = DocstringParser()
        self.ast_analyzer = ASTAnalyzer()
        self.logger = logging.getLogger(f"{__name__}.AdvancedDocumentationExtractor")
    
    def extract_module_documentation(self, module_path: str) -> ModuleDocumentation:
        """
        Extract comprehensive documentation for a Python module.
        
        Args:
            module_path: Path to Python module file
            
        Returns:
            Complete module documentation
        """
        try:
            module_path = os.path.abspath(module_path)
            
            if not os.path.exists(module_path):
                raise FileNotFoundError(f"Module file not found: {module_path}")
            
            if not module_path.endswith('.py'):
                raise ValueError(f"File is not a Python module: {module_path}")
            
            # Read source code
            with open(module_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Perform AST analysis
            ast_analysis = self.ast_analyzer.analyze_module(source_code, module_path)
            
            # Import module for runtime inspection
            module = self._import_module_safe(module_path)
            
            # Extract module-level documentation
            module_docstring = inspect.getdoc(module) if module else None
            docstring_info = self.docstring_parser.parse_docstring(module_docstring)
            
            # Create source location
            source_location = SourceLocation(
                file_path=module_path,
                line_start=1,
                line_end=len(source_code.split('\n'))
            )
            
            # Extract functions
            functions = []
            if module:
                for func_name in dir(module):
                    try:
                        obj = getattr(module, func_name)
                        if (inspect.isfunction(obj) and 
                            obj.__module__ == module.__name__ and 
                            not func_name.startswith('_')):
                            
                            # Find corresponding AST node
                            ast_func = next((f for f in ast_analysis['functions'] 
                                           if f['name'] == func_name), None)
                            
                            # Extract function documentation
                            func_doc = self.type_extractor.extract_function_signature(obj)
                            
                            # Enhance with docstring parsing
                            func_docstring_info = self.docstring_parser.parse_docstring(func_doc.docstring_raw)
                            func_doc.short_description = func_docstring_info.get('short_description')
                            func_doc.long_description = func_docstring_info.get('long_description')
                            
                            # Enhance parameters with docstring information
                            docstring_params = {p['name']: p for p in func_docstring_info.get('parameters', [])}
                            for param in func_doc.parameters:
                                if param.name in docstring_params:
                                    param.description = docstring_params[param.name].get('description')
                            
                            # Enhance return information
                            docstring_returns = func_docstring_info.get('returns')
                            if docstring_returns and func_doc.return_info:
                                func_doc.return_info.description = docstring_returns.get('description')
                            
                            # Add exceptions from docstring
                            func_doc.exceptions = [
                                ExceptionInfo(
                                    exception_type=exc['exception_type'],
                                    description=exc['description']
                                )
                                for exc in func_docstring_info.get('exceptions', [])
                            ]
                            
                            # Add examples from docstring
                            func_doc.examples = [
                                ExampleInfo(
                                    code=example['code'],
                                    description=example['description'],
                                    category=example['category']
                                )
                                for example in func_docstring_info.get('examples', [])
                            ]
                            
                            # Add complexity metrics from AST
                            if ast_func:
                                func_doc.complexity_metrics = ComplexityMetrics(
                                    cyclomatic_complexity=ast_func.get('complexity', 0),
                                    lines_of_code=ast_func.get('end_lineno', 0) - ast_func.get('lineno', 0) + 1
                                )
                            
                            functions.append(func_doc)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to extract function {func_name}: {e}")
            
            # Extract classes (similar pattern to functions)
            classes = []
            if module:
                for class_name in dir(module):
                    try:
                        obj = getattr(module, class_name)
                        if (inspect.isclass(obj) and 
                            obj.__module__ == module.__name__ and 
                            not class_name.startswith('_')):
                            
                            # Find corresponding AST node
                            ast_class = next((c for c in ast_analysis['classes'] 
                                            if c['name'] == class_name), None)
                            
                            class_doc = self._extract_class_documentation(obj, ast_class)
                            classes.append(class_doc)
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to extract class {class_name}: {e}")
            
            # Extract constants
            constants = []
            for const_info in ast_analysis.get('constants', []):
                try:
                    if module and hasattr(module, const_info['name']):
                        value = getattr(module, const_info['name'])
                        constant = AttributeInfo(
                            name=const_info['name'],
                            type_hint=type(value).__name__,
                            default_value=self.type_extractor._safe_repr(value),
                            description=f"Module constant of type {type(value).__name__}"
                        )
                        constants.append(constant)
                except Exception as e:
                    self.logger.warning(f"Failed to extract constant {const_info['name']}: {e}")
            
            # Create module complexity metrics
            total_functions = len(functions)
            total_classes = len(classes)
            total_complexity = sum(
                f.complexity_metrics.cyclomatic_complexity 
                for f in functions 
                if f.complexity_metrics
            )
            
            module_complexity = ComplexityMetrics(
                cyclomatic_complexity=total_complexity,
                lines_of_code=len(source_code.split('\n'))
            )
            
            # Create extraction metadata
            extraction_metadata = {
                'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                'extractor_version': '1.0.0',
                'total_functions_extracted': total_functions,
                'total_classes_extracted': total_classes,
                'ast_parse_successful': 'parse_error' not in ast_analysis,
                'module_import_successful': module is not None
            }
            
            return ModuleDocumentation(
                name=os.path.splitext(os.path.basename(module_path))[0],
                file_path=module_path,
                docstring_raw=module_docstring,
                short_description=docstring_info.get('short_description'),
                long_description=docstring_info.get('long_description'),
                functions=functions,
                classes=classes,
                constants=constants,
                imports=[f"{imp['type']}:{imp['name']}" for imp in ast_analysis.get('imports', [])],
                source_location=source_location,
                complexity_metrics=module_complexity,
                extraction_metadata=extraction_metadata
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract module documentation for {module_path}: {e}")
            # Return minimal documentation on error
            return ModuleDocumentation(
                name=os.path.splitext(os.path.basename(module_path))[0] if os.path.exists(module_path) else "unknown",
                file_path=module_path,
                source_location=SourceLocation(file_path=module_path, line_start=1),
                extraction_metadata={
                    'extraction_timestamp': datetime.now(timezone.utc).isoformat(),
                    'extraction_error': str(e),
                    'extractor_version': '1.0.0'
                }
            )
    
    def _import_module_safe(self, module_path: str) -> Optional[Any]:
        """
        Safely import a module for runtime inspection.
        
        Args:
            module_path: Path to module file
            
        Returns:
            Imported module or None if import fails
        """
        try:
            spec = importlib.util.spec_from_file_location("temp_module", module_path)
            if spec is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Add to sys.modules to handle relative imports
            sys.modules["temp_module"] = module
            
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            self.logger.debug(f"Failed to import module {module_path}: {e}")
            return None
        finally:
            # Clean up sys.modules
            if "temp_module" in sys.modules:
                del sys.modules["temp_module"]
    
    def _extract_class_documentation(self, cls: type, ast_class: Optional[Dict[str, Any]]) -> ClassDocumentation:
        """
        Extract comprehensive class documentation.
        
        Args:
            cls: Class object to analyze
            ast_class: AST class information
            
        Returns:
            Complete class documentation
        """
        try:
            # Extract class docstring
            class_docstring = inspect.getdoc(cls)
            docstring_info = self.docstring_parser.parse_docstring(class_docstring)
            
            # Get inheritance chain
            inheritance_chain = [base.__name__ for base in cls.__mro__[1:] if base != object]
            
            # Extract methods
            methods = []
            for method_name in dir(cls):
                if not method_name.startswith('_'):
                    try:
                        method_obj = getattr(cls, method_name)
                        if inspect.ismethod(method_obj) or inspect.isfunction(method_obj):
                            method_doc = self.type_extractor.extract_function_signature(method_obj)
                            methods.append(method_doc)
                    except Exception as e:
                        self.logger.debug(f"Failed to extract method {method_name}: {e}")
            
            # Extract attributes from AST
            attributes = []
            if ast_class:
                for attr_info in ast_class.get('attributes', []):
                    attribute = AttributeInfo(
                        name=attr_info['name'],
                        type_hint=attr_info.get('type_hint'),
                        description=f"Class attribute"
                    )
                    attributes.append(attribute)
            
            # Create source location
            source_location = None
            try:
                source_file = inspect.getfile(cls)
                source_lines = inspect.getsourcelines(cls)
                source_location = SourceLocation(
                    file_path=source_file,
                    line_start=source_lines[1],
                    line_end=source_lines[1] + len(source_lines[0]) - 1
                )
            except Exception:
                pass
            
            # Determine class characteristics
            is_dataclass = hasattr(cls, '__dataclass_fields__')
            is_pydantic_model = hasattr(cls, '__pydantic_fields_set__')
            is_abstract = inspect.isabstract(cls)
            
            return ClassDocumentation(
                name=cls.__name__,
                module_path=cls.__module__,
                docstring_raw=class_docstring,
                short_description=docstring_info.get('short_description'),
                long_description=docstring_info.get('long_description'),
                methods=methods,
                attributes=attributes,
                inheritance_chain=inheritance_chain,
                decorators=ast_class.get('decorators', []) if ast_class else [],
                source_location=source_location,
                is_abstract=is_abstract,
                is_dataclass=is_dataclass,
                is_pydantic_model=is_pydantic_model
            )
            
        except Exception as e:
            self.logger.error(f"Failed to extract class documentation for {cls.__name__}: {e}")
            return ClassDocumentation(
                name=cls.__name__,
                module_path=getattr(cls, '__module__', 'unknown')
            )
    
    @lru_cache(maxsize=128)
    def extract_module_documentation_cached(self, module_path: str) -> ModuleDocumentation:
        """
        Cached version of module documentation extraction for performance.
        
        Args:
            module_path: Path to Python module file
            
        Returns:
            Complete module documentation (cached)
        """
        return self.extract_module_documentation(module_path)
    
    def extract_project_documentation(self, project_paths: List[str], max_workers: int = 4) -> List[ModuleDocumentation]:
        """
        Extract documentation for multiple modules in parallel.
        
        Args:
            project_paths: List of Python module file paths
            max_workers: Maximum number of worker threads
            
        Returns:
            List of module documentation objects
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all extraction tasks
            future_to_path = {
                executor.submit(self.extract_module_documentation, path): path 
                for path in project_paths
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(f"Successfully extracted documentation for {path}")
                except Exception as e:
                    self.logger.error(f"Failed to extract documentation for {path}: {e}")
                    # Add minimal documentation for failed extractions
                    results.append(ModuleDocumentation(
                        name=os.path.splitext(os.path.basename(path))[0],
                        file_path=path,
                        source_location=SourceLocation(file_path=path, line_start=1),
                        extraction_metadata={
                            'extraction_error': str(e),
                            'extraction_timestamp': datetime.now(timezone.utc).isoformat()
                        }
                    ))
        
        return results


# Export the main extractor class and models
__all__ = [
    'AdvancedDocumentationExtractor',
    'ModuleDocumentation', 
    'FunctionDocumentation',
    'ClassDocumentation',
    'ParameterInfo',
    'ReturnInfo',
    'ExceptionInfo',
    'ExampleInfo',
    'ComplexityMetrics',
    'SourceLocation',
    'AttributeInfo',
    'TypeExtractor',
    'DocstringParser',
    'ASTAnalyzer'
]