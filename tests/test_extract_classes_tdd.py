#!/usr/bin/env python3
"""
TDD Test for extract_classes MCP Tool Integration

This test ensures extract_classes is implemented as a real, first-class
LTMC MCP tool with actual AST-based class analysis.

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


class TestExtractClassesTDD(unittest.TestCase):
    """Test extract_classes tool implementation following TDD principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_python_code = '''
class SimpleClass:
    """A simple class for testing."""
    
    def __init__(self, value):
        """Initialize the class.
        
        Args:
            value: Initial value
        """
        self.value = value
        
    def get_value(self):
        """Get the stored value."""
        return self.value
        
    def set_value(self, new_value):
        """Set a new value."""
        self.value = new_value

class InheritedClass(SimpleClass):
    """A class that inherits from SimpleClass."""
    
    def __init__(self, value, extra):
        super().__init__(value)
        self.extra = extra
        
    def get_extra(self):
        """Get the extra value."""
        return self.extra

class MultipleInheritance(SimpleClass, object):
    """Class with multiple inheritance."""
    pass

@dataclass
class DataClass:
    """A dataclass example."""
    name: str
    age: int = 0
    
    def greet(self) -> str:
        """Greet the person."""
        return f"Hello, {self.name}!"

class AbstractBase:
    """Abstract base class."""
    
    def abstract_method(self):
        """This should be implemented by subclasses."""
        raise NotImplementedError
        
    @staticmethod
    def static_method():
        """A static method."""
        return "static"
        
    @classmethod
    def class_method(cls):
        """A class method."""
        return cls.__name__
        
    @property
    def prop(self):
        """A property."""
        return self._prop
        
    @prop.setter
    def prop(self, value):
        """Property setter."""
        self._prop = value

class NestedClass:
    """Class with nested inner class."""
    
    class InnerClass:
        """Inner class."""
        def inner_method(self):
            return "inner"
    
    def outer_method(self):
        return "outer"
'''

        self.test_javascript_code = '''
class SimpleJSClass {
    /**
     * A simple JavaScript class
     */
    constructor(value) {
        this.value = value;
    }
    
    getValue() {
        /**
         * Get the stored value
         */
        return this.value;
    }
    
    setValue(newValue) {
        /**
         * Set a new value
         */
        this.value = newValue;
    }
}

class ExtendedClass extends SimpleJSClass {
    /**
     * Extended JavaScript class
     */
    constructor(value, extra) {
        super(value);
        this.extra = extra;
    }
    
    getExtra() {
        return this.extra;
    }
    
    static staticMethod() {
        /**
         * Static method
         */
        return "static";
    }
}

class AsyncClass {
    async asyncMethod() {
        /**
         * Async method
         */
        return await Promise.resolve("async");
    }
}
'''

    def test_extract_classes_tool_exists_in_all_tools(self):
        """Test that extract_classes tool is registered in ALL_TOOLS."""
        self.assertIn('extract_classes', ALL_TOOLS, 
                     "extract_classes must be registered in ALL_TOOLS registry")
        
    def test_extract_classes_tool_has_required_structure(self):
        """Test that extract_classes tool has proper MCP tool structure."""
        tool = ALL_TOOLS['extract_classes']
        
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
        
    def test_extract_classes_schema_validation(self):
        """Test extract_classes schema has correct parameters."""
        schema = ALL_TOOLS['extract_classes']['schema']
        properties = schema['properties']
        required = schema['required']
        
        # Test required parameters
        self.assertIn('source_code', required, "source_code must be required")
        self.assertIn('source_code', properties)
        
        # Test optional parameters exist
        optional_params = ['file_path', 'language', 'extract_relationships', 
                          'include_private', 'analyze_inheritance']
        for param in optional_params:
            self.assertIn(param, properties, f"{param} must be in schema properties")
            
        # Test parameter types
        self.assertEqual(properties['source_code']['type'], 'string')
        self.assertEqual(properties['extract_relationships']['type'], 'boolean')
        self.assertEqual(properties['analyze_inheritance']['type'], 'boolean')
        
    def test_extract_classes_python_code_analysis(self):
        """Test extract_classes with real Python code analysis."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
        # Execute real class extraction
        result = handler(
            source_code=self.test_python_code,
            file_path="test.py",
            language="python",
            extract_relationships=True,
            analyze_inheritance=True
        )
        
        # Test response structure
        self.assertIsInstance(result, dict, "Result must be a dictionary")
        self.assertIn('success', result, "Result must include success status")
        self.assertTrue(result['success'], "Extraction must succeed")
        self.assertIn('classes', result, "Result must include classes list")
        self.assertIn('relationships', result, "Result must include relationships")
        self.assertIn('metadata', result, "Result must include metadata")
        
        # Test classes extraction
        classes = result['classes']
        self.assertIsInstance(classes, list, "Classes must be a list")
        self.assertGreater(len(classes), 0, "Must extract at least one class")
        
        # Find and validate specific classes
        class_names = [c['name'] for c in classes]
        self.assertIn('SimpleClass', class_names, 
                     "Must extract SimpleClass")
        self.assertIn('InheritedClass', class_names,
                     "Must extract InheritedClass")
        self.assertIn('DataClass', class_names,
                     "Must extract DataClass")
        
        # Test SimpleClass details
        simple_class = next(c for c in classes if c['name'] == 'SimpleClass')
        self.assertEqual(simple_class['name'], 'SimpleClass')
        self.assertIn('methods', simple_class)
        self.assertIn('attributes', simple_class)
        self.assertIn('docstring', simple_class)
        self.assertIn('line_start', simple_class)
        self.assertIn('line_end', simple_class)
        self.assertIn('decorators', simple_class)
        self.assertIn('is_abstract', simple_class)
        
        # Test method extraction
        methods = simple_class['methods']
        self.assertIsInstance(methods, list)
        self.assertGreater(len(methods), 0, "SimpleClass should have methods")
        method_names = [m['name'] for m in methods]
        self.assertIn('__init__', method_names)
        self.assertIn('get_value', method_names)
        self.assertIn('set_value', method_names)
        
        # Test method details
        init_method = next(m for m in methods if m['name'] == '__init__')
        self.assertIn('signature', init_method)
        self.assertIn('visibility', init_method)
        self.assertIn('is_static', init_method)
        self.assertIn('is_class_method', init_method)
        self.assertIn('is_property', init_method)
        
        # Test inheritance extraction
        inherited_class = next(c for c in classes if c['name'] == 'InheritedClass')
        inheritance = inherited_class['inheritance']
        self.assertIsInstance(inheritance, dict)
        self.assertIn('parents', inheritance)
        self.assertIn('SimpleClass', inheritance['parents'])
        
        # Test multiple inheritance
        multi_class = next(c for c in classes if c['name'] == 'MultipleInheritance')
        multi_parents = multi_class['inheritance']['parents']
        self.assertIn('SimpleClass', multi_parents)
        self.assertIn('object', multi_parents)
        
        # Test decorator extraction
        dataclass = next(c for c in classes if c['name'] == 'DataClass')
        decorators = dataclass['decorators']
        self.assertIsInstance(decorators, list)
        self.assertIn('dataclass', decorators)
        
        # Test relationships
        relationships = result['relationships']
        self.assertIsInstance(relationships, list)
        self.assertGreater(len(relationships), 0, "Should have inheritance relationships")
        
        # Find inheritance relationship
        inheritance_rels = [r for r in relationships if r['type'] == 'inheritance']
        self.assertGreater(len(inheritance_rels), 0, "Should have inheritance relationships")
        
        # Test metadata
        metadata = result['metadata']
        self.assertIn('total_classes', metadata)
        self.assertIn('inheritance_depth', metadata)
        self.assertIn('language', metadata)
        self.assertIn('processing_time', metadata)
        self.assertEqual(metadata['language'], 'python')
        self.assertGreater(metadata['total_classes'], 0)
        
    def test_extract_classes_special_method_detection(self):
        """Test detection of special methods (static, class, property)."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
        result = handler(
            source_code=self.test_python_code,
            language="python"
        )
        
        self.assertTrue(result['success'])
        classes = result['classes']
        
        # Find AbstractBase class
        abstract_class = next(c for c in classes if c['name'] == 'AbstractBase')
        methods = abstract_class['methods']
        
        # Test static method detection
        static_methods = [m for m in methods if m.get('is_static', False)]
        self.assertGreater(len(static_methods), 0, "Should detect static methods")
        static_method = static_methods[0]
        self.assertEqual(static_method['name'], 'static_method')
        
        # Test class method detection
        class_methods = [m for m in methods if m.get('is_class_method', False)]
        self.assertGreater(len(class_methods), 0, "Should detect class methods")
        class_method = class_methods[0]
        self.assertEqual(class_method['name'], 'class_method')
        
        # Test property detection
        properties = [m for m in methods if m.get('is_property', False)]
        self.assertGreater(len(properties), 0, "Should detect properties")
        
    def test_extract_classes_nested_classes(self):
        """Test extraction of nested classes."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
        result = handler(
            source_code=self.test_python_code,
            language="python"
        )
        
        self.assertTrue(result['success'])
        classes = result['classes']
        class_names = [c['name'] for c in classes]
        
        # Should extract both outer and inner classes
        self.assertIn('NestedClass', class_names)
        self.assertIn('InnerClass', class_names)
        
        # Test nested class information
        nested_class = next(c for c in classes if c['name'] == 'NestedClass')
        self.assertIn('nested_classes', nested_class)
        nested_list = nested_class['nested_classes']
        self.assertIn('InnerClass', nested_list)
        
    def test_extract_classes_javascript_code_analysis(self):
        """Test extract_classes with real JavaScript code analysis."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
        # Execute real class extraction for JavaScript
        result = handler(
            source_code=self.test_javascript_code,
            file_path="test.js",
            language="javascript",
            extract_relationships=True
        )
        
        # Test basic response structure
        self.assertTrue(result['success'])
        self.assertIn('classes', result)
        
        # Test JavaScript-specific class extraction
        classes = result['classes']
        class_names = [c['name'] for c in classes]
        self.assertIn('SimpleJSClass', class_names, 
                     "Must extract JavaScript class")
        self.assertIn('ExtendedClass', class_names,
                     "Must extract extended class")
        
        # Test inheritance detection
        extended_class = next(c for c in classes if c['name'] == 'ExtendedClass')
        inheritance = extended_class['inheritance']
        self.assertIn('SimpleJSClass', inheritance['parents'])
        
        # Test static method detection
        methods = extended_class['methods']
        static_methods = [m for m in methods if m.get('is_static', False)]
        self.assertGreater(len(static_methods), 0, "Should detect static methods")
        
    def test_extract_classes_error_handling(self):
        """Test extract_classes error handling with invalid code."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
        # Test with malformed Python code
        result = handler(
            source_code="class BrokenClass(\n    # incomplete syntax",
            language="python"
        )
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # May succeed with partial parsing or fail gracefully
        
    def test_extract_classes_language_detection(self):
        """Test automatic language detection for classes."""
        handler = ALL_TOOLS['extract_classes']['handler']
        
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
        
    def test_extract_classes_inheritance_depth_calculation(self):
        """Test inheritance depth calculation."""
        deep_inheritance_code = '''
class A:
    pass

class B(A):
    pass

class C(B):
    pass

class D(C):
    pass
'''
        
        handler = ALL_TOOLS['extract_classes']['handler']
        result = handler(
            source_code=deep_inheritance_code,
            analyze_inheritance=True
        )
        
        self.assertTrue(result['success'])
        
        # Test inheritance depth metadata
        metadata = result['metadata']
        self.assertIn('inheritance_depth', metadata)
        self.assertGreater(metadata['inheritance_depth'], 1, 
                          "Should calculate inheritance depth > 1")
        
    def test_extract_classes_performance_requirements(self):
        """Test performance requirements are met."""
        import time
        
        handler = ALL_TOOLS['extract_classes']['handler']
        
        start_time = time.time()
        result = handler(
            source_code=self.test_python_code,
            extract_relationships=True,
            analyze_inheritance=True
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Must complete in reasonable time (less than 3 seconds for small code)
        self.assertLess(processing_time, 3.0, 
                       "Class extraction must complete in < 3 seconds")
        
        # Verify processing time is recorded
        self.assertTrue(result['success'])
        self.assertIn('processing_time', result['metadata'])
        self.assertGreater(result['metadata']['processing_time'], 0)
        
    def test_extract_classes_private_class_filtering(self):
        """Test filtering of private classes."""
        private_code = '''
class PublicClass:
    pass

class _ProtectedClass:
    pass

class __PrivateClass:
    pass
'''
        
        handler = ALL_TOOLS['extract_classes']['handler']
        
        # Test without private classes
        result = handler(
            source_code=private_code,
            include_private=False
        )
        
        self.assertTrue(result['success'])
        class_names = [c['name'] for c in result['classes']]
        self.assertIn('PublicClass', class_names)
        self.assertNotIn('_ProtectedClass', class_names)
        self.assertNotIn('__PrivateClass', class_names)
        
        # Test with private classes
        result = handler(
            source_code=private_code,
            include_private=True
        )
        
        self.assertTrue(result['success'])
        class_names = [c['name'] for c in result['classes']]
        self.assertIn('PublicClass', class_names)
        self.assertIn('_ProtectedClass', class_names)
        self.assertIn('__PrivateClass', class_names)
        
    def test_extract_classes_relationship_types(self):
        """Test different types of class relationships."""
        relationship_code = '''
class Base:
    pass

class Child(Base):
    pass

class Mixin:
    pass

class Multiple(Base, Mixin):
    pass
'''
        
        handler = ALL_TOOLS['extract_classes']['handler']
        result = handler(
            source_code=relationship_code,
            extract_relationships=True
        )
        
        self.assertTrue(result['success'])
        relationships = result['relationships']
        
        # Test relationship structure
        self.assertIsInstance(relationships, list)
        if relationships:  # May be empty for simple relationships
            rel = relationships[0]
            self.assertIn('type', rel)
            self.assertIn('source', rel)
            self.assertIn('target', rel)
            self.assertIn('description', rel)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)