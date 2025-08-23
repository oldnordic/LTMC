#!/usr/bin/env python3
"""
TDD Test for extract_comments MCP Tool Integration

This test ensures extract_comments is implemented as a real, first-class
LTMC MCP tool with actual AST and regex-based comment/docstring extraction.

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


class TestExtractCommentsTDD(unittest.TestCase):
    """Test extract_comments tool implementation following TDD principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_python_code = '''
#!/usr/bin/env python3
"""
Module-level docstring for the test module.
This explains what the module does.

Authors: Test Team
Date: 2024
"""

import os
# Standard library import
import sys  # System module import

# TODO: Implement better error handling
# FIXME: This needs refactoring

def simple_function():
    """
    A simple function with docstring.
    
    This function demonstrates basic comment extraction.
    
    Returns:
        str: A simple greeting message
    """
    # Inline comment before assignment
    message = "Hello World"  # End-of-line comment
    
    # Multi-line comment explanation:
    # This section shows how we handle
    # multiple consecutive single-line comments
    # that form a logical block
    
    return message

class TestClass:
    """
    Class docstring example.
    
    This class demonstrates various comment styles
    and docstring formats.
    
    Attributes:
        value (int): An example attribute
    """
    
    def __init__(self, value):
        """Initialize the test class.
        
        Args:
            value (int): Initial value for the instance
        """
        self.value = value  # Store the value
        
    def method_with_complex_comments(self):
        """Method with various comment types."""
        # Step 1: Initialize variables
        x = 10  # Base value
        y = 20  # Multiplier
        
        """
        Multi-line string that's not a docstring
        because it's not at the start of the function.
        This should be treated as a comment block.
        """
        
        # Calculate result with detailed explanation:
        # - First we multiply x and y
        # - Then we add a constant offset
        # - Finally we return the computed value
        result = (x * y) + 5
        
        return result  # Return the calculated result

# Module-level comment at the end
# This explains module cleanup or final notes

def function_without_docstring():
    # Just a comment, no docstring
    return "no docs"

# Decorator example with comments
@property  # Property decorator
def some_property(self):
    """Property with docstring."""
    return self._value  # Return private value

# Global variable with comment
GLOBAL_CONSTANT = 42  # The answer to everything
'''

        self.test_javascript_code = '''
/**
 * Module-level JSDoc comment
 * @fileoverview This file demonstrates JavaScript comment extraction
 * @author Test Team
 * @version 1.0.0
 */

// Import statement with comment
const fs = require('fs'); // File system module

/* 
 * Multi-line block comment
 * explaining the next section
 */

// TODO: Add error handling
// FIXME: Optimize performance

/**
 * Simple function with JSDoc
 * @param {string} name - The name to greet
 * @param {number} age - The age of the person
 * @returns {string} A greeting message
 */
function greetPerson(name, age) {
    // Validate input parameters
    if (!name || typeof name !== 'string') {
        throw new Error('Invalid name'); // Error for invalid name
    }
    
    /* 
     * Create personalized greeting
     * Based on age and name
     */
    const greeting = `Hello ${name}, you are ${age} years old`; // Template literal
    
    return greeting; // Return the formatted greeting
}

/**
 * Class with JSDoc documentation
 * @class
 */
class Person {
    /**
     * Create a person
     * @param {string} name - Person's name
     * @param {number} age - Person's age
     */
    constructor(name, age) {
        this.name = name; // Store name
        this.age = age;   // Store age
    }
    
    /**
     * Get person's info
     * @returns {Object} Person information
     */
    getInfo() {
        // Return object with person data
        return {
            name: this.name,    // Person's name
            age: this.age,      // Person's age
            // TODO: Add more fields
        };
    }
    
    // Private method (by convention)
    _validateAge() {
        /*
         * Validate age is within reasonable bounds
         * Should be between 0 and 150
         */
        return this.age >= 0 && this.age <= 150;
    }
}

// Module exports with comment
module.exports = { Person, greetPerson }; // Export main classes and functions

/* End of file comment block */
'''

        self.test_complex_python_code = '''
"""Complex module with various comment patterns."""

# -*- coding: utf-8 -*-

# Shebang and encoding comments handled separately

import asyncio
"""Not a docstring - just a string literal."""

async def async_function():
    """Async function docstring."""
    # Comment before await
    result = await some_operation()  # Inline comment
    return result

def generator_function():
    """Generator with yield."""
    # Loop with comments
    for i in range(10):  # Range from 0 to 9
        yield i  # Yield current value
        
class DecoratedClass:
    """Class with decorators and properties."""
    
    @classmethod
    def class_method(cls):
        """Class method docstring."""
        # Implementation comment
        return cls.__name__
        
    @staticmethod
    def static_method():
        """Static method docstring."""
        return "static"
        
    @property
    def prop(self):
        """Property getter."""
        return self._value  # Return private value
        
    @prop.setter
    def prop(self, value):
        """Property setter."""
        self._value = value  # Set private value

# Nested comment structures
if __name__ == "__main__":
    # Main execution block
    """
    Multi-line comment in main block.
    This explains the main execution flow.
    """
    print("Running main")  # Print statement
'''

    def test_extract_comments_tool_exists_in_all_tools(self):
        """Test that extract_comments tool is registered in ALL_TOOLS."""
        self.assertIn('extract_comments', ALL_TOOLS, 
                     "extract_comments must be registered in ALL_TOOLS registry")
        
    def test_extract_comments_tool_has_required_structure(self):
        """Test that extract_comments tool has proper MCP tool structure."""
        tool = ALL_TOOLS['extract_comments']
        
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
        
    def test_extract_comments_schema_validation(self):
        """Test extract_comments schema has correct parameters."""
        schema = ALL_TOOLS['extract_comments']['schema']
        properties = schema['properties']
        required = schema['required']
        
        # Test required parameters
        self.assertIn('source_code', required, "source_code must be required")
        self.assertIn('source_code', properties)
        
        # Test optional parameters exist
        optional_params = ['file_path', 'language', 'include_docstrings', 
                          'include_todos', 'extract_metadata']
        for param in optional_params:
            self.assertIn(param, properties, f"{param} must be in schema properties")
            
        # Test parameter types
        self.assertEqual(properties['source_code']['type'], 'string')
        self.assertEqual(properties['include_docstrings']['type'], 'boolean')
        self.assertEqual(properties['include_todos']['type'], 'boolean')
        self.assertEqual(properties['extract_metadata']['type'], 'boolean')
        
    def test_extract_comments_python_code_analysis(self):
        """Test extract_comments with real Python code analysis."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Execute real comment extraction
        result = handler(
            source_code=self.test_python_code,
            file_path="test.py",
            language="python",
            include_docstrings=True,
            include_todos=True,
            extract_metadata=True
        )
        
        # Test response structure
        self.assertIsInstance(result, dict, "Result must be a dictionary")
        self.assertIn('success', result, "Result must include success status")
        self.assertTrue(result['success'], "Extraction must succeed")
        self.assertIn('comments', result, "Result must include comments list")
        self.assertIn('docstrings', result, "Result must include docstrings list")
        self.assertIn('todos', result, "Result must include todos list")
        self.assertIn('metadata', result, "Result must include metadata")
        
        # Test comments extraction
        comments = result['comments']
        self.assertIsInstance(comments, list, "Comments must be a list")
        self.assertGreater(len(comments), 0, "Must extract at least one comment")
        
        # Test comment structure
        comment = comments[0]
        self.assertIn('text', comment, "Comment must have text")
        self.assertIn('type', comment, "Comment must have type")
        self.assertIn('line_number', comment, "Comment must have line number")
        self.assertIn('context', comment, "Comment must have context")
        
        # Test comment types
        comment_types = [c['type'] for c in comments]
        self.assertIn('single_line', comment_types, "Should extract single-line comments")
        self.assertIn('end_of_line', comment_types, "Should extract end-of-line comments")
        
        # Test specific comment content
        comment_texts = [c['text'] for c in comments]
        self.assertTrue(any('Standard library import' in text for text in comment_texts),
                       "Should extract specific comment content")
        self.assertTrue(any('End-of-line comment' in text for text in comment_texts),
                       "Should extract end-of-line comments")
        
        # Test docstrings extraction
        docstrings = result['docstrings']
        self.assertIsInstance(docstrings, list, "Docstrings must be a list")
        self.assertGreater(len(docstrings), 0, "Must extract at least one docstring")
        
        # Test docstring structure
        docstring = docstrings[0]
        self.assertIn('text', docstring, "Docstring must have text")
        self.assertIn('type', docstring, "Docstring must have type")
        self.assertIn('parent', docstring, "Docstring must have parent context")
        self.assertIn('line_number', docstring, "Docstring must have line number")
        
        # Test docstring types
        docstring_types = [d['type'] for d in docstrings]
        expected_types = ['module', 'function', 'class', 'method']
        for expected_type in expected_types:
            self.assertTrue(any(expected_type == dtype for dtype in docstring_types),
                           f"Should extract {expected_type} docstrings")
        
        # Test TODO extraction
        todos = result['todos']
        self.assertIsInstance(todos, list, "TODOs must be a list")
        self.assertGreater(len(todos), 0, "Must extract TODO comments")
        
        # Test TODO structure
        todo = todos[0]
        self.assertIn('text', todo, "TODO must have text")
        self.assertIn('type', todo, "TODO must have type")
        self.assertIn('line_number', todo, "TODO must have line number")
        
        # Test metadata
        metadata = result['metadata']
        self.assertIn('total_comments', metadata)
        self.assertIn('total_docstrings', metadata)
        self.assertIn('total_todos', metadata)
        self.assertIn('language', metadata)
        self.assertIn('processing_time', metadata)
        self.assertEqual(metadata['language'], 'python')
        self.assertGreater(metadata['total_comments'], 0)
        self.assertGreater(metadata['total_docstrings'], 0)
        
    def test_extract_comments_javascript_code_analysis(self):
        """Test extract_comments with real JavaScript code analysis."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Execute real comment extraction for JavaScript
        result = handler(
            source_code=self.test_javascript_code,
            file_path="test.js",
            language="javascript",
            include_docstrings=True,
            include_todos=True
        )
        
        # Test basic response structure
        self.assertTrue(result['success'])
        self.assertIn('comments', result)
        self.assertIn('docstrings', result)
        
        # Test JavaScript-specific comment extraction
        comments = result['comments']
        comment_types = [c['type'] for c in comments]
        self.assertIn('single_line', comment_types, "Should extract // comments")
        self.assertIn('block', comment_types, "Should extract /* */ comments")
        self.assertIn('end_of_line', comment_types, "Should extract end-of-line comments")
        
        # Test JSDoc extraction
        docstrings = result['docstrings']
        self.assertGreater(len(docstrings), 0, "Should extract JSDoc comments")
        
        # Test JSDoc structure
        jsdoc_with_params = [d for d in docstrings if '@param' in d.get('text', '') or '@returns' in d.get('text', '')]
        self.assertGreater(len(jsdoc_with_params), 0, "Should extract JSDoc with @param or @returns")
        
        # Test metadata for JavaScript
        metadata = result['metadata']
        self.assertEqual(metadata['language'], 'javascript')
        
    def test_extract_comments_docstring_types(self):
        """Test extraction of different docstring types."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        result = handler(
            source_code=self.test_python_code,
            include_docstrings=True
        )
        
        self.assertTrue(result['success'])
        docstrings = result['docstrings']
        
        # Check for different docstring types
        docstring_parents = [d['parent'] for d in docstrings]
        self.assertTrue(any('module' in parent for parent in docstring_parents),
                       "Should extract module docstrings")
        self.assertTrue(any('function' in parent for parent in docstring_parents),
                       "Should extract function docstrings")
        self.assertTrue(any('class' in parent for parent in docstring_parents),
                       "Should extract class docstrings")
        self.assertTrue(any('method' in parent for parent in docstring_parents),
                       "Should extract method docstrings")
        
    def test_extract_comments_todo_fixme_detection(self):
        """Test detection of TODO, FIXME, and other task comments."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        result = handler(
            source_code=self.test_python_code,
            include_todos=True
        )
        
        self.assertTrue(result['success'])
        todos = result['todos']
        
        # Test TODO and FIXME extraction
        todo_types = [t['type'] for t in todos]
        self.assertTrue(any('TODO' in ttype for ttype in todo_types),
                       "Should extract TODO comments")
        self.assertTrue(any('FIXME' in ttype for ttype in todo_types),
                       "Should extract FIXME comments")
        
        # Test TODO types
        todo_types = [t['type'] for t in todos]
        expected_types = ['TODO', 'FIXME']
        for expected_type in expected_types:
            self.assertTrue(any(expected_type in ttype for ttype in todo_types),
                           f"Should classify {expected_type} comments")
        
    def test_extract_comments_comment_context(self):
        """Test comment context detection (function, class, module level)."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        result = handler(
            source_code=self.test_python_code,
            extract_metadata=True
        )
        
        self.assertTrue(result['success'])
        comments = result['comments']
        
        # Test context extraction
        contexts = [c['context'] for c in comments]
        self.assertTrue(any('module' in context for context in contexts),
                       "Should detect module-level comments")
        self.assertTrue(any('function' in context for context in contexts),
                       "Should detect function-level comments")
        self.assertTrue(any('method' in context for context in contexts),
                       "Should detect method-level comments")
        
    def test_extract_comments_multiline_comments(self):
        """Test extraction of multi-line comment blocks."""
        multiline_code = '''
# This is a multi-line comment block
# that spans several lines
# and should be grouped together

def function():
    """Function docstring."""
    # Another multi-line comment
    # inside a function
    # with multiple lines
    pass
'''
        
        handler = ALL_TOOLS['extract_comments']['handler']
        result = handler(source_code=multiline_code)
        
        self.assertTrue(result['success'])
        comments = result['comments']
        
        # Should detect multi-line comment blocks
        multiline_comments = [c for c in comments if c['type'] == 'block']
        self.assertGreater(len(multiline_comments), 0, 
                          "Should detect multi-line comment blocks")
        
    def test_extract_comments_language_detection(self):
        """Test automatic language detection for comments."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Test with Python code and auto language detection
        result = handler(
            source_code=self.test_python_code,
            file_path="test.py",
            language="auto"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['language'], 'python')
        
        # Test with JavaScript code and auto detection
        result = handler(
            source_code=self.test_javascript_code,
            file_path="test.js",
            language="auto"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['metadata']['language'], 'javascript')
        
    def test_extract_comments_error_handling(self):
        """Test extract_comments error handling with invalid code."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Test with malformed code (should still extract comments if possible)
        result = handler(
            source_code="# Valid comment\nclass BrokenClass(\n    # incomplete syntax",
            language="python"
        )
        
        # Should handle gracefully and still extract valid comments
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # May succeed with partial parsing or fail gracefully
        
    def test_extract_comments_performance_requirements(self):
        """Test performance requirements are met."""
        import time
        
        handler = ALL_TOOLS['extract_comments']['handler']
        
        start_time = time.time()
        result = handler(
            source_code=self.test_complex_python_code,
            include_docstrings=True,
            include_todos=True,
            extract_metadata=True
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Must complete in reasonable time (less than 3 seconds for small code)
        self.assertLess(processing_time, 3.0, 
                       "Comment extraction must complete in < 3 seconds")
        
        # Verify processing time is recorded
        self.assertTrue(result['success'])
        self.assertIn('processing_time', result['metadata'])
        self.assertGreater(result['metadata']['processing_time'], 0)
        
    def test_extract_comments_empty_code(self):
        """Test extract_comments with empty or whitespace-only code."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Test with empty code
        result = handler(source_code="")
        self.assertTrue(result['success'])
        self.assertEqual(len(result['comments']), 0)
        self.assertEqual(len(result['docstrings']), 0)
        
        # Test with whitespace only
        result = handler(source_code="   \n\n   \t  \n")
        self.assertTrue(result['success'])
        self.assertEqual(len(result['comments']), 0)
        
    def test_extract_comments_include_flags(self):
        """Test include flags for selective extraction."""
        handler = ALL_TOOLS['extract_comments']['handler']
        
        # Test with docstrings disabled
        result = handler(
            source_code=self.test_python_code,
            include_docstrings=False
        )
        self.assertTrue(result['success'])
        self.assertEqual(len(result['docstrings']), 0)
        
        # Test with TODOs disabled
        result = handler(
            source_code=self.test_python_code,
            include_todos=False
        )
        self.assertTrue(result['success'])
        self.assertEqual(len(result['todos']), 0)
        
        # Test with all enabled
        result = handler(
            source_code=self.test_python_code,
            include_docstrings=True,
            include_todos=True
        )
        self.assertTrue(result['success'])
        self.assertGreater(len(result['docstrings']), 0)
        self.assertGreater(len(result['todos']), 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)