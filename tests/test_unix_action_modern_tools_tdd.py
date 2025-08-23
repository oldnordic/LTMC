"""
TDD Tests for Modern Unix Tools Integration in unix_action
Tests 8 new modern Unix tools with real external command integration (NO MOCKS)
"""

import os
import tempfile
import subprocess
import json
from pathlib import Path

# Add LTMC to path
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated import unix_action


class TestModernUnixToolsTDD:
    """Test modern Unix tools integration with real command execution."""
    
    def setup_method(self):
        """Setup test environment with temporary files."""
        # Create temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.test_files = []
        
        # Create test files for tools
        test_py_file = os.path.join(self.temp_dir, "test.py")
        with open(test_py_file, 'w') as f:
            f.write('''def hello_world():
    """Print hello world message."""
    print("Hello, World!")
    return "success"

class TestClass:
    def __init__(self):
        self.value = 42
''')
        self.test_files.append(test_py_file)
        
        test_json_file = os.path.join(self.temp_dir, "test.json")
        with open(test_json_file, 'w') as f:
            json.dump({
                "name": "LTMC",
                "tools": 56,
                "status": "production",
                "features": ["memory", "context", "blueprints"]
            }, f)
        self.test_files.append(test_json_file)
        
        # Create subdirectory for tree testing
        sub_dir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(sub_dir)
        with open(os.path.join(sub_dir, "nested.txt"), 'w') as f:
            f.write("nested file content")
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_fd_find_action(self):
        """Test fd (fast find) integration with real fd command."""
        result = unix_action(
            action="find",
            pattern="*.py",
            path=self.temp_dir,
            type_filter="f"
        )
        
        assert result['success'] is True
        assert 'tool' in result
        assert result['tool'] == 'fd'
        assert 'files_found' in result
        assert len(result['files_found']) >= 1
        assert any('test.py' in file for file in result['files_found'])
        assert result['pattern'] == "*.py"
        assert result['search_path'] == self.temp_dir
    
    def test_fd_find_action_with_extension(self):
        """Test fd with specific extension filtering."""
        result = unix_action(
            action="find",
            pattern="test",
            path=self.temp_dir,
            extension="py"
        )
        
        assert result['success'] is True
        assert result['tool'] == 'fd'
        assert len(result['files_found']) >= 1
        assert result['pattern'] == "test"
    
    def test_tree_action(self):
        """Test tree directory visualization with real tree command."""
        result = unix_action(
            action="tree",
            path=self.temp_dir,
            max_depth=2,
            show_hidden=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'tree'
        assert 'tree_output' in result
        assert 'directory_count' in result
        assert 'file_count' in result
        assert result['max_depth'] == 2
        assert result['root_path'] == self.temp_dir
        # Should contain our test files
        assert 'test.py' in result['tree_output']
        assert 'subdir' in result['tree_output']
    
    def test_jq_json_processing_action(self):
        """Test jq JSON processing with real jq command."""
        json_data = '{"name": "LTMC", "tools": 56, "nested": {"status": "active"}}'
        
        result = unix_action(
            action="jq",
            json_input=json_data,
            query=".tools",
            raw_output=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'jq'
        assert result['query'] == '.tools'
        assert result['result'] == '56'
        assert 'execution_time_ms' in result
    
    def test_jq_complex_query_action(self):
        """Test jq with complex JSON query."""
        json_data = '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}'
        
        result = unix_action(
            action="jq",
            json_input=json_data,
            query=".users[] | select(.age > 26) | .name",
            raw_output=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'jq'
        assert 'Alice' in result['result']
    
    def test_jq_file_processing_action(self):
        """Test jq with file input."""
        json_file = next(f for f in self.test_files if f.endswith('.json'))
        
        result = unix_action(
            action="jq",
            file_path=json_file,
            query=".name",
            raw_output=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'jq'
        assert 'LTMC' in result['result']
    
    def test_lsd_modern_ls_action(self):
        """Test lsd modern ls alternative with real lsd command."""
        result = unix_action(
            action="list_modern",
            path=self.temp_dir,
            long_format=True,
            show_all=True,
            tree_view=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'lsd'
        assert 'files' in result
        assert len(result['files']) >= 2  # test.py and test.json
        assert 'formatted_output' in result
        assert result['path'] == self.temp_dir
    
    def test_duf_disk_usage_action(self):
        """Test duf disk usage analyzer with real duf command."""
        result = unix_action(
            action="disk_usage",
            path=self.temp_dir,
            output_format="json"
        )
        
        assert result['success'] is True
        assert result['tool'] == 'duf'
        assert 'disk_info' in result
        assert 'total_size' in result
        assert 'available_space' in result
        assert result['format'] == 'json'
    
    def test_tldr_help_action(self):
        """Test tldr command help with real tldr command."""
        result = unix_action(
            action="help",
            command="git",
            update_cache=False
        )
        
        assert result['success'] is True
        assert result['tool'] == 'tldr'
        assert result['command'] == 'git'
        assert 'help_content' in result
        assert 'examples' in result
        # Should contain practical examples
        assert len(result['examples']) > 0
    
    def test_delta_diff_action(self):
        """Test delta git diff highlighting with real delta command."""
        # Create two versions of a file
        file1 = os.path.join(self.temp_dir, "version1.txt")
        file2 = os.path.join(self.temp_dir, "version2.txt")
        
        with open(file1, 'w') as f:
            f.write("line 1\nline 2\nline 3\n")
        
        with open(file2, 'w') as f:
            f.write("line 1\nmodified line 2\nline 3\nnew line 4\n")
        
        result = unix_action(
            action="diff_highlight",
            file1=file1,
            file2=file2,
            side_by_side=True
        )
        
        assert result['success'] is True
        assert result['tool'] == 'delta'
        assert 'diff_output' in result
        assert 'changes_detected' in result
        assert result['changes_detected'] is True
        assert result['file1'] == file1
        assert result['file2'] == file2
    
    def test_fzf_fuzzy_find_action(self):
        """Test fzf fuzzy finder with real fzf command (non-interactive mode)."""
        # Create input list for fzf
        input_list = [
            "test.py",
            "test.json", 
            "another_file.txt",
            "script.sh",
            "data.csv"
        ]
        
        result = unix_action(
            action="fuzzy_select",
            input_list=input_list,
            query="test",
            non_interactive=True
        )
        
        assert result['success'] is True
        assert result['tool'] == 'fzf'
        assert 'selected_items' in result
        assert len(result['selected_items']) >= 1
        # Should match items containing "test"
        assert any('test' in item for item in result['selected_items'])
        assert result['query'] == 'test'
    
    def test_error_handling_missing_tool(self):
        """Test error handling when required tool is not available."""
        # Mock a scenario where tool is not found by using invalid action
        result = unix_action(action="nonexistent_tool")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Unknown unix action' in result['error']
    
    def test_error_handling_invalid_parameters(self):
        """Test error handling with invalid parameters."""
        # Test fd without required pattern
        result = unix_action(action="find")
        
        assert result['success'] is False
        assert 'error' in result
        assert 'Missing required parameter' in result['error']
    
    def test_tree_sitter_parse_syntax_action(self):
        """Test tree-sitter syntax parsing with real tree-sitter command."""
        result = unix_action(
            action="parse_syntax",
            file_path=next(f for f in self.test_files if f.endswith('.py')),
            quiet=True
        )
        
        assert result['success'] is True
        assert result['tool'] == 'tree-sitter'
        assert 'syntax_tree' in result
        assert 'node_count' in result
        assert 'depth' in result
        # Should parse our test Python file successfully
        assert result['node_count'] > 0
    
    def test_tree_sitter_syntax_highlight_action(self):
        """Test tree-sitter syntax highlighting with real tree-sitter command."""
        result = unix_action(
            action="syntax_highlight",
            file_path=next(f for f in self.test_files if f.endswith('.py')),
            html_output=True
        )
        
        assert result['success'] is True
        assert result['tool'] == 'tree-sitter'
        assert 'highlighted_code' in result
        assert 'language_detected' in result
        # Should contain HTML highlighting markup
        assert '<span' in result['highlighted_code'] or len(result['highlighted_code']) > 0
    
    def test_tree_sitter_syntax_query_action(self):
        """Test tree-sitter syntax querying with real tree-sitter command."""
        result = unix_action(
            action="syntax_query",
            file_path=next(f for f in self.test_files if f.endswith('.py')),
            query_pattern="(function_definition name: (identifier) @function.name)",
            capture_names=["function.name"]
        )
        
        assert result['success'] is True
        assert result['tool'] == 'tree-sitter'
        assert 'query_results' in result
        assert 'matches_found' in result
        # Should find function definitions in our test file
        assert result['matches_found'] >= 1  # At least hello_world function
        assert any('hello_world' in str(match) for match in result['query_results'])

    def test_comprehensive_integration_workflow(self):
        """Test workflow using multiple modern tools together."""
        # 1. Use fd to find Python files
        find_result = unix_action(
            action="find",
            pattern="*.py",
            path=self.temp_dir,
            type_filter="f"
        )
        assert find_result['success'] is True
        
        # 2. Use tree to show directory structure
        tree_result = unix_action(
            action="tree", 
            path=self.temp_dir,
            max_depth=2
        )
        assert tree_result['success'] is True
        
        # 3. Use jq to process JSON data
        jq_result = unix_action(
            action="jq",
            json_input='{"files": 3, "tools": "integrated"}',
            query=".tools"
        )
        assert jq_result['success'] is True
        
        # 4. Use tree-sitter to parse Python syntax
        parse_result = unix_action(
            action="parse_syntax",
            file_path=next(f for f in self.test_files if f.endswith('.py')),
            quiet=True
        )
        assert parse_result['success'] is True
        
        # All tools should work in sequence
        assert len([r for r in [find_result, tree_result, jq_result, parse_result] if r['success']]) == 4


if __name__ == "__main__":
    # Run tests directly without pytest
    test_instance = TestModernUnixToolsTDD()
    
    print("=== Running TDD Tests for Modern Unix Tools Integration ===")
    
    test_methods = [method for method in dir(test_instance) if method.startswith('test_')]
    
    for test_method in test_methods:
        try:
            print(f"\n🧪 Running {test_method}...")
            test_instance.setup_method()
            getattr(test_instance, test_method)()
            test_instance.teardown_method()
            print(f"✅ {test_method} PASSED")
        except Exception as e:
            print(f"❌ {test_method} FAILED: {str(e)}")
            test_instance.teardown_method()
    
    print(f"\n🎯 TDD Tests Complete: {len(test_methods)} tests defined")