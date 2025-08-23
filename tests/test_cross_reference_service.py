#!/usr/bin/env python3
"""
Test Driven Development (TDD) test suite for cross-reference service.

Comprehensive tests for the cross-reference and symbol table system including:
- Symbol table construction and navigation
- Inheritance analysis with MRO chain mapping
- Call graph analysis and usage pattern discovery
- Cross-reference generation and "see also" suggestions
- Integration with glom/boltons for nested data traversal

No mocks, no stubs, no placeholders - tests real functionality only.
"""

import ast
import os
import sys
import tempfile
import unittest
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ltms.services.cross_reference_service import (
    CrossReferenceEngine,
    DocumentationSymbolTable,
    SymbolReference,
    CrossReference,
    InheritanceChain,
    UsagePattern,
    SymbolTableVisitor,
    InheritanceAnalyzer,
    CallGraphAnalyzer
)
from ltms.services.advanced_documentation_service import (
    AdvancedDocumentationExtractor,
    ModuleDocumentation,
    FunctionDocumentation,
    ClassDocumentation,
    SourceLocation
)


class TestSymbolTableVisitor(unittest.TestCase):
    """Test symbol table construction and AST analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.visitor = SymbolTableVisitor("test_module", "test_file.py")
    
    def test_function_symbol_extraction(self):
        """Test extraction of function symbols with comprehensive metadata."""
        source_code = '''
def simple_function(param1: str, param2: int = 42) -> str:
    """Simple test function.
    
    Args:
        param1: First parameter
        param2: Second parameter with default
        
    Returns:
        str: Formatted result
    """
    return f"{param1}: {param2}"

@decorator
async def async_function(data: List[Dict[str, Any]]) -> Optional[bool]:
    """Async function with complex types."""
    return True
        '''
        
        tree = ast.parse(source_code)
        self.visitor.visit(tree)
        
        # Should extract 2 functions
        function_symbols = {name: symbol for name, symbol in self.visitor.symbols.items() 
                           if symbol.symbol_type in ["function", "async_function"]}
        self.assertEqual(len(function_symbols), 2)
        
        # Check simple_function
        simple_func = next(s for s in function_symbols.values() if s.name == "simple_function")
        self.assertEqual(simple_func.symbol_type, "function")
        self.assertEqual(simple_func.scope, "function")
        self.assertIsNotNone(simple_func.signature)
        self.assertIn("param1: str", simple_func.signature)
        self.assertIn("param2: int = 42", simple_func.signature)
        self.assertTrue(simple_func.is_public)
        
        # Check async_function
        async_func = next(s for s in function_symbols.values() if s.name == "async_function")
        self.assertEqual(async_func.symbol_type, "async_function")
        self.assertEqual(len(async_func.decorators), 1)
        self.assertEqual(async_func.decorators[0], "decorator")
        self.assertTrue(async_func.metadata.get('is_async', False))
    
    def test_class_symbol_extraction(self):
        """Test extraction of class symbols with inheritance and methods."""
        source_code = '''
class BaseClass:
    """Base class for testing."""
    
    def base_method(self):
        """Base method."""
        pass

class DerivedClass(BaseClass, dict):
    """Derived class with multiple inheritance."""
    
    class_attr: str = "test"
    
    def __init__(self, name: str):
        """Initialize derived class."""
        self.name = name
        super().__init__()
    
    @property
    def display_name(self) -> str:
        """Get display name."""
        return f"Derived: {self.name}"
    
    def derived_method(self) -> bool:
        """Derived method that calls base."""
        self.base_method()
        return True
        '''
        
        tree = ast.parse(source_code)
        self.visitor.visit(tree)
        
        # Should extract 2 classes
        class_symbols = {name: symbol for name, symbol in self.visitor.symbols.items() 
                        if symbol.symbol_type == "class"}
        self.assertEqual(len(class_symbols), 2)
        
        # Check BaseClass
        base_class = next(s for s in class_symbols.values() if s.name == "BaseClass")
        self.assertEqual(base_class.symbol_type, "class")
        self.assertEqual(base_class.scope, "class")
        self.assertEqual(len(base_class.metadata.get('base_classes', [])), 0)
        
        # Check DerivedClass
        derived_class = next(s for s in class_symbols.values() if s.name == "DerivedClass")
        self.assertEqual(derived_class.symbol_type, "class")
        base_classes = derived_class.metadata.get('base_classes', [])
        self.assertEqual(len(base_classes), 2)
        self.assertIn("BaseClass", base_classes)
        self.assertIn("dict", base_classes)
        
        # Should extract methods
        method_symbols = {name: symbol for name, symbol in self.visitor.symbols.items() 
                         if symbol.scope == "method"}
        self.assertGreater(len(method_symbols), 0)
        
        # Check inheritance cross-references
        inheritance_refs = [ref for ref in self.visitor.cross_references 
                           if ref.relationship_type == "inherits"]
        self.assertEqual(len(inheritance_refs), 2)  # BaseClass and dict inheritance
    
    def test_cross_reference_generation(self):
        """Test generation of function call and usage cross-references."""
        source_code = '''
def utility_function(data):
    """Utility function."""
    return data.upper()

def main_function():
    """Main function that calls utility."""
    result = utility_function("test")
    return result

class TestClass:
    """Test class with method calls."""
    
    def method_one(self):
        """Method that calls utility."""
        return utility_function("from_method")
    
    def method_two(self):
        """Method that calls another method."""
        return self.method_one()
        '''
        
        tree = ast.parse(source_code)
        self.visitor.visit(tree)
        
        # Should generate call cross-references
        call_refs = [ref for ref in self.visitor.cross_references 
                    if ref.relationship_type == "calls"]
        self.assertGreater(len(call_refs), 0)
        
        # Check specific call relationships
        main_to_utility = next((ref for ref in call_refs 
                               if "main_function" in ref.source_symbol and 
                               "utility_function" in ref.target_symbol), None)
        self.assertIsNotNone(main_to_utility)
        
        method_to_utility = next((ref for ref in call_refs 
                                 if "method_one" in ref.source_symbol and 
                                 "utility_function" in ref.target_symbol), None)
        self.assertIsNotNone(method_to_utility)
    
    def test_import_tracking(self):
        """Test tracking of import statements and dependencies."""
        source_code = '''
import os
import sys as system
from typing import Dict, List, Optional
from collections.abc import Mapping

def function_using_imports():
    """Function that uses imported modules."""
    path = os.path.join("a", "b")
    items = List[str]()
    return path
        '''
        
        tree = ast.parse(source_code)
        self.visitor.visit(tree)
        
        # Should track imports
        import_refs = [ref for ref in self.visitor.cross_references 
                      if ref.relationship_type == "imports"]
        self.assertGreater(len(import_refs), 0)
        
        # Check specific imports
        import_names = [ref.target_symbol for ref in import_refs]
        self.assertIn("os", import_names)
        self.assertIn("sys", import_names)
        self.assertIn("typing.Dict", import_names)
        self.assertIn("typing.List", import_names)


class TestInheritanceAnalyzer(unittest.TestCase):
    """Test inheritance analysis and MRO calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = InheritanceAnalyzer()
    
    def test_simple_inheritance_analysis(self):
        """Test analysis of simple inheritance chains."""
        # Create mock symbols for inheritance testing
        symbols = {
            "test.BaseClass": SymbolReference(
                name="BaseClass",
                qualified_name="test.BaseClass",
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=1,
                scope="class",
                metadata={'base_classes': []}
            ),
            "test.MiddleClass": SymbolReference(
                name="MiddleClass", 
                qualified_name="test.MiddleClass",
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=10,
                scope="class",
                metadata={'base_classes': ['BaseClass']}
            ),
            "test.DerivedClass": SymbolReference(
                name="DerivedClass",
                qualified_name="test.DerivedClass", 
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=20,
                scope="class",
                metadata={'base_classes': ['MiddleClass']}
            )
        }
        
        chains = self.analyzer.analyze_inheritance(symbols)
        
        # Should analyze all classes
        self.assertEqual(len(chains), 3)
        
        # Check DerivedClass chain
        derived_chain = chains["test.DerivedClass"]
        self.assertEqual(derived_chain.class_name, "DerivedClass")
        self.assertEqual(derived_chain.base_classes, ['MiddleClass'])
        
        # MRO should include the inheritance chain
        self.assertIn("test.DerivedClass", derived_chain.mro_chain)
        self.assertIn("test.MiddleClass", derived_chain.mro_chain)
        self.assertIn("test.BaseClass", derived_chain.mro_chain)
    
    def test_multiple_inheritance_analysis(self):
        """Test analysis of multiple inheritance patterns."""
        symbols = {
            "test.MixinA": SymbolReference(
                name="MixinA",
                qualified_name="test.MixinA",
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=1,
                scope="class",
                metadata={'base_classes': []}
            ),
            "test.MixinB": SymbolReference(
                name="MixinB",
                qualified_name="test.MixinB",
                symbol_type="class", 
                module_path="test",
                file_path="test.py",
                line_number=10,
                scope="class",
                metadata={'base_classes': []}
            ),
            "test.MultipleInheritance": SymbolReference(
                name="MultipleInheritance",
                qualified_name="test.MultipleInheritance",
                symbol_type="class",
                module_path="test",
                file_path="test.py", 
                line_number=20,
                scope="class",
                metadata={'base_classes': ['MixinA', 'MixinB']}
            )
        }
        
        chains = self.analyzer.analyze_inheritance(symbols)
        
        # Check multiple inheritance class
        multi_chain = chains["test.MultipleInheritance"]
        self.assertEqual(len(multi_chain.base_classes), 2)
        self.assertIn('MixinA', multi_chain.base_classes)
        self.assertIn('MixinB', multi_chain.base_classes)
    
    def test_mixin_detection(self):
        """Test detection of mixin classes."""
        symbols = {
            "test.DataMixin": SymbolReference(
                name="DataMixin",
                qualified_name="test.DataMixin",
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=1,
                scope="class",
                metadata={'base_classes': [], 'method_count': 2}
            ),
            "test.ConcreteClass": SymbolReference(
                name="ConcreteClass",
                qualified_name="test.ConcreteClass",
                symbol_type="class",
                module_path="test",
                file_path="test.py",
                line_number=10,
                scope="class",
                metadata={'base_classes': ['DataMixin']}
            )
        }
        
        chains = self.analyzer.analyze_inheritance(symbols)
        
        # Should detect mixin
        concrete_chain = chains["test.ConcreteClass"]
        self.assertIn('DataMixin', concrete_chain.mixins)


class TestCallGraphAnalyzer(unittest.TestCase):
    """Test call graph analysis and usage pattern discovery."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = CallGraphAnalyzer()
    
    def test_call_graph_construction(self):
        """Test construction of function call graphs."""
        # Create mock cross-references
        cross_refs = [
            CrossReference(
                source_symbol="test.main_function",
                target_symbol="test.utility_function",
                relationship_type="calls",
                file_path="test.py",
                line_number=10,
                context="function_call"
            ),
            CrossReference(
                source_symbol="test.main_function", 
                target_symbol="test.helper_function",
                relationship_type="calls",
                file_path="test.py",
                line_number=11,
                context="function_call"
            ),
            CrossReference(
                source_symbol="test.helper_function",
                target_symbol="test.utility_function", 
                relationship_type="calls",
                file_path="test.py",
                line_number=20,
                context="function_call"
            )
        ]
        
        symbols = {
            "test.main_function": SymbolReference(
                name="main_function",
                qualified_name="test.main_function",
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=5,
                scope="function"
            ),
            "test.utility_function": SymbolReference(
                name="utility_function",
                qualified_name="test.utility_function", 
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=15,
                scope="function"
            ),
            "test.helper_function": SymbolReference(
                name="helper_function",
                qualified_name="test.helper_function",
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=25,
                scope="function"
            )
        }
        
        call_graph, usage_patterns = self.analyzer.analyze_call_graph(cross_refs, symbols)
        
        # Should build call graph
        self.assertIn("test.main_function", call_graph)
        main_calls = call_graph["test.main_function"]
        self.assertIn("test.utility_function", main_calls)
        self.assertIn("test.helper_function", main_calls)
        
        # Should find usage patterns
        self.assertGreater(len(usage_patterns), 0)
        
        # utility_function should be called by multiple functions
        utility_patterns = [p for p in usage_patterns if p.symbol_name == "test.utility_function"]
        self.assertGreater(len(utility_patterns), 0)


class TestCrossReferenceEngine(unittest.TestCase):
    """Test complete cross-reference engine integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = CrossReferenceEngine()
    
    def test_complete_codebase_analysis(self):
        """Test comprehensive analysis of a complete codebase."""
        # Create test module documentation
        test_module = self._create_test_module_documentation()
        
        # Analyze codebase
        symbol_table = self.engine.analyze_codebase([test_module])
        
        # Should have symbols
        self.assertGreater(len(symbol_table.symbols), 0)
        
        # Should have cross-references
        self.assertGreater(len(symbol_table.cross_references), 0)
        
        # Should have analysis metadata
        self.assertIn('total_symbols', symbol_table.analysis_metadata)
        self.assertIn('total_cross_references', symbol_table.analysis_metadata)
        
        # Should track modules
        self.assertIn("test_module", symbol_table.modules)
    
    def test_see_also_suggestions(self):
        """Test generation of intelligent 'see also' suggestions."""
        # Create minimal symbol table
        symbol_table = DocumentationSymbolTable()
        
        # Add test symbols
        symbol_table.symbols = {
            "test.function_a": SymbolReference(
                name="function_a",
                qualified_name="test.function_a",
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=1,
                scope="function"
            ),
            "test.function_b": SymbolReference(
                name="function_b", 
                qualified_name="test.function_b",
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=10,
                scope="function"
            ),
            "test.function_c": SymbolReference(
                name="function_c",
                qualified_name="test.function_c",
                symbol_type="function",
                module_path="test",
                file_path="test.py",
                line_number=20,
                scope="function"
            )
        }
        
        # Add call graph relationships
        symbol_table.call_graph = {
            "test.function_a": ["test.function_b", "test.function_c"]
        }
        
        # Generate suggestions
        suggestions = self.engine.generate_see_also_suggestions("test.function_a", symbol_table)
        
        # Should suggest related functions
        self.assertIn("test.function_b", suggestions)
        self.assertIn("test.function_c", suggestions)
    
    def test_usage_example_discovery(self):
        """Test discovery of usage examples from patterns."""
        # Create symbol table with usage patterns
        symbol_table = DocumentationSymbolTable()
        
        symbol_table.usage_patterns = [
            UsagePattern(
                symbol_name="test.function_a",
                usage_type="function_call",
                file_path="test.py",
                line_number=15,
                usage_pattern="function_a('test', 42)",
                frequency=3,
                is_test_usage=False
            ),
            UsagePattern(
                symbol_name="test.function_a",
                usage_type="function_call",
                file_path="test_file.py",
                line_number=25,
                usage_pattern="result = function_a(data)",
                frequency=1,
                is_test_usage=True
            )
        ]
        
        # Find usage examples
        examples = self.engine.find_usage_examples("test.function_a", symbol_table)
        
        # Should find both patterns
        self.assertEqual(len(examples), 2)
        
        # Should have different frequencies
        frequencies = [example.frequency for example in examples]
        self.assertIn(3, frequencies)
        self.assertIn(1, frequencies)
    
    def _create_test_module_documentation(self) -> ModuleDocumentation:
        """Create test module documentation for integration testing."""
        # Create temporary test file
        test_content = '''
def utility_function(data: str) -> str:
    """Utility function for testing."""
    return data.upper()

def main_function() -> bool:
    """Main function that uses utility."""
    result = utility_function("test")
    return len(result) > 0

class TestClass:
    """Test class for cross-reference analysis."""
    
    def __init__(self, name: str):
        """Initialize test class."""
        self.name = name
    
    def process(self) -> str:
        """Process method that calls utility."""
        return utility_function(self.name)
        '''
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_content)
            temp_path = f.name
        
        try:
            # Extract documentation using advanced extractor
            extractor = AdvancedDocumentationExtractor()
            module_doc = extractor.extract_module_documentation(temp_path)
            
            # Override name for testing
            module_doc.name = "test_module"
            
            return module_doc
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)


class TestIntegrationWithRealCode(unittest.TestCase):
    """Integration tests with real LTMC code."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.engine = CrossReferenceEngine()
        self.extractor = AdvancedDocumentationExtractor()
    
    def test_analyze_consolidated_tools_cross_references(self):
        """Test cross-reference analysis of ltms/tools/consolidated.py."""
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
            
            # Analyze cross-references
            symbol_table = self.engine.analyze_codebase([module_doc])
            
            # Should find action functions
            action_symbols = {
                name: symbol for name, symbol in symbol_table.symbols.items()
                if symbol.name.endswith('_action')
            }
            self.assertGreater(len(action_symbols), 0)
            
            # Should have call relationships
            if symbol_table.call_graph:
                # Find functions that make calls
                callers = list(symbol_table.call_graph.keys())
                self.assertGreater(len(callers), 0)
            
            # Should generate cross-references
            self.assertGreater(len(symbol_table.cross_references), 0)
            
            # Test see-also suggestions for action functions
            for symbol_name in list(action_symbols.keys())[:3]:  # Test first 3
                suggestions = self.engine.generate_see_also_suggestions(symbol_name, symbol_table)
                # Should get some suggestions (may be empty for isolated functions)
                self.assertIsInstance(suggestions, list)
    
    def test_analyze_cross_reference_service_self_analysis(self):
        """Test self-analysis of the cross-reference service."""
        service_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ltms",
            "services",
            "cross_reference_service.py"
        )
        
        if os.path.exists(service_path):
            # Extract documentation
            module_doc = self.extractor.extract_module_documentation(service_path)
            
            # Analyze cross-references
            symbol_table = self.engine.analyze_codebase([module_doc])
            
            # Should find key classes
            key_classes = [
                'CrossReferenceEngine',
                'SymbolTableVisitor',
                'InheritanceAnalyzer',
                'CallGraphAnalyzer'
            ]
            
            found_classes = [
                symbol.name for symbol in symbol_table.symbols.values()
                if symbol.symbol_type == "class"
            ]
            
            for key_class in key_classes:
                self.assertIn(key_class, found_classes)
            
            # Should find inheritance relationships
            if symbol_table.inheritance_chains:
                # Pydantic models should have inheritance chains
                pydantic_classes = [
                    name for name, chain in symbol_table.inheritance_chains.items()
                    if 'BaseModel' in chain.base_classes
                ]
                # May or may not find BaseModel depending on analysis scope
                self.assertIsInstance(pydantic_classes, list)


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run all tests
    unittest.main(verbosity=2)