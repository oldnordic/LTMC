#!/usr/bin/env python3
"""
TDD Test for summarize_code MCP Tool Integration

This test ensures summarize_code is implemented as a real, first-class
LTMC MCP tool with actual AST-based analysis and natural language summarization.

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


class TestSummarizeCodeTDD(unittest.TestCase):
    """Test summarize_code tool implementation following TDD principles."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_small_python_code = '''
"""Simple Python module for testing."""

import os
import sys

# Global constant
MAX_ITEMS = 100

def calculate_sum(numbers):
    """Calculate sum of numbers."""
    return sum(numbers)

class Calculator:
    """Basic calculator class."""
    
    def __init__(self):
        self.result = 0
    
    def add(self, x, y):
        """Add two numbers."""
        return x + y
'''

        self.test_large_python_code = '''
#!/usr/bin/env python3
"""
Advanced data processing module for scientific calculations.

This module provides comprehensive data analysis tools including
statistical functions, data validation, and complex mathematical operations.

Authors: Data Science Team
Version: 2.1.0
License: MIT
"""

import os
import sys
import math
import logging
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global constants
DEFAULT_PRECISION = 1e-6
MAX_ITERATIONS = 1000
SUPPORTED_FORMATS = ['csv', 'json', 'xml']

# TODO: Add support for parquet format
# FIXME: Optimize memory usage for large datasets

@dataclass
class DataPoint:
    """Represents a single data point with metadata."""
    value: float
    timestamp: str
    quality: str = "good"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DataProcessor(ABC):
    """Abstract base class for data processors."""
    
    @abstractmethod
    def process(self, data: List[DataPoint]) -> Dict[str, Any]:
        """Process data and return results."""
        pass
    
    @abstractmethod
    def validate(self, data: List[DataPoint]) -> bool:
        """Validate input data."""
        pass

class StatisticalProcessor(DataProcessor):
    """Statistical analysis processor."""
    
    def __init__(self, precision: float = DEFAULT_PRECISION):
        """Initialize processor with precision setting."""
        self.precision = precision
        self.processed_count = 0
        self._cache = {}
        logger.info(f"Initialized StatisticalProcessor with precision {precision}")
    
    def process(self, data: List[DataPoint]) -> Dict[str, Any]:
        """
        Process statistical data and calculate metrics.
        
        Args:
            data: List of DataPoint objects to process
            
        Returns:
            Dictionary containing statistical metrics
            
        Raises:
            ValueError: If data is empty or invalid
        """
        if not data:
            raise ValueError("Data cannot be empty")
        
        if not self.validate(data):
            raise ValueError("Data validation failed")
        
        values = [dp.value for dp in data]
        
        # Calculate basic statistics
        n = len(values)
        mean = sum(values) / n
        variance = sum((x - mean) ** 2 for x in values) / n
        std_dev = math.sqrt(variance)
        
        # Calculate quartiles
        sorted_values = sorted(values)
        q1 = self._calculate_quartile(sorted_values, 0.25)
        q2 = self._calculate_quartile(sorted_values, 0.5)  # median
        q3 = self._calculate_quartile(sorted_values, 0.75)
        
        self.processed_count += 1
        
        results = {
            'count': n,
            'mean': round(mean, 6),
            'variance': round(variance, 6),
            'std_dev': round(std_dev, 6),
            'min': min(values),
            'max': max(values),
            'q1': round(q1, 6),
            'median': round(q2, 6),
            'q3': round(q3, 6),
            'processed_by': self.__class__.__name__,
            'processing_count': self.processed_count
        }
        
        logger.info(f"Processed {n} data points successfully")
        return results
    
    def validate(self, data: List[DataPoint]) -> bool:
        """
        Validate data points for statistical processing.
        
        Args:
            data: List of DataPoint objects to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        if not data:
            return False
        
        for dp in data:
            if not isinstance(dp, DataPoint):
                logger.warning("Invalid data point type found")
                return False
            
            if not isinstance(dp.value, (int, float)):
                logger.warning(f"Invalid value type: {type(dp.value)}")
                return False
            
            if math.isnan(dp.value) or math.isinf(dp.value):
                logger.warning("NaN or Inf value detected")
                return False
        
        return True
    
    def _calculate_quartile(self, sorted_values: List[float], percentile: float) -> float:
        """Calculate quartile value."""
        n = len(sorted_values)
        index = percentile * (n - 1)
        
        if index.is_integer():
            return sorted_values[int(index)]
        else:
            lower = sorted_values[int(index)]
            upper = sorted_values[int(index) + 1]
            fraction = index - int(index)
            return lower + fraction * (upper - lower)
    
    @staticmethod
    def calculate_correlation(x_values: List[float], y_values: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x_values) != len(y_values):
            raise ValueError("Input lists must have same length")
        
        n = len(x_values)
        if n < 2:
            raise ValueError("Need at least 2 data points")
        
        # Calculate means
        x_mean = sum(x_values) / n
        y_mean = sum(y_values) / n
        
        # Calculate correlation
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        x_var = sum((x - x_mean) ** 2 for x in x_values)
        y_var = sum((y - y_mean) ** 2 for y in y_values)
        
        denominator = math.sqrt(x_var * y_var)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator

class DataLoader:
    """Utility class for loading data from various sources."""
    
    def __init__(self, format_type: str = 'csv'):
        """Initialize loader with format type."""
        if format_type not in SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {format_type}")
        
        self.format_type = format_type
        self.loaded_files = []
    
    def load_from_file(self, file_path: str) -> List[DataPoint]:
        """
        Load data from file based on format type.
        
        Args:
            file_path: Path to the data file
            
        Returns:
            List of DataPoint objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        self.loaded_files.append(file_path)
        
        # Simplified loading logic for testing
        # In real implementation, would parse actual file formats
        data_points = []
        
        if self.format_type == 'csv':
            data_points = self._load_csv(file_path)
        elif self.format_type == 'json':
            data_points = self._load_json(file_path)
        elif self.format_type == 'xml':
            data_points = self._load_xml(file_path)
        
        logger.info(f"Loaded {len(data_points)} data points from {file_path}")
        return data_points
    
    def _load_csv(self, file_path: str) -> List[DataPoint]:
        """Load data from CSV file."""
        # Placeholder implementation
        return []
    
    def _load_json(self, file_path: str) -> List[DataPoint]:
        """Load data from JSON file.""" 
        # Placeholder implementation
        return []
    
    def _load_xml(self, file_path: str) -> List[DataPoint]:
        """Load data from XML file."""
        # Placeholder implementation
        return []

# Utility functions
def create_sample_data(count: int = 100) -> List[DataPoint]:
    """Create sample data for testing."""
    import random
    
    data_points = []
    for i in range(count):
        value = random.gauss(50, 15)  # Normal distribution
        timestamp = f"2024-01-{(i % 30) + 1:02d}T{(i % 24):02d}:00:00"
        quality = "good" if random.random() > 0.1 else "poor"
        
        dp = DataPoint(
            value=value,
            timestamp=timestamp,
            quality=quality,
            metadata={"source": "synthetic", "batch": i // 10}
        )
        data_points.append(dp)
    
    return data_points

def export_results(results: Dict[str, Any], output_path: str):
    """Export processing results to file."""
    import json
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results exported to {output_path}")

# Main execution
if __name__ == "__main__":
    # Example usage
    processor = StatisticalProcessor(precision=1e-8)
    sample_data = create_sample_data(50)
    
    try:
        results = processor.process(sample_data)
        export_results(results, "analysis_results.json")
        print(f"Analysis complete. Processed {results['count']} data points.")
        print(f"Mean: {results['mean']}, Std Dev: {results['std_dev']}")
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)
'''

        self.test_javascript_code = '''
/**
 * Advanced JavaScript module for web application utilities
 * @fileoverview Comprehensive utility functions for DOM manipulation and API handling
 * @author Frontend Team
 * @version 3.2.1
 */

// Import external dependencies
const axios = require('axios');
const moment = require('moment');

// Configuration constants
const CONFIG = {
    API_BASE_URL: 'https://api.example.com',
    TIMEOUT: 5000,
    RETRY_ATTEMPTS: 3
};

// TODO: Add WebSocket support
// FIXME: Optimize DOM queries for better performance

/**
 * Utility class for DOM manipulation and event handling
 * @class DOMUtils
 */
class DOMUtils {
    /**
     * Create a new DOMUtils instance
     * @param {HTMLElement} container - Root container element
     */
    constructor(container = document.body) {
        this.container = container;
        this.eventListeners = new Map();
        this.initialized = false;
    }
    
    /**
     * Initialize the utility with default settings
     */
    init() {
        if (this.initialized) {
            console.warn('DOMUtils already initialized');
            return;
        }
        
        this.setupGlobalListeners();
        this.initialized = true;
        console.log('DOMUtils initialized successfully');
    }
    
    /**
     * Create and append an element to the container
     * @param {string} tagName - HTML tag name
     * @param {Object} attributes - Element attributes
     * @param {string} textContent - Text content
     * @returns {HTMLElement} Created element
     */
    createElement(tagName, attributes = {}, textContent = '') {
        const element = document.createElement(tagName);
        
        // Set attributes
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'style' && typeof value === 'object') {
                Object.assign(element.style, value);
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (textContent) {
            element.textContent = textContent;
        }
        
        return element;
    }
    
    /**
     * Setup global event listeners
     * @private
     */
    setupGlobalListeners() {
        // Global click handler for delegation
        this.container.addEventListener('click', this.handleGlobalClick.bind(this));
        
        // Window resize handler
        window.addEventListener('resize', this.debounce(this.handleResize.bind(this), 250));
        
        // Storage for cleanup
        this.eventListeners.set('global-click', this.handleGlobalClick.bind(this));
        this.eventListeners.set('global-resize', this.handleResize.bind(this));
    }
    
    /**
     * Handle global click events with delegation
     * @param {Event} event - Click event
     * @private
     */
    handleGlobalClick(event) {
        const target = event.target;
        
        // Handle button clicks
        if (target.matches('[data-action]')) {
            const action = target.dataset.action;
            this.executeAction(action, target, event);
        }
        
        // Handle modal triggers
        if (target.matches('[data-modal]')) {
            const modalId = target.dataset.modal;
            this.showModal(modalId);
        }
    }
    
    /**
     * Execute a registered action
     * @param {string} actionName - Name of the action
     * @param {HTMLElement} element - Target element
     * @param {Event} event - Original event
     */
    executeAction(actionName, element, event) {
        console.log(`Executing action: ${actionName}`);
        
        switch (actionName) {
            case 'toggle-class':
                this.toggleClass(element);
                break;
            case 'submit-form':
                this.submitForm(element);
                break;
            case 'load-content':
                this.loadContent(element);
                break;
            default:
                console.warn(`Unknown action: ${actionName}`);
        }
    }
    
    /**
     * Debounce function execution
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in milliseconds
     * @returns {Function} Debounced function
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func.apply(this, args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

/**
 * API client class for handling HTTP requests
 * @class APIClient
 */
class APIClient {
    /**
     * Create a new API client
     * @param {string} baseURL - Base URL for API requests
     * @param {Object} defaultHeaders - Default headers for requests
     */
    constructor(baseURL = CONFIG.API_BASE_URL, defaultHeaders = {}) {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            ...defaultHeaders
        };
        this.requestInterceptors = [];
        this.responseInterceptors = [];
    }
    
    /**
     * Make a GET request
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise} Request promise
     */
    async get(endpoint, params = {}) {
        const url = this.buildURL(endpoint, params);
        
        try {
            const response = await this.makeRequest('GET', url);
            return response.data;
        } catch (error) {
            console.error(`GET request failed: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Make a POST request
     * @param {string} endpoint - API endpoint
     * @param {Object} data - Request payload
     * @returns {Promise} Request promise
     */
    async post(endpoint, data = {}) {
        const url = this.buildURL(endpoint);
        
        try {
            const response = await this.makeRequest('POST', url, data);
            return response.data;
        } catch (error) {
            console.error(`POST request failed: ${error.message}`);
            throw error;
        }
    }
    
    /**
     * Build full URL with query parameters
     * @param {string} endpoint - API endpoint
     * @param {Object} params - Query parameters
     * @returns {string} Complete URL
     * @private
     */
    buildURL(endpoint, params = {}) {
        const url = new URL(endpoint, this.baseURL);
        
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined) {
                url.searchParams.append(key, value);
            }
        });
        
        return url.toString();
    }
    
    /**
     * Make HTTP request with retry logic
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object} data - Request data
     * @returns {Promise} Request promise
     * @private
     */
    async makeRequest(method, url, data = null) {
        let lastError;
        
        for (let attempt = 1; attempt <= CONFIG.RETRY_ATTEMPTS; attempt++) {
            try {
                const config = {
                    method,
                    url,
                    headers: this.defaultHeaders,
                    timeout: CONFIG.TIMEOUT
                };
                
                if (data && method !== 'GET') {
                    config.data = data;
                }
                
                const response = await axios(config);
                return response;
                
            } catch (error) {
                lastError = error;
                console.warn(`Request attempt ${attempt} failed: ${error.message}`);
                
                if (attempt < CONFIG.RETRY_ATTEMPTS) {
                    await this.delay(1000 * attempt); // Exponential backoff
                }
            }
        }
        
        throw lastError;
    }
    
    /**
     * Delay execution for specified milliseconds
     * @param {number} ms - Milliseconds to delay
     * @returns {Promise} Delay promise
     * @private
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Utility functions
function formatDate(date, format = 'YYYY-MM-DD') {
    return moment(date).format(format);
}

function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export for use in other modules
module.exports = {
    DOMUtils,
    APIClient,
    formatDate,
    generateUUID,
    throttle,
    CONFIG
};
'''

        self.test_python_no_docstrings = '''
import os
import sys

MAX_COUNT = 50

def process_data(items):
    result = []
    for item in items:
        if item > 0:
            result.append(item * 2)
    return result

class Handler:
    def __init__(self):
        self.items = []
    
    def add_item(self, item):
        self.items.append(item)
    
    def process_all(self):
        return process_data(self.items)

def main():
    handler = Handler()
    handler.add_item(10)
    handler.add_item(20)
    print(handler.process_all())

if __name__ == "__main__":
    main()
'''

        self.test_edge_case_code = '''
# -*- coding: utf-8 -*-

"""Edge case module with unusual patterns."""

import sys; import os; import re  # Multiple imports on one line

# Unusual class definition
class   WeirdSpacing   :
    """Class with weird spacing."""
    
    def method_with_complex_args(self, *args, **kwargs):
        pass
    
    @property
    def strange_property(self):
        return lambda x: x ** 2
    
    class NestedClass:
        def nested_method(self):
            def inner_function():
                return "nested"
            return inner_function()

# Functions with decorators
@staticmethod
def standalone_static():
    return "static"

@classmethod
def standalone_class_method(cls):
    return cls

# Complex lambda and generator expressions
process = lambda data: (x for x in data if x % 2 == 0)
result = [func(x) for func in [lambda a: a*2, lambda b: b+1] for x in range(5)]

# Unusual string patterns
multiline_string = """
This is a multiline string
that might confuse parsers
with its """ + "concatenation"

# Global variables with complex expressions
COMPLEX_DICT = {
    'key1': [i for i in range(10) if i % 2],
    'key2': {j: j**2 for j in range(5)},
    'key3': lambda: print("lambda in dict")
}
'''

    def test_summarize_code_tool_exists_in_all_tools(self):
        """Test that summarize_code tool is registered in ALL_TOOLS."""
        self.assertIn('summarize_code', ALL_TOOLS, 
                     "summarize_code must be registered in ALL_TOOLS registry")
        
    def test_summarize_code_tool_has_required_structure(self):
        """Test that summarize_code tool has proper MCP tool structure."""
        tool = ALL_TOOLS['summarize_code']
        
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
        
    def test_summarize_code_schema_validation(self):
        """Test summarize_code schema has correct parameters."""
        schema = ALL_TOOLS['summarize_code']['schema']
        properties = schema['properties']
        required = schema['required']
        
        # Test required parameters
        self.assertIn('source_code', required, "source_code must be required")
        self.assertIn('source_code', properties)
        
        # Test optional parameters exist
        optional_params = ['file_path', 'language', 'include_complexity', 
                          'summary_length', 'include_todos']
        for param in optional_params:
            self.assertIn(param, properties, f"{param} must be in schema properties")
            
        # Test parameter types
        self.assertEqual(properties['source_code']['type'], 'string')
        self.assertEqual(properties['include_complexity']['type'], 'boolean')
        self.assertEqual(properties['include_todos']['type'], 'boolean')
        self.assertEqual(properties['summary_length']['type'], 'string')
        
    def test_summarize_small_python_code(self):
        """Test summarize_code with small Python code sample."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Execute real code summarization
        result = handler(
            source_code=self.test_small_python_code,
            file_path="small_test.py",
            language="python",
            include_complexity=True,
            include_todos=True
        )
        
        # Test response structure
        self.assertIsInstance(result, dict, "Result must be a dictionary")
        self.assertIn('success', result, "Result must include success status")
        self.assertTrue(result['success'], "Summarization must succeed")
        
        # Test required sections
        required_sections = ['module_purpose', 'structure', 'statistics', 
                           'summary', 'metadata']
        for section in required_sections:
            self.assertIn(section, result, f"Result must include {section}")
        
        # Test module_purpose
        module_purpose = result['module_purpose']
        self.assertIsInstance(module_purpose, str)
        self.assertGreater(len(module_purpose), 0, "Module purpose must not be empty")
        
        # Test structure
        structure = result['structure']
        self.assertIn('functions', structure)
        self.assertIn('classes', structure)
        self.assertIn('imports', structure)
        
        functions = structure['functions']
        self.assertIsInstance(functions, list)
        self.assertGreater(len(functions), 0, "Should detect functions")
        
        # Test function structure
        func = functions[0]
        self.assertIn('name', func)
        self.assertIn('line_start', func)
        self.assertIn('signature', func)
        
        classes = structure['classes']
        self.assertIsInstance(classes, list)
        self.assertGreater(len(classes), 0, "Should detect classes")
        
        # Test class structure
        cls = classes[0]
        self.assertIn('name', cls)
        self.assertIn('line_start', cls)
        self.assertIn('methods', cls)
        
        # Test statistics
        statistics = result['statistics']
        self.assertIn('lines_of_code', statistics)
        self.assertIn('function_count', statistics)
        self.assertIn('class_count', statistics)
        self.assertIn('import_count', statistics)
        
        self.assertGreater(statistics['lines_of_code'], 0)
        self.assertGreater(statistics['function_count'], 0)
        self.assertGreater(statistics['class_count'], 0)
        
        # Test summary
        summary = result['summary']
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 50, "Summary should be descriptive")
        
        # Test metadata
        metadata = result['metadata']
        self.assertIn('language', metadata)
        self.assertIn('file_path', metadata)
        self.assertIn('processing_time', metadata)
        self.assertEqual(metadata['language'], 'python')
        
    def test_summarize_large_python_code(self):
        """Test summarize_code with large Python code sample."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        result = handler(
            source_code=self.test_large_python_code,
            file_path="large_test.py",
            language="python",
            include_complexity=True,
            include_todos=True,
            summary_length="detailed"
        )
        
        self.assertTrue(result['success'])
        
        # Test detailed analysis for large code
        structure = result['structure']
        
        # Should detect multiple classes
        classes = structure['classes']
        self.assertGreater(len(classes), 2, "Should detect multiple classes")
        
        # Should detect class hierarchy
        abstract_classes = [c for c in classes if c.get('is_abstract', False)]
        self.assertGreater(len(abstract_classes), 0, "Should detect abstract classes")
        
        # Should detect inheritance
        inheritance_found = any(c.get('inheritance', {}).get('parents') for c in classes)
        self.assertTrue(inheritance_found, "Should detect inheritance relationships")
        
        # Should detect decorators
        decorated_functions = [f for f in structure['functions'] 
                              if f.get('decorators') and len(f['decorators']) > 0]
        self.assertGreater(len(decorated_functions), 0, "Should detect decorated functions")
        
        # Test TODOs detection
        if 'todos' in result:
            todos = result['todos']
            self.assertGreater(len(todos), 0, "Should detect TODO comments")
            self.assertTrue(any('TODO' in t['type'] for t in todos))
        
        # Test comprehensive statistics
        statistics = result['statistics']
        self.assertGreater(statistics['lines_of_code'], 100, "Large file should have many LOC")
        self.assertGreater(statistics['function_count'], 5, "Should have multiple functions")
        
        # Test detailed summary
        summary = result['summary']
        self.assertGreater(len(summary), 200, "Detailed summary should be comprehensive")
        
    def test_summarize_javascript_code(self):
        """Test summarize_code with JavaScript code."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        result = handler(
            source_code=self.test_javascript_code,
            file_path="test.js",
            language="javascript",
            include_complexity=True
        )
        
        self.assertTrue(result['success'])
        
        # Test JavaScript-specific analysis
        structure = result['structure']
        
        # Test classes detection
        classes = structure['classes']
        self.assertGreater(len(classes), 0, "Should detect JavaScript classes")
        
        # Test methods detection
        for cls in classes:
            if cls['name'] == 'DOMUtils':
                methods = cls['methods']
                self.assertGreater(len(methods), 3, "DOMUtils should have multiple methods")
                method_names = [m['name'] for m in methods]
                self.assertIn('constructor', method_names)
                self.assertIn('init', method_names)
        
        # Test functions detection
        functions = structure['functions']
        self.assertGreater(len(functions), 0, "Should detect utility functions")
        
        # Test JSDoc detection if included
        metadata = result['metadata']
        self.assertEqual(metadata['language'], 'javascript')
        
        # Test summary contains JavaScript-specific terms
        summary = result['summary']
        js_terms = ['JavaScript', 'class', 'function', 'async', 'module']
        has_js_terms = any(term.lower() in summary.lower() for term in js_terms)
        self.assertTrue(has_js_terms, "Summary should contain JavaScript-specific terms")
        
    def test_summarize_code_without_docstrings(self):
        """Test summarize_code with code that lacks docstrings."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        result = handler(
            source_code=self.test_python_no_docstrings,
            language="python"
        )
        
        self.assertTrue(result['success'])
        
        # Should still analyze structure even without docstrings
        structure = result['structure']
        self.assertGreater(len(structure['functions']), 0)
        self.assertGreater(len(structure['classes']), 0)
        
        # Summary should acknowledge lack of documentation
        summary = result['summary']
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 30, "Should provide meaningful summary even without docs")
        
        # Module purpose might be minimal but should exist
        module_purpose = result['module_purpose']
        self.assertIsInstance(module_purpose, str)
        
    def test_summarize_edge_case_code(self):
        """Test summarize_code with edge cases and unusual patterns."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        result = handler(
            source_code=self.test_edge_case_code,
            language="python",
            include_complexity=True
        )
        
        self.assertTrue(result['success'])
        
        structure = result['structure']
        
        # Should handle unusual class spacing
        classes = structure['classes']
        weird_class = next((c for c in classes if 'WeirdSpacing' in c['name']), None)
        self.assertIsNotNone(weird_class, "Should detect class with weird spacing")
        
        # Should detect nested classes
        nested_classes = [c for c in classes if 'Nested' in c['name']]
        self.assertGreater(len(nested_classes), 0, "Should detect nested classes")
        
        # Should handle complex expressions gracefully
        statistics = result['statistics']
        self.assertGreater(statistics['lines_of_code'], 0)
        
        # Summary should handle unusual code patterns
        summary = result['summary']
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 20)
        
    def test_summarize_code_language_detection(self):
        """Test automatic language detection."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test with Python code and auto detection
        result = handler(
            source_code=self.test_small_python_code,
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
        
    def test_summarize_code_complexity_analysis(self):
        """Test complexity analysis inclusion."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test with complexity analysis enabled
        result = handler(
            source_code=self.test_large_python_code,
            include_complexity=True
        )
        
        self.assertTrue(result['success'])
        
        # Should include complexity metrics
        if 'complexity' in result:
            complexity = result['complexity']
            self.assertIn('average_function_complexity', complexity)
            self.assertIn('max_complexity', complexity)
            self.assertIsInstance(complexity['average_function_complexity'], (int, float))
        
        # Functions should have complexity info
        structure = result['structure']
        functions = structure['functions']
        if functions:
            func = functions[0]
            if 'complexity' in func:
                self.assertIn('cyclomatic', func['complexity'])
        
    def test_summarize_code_summary_length_options(self):
        """Test different summary length options."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test brief summary
        result_brief = handler(
            source_code=self.test_large_python_code,
            summary_length="brief"
        )
        
        self.assertTrue(result_brief['success'])
        brief_summary = result_brief['summary']
        
        # Test detailed summary
        result_detailed = handler(
            source_code=self.test_large_python_code,
            summary_length="detailed"
        )
        
        self.assertTrue(result_detailed['success'])
        detailed_summary = result_detailed['summary']
        
        # Detailed should be longer than brief
        self.assertGreater(len(detailed_summary), len(brief_summary),
                          "Detailed summary should be longer than brief")
        
    def test_summarize_code_error_handling(self):
        """Test error handling with invalid code."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test with malformed Python code
        result = handler(
            source_code="def broken_function(\n    # incomplete syntax",
            language="python"
        )
        
        # Should handle gracefully
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        # May succeed with partial analysis or fail gracefully
        
    def test_summarize_code_empty_code(self):
        """Test summarize_code with empty or minimal code."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test with empty code
        result = handler(source_code="")
        self.assertTrue(result['success'])
        self.assertEqual(result['statistics']['lines_of_code'], 0)
        
        # Test with only comments
        result = handler(source_code="# Just a comment\n# Another comment")
        self.assertTrue(result['success'])
        
        # Test with only imports
        result = handler(source_code="import os\nimport sys")
        self.assertTrue(result['success'])
        imports = result['structure']['imports']
        self.assertGreater(len(imports), 0)
        
    def test_summarize_code_performance_requirements(self):
        """Test performance requirements are met."""
        import time
        
        handler = ALL_TOOLS['summarize_code']['handler']
        
        start_time = time.time()
        result = handler(
            source_code=self.test_large_python_code,
            include_complexity=True,
            include_todos=True
        )
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Must complete in reasonable time (less than 10 seconds for large code)
        self.assertLess(processing_time, 10.0, 
                       "Code summarization must complete in < 10 seconds")
        
        # Verify processing time is recorded
        self.assertTrue(result['success'])
        self.assertIn('processing_time', result['metadata'])
        self.assertGreater(result['metadata']['processing_time'], 0)
        
    def test_summarize_code_include_todos_flag(self):
        """Test TODO inclusion flag functionality."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        # Test with TODOs enabled
        result_with_todos = handler(
            source_code=self.test_large_python_code,
            include_todos=True
        )
        
        self.assertTrue(result_with_todos['success'])
        
        # Test with TODOs disabled
        result_without_todos = handler(
            source_code=self.test_large_python_code,
            include_todos=False
        )
        
        self.assertTrue(result_without_todos['success'])
        
        # Compare results
        if 'todos' in result_with_todos:
            self.assertGreater(len(result_with_todos['todos']), 0)
        
        if 'todos' in result_without_todos:
            self.assertEqual(len(result_without_todos['todos']), 0)
        
    def test_summarize_code_natural_language_quality(self):
        """Test natural language summary quality."""
        handler = ALL_TOOLS['summarize_code']['handler']
        
        result = handler(
            source_code=self.test_large_python_code,
            summary_length="detailed"
        )
        
        self.assertTrue(result['success'])
        
        summary = result['summary']
        module_purpose = result['module_purpose']
        
        # Test summary quality indicators
        self.assertGreater(len(summary), 100, "Summary should be substantial")
        self.assertGreater(len(module_purpose), 20, "Module purpose should be descriptive")
        
        # Should contain technical terms
        technical_terms = ['class', 'function', 'method', 'module', 'data', 'process']
        has_technical_terms = any(term in summary.lower() for term in technical_terms)
        self.assertTrue(has_technical_terms, "Summary should contain technical terms")
        
        # Should be readable (basic heuristics)
        sentences = summary.split('.')
        self.assertGreater(len(sentences), 2, "Summary should have multiple sentences")
        
        # Should not contain code syntax in natural language parts
        code_indicators = ['def ', 'class ', 'import ', '()', '{', '}']
        has_code_syntax = any(indicator in summary for indicator in code_indicators)
        self.assertFalse(has_code_syntax, "Summary should be natural language, not code")


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)