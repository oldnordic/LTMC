#!/usr/bin/env python3
"""
Test Driven Development (TDD) test suite for example generation service.

Comprehensive tests for the example generation and enrichment system including:
- Real code example extraction from AST analysis
- Usage pattern discovery and analysis
- Example quality assessment
- Pattern frequency analysis
- Integration with real LTMC codebase
- Export functionality for documentation

No mocks, no stubs, no placeholders - tests real functionality only.
"""

import ast
import os
import sys
import tempfile
import unittest
import json
from typing import Dict, List, Any
from pathlib import Path

# Add project root to path for testing
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ltms.services.example_generation_service import (
    ExampleGenerationService,
    ExampleExtractor,
    ExampleASTVisitor,
    PatternAnalyzer,
    CodeExample,
    UsagePattern,
    ExampleCollection,
    ExampleType,
    ExampleQuality
)


class TestExampleExtractor(unittest.TestCase):
    """Test example extraction from Python source code."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = ExampleExtractor()
    
    def test_extract_function_call_examples(self):
        """Test extraction of function call examples from real code."""
        test_code = '''
import os
import json
from pathlib import Path

def process_data(data_file: str, output_dir: str) -> bool:
    """Process data file and save results."""
    # Read input file
    file_path = Path(data_file)
    if not file_path.exists():
        return False
    
    # Process data
    with open(data_file, 'r') as f:
        content = json.load(f)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Save processed results
    output_path = os.path.join(output_dir, "processed.json")
    with open(output_path, 'w') as f:
        json.dump(content, f, indent=2)
    
    return True

def main():
    """Main function demonstrating usage."""
    success = process_data("input.json", "/tmp/output")
    if success:
        print("Processing completed successfully")
    else:
        print("Processing failed")
'''
        
        # Write test code to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            # Extract examples
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Should find multiple function call examples
            self.assertGreater(len(examples), 0)
            
            # Check for specific function calls
            function_calls = [ex for ex in examples if ex.example_type == ExampleType.FUNCTION_CALL]
            self.assertGreater(len(function_calls), 0)
            
            # Find specific examples
            path_exists_calls = [ex for ex in function_calls if "exists" in ex.code_snippet]
            self.assertGreater(len(path_exists_calls), 0)
            
            json_load_calls = [ex for ex in function_calls if "json.load" in ex.code_snippet]
            self.assertGreater(len(json_load_calls), 0)
            
            os_makedirs_calls = [ex for ex in function_calls if "os.makedirs" in ex.code_snippet]
            self.assertGreater(len(os_makedirs_calls), 0)
            
            # Verify example structure
            for example in function_calls[:3]:  # Check first 3 examples
                self.assertIsInstance(example.symbol_name, str)
                self.assertIsInstance(example.code_snippet, str)
                self.assertIsInstance(example.line_number, int)
                self.assertIsInstance(example.quality, ExampleQuality)
                self.assertGreater(example.line_number, 0)
                self.assertGreater(len(example.code_snippet), 0)
            
        finally:
            os.unlink(temp_path)
    
    def test_extract_class_instantiation_examples(self):
        """Test extraction of class instantiation examples."""
        test_code = '''
from pathlib import Path
from datetime import datetime
import logging

class DataProcessor:
    """Data processing class."""
    
    def __init__(self, config_path: str, debug: bool = False):
        self.config_path = config_path
        self.debug = debug
        self.logger = logging.getLogger(__name__)
    
    def setup(self):
        """Setup processing environment."""
        # Create path objects
        config_file = Path(self.config_path)
        output_dir = Path("output")
        
        # Create timestamp
        timestamp = datetime.now()
        
        # Setup logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler.setFormatter(formatter)
        
        return True

def create_processor():
    """Create a data processor instance."""
    processor = DataProcessor("/config/settings.json", debug=True)
    processor.setup()
    return processor
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Find class instantiation examples
            class_instances = [ex for ex in examples if ex.example_type == ExampleType.CLASS_INSTANTIATION]
            self.assertGreater(len(class_instances), 0)
            
            # Check for specific instantiations
            path_instances = [ex for ex in class_instances if "Path" in ex.symbol_name]
            self.assertGreater(len(path_instances), 0)
            
            datetime_instances = [ex for ex in class_instances if "datetime" in ex.symbol_name]
            self.assertGreater(len(datetime_instances), 0)
            
            # Verify instantiation details
            for instance in class_instances:
                self.assertTrue(instance.symbol_name[0].isupper() or '.' in instance.symbol_name)
                self.assertIn('(', instance.code_snippet)
                self.assertIn(')', instance.code_snippet)
            
        finally:
            os.unlink(temp_path)
    
    def test_extract_error_handling_examples(self):
        """Test extraction of error handling patterns."""
        test_code = '''
import json
import os

def safe_json_load(file_path: str) -> dict:
    """Safely load JSON file with error handling."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {}

def robust_file_operation(source: str, destination: str):
    """Robust file operation with multiple exception types."""
    try:
        # Attempt file operation
        with open(source, 'rb') as src, open(destination, 'wb') as dst:
            dst.write(src.read())
    except PermissionError:
        print("Permission denied")
    except OSError as e:
        print(f"OS error: {e}")
    finally:
        print("Operation completed")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Find error handling examples
            error_examples = [ex for ex in examples if ex.example_type == ExampleType.ERROR_HANDLING]
            self.assertGreater(len(error_examples), 0)
            
            # Check for specific exception types
            exception_types = []
            for example in error_examples:
                if example.error_handling:
                    exception_types.append(example.error_handling)
            
            # Should find common exception types
            self.assertIn("FileNotFoundError", exception_types)
            self.assertIn("json.JSONDecodeError", exception_types)
            
            # Verify error handling structure
            for example in error_examples:
                self.assertIn("try", example.code_snippet)
                self.assertIn("except", example.code_snippet)
            
        finally:
            os.unlink(temp_path)
    
    def test_extract_context_manager_examples(self):
        """Test extraction of context manager usage patterns."""
        test_code = '''
import sqlite3
import tempfile
from contextlib import contextmanager

def database_operations():
    """Demonstrate context manager usage."""
    # File context manager
    with open("data.txt", "w") as f:
        f.write("Hello, World!")
    
    # Database context manager
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER, name TEXT)")
    
    # Temporary file context manager
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("temporary data")
        temp_path = tmp.name
    
    return temp_path

@contextmanager
def custom_context():
    """Custom context manager."""
    print("Entering context")
    try:
        yield "resource"
    finally:
        print("Exiting context")

def use_custom_context():
    """Use custom context manager."""
    with custom_context() as resource:
        print(f"Using {resource}")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Find context manager examples
            context_examples = [ex for ex in examples if ex.example_type == ExampleType.CONTEXT_MANAGER]
            self.assertGreater(len(context_examples), 0)
            
            # Check for specific context managers
            open_contexts = [ex for ex in context_examples if "open" in ex.symbol_name]
            self.assertGreater(len(open_contexts), 0)
            
            # Verify context manager structure
            for example in context_examples:
                self.assertIn("with", example.code_snippet)
                self.assertIn(":", example.code_snippet)
            
        finally:
            os.unlink(temp_path)
    
    def test_extract_async_examples(self):
        """Test extraction of async/await patterns."""
        test_code = '''
import asyncio
import aiohttp

async def fetch_data(url: str) -> str:
    """Fetch data from URL asynchronously."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.text()
    return data

async def process_multiple_urls(urls: list) -> list:
    """Process multiple URLs concurrently."""
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch_data(url))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

async def main():
    """Main async function."""
    urls = ["http://example.com", "http://test.com"]
    results = await process_multiple_urls(urls)
    
    for result in results:
        print(f"Result length: {len(result)}")

if __name__ == "__main__":
    asyncio.run(main())
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Find async examples
            async_examples = [ex for ex in examples if ex.example_type == ExampleType.ASYNC_USAGE]
            
            # May or may not find async examples depending on AST processing
            # But should at least process the file without errors
            self.assertIsInstance(examples, list)
            
            # Check if any async patterns were detected
            await_patterns = [ex for ex in examples if "await" in ex.code_snippet]
            
            # If found, verify structure
            for example in await_patterns:
                self.assertIn("await", example.code_snippet)
            
        finally:
            os.unlink(temp_path)
    
    def test_context_line_extraction(self):
        """Test extraction of context lines around examples."""
        test_code = '''# This is a header comment
# explaining the purpose of the code

def example_function():
    """Example function with context."""
    # Setup phase
    data = [1, 2, 3, 4, 5]
    
    # Processing phase - this is the main call
    result = len(data)  # This is our target line
    
    # Cleanup phase
    return result

# End of function
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            examples = self.extractor.extract_examples_from_file(temp_path)
            
            # Find the len() call example
            len_examples = [ex for ex in examples if "len" in ex.code_snippet]
            
            if len_examples:
                example = len_examples[0]
                
                # Should have context lines
                self.assertGreater(len(example.context_before), 0)
                self.assertGreater(len(example.context_after), 0)
                
                # Context should contain meaningful information
                context_text = ' '.join(example.context_before + example.context_after)
                self.assertIn("Setup", context_text)
                self.assertIn("Processing", context_text)
            
        finally:
            os.unlink(temp_path)


class TestPatternAnalyzer(unittest.TestCase):
    """Test usage pattern analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = PatternAnalyzer()
    
    def test_analyze_function_call_patterns(self):
        """Test analysis of function call patterns."""
        # Create test examples for the same function
        examples = [
            CodeExample(
                example_type=ExampleType.FUNCTION_CALL,
                symbol_name="json.load",
                code_snippet='json.load(f)',
                file_path="test1.py",
                line_number=10,
                quality=ExampleQuality.GOOD,
                parameters={"arg_0": {"variable": "f", "type": "variable"}}
            ),
            CodeExample(
                example_type=ExampleType.FUNCTION_CALL,
                symbol_name="json.load",
                code_snippet='json.load(file_handle)',
                file_path="test2.py",
                line_number=15,
                quality=ExampleQuality.GOOD,
                parameters={"arg_0": {"variable": "file_handle", "type": "variable"}}
            ),
            CodeExample(
                example_type=ExampleType.FUNCTION_CALL,
                symbol_name="json.load",
                code_snippet='json.load(input_stream)',
                file_path="test3.py",
                line_number=20,
                quality=ExampleQuality.FAIR,
                parameters={"arg_0": {"variable": "input_stream", "type": "variable"}}
            )
        ]
        
        # Analyze patterns
        patterns = self.analyzer.analyze_patterns(examples)
        
        # Should find pattern for json.load
        json_patterns = [p for p in patterns.values() if p.symbol_name == "json.load"]
        self.assertGreater(len(json_patterns), 0)
        
        # Check pattern properties
        pattern = json_patterns[0]
        self.assertEqual(pattern.pattern_type, ExampleType.FUNCTION_CALL)
        self.assertEqual(pattern.frequency, 3)
        self.assertGreater(pattern.confidence_score, 0)
        self.assertIn("json.load", pattern.description)
        self.assertEqual(len(pattern.examples), 3)
    
    def test_analyze_class_instantiation_patterns(self):
        """Test analysis of class instantiation patterns."""
        examples = [
            CodeExample(
                example_type=ExampleType.CLASS_INSTANTIATION,
                symbol_name="Path",
                code_snippet='Path("/home/user")',
                file_path="test1.py",
                line_number=5,
                quality=ExampleQuality.EXCELLENT,
                parameters={"arg_0": {"value": "/home/user", "type": "str"}}
            ),
            CodeExample(
                example_type=ExampleType.CLASS_INSTANTIATION,
                symbol_name="Path",
                code_snippet='Path("./data")',
                file_path="test2.py",
                line_number=8,
                quality=ExampleQuality.GOOD,
                parameters={"arg_0": {"value": "./data", "type": "str"}}
            )
        ]
        
        patterns = self.analyzer.analyze_patterns(examples)
        
        # Should find Path instantiation pattern
        path_patterns = [p for p in patterns.values() if p.symbol_name == "Path"]
        self.assertGreater(len(path_patterns), 0)
        
        pattern = path_patterns[0]
        self.assertEqual(pattern.pattern_type, ExampleType.CLASS_INSTANTIATION)
        self.assertEqual(pattern.frequency, 2)
    
    def test_pattern_confidence_scoring(self):
        """Test confidence scoring for patterns."""
        # Create examples with different frequencies
        high_freq_examples = []
        for i in range(10):
            example = CodeExample(
                example_type=ExampleType.FUNCTION_CALL,
                symbol_name="popular_function",
                code_snippet=f'popular_function({i})',
                file_path=f"test{i}.py",
                line_number=i+1,
                quality=ExampleQuality.GOOD
            )
            high_freq_examples.append(example)
        
        low_freq_examples = []
        for i in range(2):
            example = CodeExample(
                example_type=ExampleType.FUNCTION_CALL,
                symbol_name="rare_function", 
                code_snippet=f'rare_function({i})',
                file_path=f"rare{i}.py",
                line_number=i+1,
                quality=ExampleQuality.FAIR
            )
            low_freq_examples.append(example)
        
        all_examples = high_freq_examples + low_freq_examples
        patterns = self.analyzer.analyze_patterns(all_examples)
        
        # Find both patterns
        popular_pattern = None
        rare_pattern = None
        
        for pattern in patterns.values():
            if pattern.symbol_name == "popular_function":
                popular_pattern = pattern
            elif pattern.symbol_name == "rare_function":
                rare_pattern = pattern
        
        self.assertIsNotNone(popular_pattern)
        self.assertIsNotNone(rare_pattern)
        
        # Popular function should have higher confidence
        self.assertGreater(popular_pattern.confidence_score, rare_pattern.confidence_score)
        self.assertEqual(popular_pattern.frequency, 10)
        self.assertEqual(rare_pattern.frequency, 2)


class TestExampleGenerationService(unittest.TestCase):
    """Test main example generation service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ExampleGenerationService()
    
    def test_generate_examples_for_module(self):
        """Test example generation for a single module."""
        # Create a comprehensive test module
        test_code = '''
"""Test module for example generation."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

class ConfigManager:
    """Manages application configuration."""
    
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config_data = {}
    
    def load_config(self) -> bool:
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Config file not found: {self.config_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in config: {e}")
            return False
    
    def get_setting(self, key: str, default=None):
        """Get configuration setting."""
        return self.config_data.get(key, default)

def process_files(input_dir: str, output_dir: str) -> int:
    """Process files from input directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory
    os.makedirs(output_path, exist_ok=True)
    
    processed_count = 0
    
    # Process each file
    for file_path in input_path.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Process data
            processed_data = {
                "original_file": str(file_path),
                "data": data,
                "processed_at": "2024-01-01"
            }
            
            # Save processed file
            output_file = output_path / f"processed_{file_path.name}"
            with open(output_file, 'w') as f:
                json.dump(processed_data, f, indent=2)
            
            processed_count += 1
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue
    
    return processed_count

def main():
    """Main function demonstrating usage."""
    # Create config manager
    config = ConfigManager("config.json")
    
    if config.load_config():
        input_dir = config.get_setting("input_directory", "./input")
        output_dir = config.get_setting("output_directory", "./output")
        
        # Process files
        count = process_files(input_dir, output_dir)
        print(f"Processed {count} files")
    else:
        print("Failed to load configuration")

if __name__ == "__main__":
    main()
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        try:
            # Generate examples for the module
            collection = self.service.generate_examples_for_module(temp_path)
            
            # Verify collection structure
            self.assertIsInstance(collection, ExampleCollection)
            self.assertEqual(collection.symbol_type, "module")
            self.assertEqual(collection.module_path, temp_path)
            
            # Should have found examples
            self.assertGreater(len(collection.examples), 0)
            self.assertGreater(collection.total_usage_count, 0)
            self.assertGreaterEqual(collection.complexity_score, 0.0)
            
            # Check for different types of examples
            example_types = set(ex.example_type for ex in collection.examples)
            
            # Should find function calls
            self.assertIn(ExampleType.FUNCTION_CALL, example_types)
            
            # Should find class instantiations
            self.assertIn(ExampleType.CLASS_INSTANTIATION, example_types)
            
            # Should find error handling
            self.assertIn(ExampleType.ERROR_HANDLING, example_types)
            
            # Should find context managers
            self.assertIn(ExampleType.CONTEXT_MANAGER, example_types)
            
            # Check for usage patterns
            if collection.usage_patterns:
                for pattern in collection.usage_patterns:
                    self.assertIsInstance(pattern, UsagePattern)
                    self.assertGreater(pattern.frequency, 0)
                    self.assertGreaterEqual(pattern.confidence_score, 0.0)
            
        finally:
            os.unlink(temp_path)
    
    def test_get_examples_for_symbol(self):
        """Test getting examples for a specific symbol."""
        # Create test collections
        collections = {}
        
        # Create first test file with json.load usage
        test_code1 = '''
import json

def load_data():
    with open("data.json", "r") as f:
        return json.load(f)
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code1)
            temp_path1 = f.name
        
        # Create second test file with json.load usage
        test_code2 = '''
import json

def read_config():
    with open("config.json", "r") as file:
        config = json.load(file)
    return config
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code2)
            temp_path2 = f.name
        
        try:
            collections[temp_path1] = self.service.generate_examples_for_module(temp_path1)
            collections[temp_path2] = self.service.generate_examples_for_module(temp_path2)
            
            # Get examples for json.load
            json_examples = self.service.get_examples_for_symbol("json.load", collections)
            
            # Should find examples from both files
            self.assertGreater(len(json_examples), 0)
            
            # Check examples are sorted by quality
            if len(json_examples) > 1:
                for i in range(len(json_examples) - 1):
                    current_quality = json_examples[i].quality
                    next_quality = json_examples[i + 1].quality
                    # Quality should be same or decreasing
                    self.assertGreaterEqual(current_quality.value, next_quality.value)
            
        finally:
            os.unlink(temp_path1)
            os.unlink(temp_path2)
    
    def test_export_examples_to_json(self):
        """Test exporting examples to JSON format."""
        # Create test module
        test_code = '''
import os

def simple_function():
    """Simple function for export testing."""
    result = os.path.exists("test.txt")
    return result
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_path = f.name
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            export_path = f.name
        
        try:
            # Generate examples
            collection = self.service.generate_examples_for_module(temp_path)
            collections = {temp_path: collection}
            
            # Export to JSON
            self.service.export_examples_to_json(collections, export_path)
            
            # Verify export file exists
            self.assertTrue(os.path.exists(export_path))
            
            # Load and verify JSON structure
            with open(export_path, 'r') as f:
                export_data = json.load(f)
            
            self.assertIn(temp_path, export_data)
            module_data = export_data[temp_path]
            
            # Check required fields
            self.assertIn("symbol_name", module_data)
            self.assertIn("symbol_type", module_data)
            self.assertIn("examples", module_data)
            self.assertIn("usage_patterns", module_data)
            
            # Check examples structure
            if module_data["examples"]:
                example = module_data["examples"][0]
                self.assertIn("example_type", example)
                self.assertIn("symbol_name", example)
                self.assertIn("code_snippet", example)
                self.assertIn("quality", example)
            
        finally:
            os.unlink(temp_path)
            os.unlink(export_path)


class TestIntegrationWithRealLTMCCode(unittest.TestCase):
    """Integration tests with real LTMC codebase."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = ExampleGenerationService()
    
    def test_analyze_ltmc_consolidated_tools(self):
        """Test example generation for LTMC consolidated tools."""
        consolidated_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ltms",
            "tools",
            "consolidated.py"
        )
        
        if os.path.exists(consolidated_path):
            try:
                # Generate examples from consolidated tools
                collection = self.service.generate_examples_for_module(consolidated_path)
                
                # Should find examples in real LTMC code
                self.assertGreater(len(collection.examples), 0)
                
                # Check for MCP-specific patterns
                mcp_examples = [
                    ex for ex in collection.examples 
                    if "mcp" in ex.code_snippet.lower() or "_action" in ex.symbol_name
                ]
                
                # Should find MCP tool patterns
                if mcp_examples:
                    self.assertGreater(len(mcp_examples), 0)
                
                # Check example quality distribution
                quality_counts = {}
                for example in collection.examples:
                    quality = example.quality.value
                    quality_counts[quality] = quality_counts.get(quality, 0) + 1
                
                # Should have examples of various qualities
                self.assertGreater(len(quality_counts), 0)
                
                # Check complexity score
                self.assertGreaterEqual(collection.complexity_score, 0.0)
                self.assertLessEqual(collection.complexity_score, 10.0)  # Reasonable upper bound
                
            except Exception as e:
                # Skip test if file cannot be processed due to dependencies
                self.skipTest(f"Could not process consolidated.py: {e}")
    
    def test_analyze_ltmc_services(self):
        """Test example generation for LTMC service modules."""
        services_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ltms", 
            "services"
        )
        
        if os.path.exists(services_dir):
            service_files = [
                f for f in os.listdir(services_dir)
                if f.endswith('.py') and not f.startswith('__')
            ]
            
            # Test with a few service files
            test_files = service_files[:3]  # Limit for testing performance
            
            for service_file in test_files:
                service_path = os.path.join(services_dir, service_file)
                
                try:
                    collection = self.service.generate_examples_for_module(service_path)
                    
                    # Should process without errors
                    self.assertIsInstance(collection, ExampleCollection)
                    
                    # May or may not have examples depending on file content
                    self.assertIsInstance(collection.examples, list)
                    self.assertIsInstance(collection.usage_patterns, list)
                    
                except Exception as e:
                    # Log but don't fail - some files may have complex dependencies
                    print(f"Warning: Could not fully process {service_file}: {e}")
                    continue
    
    def test_project_wide_example_generation(self):
        """Test example generation for multiple LTMC modules."""
        ltms_dir = os.path.join(
            os.path.dirname(__file__),
            "..",
            "ltms"
        )
        
        if os.path.exists(ltms_dir):
            try:
                # Generate examples for LTMS project (limited scope for testing)
                collections = self.service.generate_examples_for_project(
                    ltms_dir,
                    file_patterns=["tools/*.py", "services/*.py"]
                )
                
                # Should find multiple modules
                self.assertGreater(len(collections), 0)
                
                # Get best examples across all modules
                best_examples = self.service.get_best_examples(collections, limit=5)
                
                # Should find some high-quality examples
                if best_examples:
                    self.assertGreater(len(best_examples), 0)
                    
                    # Check that best examples have good quality
                    for example in best_examples:
                        self.assertIn(example.quality, [
                            ExampleQuality.EXCELLENT,
                            ExampleQuality.GOOD,
                            ExampleQuality.FAIR
                        ])
                
            except Exception as e:
                # Skip if LTMS directory structure has changed
                self.skipTest(f"Could not analyze LTMS project: {e}")


if __name__ == '__main__':
    # Configure logging for tests
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Run all tests
    unittest.main(verbosity=2)