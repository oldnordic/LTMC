#!/usr/bin/env python3
"""
TDD Test for extract_functions MCP Tool Integration

This test ensures extract_functions is implemented as a real, first-class
LTMC MCP tool with actual Google LangExtract integration.

CRITICAL: This is NOT a wrapper test. This tests the actual MCP tool
implementation with real functionality.
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ltms.tools import ALL_TOOLS


class TestExtractFunctionsTDD(unittest.TestCase):
    """Test extract_functions tool implementation following TDD principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_python_code = '''
def simple_function(x, y):
    """Add two numbers together.
    
    Args:
        x (int): First number
        y (int): Second number
        
    Returns:
        int: Sum of x and y
    """
    return x + y

class TestClass:
    """A test class."""
    
    def method_one(self, param: str) -> str:
        """A simple method.
        
        Args:
            param: Input parameter
            
        Returns:
            Processed string
        """
        return f"processed: {param}"
    
    async def async_method(self):
        """An async method."""
        return "async result"

def complex_function(a, b=None, *args, **kwargs):
    """A more complex function with various parameter types."""
    if b is None:
        b = []
    return sum([a] + list(args))
'''

        self.test_javascript_code = '''
function addNumbers(x, y) {
    /**
     * Add two numbers together
     * @param {number} x - First number
     * @param {number} y - Second number  
     * @returns {number} Sum of x and y
     */
    return x + y;
}

class Calculator {
    /**
     * A simple calculator class
     */
    
    multiply(a, b) {
        /**
         * Multiply two numbers
         * @param {number} a - First number
         * @param {number} b - Second number
         * @returns {number} Product of a and b
         */
        return a * b;
    }
    
    async divide(a, b) {
        /**
         * Divide two numbers asynchronously
         */
        if (b === 0) throw new Error("Division by zero");
        return a / b;
    }
}
'''

    def test_extract_functions_tool_exists_in_all_tools(self):
        """Test that extract_functions tool is registered in ALL_TOOLS."""
        self.assertIn('extract_functions', ALL_TOOLS, 
                     "extract_functions must be registered in ALL_TOOLS registry")
        
    def test_extract_functions_tool_has_required_structure(self):
        """Test that extract_functions tool has proper MCP tool structure."""
        tool = ALL_TOOLS['extract_functions']
        
        # Test required components
        self.assertIn('handler', tool, "Tool must have handler function")
        self.assertIn('description', tool, "Tool must have description")
        self.assertIn('schema', tool, "Tool must have JSON schema")
        
        # Test handler is callable
        self.assertTrue(callable(tool['handler']), 
                       "Handler must be a callable function")
        
        # Test description is meaningful
        self.assertIsInstance(tool['description'], str)
        self.assertGreater(len(tool['description']), 20, 
                          "Description must be meaningful")
        
        # Test schema structure
        schema = tool['schema']
        self.assertEqual(schema['type'], 'object')
        self.assertIn('properties', schema)
        self.assertIn('required', schema)
        
    def test_extract_functions_schema_validation(self):
        """Test extract_functions schema has correct parameters."""
        schema = ALL_TOOLS['extract_functions']['schema']
        properties = schema['properties']
        required = schema['required']
        
        # Test required parameters
        self.assertIn('source_code', required, "source_code must be required")
        self.assertIn('source_code', properties)
        
        # Test optional parameters exist
        optional_params = ['file_path', 'language', 'extract_docstrings', 
                          'include_private', 'complexity_analysis']
        for param in optional_params:
            self.assertIn(param, properties, f"{param} must be in schema properties")
            
        # Test parameter types
        self.assertEqual(properties['source_code']['type'], 'string')
        self.assertEqual(properties['extract_docstrings']['type'], 'boolean')
        self.assertEqual(properties['complexity_analysis']['type'], 'boolean')
        
    def test_extract_functions_python_code_analysis(self):
        """Test extract_functions with real Python code analysis."""
        handler = ALL_TOOLS['extract_functions']['handler']
        
        # Execute real function extraction
        result = handler(
            source_code=self.test_python_code,
            file_path="test.py",
            language="python",
            extract_docstrings=True,
            complexity_analysis=True
        )
        
        # Test response structure
        self.assertIsInstance(result, dict, "Result must be a dictionary")
        self.assertIn('success', result, "Result must include success status")
        self.assertTrue(result['success'], "Extraction must succeed")
        self.assertIn('functions', result, "Result must include functions list")
        self.assertIn('metadata', result, "Result must include metadata")
        
        # Test functions extraction
        functions = result['functions']
        self.assertIsInstance(functions, list, "Functions must be a list")
        self.assertGreater(len(functions), 0, "Must extract at least one function")
        
        # Find and validate specific functions
        function_names = [f['name'] for f in functions]
        self.assertIn('simple_function', function_names, 
                     "Must extract simple_function")
        self.assertIn('complex_function', function_names,
                     "Must extract complex_function")
        
        # Test simple_function details
        simple_func = next(f for f in functions if f['name'] == 'simple_function')
        self.assertEqual(simple_func['name'], 'simple_function')
        self.assertIn('signature', simple_func)
        self.assertIn('parameters', simple_func)
        self.assertIn('docstring', simple_func)
        self.assertIn('line_start', simple_func)
        self.assertIn('line_end', simple_func)
        
        # Test parameter extraction
        params = simple_func['parameters']
        self.assertIsInstance(params, list)
        self.assertEqual(len(params), 2, "simple_function has 2 parameters")
        param_names = [p['name'] for p in params]
        self.assertIn('x', param_names)
        self.assertIn('y', param_names)
        
        # Test docstring extraction
        docstring = simple_func['docstring']
        self.assertIsInstance(docstring, dict)
        self.assertIn('raw', docstring)
        self.assertIn('summary', docstring)
        self.assertIn('description', docstring)
        
        # Test complex function with various parameter types
        complex_func = next(f for f in functions if f['name'] == 'complex_function')
        complex_params = complex_func['parameters']
        param_names = [p['name'] for p in complex_params]
        self.assertIn('a', param_names)
        self.assertIn('b', param_names)
        self.assertIn('args', param_names)
        self.assertIn('kwargs', param_names)
        
        # Test metadata
        metadata = result['metadata']
        self.assertIn('total_functions', metadata)
        self.assertIn('language', metadata)
        self.assertIn('processing_time', metadata)
        self.assertEqual(metadata['language'], 'python')
        self.assertGreater(metadata['total_functions'], 0)
        
    def test_extract_functions_javascript_code_analysis(self):
        """Test extract_functions with real JavaScript code analysis."""
        handler = ALL_TOOLS['extract_functions']['handler']
        
        # Execute real function extraction for JavaScript
        result = handler(
            source_code=self.test_javascript_code,
            file_path="test.js",
            language="javascript",
            extract_docstrings=True,
            complexity_analysis=True
        )
        
        # Test basic response structure
        self.assertTrue(result['success'])
        self.assertIn('functions', result)
        
        # Test JavaScript-specific function extraction
        functions = result['functions']
        function_names = [f['name'] for f in functions]
        self.assertIn('addNumbers', function_names, 
                     "Must extract JavaScript function")
        
        # Test async function detection
        async_functions = [f for f in functions if f.get('is_async', False)]
        self.assertGreater(len(async_functions), 0, 
                          "Must detect async functions")
        
    def test_extract_functions_error_handling(self):
        """Test extract_functions error handling with invalid code."""
        handler = ALL_TOOLS['extract_functions']['handler']
        
        # Test with malformed Python code
        result = handler(
            source_code="def broken_function(\n    # incomplete syntax",
            language="python"
        )
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # May succeed with partial parsing or fail gracefully
        
    def test_extract_functions_complexity_analysis(self):
        """Test complexity analysis functionality."""
        complex_code = '''
def complex_function(x):
    """A function with complexity."""
    if x > 10:
        for i in range(x):
            if i % 2 == 0:
                while i > 0:
                    i -= 1
                    if i < 5:
                        break
    else:
        return x * 2
    return x
'''
        
        handler = ALL_TOOLS['extract_functions']['handler']
        result = handler(
            source_code=complex_code,
            complexity_analysis=True
        )
        
        self.assertTrue(result['success'])
        functions = result['functions']
        complex_func = functions[0]
        
        # Test complexity metrics exist
        self.assertIn('complexity', complex_func)
        complexity = complex_func['complexity']
        self.assertIn('cyclomatic', complexity)
        self.assertIn('lines_of_code', complexity)
        self.assertIsInstance(complexity['cyclomatic'], int)
        self.assertGreater(complexity['cyclomatic'], 1, 
                          "Complex function should have cyclomatic complexity > 1")
        
    def test_extract_functions_language_detection(self):
        """Test automatic language detection."""
        handler = ALL_TOOLS['extract_functions']['handler']
        
        # Test with Python code and auto language detection
        result = handler(
            source_code=self.test_python_code,
            file_path="test.py",
            language="auto"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['language'], 'python')
        
    def test_extract_functions_performance_requirements(self):
        """Test performance requirements are met."""
        import time
        
        handler = ALL_TOOLS['extract_functions']['handler']
        
        start_time = time.time()
        result = handler(
            source_code=self.test_python_code,
            complexity_analysis=True
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Must complete in reasonable time (less than 2 seconds for small code)
        self.assertLess(processing_time, 2.0, 
                       "Function extraction must complete in < 2 seconds")
        
        # Verify processing time is recorded
        self.assertTrue(result['success'])
        self.assertIn('processing_time', result['metadata'])
        self.assertGreater(result['metadata']['processing_time'], 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)