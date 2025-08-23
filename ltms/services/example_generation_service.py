#!/usr/bin/env python3
"""
Example Generation & Enrichment Service for LTMC Documentation Generation.

This service extracts real usage patterns and examples from the codebase including:
- Function call examples with actual parameters
- Class instantiation patterns with real constructor arguments
- Method chaining patterns and fluent interfaces
- Error handling patterns and exception usage
- Configuration and setup examples
- Integration patterns between modules

Analyzes real code to find actual usage patterns, not synthetic examples.
Uses AST analysis, regex patterns, and code context to extract meaningful examples.

Real implementations only - no stubs, mocks, or placeholders.
"""

import ast
import os
import re
import json
import logging
from typing import Dict, List, Optional, Set, Any, Union, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import inspect
import textwrap
from collections import defaultdict, Counter

# Import our existing services
from .cross_reference_service import (
    CrossReferenceEngine,
    DocumentationSymbolTable,
    SymbolReference,
    CrossReference
)
from .advanced_documentation_service import (
    AdvancedDocumentationExtractor,
    ModuleDocumentation,
    FunctionDocumentation,
    ClassDocumentation
)

logger = logging.getLogger(__name__)

class ExampleType(Enum):
    """Types of code examples that can be extracted."""
    FUNCTION_CALL = "function_call"
    CLASS_INSTANTIATION = "class_instantiation"
    METHOD_CHAIN = "method_chain"
    ERROR_HANDLING = "error_handling"
    CONFIGURATION = "configuration"
    INTEGRATION = "integration"
    ASYNC_USAGE = "async_usage"
    DECORATOR_USAGE = "decorator_usage"
    CONTEXT_MANAGER = "context_manager"
    COMPREHENSION = "comprehension"

class ExampleQuality(Enum):
    """Quality levels for extracted examples."""
    EXCELLENT = "excellent"  # Complete, well-documented, real-world usage
    GOOD = "good"           # Clear usage pattern, good context
    FAIR = "fair"           # Basic usage, minimal context
    POOR = "poor"           # Incomplete or unclear usage

@dataclass
class CodeExample:
    """Represents a real code usage example."""
    example_type: ExampleType
    symbol_name: str
    code_snippet: str
    file_path: str
    line_number: int
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)
    description: Optional[str] = None
    quality: ExampleQuality = ExampleQuality.FAIR
    parameters: Dict[str, Any] = field(default_factory=dict)
    return_value: Optional[str] = None
    imports_required: List[str] = field(default_factory=list)
    error_handling: Optional[str] = None
    related_examples: List[str] = field(default_factory=list)
    usage_frequency: int = 1
    docstring_context: Optional[str] = None

@dataclass
class UsagePattern:
    """Represents a common usage pattern for a symbol."""
    pattern_name: str
    symbol_name: str
    pattern_type: ExampleType
    examples: List[CodeExample] = field(default_factory=list)
    frequency: int = 0
    confidence_score: float = 0.0
    description: str = ""
    best_practices: List[str] = field(default_factory=list)
    common_mistakes: List[str] = field(default_factory=list)

@dataclass
class ExampleCollection:
    """Collection of examples for a symbol or module."""
    symbol_name: str
    symbol_type: str  # function, class, method, etc.
    module_path: str
    examples: List[CodeExample] = field(default_factory=list)
    usage_patterns: List[UsagePattern] = field(default_factory=list)
    total_usage_count: int = 0
    complexity_score: float = 0.0
    documentation_coverage: float = 0.0

class ExampleExtractor:
    """Extracts code examples from AST analysis."""
    
    def __init__(self):
        self.current_file = ""
        self.current_module = ""
        self.source_lines = []
        self.imports = {}
        self.context_window = 3  # Lines of context before/after
    
    def extract_examples_from_file(self, file_path: str) -> List[CodeExample]:
        """Extract all examples from a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
                self.source_lines = source_code.splitlines()
            
            self.current_file = file_path
            self.current_module = self._get_module_name(file_path)
            
            # Parse AST
            tree = ast.parse(source_code)
            
            # Extract imports first
            self.imports = self._extract_imports(tree)
            
            # Extract examples
            extractor = ExampleASTVisitor(self)
            extractor.visit(tree)
            
            return extractor.examples
            
        except Exception as e:
            logger.error(f"Failed to extract examples from {file_path}: {e}")
            return []
    
    def _get_module_name(self, file_path: str) -> str:
        """Get module name from file path."""
        path = Path(file_path)
        if path.name == "__init__.py":
            return path.parent.name
        return path.stem
    
    def _extract_imports(self, tree: ast.AST) -> Dict[str, str]:
        """Extract import statements and their aliases."""
        imports = {}
        
        class ImportVisitor(ast.NodeVisitor):
            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = alias.name
            
            def visit_ImportFrom(self, node):
                if node.module:
                    for alias in node.names:
                        name = alias.asname if alias.asname else alias.name
                        imports[name] = f"{node.module}.{alias.name}"
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        return imports
    
    def get_context_lines(self, line_number: int) -> Tuple[List[str], List[str]]:
        """Get context lines before and after the given line."""
        start_idx = max(0, line_number - self.context_window - 1)
        end_idx = min(len(self.source_lines), line_number + self.context_window)
        
        before_lines = self.source_lines[start_idx:line_number-1] if line_number > 1 else []
        after_lines = self.source_lines[line_number:end_idx] if line_number < len(self.source_lines) else []
        
        return before_lines, after_lines

class ExampleASTVisitor(ast.NodeVisitor):
    """AST visitor that extracts code examples."""
    
    def __init__(self, extractor: ExampleExtractor):
        self.extractor = extractor
        self.examples = []
        self.current_function = None
        self.current_class = None
        self.in_try_block = False
        self.in_with_block = False
    
    def visit_FunctionDef(self, node):
        """Visit function definitions to find usage examples within."""
        old_function = self.current_function
        self.current_function = node.name
        
        # Extract function call examples from the body
        self._extract_function_calls_from_body(node.body)
        
        # Look for decorator usage examples
        if node.decorator_list:
            self._extract_decorator_examples(node, node.decorator_list)
        
        # Check for async function patterns
        if isinstance(node, ast.AsyncFunctionDef):
            self._extract_async_patterns(node)
        
        self.generic_visit(node)
        self.current_function = old_function
    
    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions."""
        self.visit_FunctionDef(node)  # Reuse function logic
    
    def visit_ClassDef(self, node):
        """Visit class definitions to find instantiation patterns."""
        old_class = self.current_class
        self.current_class = node.name
        
        # Look for __init__ method examples
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "__init__":
                self._extract_init_examples(child)
        
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Call(self, node):
        """Visit function/method calls to extract usage examples."""
        try:
            # Extract function call example
            example = self._create_call_example(node)
            if example:
                self.examples.append(example)
            
            # Check for method chaining
            if self._is_method_chain(node):
                chain_example = self._extract_method_chain(node)
                if chain_example:
                    self.examples.append(chain_example)
        
        except Exception as e:
            logger.debug(f"Failed to extract call example: {e}")
        
        self.generic_visit(node)
    
    def visit_With(self, node):
        """Visit with statements to extract context manager examples."""
        old_with = self.in_with_block
        self.in_with_block = True
        
        try:
            example = self._extract_context_manager_example(node)
            if example:
                self.examples.append(example)
        except Exception as e:
            logger.debug(f"Failed to extract context manager example: {e}")
        
        self.generic_visit(node)
        self.in_with_block = old_with
    
    def visit_Try(self, node):
        """Visit try blocks to extract error handling examples."""
        old_try = self.in_try_block
        self.in_try_block = True
        
        try:
            examples = self._extract_error_handling_examples(node)
            self.examples.extend(examples)
        except Exception as e:
            logger.debug(f"Failed to extract error handling examples: {e}")
        
        self.generic_visit(node)
        self.in_try_block = old_try
    
    def visit_ListComp(self, node):
        """Visit list comprehensions."""
        self._extract_comprehension_example(node, "list")
        self.generic_visit(node)
    
    def visit_DictComp(self, node):
        """Visit dict comprehensions."""
        self._extract_comprehension_example(node, "dict")
        self.generic_visit(node)
    
    def visit_SetComp(self, node):
        """Visit set comprehensions."""
        self._extract_comprehension_example(node, "set")
        self.generic_visit(node)
    
    def _create_call_example(self, node: ast.Call) -> Optional[CodeExample]:
        """Create a function call example from AST node."""
        # Get function name
        func_name = self._get_function_name(node)
        if not func_name:
            return None
        
        # Skip built-in functions and simple calls
        if func_name in ['print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set']:
            return None
        
        # Get the actual code snippet
        code_snippet = self._node_to_code(node)
        if not code_snippet or len(code_snippet) > 200:  # Skip very long calls
            return None
        
        # Get context
        before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
        
        # Extract parameters
        parameters = self._extract_call_parameters(node)
        
        # Determine example type
        example_type = ExampleType.FUNCTION_CALL
        if self._is_class_instantiation(node, func_name):
            example_type = ExampleType.CLASS_INSTANTIATION
        
        # Calculate quality
        quality = self._assess_example_quality(code_snippet, before_lines, after_lines, parameters)
        
        return CodeExample(
            example_type=example_type,
            symbol_name=func_name,
            code_snippet=code_snippet,
            file_path=self.extractor.current_file,
            line_number=node.lineno,
            context_before=before_lines,
            context_after=after_lines,
            quality=quality,
            parameters=parameters,
            imports_required=self._get_required_imports(func_name)
        )
    
    def _get_function_name(self, node: ast.Call) -> Optional[str]:
        """Extract function name from call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            # Handle method calls like obj.method()
            if isinstance(node.func.value, ast.Name):
                return f"{node.func.value.id}.{node.func.attr}"
            else:
                return node.func.attr
        elif isinstance(node.func, ast.Subscript):
            # Handle calls like Type[str]()
            return self._node_to_code(node.func)
        return None
    
    def _node_to_code(self, node: ast.AST) -> str:
        """Convert AST node back to source code."""
        try:
            import astor
            return astor.to_source(node).strip()
        except ImportError:
            # Fallback to simple reconstruction for common cases
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node)
                if func_name:
                    args = []
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            if isinstance(arg.value, str):
                                args.append(f'"{arg.value}"')
                            else:
                                args.append(str(arg.value))
                        elif isinstance(arg, ast.Name):
                            args.append(arg.id)
                        else:
                            args.append("...")
                    
                    kwargs = []
                    for keyword in node.keywords:
                        if isinstance(keyword.value, ast.Constant):
                            if isinstance(keyword.value.value, str):
                                kwargs.append(f'{keyword.arg}="{keyword.value.value}"')
                            else:
                                kwargs.append(f'{keyword.arg}={keyword.value.value}')
                        else:
                            kwargs.append(f'{keyword.arg}=...')
                    
                    all_args = args + kwargs
                    return f"{func_name}({', '.join(all_args)})"
            return "..."
    
    def _extract_call_parameters(self, node: ast.Call) -> Dict[str, Any]:
        """Extract parameter information from a function call."""
        parameters = {}
        
        # Positional arguments
        for i, arg in enumerate(node.args):
            if isinstance(arg, ast.Constant):
                parameters[f"arg_{i}"] = {
                    "value": arg.value,
                    "type": type(arg.value).__name__
                }
            elif isinstance(arg, ast.Name):
                parameters[f"arg_{i}"] = {
                    "variable": arg.id,
                    "type": "variable"
                }
        
        # Keyword arguments
        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Constant):
                parameters[keyword.arg] = {
                    "value": keyword.value.value,
                    "type": type(keyword.value.value).__name__
                }
            elif isinstance(keyword.value, ast.Name):
                parameters[keyword.arg] = {
                    "variable": keyword.value.id,
                    "type": "variable"
                }
        
        return parameters
    
    def _is_class_instantiation(self, node: ast.Call, func_name: str) -> bool:
        """Check if this call is a class instantiation."""
        # Simple heuristic: if function name starts with uppercase, likely a class
        if func_name and len(func_name) > 0:
            simple_name = func_name.split('.')[-1]
            return simple_name[0].isupper()
        return False
    
    def _assess_example_quality(self, code_snippet: str, before_lines: List[str], 
                               after_lines: List[str], parameters: Dict[str, Any]) -> ExampleQuality:
        """Assess the quality of an extracted example."""
        score = 0
        
        # Check code snippet quality
        if len(code_snippet) > 10:
            score += 1
        if '...' not in code_snippet:
            score += 1
        if len(parameters) > 0:
            score += 1
        
        # Check context quality
        if len(before_lines) > 0:
            score += 1
        if len(after_lines) > 0:
            score += 1
        
        # Check for comments or docstrings in context
        all_context = before_lines + after_lines
        for line in all_context:
            if '"""' in line or "'''" in line or line.strip().startswith('#'):
                score += 1
                break
        
        # Map score to quality
        if score >= 5:
            return ExampleQuality.EXCELLENT
        elif score >= 3:
            return ExampleQuality.GOOD
        elif score >= 1:
            return ExampleQuality.FAIR
        else:
            return ExampleQuality.POOR
    
    def _get_required_imports(self, func_name: str) -> List[str]:
        """Get required imports for a function name."""
        required = []
        
        # Check if function is from an imported module
        base_name = func_name.split('.')[0]
        if base_name in self.extractor.imports:
            required.append(f"import {self.extractor.imports[base_name]}")
        
        return required
    
    def _is_method_chain(self, node: ast.Call) -> bool:
        """Check if this call is part of a method chain."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Call):
                return True
            if isinstance(node.func.value, ast.Attribute):
                return True
        return False
    
    def _extract_method_chain(self, node: ast.Call) -> Optional[CodeExample]:
        """Extract method chaining example."""
        chain_code = self._node_to_code(node)
        if not chain_code or '.' not in chain_code:
            return None
        
        # Count the number of chained calls
        chain_count = chain_code.count('.') 
        if chain_count < 2:  # Need at least 2 chained calls
            return None
        
        before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
        
        return CodeExample(
            example_type=ExampleType.METHOD_CHAIN,
            symbol_name=self._get_function_name(node) or "method_chain",
            code_snippet=chain_code,
            file_path=self.extractor.current_file,
            line_number=node.lineno,
            context_before=before_lines,
            context_after=after_lines,
            quality=ExampleQuality.GOOD if chain_count >= 3 else ExampleQuality.FAIR,
            parameters={"chain_length": chain_count}
        )
    
    def _extract_context_manager_example(self, node: ast.With) -> Optional[CodeExample]:
        """Extract context manager usage example."""
        if not node.items:
            return None
        
        # Get the context manager expression
        context_item = node.items[0]
        context_code = self._node_to_code(context_item.context_expr)
        
        # Get the full with statement
        before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
        
        # Try to reconstruct the with statement
        with_code = f"with {context_code}"
        if context_item.optional_vars:
            var_name = self._node_to_code(context_item.optional_vars)
            with_code += f" as {var_name}"
        with_code += ":"
        
        return CodeExample(
            example_type=ExampleType.CONTEXT_MANAGER,
            symbol_name=context_code.split('(')[0],  # Get the context manager name
            code_snippet=with_code,
            file_path=self.extractor.current_file,
            line_number=node.lineno,
            context_before=before_lines,
            context_after=after_lines,
            quality=ExampleQuality.GOOD
        )
    
    def _extract_error_handling_examples(self, node: ast.Try) -> List[CodeExample]:
        """Extract error handling patterns from try blocks."""
        examples = []
        
        for handler in node.handlers:
            if handler.type:
                exception_name = self._node_to_code(handler.type)
                
                # Get the try/except block context
                before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
                
                # Create simplified example
                try_code = "try:\n    # ... operation that might fail\nexcept"
                if exception_name:
                    try_code += f" {exception_name}"
                if handler.name:
                    try_code += f" as {handler.name}"
                try_code += ":\n    # ... error handling"
                
                example = CodeExample(
                    example_type=ExampleType.ERROR_HANDLING,
                    symbol_name=exception_name or "Exception",
                    code_snippet=try_code,
                    file_path=self.extractor.current_file,
                    line_number=node.lineno,
                    context_before=before_lines,
                    context_after=after_lines,
                    quality=ExampleQuality.FAIR,
                    error_handling=exception_name
                )
                examples.append(example)
        
        return examples
    
    def _extract_decorator_examples(self, node: ast.FunctionDef, decorators: List[ast.expr]) -> None:
        """Extract decorator usage examples."""
        for decorator in decorators:
            decorator_code = self._node_to_code(decorator)
            if decorator_code and decorator_code != '...':
                before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
                
                example = CodeExample(
                    example_type=ExampleType.DECORATOR_USAGE,
                    symbol_name=decorator_code,
                    code_snippet=f"@{decorator_code}\ndef {node.name}(...):",
                    file_path=self.extractor.current_file,
                    line_number=decorator.lineno if hasattr(decorator, 'lineno') else node.lineno,
                    context_before=before_lines,
                    context_after=after_lines,
                    quality=ExampleQuality.GOOD
                )
                self.examples.append(example)
    
    def _extract_async_patterns(self, node: ast.AsyncFunctionDef) -> None:
        """Extract async/await usage patterns."""
        # Look for await expressions in the function body
        class AwaitVisitor(ast.NodeVisitor):
            def __init__(self, parent_visitor):
                self.parent = parent_visitor
                self.awaits = []
            
            def visit_Await(self, node):
                await_code = self.parent._node_to_code(node)
                if await_code and await_code != '...':
                    self.awaits.append({
                        'code': await_code,
                        'line': node.lineno if hasattr(node, 'lineno') else 0
                    })
                self.generic_visit(node)
        
        await_visitor = AwaitVisitor(self)
        await_visitor.visit(node)
        
        for await_info in await_visitor.awaits:
            before_lines, after_lines = self.extractor.get_context_lines(await_info['line'])
            
            example = CodeExample(
                example_type=ExampleType.ASYNC_USAGE,
                symbol_name=node.name,
                code_snippet=f"async def {node.name}(...):\n    result = {await_info['code']}",
                file_path=self.extractor.current_file,
                line_number=await_info['line'],
                context_before=before_lines,
                context_after=after_lines,
                quality=ExampleQuality.GOOD
            )
            self.examples.append(example)
    
    def _extract_comprehension_example(self, node: ast.AST, comp_type: str) -> None:
        """Extract comprehension examples."""
        comp_code = self._node_to_code(node)
        if comp_code and comp_code != '...' and len(comp_code) < 150:
            before_lines, after_lines = self.extractor.get_context_lines(node.lineno)
            
            example = CodeExample(
                example_type=ExampleType.COMPREHENSION,
                symbol_name=f"{comp_type}_comprehension",
                code_snippet=comp_code,
                file_path=self.extractor.current_file,
                line_number=node.lineno,
                context_before=before_lines,
                context_after=after_lines,
                quality=ExampleQuality.FAIR
            )
            self.examples.append(example)
    
    def _extract_function_calls_from_body(self, body: List[ast.stmt]) -> None:
        """Extract function calls from function body with better context."""
        for stmt in body:
            if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
                # This is a standalone function call
                call_example = self._create_call_example(stmt.value)
                if call_example:
                    # Mark as having good context since it's in a function
                    if call_example.quality == ExampleQuality.FAIR:
                        call_example.quality = ExampleQuality.GOOD
                    self.examples.append(call_example)
    
    def _extract_init_examples(self, init_node: ast.FunctionDef) -> None:
        """Extract class initialization examples from __init__ method."""
        # Look for assignment patterns in __init__
        for stmt in init_node.body:
            if isinstance(stmt, ast.Assign):
                for target in stmt.targets:
                    if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                        if target.value.id == 'self':
                            # This is a self.attr = value assignment
                            attr_name = target.attr
                            value_code = self._node_to_code(stmt.value)
                            
                            if value_code and value_code != '...':
                                before_lines, after_lines = self.extractor.get_context_lines(stmt.lineno)
                                
                                example = CodeExample(
                                    example_type=ExampleType.CLASS_INSTANTIATION,
                                    symbol_name=self.current_class or "Unknown",
                                    code_snippet=f"self.{attr_name} = {value_code}",
                                    file_path=self.extractor.current_file,
                                    line_number=stmt.lineno,
                                    context_before=before_lines,
                                    context_after=after_lines,
                                    quality=ExampleQuality.FAIR,
                                    parameters={attr_name: {"initialization_pattern": value_code}}
                                )
                                self.examples.append(example)

class PatternAnalyzer:
    """Analyzes extracted examples to find common usage patterns."""
    
    def __init__(self):
        self.symbol_patterns = defaultdict(list)
        self.pattern_frequency = Counter()
    
    def analyze_patterns(self, examples: List[CodeExample]) -> Dict[str, UsagePattern]:
        """Analyze examples to identify common usage patterns."""
        # Group examples by symbol
        symbol_examples = defaultdict(list)
        for example in examples:
            symbol_examples[example.symbol_name].append(example)
        
        patterns = {}
        
        for symbol_name, symbol_exs in symbol_examples.items():
            if len(symbol_exs) < 2:  # Need at least 2 examples to find patterns
                continue
            
            # Analyze patterns for this symbol
            symbol_patterns = self._find_symbol_patterns(symbol_name, symbol_exs)
            patterns.update(symbol_patterns)
        
        return patterns
    
    def _find_symbol_patterns(self, symbol_name: str, examples: List[CodeExample]) -> Dict[str, UsagePattern]:
        """Find patterns for a specific symbol."""
        patterns = {}
        
        # Group by example type
        type_groups = defaultdict(list)
        for example in examples:
            type_groups[example.example_type].append(example)
        
        for example_type, type_examples in type_groups.items():
            if len(type_examples) < 2:
                continue
            
            # Find common parameter patterns
            param_patterns = self._analyze_parameter_patterns(type_examples)
            
            # Calculate frequency and confidence
            frequency = len(type_examples)
            confidence = min(1.0, frequency / 10.0)  # Max confidence at 10+ examples
            
            # Create pattern
            pattern_name = f"{symbol_name}_{example_type.value}_pattern"
            pattern = UsagePattern(
                pattern_name=pattern_name,
                symbol_name=symbol_name,
                pattern_type=example_type,
                examples=type_examples[:5],  # Keep top 5 examples
                frequency=frequency,
                confidence_score=confidence,
                description=self._generate_pattern_description(symbol_name, example_type, type_examples)
            )
            
            patterns[pattern_name] = pattern
        
        return patterns
    
    def _analyze_parameter_patterns(self, examples: List[CodeExample]) -> Dict[str, Any]:
        """Analyze common parameter usage patterns."""
        all_params = []
        for example in examples:
            all_params.extend(example.parameters.keys())
        
        # Find most common parameters
        param_frequency = Counter(all_params)
        return dict(param_frequency.most_common(10))
    
    def _generate_pattern_description(self, symbol_name: str, example_type: ExampleType, 
                                    examples: List[CodeExample]) -> str:
        """Generate a description for a usage pattern."""
        if example_type == ExampleType.FUNCTION_CALL:
            return f"Common usage patterns for calling {symbol_name}() function"
        elif example_type == ExampleType.CLASS_INSTANTIATION:
            return f"Typical instantiation patterns for {symbol_name} class"
        elif example_type == ExampleType.METHOD_CHAIN:
            return f"Method chaining patterns involving {symbol_name}"
        elif example_type == ExampleType.ERROR_HANDLING:
            return f"Error handling patterns for {symbol_name}"
        elif example_type == ExampleType.ASYNC_USAGE:
            return f"Async/await usage patterns for {symbol_name}"
        else:
            return f"Usage patterns for {symbol_name} ({example_type.value})"

class ExampleGenerationService:
    """Main service for generating and managing code examples."""
    
    def __init__(self):
        self.extractor = ExampleExtractor()
        self.pattern_analyzer = PatternAnalyzer()
        self.cross_ref_engine = CrossReferenceEngine()
        self.doc_extractor = AdvancedDocumentationExtractor()
    
    def generate_examples_for_module(self, module_path: str) -> ExampleCollection:
        """Generate examples for a single module."""
        if not os.path.exists(module_path):
            logger.error(f"Module path does not exist: {module_path}")
            return ExampleCollection(
                symbol_name=Path(module_path).stem,
                symbol_type="module",
                module_path=module_path
            )
        
        # Extract examples from the file
        examples = self.extractor.extract_examples_from_file(module_path)
        
        # Analyze patterns
        patterns = self.pattern_analyzer.analyze_patterns(examples)
        
        # Calculate metrics
        total_usage = len(examples)
        complexity_score = self._calculate_complexity_score(examples)
        
        return ExampleCollection(
            symbol_name=Path(module_path).stem,
            symbol_type="module", 
            module_path=module_path,
            examples=examples,
            usage_patterns=list(patterns.values()),
            total_usage_count=total_usage,
            complexity_score=complexity_score
        )
    
    def generate_examples_for_project(self, project_path: str, 
                                    file_patterns: List[str] = None) -> Dict[str, ExampleCollection]:
        """Generate examples for an entire project."""
        if file_patterns is None:
            file_patterns = ["**/*.py"]
        
        project_root = Path(project_path)
        python_files = []
        
        for pattern in file_patterns:
            python_files.extend(project_root.glob(pattern))
        
        # Filter out __pycache__ and other non-source files
        python_files = [
            f for f in python_files 
            if "__pycache__" not in str(f) and not f.name.startswith(".")
        ]
        
        collections = {}
        
        for py_file in python_files:
            try:
                collection = self.generate_examples_for_module(str(py_file))
                if collection.examples:  # Only include modules with examples
                    collections[str(py_file)] = collection
            except Exception as e:
                logger.error(f"Failed to process {py_file}: {e}")
                continue
        
        return collections
    
    def get_examples_for_symbol(self, symbol_name: str, 
                               collections: Dict[str, ExampleCollection]) -> List[CodeExample]:
        """Get all examples for a specific symbol across collections."""
        symbol_examples = []
        
        for collection in collections.values():
            for example in collection.examples:
                if example.symbol_name == symbol_name or symbol_name in example.symbol_name:
                    symbol_examples.append(example)
        
        # Sort by quality and frequency
        symbol_examples.sort(
            key=lambda x: (x.quality.value, x.usage_frequency), 
            reverse=True
        )
        
        return symbol_examples
    
    def get_best_examples(self, collections: Dict[str, ExampleCollection], 
                         limit: int = 10) -> List[CodeExample]:
        """Get the best examples across all collections."""
        all_examples = []
        
        for collection in collections.values():
            all_examples.extend(collection.examples)
        
        # Filter and sort by quality
        quality_order = {
            ExampleQuality.EXCELLENT: 4,
            ExampleQuality.GOOD: 3,
            ExampleQuality.FAIR: 2,
            ExampleQuality.POOR: 1
        }
        
        all_examples.sort(
            key=lambda x: (
                quality_order.get(x.quality, 0),
                len(x.code_snippet),
                x.usage_frequency
            ),
            reverse=True
        )
        
        return all_examples[:limit]
    
    def _calculate_complexity_score(self, examples: List[CodeExample]) -> float:
        """Calculate complexity score based on examples."""
        if not examples:
            return 0.0
        
        total_score = 0.0
        for example in examples:
            # Base score from code length
            code_score = min(1.0, len(example.code_snippet) / 100.0)
            
            # Bonus for parameters
            param_score = min(0.5, len(example.parameters) / 10.0)
            
            # Bonus for context
            context_score = 0.0
            if example.context_before:
                context_score += 0.1
            if example.context_after:
                context_score += 0.1
            
            # Quality multiplier
            quality_multiplier = {
                ExampleQuality.EXCELLENT: 1.0,
                ExampleQuality.GOOD: 0.8,
                ExampleQuality.FAIR: 0.6,
                ExampleQuality.POOR: 0.3
            }.get(example.quality, 0.5)
            
            example_score = (code_score + param_score + context_score) * quality_multiplier
            total_score += example_score
        
        return total_score / len(examples)
    
    def export_examples_to_json(self, collections: Dict[str, ExampleCollection], 
                               output_path: str) -> None:
        """Export examples to JSON format."""
        export_data = {}
        
        for file_path, collection in collections.items():
            export_data[file_path] = {
                "symbol_name": collection.symbol_name,
                "symbol_type": collection.symbol_type,
                "module_path": collection.module_path,
                "total_usage_count": collection.total_usage_count,
                "complexity_score": collection.complexity_score,
                "examples": [],
                "usage_patterns": []
            }
            
            # Export examples
            for example in collection.examples:
                export_data[file_path]["examples"].append({
                    "example_type": example.example_type.value,
                    "symbol_name": example.symbol_name,
                    "code_snippet": example.code_snippet,
                    "file_path": example.file_path,
                    "line_number": example.line_number,
                    "quality": example.quality.value,
                    "parameters": example.parameters,
                    "imports_required": example.imports_required
                })
            
            # Export patterns
            for pattern in collection.usage_patterns:
                export_data[file_path]["usage_patterns"].append({
                    "pattern_name": pattern.pattern_name,
                    "symbol_name": pattern.symbol_name,
                    "pattern_type": pattern.pattern_type.value,
                    "frequency": pattern.frequency,
                    "confidence_score": pattern.confidence_score,
                    "description": pattern.description
                })
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Example usage and testing
    service = ExampleGenerationService()
    
    # Test with current file
    current_file = __file__
    collection = service.generate_examples_for_module(current_file)
    
    print(f"Found {len(collection.examples)} examples in {current_file}")
    print(f"Complexity score: {collection.complexity_score:.2f}")
    
    # Show best examples
    best_examples = [ex for ex in collection.examples if ex.quality in [ExampleQuality.EXCELLENT, ExampleQuality.GOOD]]
    for example in best_examples[:3]:
        print(f"\n{example.example_type.value}: {example.symbol_name}")
        print(f"Code: {example.code_snippet}")
        print(f"Quality: {example.quality.value}")