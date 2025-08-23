#!/usr/bin/env python3
"""
Test Driven Development (TDD) test suite for advanced documentation service.

Comprehensive tests for the advanced documentation extraction system including:
- Pydantic model validation
- Type extraction functionality
- Docstring parsing across multiple styles
- AST analysis capabilities
- Complete module documentation extraction

No mocks, no stubs, no placeholders - tests real functionality only.
"""

import ast
import inspect
import os
import sys
import tempfile
import unittest
from typing import Dict, List, Optional, Union, Any
from pathlib import Path

# Add project root to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ltms.services.advanced_documentation_service import (
    AdvancedDocumentationExtractor,
    TypeExtractor,
    DocstringParser,
    ASTAnalyzer,
    ModuleDocumentation,
    FunctionDocumentation,
    ClassDocumentation,
    ParameterInfo,
    ReturnInfo,
    ExceptionInfo,
    ExampleInfo,
    ComplexityMetrics,
    SourceLocation,
    AttributeInfo
)
from pydantic import ValidationError


class TestPydanticModels(unittest.TestCase):
    """Test Pydantic model validation and schema generation."""
    
    def test_parameter_info_validation(self):
        """Test ParameterInfo model validation with various parameter types."""
        # Valid parameter
        param = ParameterInfo(
            name="test_param",
            type_hint="str",
            default_value=None,
            description="Test parameter description",
            is_required=True,
            kind="POSITIONAL_OR_KEYWORD"
        )
        
        self.assertEqual(param.name, "test_param")
        self.assertEqual(param.type_hint, "str")
        self.assertTrue(param.is_required)
        
        # Parameter with constraints
        param_with_constraints = ParameterInfo(
            name="constrained_param",
            type_hint="int",
            constraints={"min_value": 0, "max_value": 100},
            kind="POSITIONAL_OR_KEYWORD"
        )
        
        self.assertEqual(param_with_constraints.constraints["min_value"], 0)
        
        # Invalid parameter (missing required fields)
        with self.assertRaises(ValidationError):
            ParameterInfo(name="invalid")  # Missing kind field
    
    def test_function_documentation_validation(self):
        """Test FunctionDocumentation model with comprehensive data."""
        func_doc = FunctionDocumentation(
            name="test_function",
            module_path="test_module",
            signature="test_function(param1: str, param2: int = 42) -> Dict[str, Any]",
            docstring_raw="Test function docstring",
            short_description="Brief description",
            parameters=[
                ParameterInfo(
                    name="param1",
                    type_hint="str",
                    is_required=True,
                    kind="POSITIONAL_OR_KEYWORD"
                ),
                ParameterInfo(
                    name="param2", 
                    type_hint="int",
                    default_value="42",
                    is_required=False,
                    kind="POSITIONAL_OR_KEYWORD"
                )
            ],
            return_info=ReturnInfo(
                type_hint="Dict[str, Any]",
                description="Returns a dictionary with results"
            ),
            exceptions=[
                ExceptionInfo(
                    exception_type="ValueError",
                    description="Raised when invalid parameters are provided"
                )
            ],
            examples=[
                ExampleInfo(
                    code='test_function("hello", 123)',
                    description="Basic usage example"
                )
            ],
            is_async=False
        )
        
        self.assertEqual(func_doc.name, "test_function")
        self.assertEqual(len(func_doc.parameters), 2)
        self.assertEqual(len(func_doc.exceptions), 1)
        self.assertEqual(len(func_doc.examples), 1)
        self.assertFalse(func_doc.is_async)
    
    def test_module_documentation_validation(self):
        """Test ModuleDocumentation model with complete module data."""
        module_doc = ModuleDocumentation(
            name="test_module",
            file_path="/path/to/test_module.py",
            source_location=SourceLocation(
                file_path="/path/to/test_module.py",
                line_start=1,
                line_end=100
            ),
            functions=[
                FunctionDocumentation(
                    name="func1",
                    module_path="test_module",
                    signature="func1() -> None"
                )
            ],
            classes=[
                ClassDocumentation(
                    name="TestClass",
                    module_path="test_module"
                )
            ],
            extraction_metadata={
                "extraction_timestamp": "2025-01-01T00:00:00Z",
                "extractor_version": "1.0.0"
            }
        )
        
        self.assertEqual(module_doc.name, "test_module")
        self.assertEqual(len(module_doc.functions), 1)
        self.assertEqual(len(module_doc.classes), 1)
        self.assertIn("extraction_timestamp", module_doc.extraction_metadata)


class TestTypeExtractor(unittest.TestCase):
    """Test type extraction functionality with real functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.type_extractor = TypeExtractor()
    
    def test_simple_function_extraction(self):
        """Test extraction of simple function with basic types."""
        def simple_function(name: str, count: int = 10) -> str:
            """A simple test function.
            
            Args:
                name: Name parameter
                count: Count parameter with default
                
            Returns:
                Formatted string result
            """
            return f"{name}: {count}"
        
        func_doc = self.type_extractor.extract_function_signature(simple_function)
        
        self.assertEqual(func_doc.name, "simple_function")
        self.assertEqual(len(func_doc.parameters), 2)
        
        # Check first parameter
        param1 = func_doc.parameters[0]
        self.assertEqual(param1.name, "name")
        self.assertEqual(param1.type_hint, "str")
        self.assertTrue(param1.is_required)
        
        # Check second parameter
        param2 = func_doc.parameters[1]
        self.assertEqual(param2.name, "count")
        self.assertEqual(param2.type_hint, "int")
        self.assertFalse(param2.is_required)
        
        # Check return type
        self.assertIsNotNone(func_doc.return_info)
        self.assertEqual(func_doc.return_info.type_hint, "str")
    
    def test_complex_types_extraction(self):
        """Test extraction of complex generic types."""
        def complex_function(
            items: List[Dict[str, Any]], 
            mapping: Optional[Dict[str, Union[str, int]]] = None
        ) -> Union[List[str], None]:
            """Function with complex type hints."""
            return None
        
        func_doc = self.type_extractor.extract_function_signature(complex_function)
        
        self.assertEqual(func_doc.name, "complex_function")
        
        # Check complex type formatting
        param1 = func_doc.parameters[0]
        self.assertEqual(param1.name, "items")
        self.assertIn("List", param1.type_hint)
        self.assertIn("Dict", param1.type_hint)
        
        param2 = func_doc.parameters[1]
        self.assertEqual(param2.name, "mapping")
        self.assertIn("Optional", param2.type_hint or "")
        
        # Check return type
        return_type = func_doc.return_info.type_hint if func_doc.return_info else None
        self.assertIn("Union", return_type or "")
    
    def test_async_function_extraction(self):
        """Test extraction of async functions."""
        async def async_function(param: str) -> None:
            """An async test function."""
            pass
        
        func_doc = self.type_extractor.extract_function_signature(async_function)
        
        self.assertEqual(func_doc.name, "async_function")
        self.assertTrue(func_doc.is_async)
    
    def test_function_without_type_hints(self):
        """Test extraction of functions without type hints."""
        def no_hints_function(param1, param2=None):
            """Function without type hints."""
            return param1
        
        func_doc = self.type_extractor.extract_function_signature(no_hints_function)
        
        self.assertEqual(func_doc.name, "no_hints_function")
        self.assertEqual(len(func_doc.parameters), 2)
        
        # Parameters should have None type hints
        param1 = func_doc.parameters[0]
        self.assertEqual(param1.name, "param1")
        self.assertIsNone(param1.type_hint)
        
        param2 = func_doc.parameters[1]
        self.assertEqual(param2.name, "param2")
        self.assertIsNone(param2.type_hint)


class TestDocstringParser(unittest.TestCase):
    """Test docstring parsing for different styles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.docstring_parser = DocstringParser()
    
    def test_google_style_docstring(self):
        """Test parsing of Google-style docstrings."""
        google_docstring = '''
        Function with Google-style docstring.
        
        This function demonstrates Google-style docstring parsing
        with comprehensive parameter and return documentation.
        
        Args:
            param1 (str): First parameter description
            param2 (int, optional): Second parameter. Defaults to 42.
            param3 (List[str]): List of string values
            
        Returns:
            Dict[str, Any]: Dictionary with processing results containing:
                - success (bool): Operation success status
                - data (List): Processed data items
                - count (int): Number of items processed
                
        Raises:
            ValueError: When param1 is empty
            TypeError: When param3 is not a list
            
        Examples:
            >>> result = test_function("test", 100, ["a", "b"])
            >>> print(result["success"])
            True
            
            >>> result = test_function("", 0, [])
            Traceback (most recent call last):
                ...
            ValueError: param1 cannot be empty
            
        Note:
            This function requires all parameters to be properly formatted.
            Performance is O(n) where n is the length of param3.
        '''
        
        parsed = self.docstring_parser.parse_docstring(google_docstring)
        
        # Check basic parsing
        self.assertIsNotNone(parsed['short_description'])
        self.assertIn("Google-style", parsed['short_description'])
        
        # Check parameters
        self.assertEqual(len(parsed['parameters']), 3)
        param1 = next(p for p in parsed['parameters'] if p['name'] == 'param1')
        self.assertEqual(param1['type_hint'], 'str')
        self.assertIn("First parameter", param1['description'])
        
        # Check returns
        self.assertIsNotNone(parsed['returns'])
        self.assertIn("Dictionary", parsed['returns']['description'])
        
        # Check exceptions
        self.assertEqual(len(parsed['exceptions']), 2)
        value_error = next(e for e in parsed['exceptions'] if e['exception_type'] == 'ValueError')
        self.assertIn("empty", value_error['description'])
        
        # Check examples
        self.assertGreaterEqual(len(parsed['examples']), 1)
        
        # Check style detection
        self.assertEqual(parsed['style'], 'google')
    
    def test_numpy_style_docstring(self):
        """Test parsing of Numpy-style docstrings."""
        numpy_docstring = '''
        Function with Numpy-style docstring.
        
        Longer description of the function that explains
        what it does in more detail.
        
        Parameters
        ----------
        param1 : str
            Description of the first parameter
        param2 : int, optional
            Description of the second parameter (default is 42)
        param3 : list of str
            Description of the third parameter
        
        Returns
        -------
        dict
            Dictionary containing results with the following keys:
            - success : bool
            - data : list
            - count : int
        
        Raises
        ------
        ValueError
            If param1 is invalid
        TypeError
            If param3 is not a list
        '''
        
        parsed = self.docstring_parser.parse_docstring(numpy_docstring)
        
        # Should detect numpy style
        self.assertEqual(parsed.get('style'), 'numpy')
        
        # Should parse parameters
        self.assertGreater(len(parsed.get('parameters', [])), 0)
    
    def test_sphinx_style_docstring(self):
        """Test parsing of Sphinx-style docstrings."""
        sphinx_docstring = '''
        Function with Sphinx-style docstring.
        
        Detailed description of what the function does
        and how it should be used.
        
        :param param1: Description of first parameter
        :type param1: str
        :param param2: Description of second parameter
        :type param2: int
        :param param3: Description of third parameter
        :type param3: list
        :return: Description of return value
        :rtype: dict
        :raises ValueError: When param1 is invalid
        :raises TypeError: When types are wrong
        '''
        
        parsed = self.docstring_parser.parse_docstring(sphinx_docstring)
        
        # Should detect sphinx style
        self.assertEqual(parsed.get('style'), 'sphinx')
    
    def test_malformed_docstring(self):
        """Test handling of malformed or empty docstrings."""
        # Empty docstring
        empty_parsed = self.docstring_parser.parse_docstring("")
        self.assertEqual(empty_parsed, {})
        
        # None docstring
        none_parsed = self.docstring_parser.parse_docstring(None)
        self.assertEqual(none_parsed, {})
        
        # Malformed docstring
        malformed = "This is just text without proper structure"
        malformed_parsed = self.docstring_parser.parse_docstring(malformed)
        self.assertIn('short_description', malformed_parsed)
        self.assertEqual(malformed_parsed['short_description'], malformed)


class TestASTAnalyzer(unittest.TestCase):
    """Test AST analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ast_analyzer = ASTAnalyzer()
    
    def test_function_analysis(self):
        """Test AST analysis of functions."""
        source_code = '''
def simple_function(param1, param2=None):
    """Simple function for testing."""
    if param1:
        return param1 * 2
    else:
        return param2

@decorator
def decorated_function():
    """Function with decorator."""
    pass

async def async_function():
    """Async function."""
    return True
        '''
        
        analysis = self.ast_analyzer.analyze_module(source_code, "test.py")
        
        # Should find 3 functions
        self.assertEqual(len(analysis['functions']), 3)
        
        # Check simple function
        simple_func = next(f for f in analysis['functions'] if f['name'] == 'simple_function')
        self.assertEqual(simple_func['name'], 'simple_function')
        self.assertEqual(len(simple_func['args']), 2)
        self.assertGreater(simple_func['complexity'], 1)  # Has if statement
        
        # Check decorated function
        decorated_func = next(f for f in analysis['functions'] if f['name'] == 'decorated_function')
        self.assertEqual(len(decorated_func['decorators']), 1)
        self.assertEqual(decorated_func['decorators'][0], 'decorator')
        
        # Check async function
        async_func = next(f for f in analysis['functions'] if f['name'] == 'async_function')
        self.assertTrue(async_func['is_async'])
    
    def test_class_analysis(self):
        """Test AST analysis of classes."""
        source_code = '''
class SimpleClass:
    """Simple class for testing."""
    
    def method1(self):
        """Method 1."""
        pass

@dataclass
class DataClassExample:
    """Example dataclass."""
    name: str
    age: int = 25

class InheritedClass(SimpleClass, dict):
    """Class with inheritance."""
    
    def method2(self):
        """Method 2."""
        return super().method1()
        '''
        
        analysis = self.ast_analyzer.analyze_module(source_code, "test.py")
        
        # Should find 3 classes
        self.assertEqual(len(analysis['classes']), 3)
        
        # Check simple class
        simple_class = next(c for c in analysis['classes'] if c['name'] == 'SimpleClass')
        self.assertEqual(simple_class['name'], 'SimpleClass')
        self.assertEqual(len(simple_class['bases']), 0)
        
        # Check dataclass
        dataclass_example = next(c for c in analysis['classes'] if c['name'] == 'DataClassExample')
        self.assertEqual(len(dataclass_example['decorators']), 1)
        self.assertTrue(dataclass_example['is_dataclass'])
        
        # Check inherited class
        inherited_class = next(c for c in analysis['classes'] if c['name'] == 'InheritedClass')
        self.assertEqual(len(inherited_class['bases']), 2)
        self.assertIn('SimpleClass', inherited_class['bases'])
        self.assertIn('dict', inherited_class['bases'])
    
    def test_complexity_calculation(self):
        """Test cyclomatic complexity calculation."""
        source_code = '''
def complex_function(x, y):
    """Function with high complexity."""
    if x > 0:
        if y > 0:
            return x + y
        else:
            return x - y
    elif x < 0:
        return -x
    else:
        for i in range(10):
            if i % 2 == 0:
                continue
            x += i
        return x
        '''
        
        analysis = self.ast_analyzer.analyze_module(source_code, "test.py")
        
        func = analysis['functions'][0]
        # Should have high complexity due to nested conditions and loops
        self.assertGreater(func['complexity'], 5)
    
    def test_import_analysis(self):
        """Test import statement analysis."""
        source_code = '''
import os
import sys as system
from typing import Dict, List, Optional
from collections.abc import Mapping
        '''
        
        analysis = self.ast_analyzer.analyze_module(source_code, "test.py")
        
        imports = analysis['imports']
        self.assertGreater(len(imports), 0)
        
        # Check different import types
        import_names = [imp['name'] for imp in imports]
        self.assertIn('os', import_names)
        self.assertIn('sys', import_names)
        self.assertIn('Dict', import_names)
        
        # Check alias
        sys_import = next(imp for imp in imports if imp['name'] == 'sys')
        self.assertEqual(sys_import['alias'], 'system')


class TestAdvancedDocumentationExtractor(unittest.TestCase):
    """Test complete module documentation extraction."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = AdvancedDocumentationExtractor()
    
    def test_extract_real_module_documentation(self):
        """Test extraction of documentation from a real Python file."""
        # Create a temporary test module
        test_module_content = '''#!/usr/bin/env python3
"""
Test module for documentation extraction.

This module provides comprehensive testing functionality
for the advanced documentation system.
"""

from typing import List, Dict, Optional, Union, Any
import logging

logger = logging.getLogger(__name__)

# Module constant
VERSION = "1.0.0"
DEBUG_MODE = False

class TestClass:
    """
    A test class for documentation extraction.
    
    This class demonstrates various Python features including
    methods, properties, and class variables.
    
    Attributes:
        class_var: A class variable
    """
    
    class_var = "test"
    
    def __init__(self, name: str):
        """
        Initialize the test class.
        
        Args:
            name: Name of the instance
        """
        self.name = name
    
    @property
    def display_name(self) -> str:
        """Get the display name."""
        return f"Test: {self.name}"
    
    def process_data(self, items: List[Dict[str, Any]], 
                    filter_func: Optional[callable] = None) -> List[Dict[str, Any]]:
        """
        Process a list of data items.
        
        Args:
            items: List of data dictionaries to process
            filter_func: Optional filter function to apply
            
        Returns:
            List[Dict[str, Any]]: Processed data items
            
        Raises:
            ValueError: When items list is empty
            TypeError: When items contains non-dict values
            
        Examples:
            >>> test_obj = TestClass("example")
            >>> result = test_obj.process_data([{"key": "value"}])
            >>> len(result)
            1
        """
        if not items:
            raise ValueError("Items list cannot be empty")
        
        if not all(isinstance(item, dict) for item in items):
            raise TypeError("All items must be dictionaries")
        
        processed = []
        for item in items:
            if filter_func is None or filter_func(item):
                processed.append(item.copy())
        
        return processed

def utility_function(text: str, count: int = 1) -> str:
    """
    Utility function for string processing.
    
    Args:
        text: Input text to process
        count: Number of times to repeat (default: 1)
        
    Returns:
        str: Processed text result
        
    Examples:
        >>> utility_function("hello", 3)
        'hellohellohello'
    """
    return text * count

async def async_utility(delay: float = 1.0) -> bool:
    """
    Async utility function.
    
    Args:
        delay: Delay time in seconds
        
    Returns:
        bool: Always returns True after delay
    """
    import asyncio
    await asyncio.sleep(delay)
    return True
'''
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_module_content)
            temp_path = f.name
        
        try:
            # Extract documentation
            module_doc = self.extractor.extract_module_documentation(temp_path)
            
            # Validate extraction
            self.assertEqual(module_doc.name, os.path.splitext(os.path.basename(temp_path))[0])
            self.assertEqual(module_doc.file_path, temp_path)
            
            # Check module docstring
            self.assertIsNotNone(module_doc.short_description)
            self.assertIn("Test module", module_doc.short_description)
            
            # Check functions
            self.assertGreater(len(module_doc.functions), 0)
            
            # Find specific function
            utility_func = next((f for f in module_doc.functions if f.name == 'utility_function'), None)
            self.assertIsNotNone(utility_func)
            self.assertEqual(len(utility_func.parameters), 2)
            self.assertIsNotNone(utility_func.return_info)
            self.assertGreater(len(utility_func.examples), 0)
            
            # Find async function
            async_func = next((f for f in module_doc.functions if f.name == 'async_utility'), None)
            self.assertIsNotNone(async_func)
            self.assertTrue(async_func.is_async)
            
            # Check classes
            self.assertGreater(len(module_doc.classes), 0)
            test_class = next((c for c in module_doc.classes if c.name == 'TestClass'), None)
            self.assertIsNotNone(test_class)
            self.assertGreater(len(test_class.methods), 0)
            
            # Find specific method
            process_method = next((m for m in test_class.methods if m.name == 'process_data'), None)
            self.assertIsNotNone(process_method)
            self.assertGreater(len(process_method.parameters), 0)
            self.assertGreater(len(process_method.exceptions), 0)
            self.assertGreater(len(process_method.examples), 0)
            
            # Check constants
            self.assertGreater(len(module_doc.constants), 0)
            version_constant = next((c for c in module_doc.constants if c.name == 'VERSION'), None)
            self.assertIsNotNone(version_constant)
            
            # Check extraction metadata
            self.assertIn('extraction_timestamp', module_doc.extraction_metadata)
            self.assertIn('extractor_version', module_doc.extraction_metadata)
            self.assertTrue(module_doc.extraction_metadata.get('ast_parse_successful', False))
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    
    def test_extract_invalid_module(self):
        """Test extraction behavior with invalid module."""
        # Test with non-existent file
        result = self.extractor.extract_module_documentation("/nonexistent/file.py")
        
        self.assertEqual(result.name, "file")
        self.assertIn('extraction_error', result.extraction_metadata)
    
    def test_parallel_extraction(self):
        """Test parallel extraction of multiple modules."""
        # Create multiple temporary test modules
        temp_files = []
        
        for i in range(3):
            content = f'''
"""Test module {i}."""

def test_function_{i}():
    """Test function {i}."""
    return {i}
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(content)
                temp_files.append(f.name)
        
        try:
            # Extract documentation in parallel
            results = self.extractor.extract_project_documentation(temp_files, max_workers=2)
            
            self.assertEqual(len(results), 3)
            
            # Check that all modules were processed
            for i, result in enumerate(results):
                self.assertGreater(len(result.functions), 0)
                self.assertIn('extraction_timestamp', result.extraction_metadata)
                
        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                os.unlink(temp_file)


class TestIntegrationWithRealCode(unittest.TestCase):
    """Integration tests with real LTMC code."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = AdvancedDocumentationExtractor()
    
    def test_extract_consolidated_tools(self):
        """Test extraction of ltms/tools/consolidated.py."""
        consolidated_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "ltms", 
            "tools", 
            "consolidated.py"
        )
        
        if os.path.exists(consolidated_path):
            # Extract documentation
            module_doc = self.extractor.extract_module_documentation(consolidated_path)
            
            # Should find action functions
            action_functions = [
                f for f in module_doc.functions 
                if f.name.endswith('_action')
            ]
            
            self.assertGreater(len(action_functions), 0)
            
            # Check that functions have proper documentation
            for func in action_functions:
                self.assertIsNotNone(func.docstring_raw)
                self.assertGreater(len(func.parameters), 0)
                
                # Should have action parameter
                action_param = next((p for p in func.parameters if p.name == 'action'), None)
                self.assertIsNotNone(action_param)
    
    def test_extract_advanced_documentation_service(self):
        """Test self-extraction of the advanced documentation service."""
        service_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "ltms", 
            "services", 
            "advanced_documentation_service.py"
        )
        
        if os.path.exists(service_path):
            # Extract documentation
            module_doc = self.extractor.extract_module_documentation(service_path)
            
            # Should find key classes
            key_classes = [
                'AdvancedDocumentationExtractor',
                'TypeExtractor', 
                'DocstringParser',
                'ASTAnalyzer'
            ]
            
            found_classes = [c.name for c in module_doc.classes]
            for key_class in key_classes:
                self.assertIn(key_class, found_classes)
            
            # Should find Pydantic models
            pydantic_models = [
                'ModuleDocumentation',
                'FunctionDocumentation', 
                'ClassDocumentation'
            ]
            
            for model in pydantic_models:
                self.assertIn(model, found_classes)


if __name__ == '__main__':
    # Configure logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run all tests
    unittest.main(verbosity=2)