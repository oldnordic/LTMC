"""
Comprehensive TDD tests for Legacy Code Processing Utilities extraction.
Tests helper methods and data processing functionality.

Following TDD methodology: Tests written FIRST before extraction.
LegacyCodeProcessingUtilities will handle _process_legacy_decorators, _map_functional_tools, _create_analysis_report.
MANDATORY: Uses ALL required LTMC tools for data processing and validation.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestLegacyCodeProcessingUtilities:
    """Test LegacyCodeProcessingUtilities class - to be extracted from legacy_code_analyzer.py"""
    
    def test_legacy_code_processing_utilities_creation(self):
        """Test LegacyCodeProcessingUtilities can be instantiated"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        # Mock agent ID
        agent_id = "test_processing_analyzer"
        
        utilities = LegacyCodeProcessingUtilities(agent_id)
        
        assert hasattr(utilities, 'agent_id')
        assert hasattr(utilities, 'legacy_decorators')
        assert hasattr(utilities, 'functional_tools')
        assert hasattr(utilities, 'analysis_report')
        assert utilities.agent_id == agent_id
        assert isinstance(utilities.legacy_decorators, list)
        assert isinstance(utilities.functional_tools, list)
        assert isinstance(utilities.analysis_report, dict)
    
    def test_process_legacy_decorators_identification(self):
        """Test legacy decorator processing and identification"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("decorator_test_analyzer")
        
        # Test functions with various decorator patterns
        test_functions = [
            {
                'name': 'legacy_function_1',
                'decorators': ['@mcp.tool', '@some_other_decorator'],
                'file': '/test/legacy1.py',
                'line': 15,
                'signature': 'def legacy_function_1(arg1, arg2)'
            },
            {
                'name': 'modern_function',
                'decorators': ['@modern_decorator', '@another_modern'],
                'file': '/test/modern.py',
                'line': 25,
                'signature': 'def modern_function()'
            },
            {
                'name': 'legacy_function_2',
                'decorators': ['@mcp.tool'],
                'file': '/test/legacy2.py',
                'line': 35,
                'signature': 'def legacy_function_2(param)'
            },
            {
                'name': 'mixed_function',
                'decorators': ['@modern_decorator', '@mcp.tool', '@other'],
                'file': '/test/mixed.py',
                'line': 45,
                'signature': 'def mixed_function(a, b, c)'
            },
            {
                'name': 'no_decorators_function',
                'decorators': [],
                'file': '/test/plain.py',
                'line': 55,
                'signature': 'def no_decorators_function()'
            }
        ]
        
        # Process legacy decorators
        utilities.process_legacy_decorators(test_functions)
        
        # Verify only functions with @mcp.tool decorator were identified
        assert len(utilities.legacy_decorators) == 3
        
        # Verify first legacy function
        legacy_1 = utilities.legacy_decorators[0]
        assert legacy_1['name'] == 'legacy_function_1'
        assert '@mcp.tool' in legacy_1['decorators']
        assert '@some_other_decorator' in legacy_1['decorators']
        assert legacy_1['file'] == '/test/legacy1.py'
        assert legacy_1['line'] == 15
        assert legacy_1['signature'] == 'def legacy_function_1(arg1, arg2)'
        assert legacy_1['identified_by'] == 'decorator_test_analyzer'
        
        # Verify second legacy function
        legacy_2 = utilities.legacy_decorators[1]
        assert legacy_2['name'] == 'legacy_function_2'
        assert legacy_2['decorators'] == ['@mcp.tool']
        assert legacy_2['file'] == '/test/legacy2.py'
        assert legacy_2['line'] == 35
        
        # Verify mixed function (has @mcp.tool among others)
        legacy_3 = utilities.legacy_decorators[2]
        assert legacy_3['name'] == 'mixed_function'
        assert '@mcp.tool' in legacy_3['decorators']
        assert '@modern_decorator' in legacy_3['decorators']
        assert legacy_3['file'] == '/test/mixed.py'
    
    def test_process_legacy_decorators_empty_input(self):
        """Test legacy decorator processing with empty input"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("empty_test_analyzer")
        
        # Process empty function list
        utilities.process_legacy_decorators([])
        
        # Should result in empty legacy decorators list
        assert len(utilities.legacy_decorators) == 0
        assert utilities.legacy_decorators == []
    
    def test_process_legacy_decorators_no_legacy_found(self):
        """Test legacy decorator processing when no legacy decorators exist"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("no_legacy_analyzer")
        
        # Test functions without @mcp.tool decorators
        modern_functions = [
            {
                'name': 'modern_func_1',
                'decorators': ['@modern_decorator'],
                'file': '/test/modern1.py',
                'line': 10
            },
            {
                'name': 'modern_func_2',
                'decorators': ['@another_modern', '@third_modern'],
                'file': '/test/modern2.py',
                'line': 20
            },
            {
                'name': 'plain_func',
                'decorators': [],
                'file': '/test/plain.py',
                'line': 30
            }
        ]
        
        # Process modern functions
        utilities.process_legacy_decorators(modern_functions)
        
        # Should find no legacy decorators
        assert len(utilities.legacy_decorators) == 0
    
    def test_map_functional_tools_complete_mapping(self):
        """Test functional tools mapping with all consolidated tools"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("mapping_test_analyzer")
        
        # Map functional tools
        utilities.map_functional_tools()
        
        # Verify all expected consolidated tools are mapped
        expected_tools = [
            'memory_action', 'todo_action', 'chat_action', 'unix_action',
            'pattern_action', 'blueprint_action', 'cache_action', 'graph_action',
            'documentation_action', 'sync_action', 'config_action'
        ]
        
        assert len(utilities.functional_tools) == len(expected_tools)
        
        # Verify each tool is properly mapped
        tool_names = [tool['name'] for tool in utilities.functional_tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names, f"Missing tool: {expected_tool}"
        
        # Verify tool structure
        for tool in utilities.functional_tools:
            assert 'name' in tool
            assert 'file' in tool
            assert 'type' in tool
            assert 'status' in tool
            
            # Verify values
            assert tool['file'] == 'ltms/tools/consolidated.py'
            assert tool['type'] == 'functional_replacement'
            assert tool['status'] == 'active'
            
            # Verify name is valid
            assert tool['name'] in expected_tools
    
    def test_create_analysis_report_comprehensive_structure(self):
        """Test analysis report creation with comprehensive data"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("report_test_analyzer")
        
        # Setup test data
        utilities.legacy_decorators = [
            {'name': 'legacy1', 'file': '/test1.py', 'line': 10},
            {'name': 'legacy2', 'file': '/test2.py', 'line': 20},
            {'name': 'legacy3', 'file': '/test3.py', 'line': 30}
        ]
        
        utilities.functional_tools = [
            {'name': 'tool1', 'status': 'active'},
            {'name': 'tool2', 'status': 'active'},
            {'name': 'tool3', 'status': 'active'},
            {'name': 'tool4', 'status': 'active'},
            {'name': 'tool5', 'status': 'active'}
        ]
        
        # Create analysis report
        utilities.create_analysis_report()
        
        # Verify report structure
        report = utilities.analysis_report
        
        # Required fields
        required_fields = [
            'total_legacy_decorators', 'total_functional_tools',
            'removal_recommendations', 'analysis_agent', 'analysis_timestamp'
        ]
        for field in required_fields:
            assert field in report, f"Missing report field: {field}"
        
        # Verify counts
        assert report['total_legacy_decorators'] == 3
        assert report['total_functional_tools'] == 5
        
        # Verify removal recommendations
        assert len(report['removal_recommendations']) == 3
        expected_recommendations = [
            'Remove legacy1 from /test1.py:10',
            'Remove legacy2 from /test2.py:20',
            'Remove legacy3 from /test3.py:30'
        ]
        for expected in expected_recommendations:
            assert expected in report['removal_recommendations']
        
        # Verify metadata
        assert report['analysis_agent'] == 'report_test_analyzer'
        assert isinstance(report['analysis_timestamp'], str)
        
        # Verify timestamp format (ISO format)
        timestamp = report['analysis_timestamp']
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # Should not raise exception
    
    def test_create_analysis_report_empty_data(self):
        """Test analysis report creation with empty data"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("empty_report_analyzer")
        
        # Create report with empty data
        utilities.create_analysis_report()
        
        # Verify report structure with zero counts
        report = utilities.analysis_report
        assert report['total_legacy_decorators'] == 0
        assert report['total_functional_tools'] == 0
        assert report['removal_recommendations'] == []
        assert report['analysis_agent'] == 'empty_report_analyzer'
        assert 'analysis_timestamp' in report
    
    def test_decorator_processing_edge_cases(self):
        """Test decorator processing with edge cases and malformed data"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("edge_case_analyzer")
        
        # Test edge cases and malformed data
        edge_case_functions = [
            {
                'name': 'missing_decorators',
                # Missing 'decorators' field
                'file': '/test/missing.py',
                'line': 10
            },
            {
                'name': 'none_decorators',
                'decorators': None,
                'file': '/test/none.py',
                'line': 20
            },
            {
                'name': 'partial_mcp_tool',
                'decorators': ['@mcp.tool_partial'],  # Similar but not exact
                'file': '/test/partial.py',
                'line': 30
            },
            {
                'name': 'exact_mcp_tool',
                'decorators': ['@mcp.tool'],
                'file': '/test/exact.py',
                'line': 40
            },
            {
                'name': 'missing_file_info',
                'decorators': ['@mcp.tool'],
                # Missing 'file' and 'line' fields
                'signature': 'def missing_file_info()'
            }
        ]
        
        # Process edge cases (should not raise exceptions)
        utilities.process_legacy_decorators(edge_case_functions)
        
        # Should find only exact matches
        assert len(utilities.legacy_decorators) == 2  # exact_mcp_tool and missing_file_info
        
        # Verify exact match
        exact_match = next(d for d in utilities.legacy_decorators if d['name'] == 'exact_mcp_tool')
        assert exact_match['file'] == '/test/exact.py'
        assert exact_match['line'] == 40
        
        # Verify missing file info handling
        missing_file = next(d for d in utilities.legacy_decorators if d['name'] == 'missing_file_info')
        assert missing_file['file'] == 'unknown'
        assert missing_file['line'] == 0
    
    def test_comprehensive_data_processing_workflow(self):
        """Test complete data processing workflow with all utilities"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("workflow_test_analyzer")
        
        # Setup comprehensive test data
        comprehensive_functions = [
            {
                'name': 'workflow_legacy_1',
                'decorators': ['@mcp.tool', '@deprecated'],
                'file': '/workflow/legacy1.py',
                'line': 100,
                'signature': 'def workflow_legacy_1(param1, param2)'
            },
            {
                'name': 'workflow_modern',
                'decorators': ['@modern_tool'],
                'file': '/workflow/modern.py',
                'line': 200,
                'signature': 'def workflow_modern()'
            },
            {
                'name': 'workflow_legacy_2',
                'decorators': ['@other', '@mcp.tool'],
                'file': '/workflow/legacy2.py',
                'line': 300,
                'signature': 'def workflow_legacy_2(a, b, c, d)'
            }
        ]
        
        # Execute complete workflow
        # Step 1: Process legacy decorators
        utilities.process_legacy_decorators(comprehensive_functions)
        
        # Step 2: Map functional tools
        utilities.map_functional_tools()
        
        # Step 3: Create analysis report
        utilities.create_analysis_report()
        
        # Verify complete workflow results
        
        # Legacy decorators processing
        assert len(utilities.legacy_decorators) == 2
        legacy_names = [d['name'] for d in utilities.legacy_decorators]
        assert 'workflow_legacy_1' in legacy_names
        assert 'workflow_legacy_2' in legacy_names
        assert 'workflow_modern' not in legacy_names
        
        # Functional tools mapping
        assert len(utilities.functional_tools) == 11  # All consolidated tools
        tool_names = [t['name'] for t in utilities.functional_tools]
        assert 'memory_action' in tool_names
        assert 'chat_action' in tool_names
        assert 'pattern_action' in tool_names
        
        # Analysis report creation
        report = utilities.analysis_report
        assert report['total_legacy_decorators'] == 2
        assert report['total_functional_tools'] == 11
        assert len(report['removal_recommendations']) == 2
        assert 'Remove workflow_legacy_1 from /workflow/legacy1.py:100' in report['removal_recommendations']
        assert 'Remove workflow_legacy_2 from /workflow/legacy2.py:300' in report['removal_recommendations']
        assert report['analysis_agent'] == 'workflow_test_analyzer'
    
    def test_data_consistency_across_processing_steps(self):
        """Test data consistency across all processing steps"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        utilities = LegacyCodeProcessingUtilities("consistency_analyzer")
        
        # Setup consistent test data
        consistent_functions = [
            {
                'name': 'consistent_legacy',
                'decorators': ['@mcp.tool'],
                'file': '/consistency/test.py',
                'line': 999,
                'signature': 'def consistent_legacy(consistency_param)'
            }
        ]
        
        # Execute all steps
        utilities.process_legacy_decorators(consistent_functions)
        utilities.map_functional_tools()
        utilities.create_analysis_report()
        
        # Verify consistency across all data structures
        
        # Legacy decorator consistency
        assert len(utilities.legacy_decorators) == 1
        legacy = utilities.legacy_decorators[0]
        assert legacy['name'] == 'consistent_legacy'
        assert legacy['identified_by'] == 'consistency_analyzer'
        
        # Report consistency
        report = utilities.analysis_report
        assert report['total_legacy_decorators'] == len(utilities.legacy_decorators)
        assert report['total_functional_tools'] == len(utilities.functional_tools)
        assert report['analysis_agent'] == utilities.agent_id
        
        # Recommendation consistency
        expected_recommendation = 'Remove consistent_legacy from /consistency/test.py:999'
        assert expected_recommendation in report['removal_recommendations']


class TestLegacyCodeProcessingUtilitiesIntegration:
    """Test LegacyCodeProcessingUtilities integration scenarios"""
    
    def test_integration_with_analysis_engine_data_flow(self):
        """Test integration with analysis engine data flow"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        # Simulate data flow from analysis engine
        utilities = LegacyCodeProcessingUtilities("integration_analyzer")
        
        # Simulate pattern_action output format
        pattern_action_result = {
            'functions': [
                {
                    'name': 'integration_legacy_function',
                    'decorators': ['@mcp.tool'],
                    'file': '/integration/analysis.py',
                    'line': 150,
                    'signature': 'def integration_legacy_function(engine_param)',
                    'complexity': 3
                }
            ]
        }
        
        # Process as if coming from analysis engine
        utilities.process_legacy_decorators(pattern_action_result['functions'])
        utilities.map_functional_tools()
        utilities.create_analysis_report()
        
        # Verify integration compatibility
        assert len(utilities.legacy_decorators) == 1
        legacy = utilities.legacy_decorators[0]
        assert legacy['name'] == 'integration_legacy_function'
        assert legacy['file'] == '/integration/analysis.py'
        
        # Verify report is suitable for communication module
        report = utilities.analysis_report
        assert 'total_legacy_decorators' in report
        assert 'removal_recommendations' in report
        assert isinstance(report['removal_recommendations'], list)
    
    def test_utilities_state_isolation(self):
        """Test that utilities maintain proper state isolation"""
        from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
        
        # Create two separate utilities instances
        utilities_1 = LegacyCodeProcessingUtilities("isolated_analyzer_1")
        utilities_2 = LegacyCodeProcessingUtilities("isolated_analyzer_2")
        
        # Process different data in each
        functions_1 = [
            {'name': 'isolated_func_1', 'decorators': ['@mcp.tool'], 'file': '/iso1.py', 'line': 1}
        ]
        functions_2 = [
            {'name': 'isolated_func_2', 'decorators': ['@mcp.tool'], 'file': '/iso2.py', 'line': 2},
            {'name': 'isolated_func_3', 'decorators': ['@mcp.tool'], 'file': '/iso3.py', 'line': 3}
        ]
        
        utilities_1.process_legacy_decorators(functions_1)
        utilities_1.create_analysis_report()
        
        utilities_2.process_legacy_decorators(functions_2)
        utilities_2.create_analysis_report()
        
        # Verify isolation
        assert len(utilities_1.legacy_decorators) == 1
        assert len(utilities_2.legacy_decorators) == 2
        
        assert utilities_1.analysis_report['total_legacy_decorators'] == 1
        assert utilities_2.analysis_report['total_legacy_decorators'] == 2
        
        # Verify no cross-contamination
        func_1_names = [d['name'] for d in utilities_1.legacy_decorators]
        func_2_names = [d['name'] for d in utilities_2.legacy_decorators]
        
        assert 'isolated_func_1' in func_1_names
        assert 'isolated_func_1' not in func_2_names
        assert 'isolated_func_2' not in func_1_names
        assert 'isolated_func_2' in func_2_names


# Pytest fixtures for processing utilities testing
@pytest.fixture
def legacy_code_processing_utilities():
    """Fixture providing LegacyCodeProcessingUtilities instance"""
    from ltms.coordination.legacy_code_processing_utilities import LegacyCodeProcessingUtilities
    
    return LegacyCodeProcessingUtilities("fixture_utilities_analyzer")

@pytest.fixture
def sample_functions_with_legacy():
    """Fixture providing sample functions with legacy decorators"""
    return [
        {
            'name': 'fixture_legacy_1',
            'decorators': ['@mcp.tool'],
            'file': '/fixture/legacy1.py',
            'line': 50,
            'signature': 'def fixture_legacy_1()'
        },
        {
            'name': 'fixture_modern',
            'decorators': ['@modern_decorator'],
            'file': '/fixture/modern.py',
            'line': 60,
            'signature': 'def fixture_modern()'
        },
        {
            'name': 'fixture_legacy_2',
            'decorators': ['@other', '@mcp.tool', '@another'],
            'file': '/fixture/legacy2.py',
            'line': 70,
            'signature': 'def fixture_legacy_2(param1, param2)'
        }
    ]

@pytest.fixture
def expected_consolidated_tools():
    """Fixture providing expected consolidated tools list"""
    return [
        'memory_action', 'todo_action', 'chat_action', 'unix_action',
        'pattern_action', 'blueprint_action', 'cache_action', 'graph_action',
        'documentation_action', 'sync_action', 'config_action'
    ]