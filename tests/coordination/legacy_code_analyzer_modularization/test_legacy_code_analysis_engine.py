"""
Comprehensive TDD tests for Legacy Code Analysis Engine extraction.
Tests legacy code analysis and LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
LegacyCodeAnalysisEngine will handle analyze_legacy_code and pattern analysis.
MANDATORY: Uses ALL required LTMC tools (pattern_action, unix_action, memory_action, graph_action).
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestLegacyCodeAnalysisEngine:
    """Test LegacyCodeAnalysisEngine class - to be extracted from legacy_code_analyzer.py"""
    
    def test_legacy_code_analysis_engine_creation(self):
        """Test LegacyCodeAnalysisEngine can be instantiated"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        assert hasattr(engine, 'coordinator')
        assert hasattr(engine, 'state_manager')
        assert hasattr(engine, 'legacy_decorators')
        assert hasattr(engine, 'functional_tools')
        assert hasattr(engine, 'analysis_report')
        assert engine.coordinator == mock_coordinator
    
    @patch('ltms.coordination.legacy_code_analysis_engine.pattern_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.unix_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.memory_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.graph_action')
    def test_analyze_legacy_code_success(self, mock_graph, mock_memory, mock_unix, mock_pattern):
        """Test successful legacy code analysis with LTMC tools integration"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition
        
        # Setup LTMC tool mocks - MANDATORY
        mock_pattern.return_value = {
            'success': True,
            'functions': [
                {
                    'name': 'test_legacy_function',
                    'decorators': ['@mcp.tool'],
                    'file': '/test/file.py',
                    'line': 42,
                    'signature': 'def test_legacy_function(arg1, arg2)'
                }
            ]
        }
        mock_unix.return_value = {'success': True, 'tree': 'file_structure_data'}
        mock_memory.return_value = {'success': True, 'stored_id': 'memory_123'}
        mock_graph.return_value = {'success': True, 'relationship_id': 'graph_456'}
        
        # Setup coordinator
        mock_coordinator = Mock()
        mock_coordinator.task_id = "analysis_test_task"
        mock_coordinator.conversation_id = "analysis_test_conv"
        
        # Setup state manager
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test analysis
        result = engine.analyze_legacy_code()
        
        # Verify success
        assert result['success'] is True
        assert 'legacy_decorators' in result
        assert 'functional_tools' in result
        assert 'analysis_report' in result
        assert 'memory_storage' in result
        assert result['next_agent'] == 'safety_validator'
        
        # Verify legacy decorators were found
        assert len(result['legacy_decorators']) == 1
        decorator = result['legacy_decorators'][0]
        assert decorator['name'] == 'test_legacy_function'
        assert '@mcp.tool' in decorator['decorators']
        
        # Verify state transitions
        assert mock_state_manager.transition_agent_state.call_count == 2
        
        # First transition: ACTIVE
        first_call = mock_state_manager.transition_agent_state.call_args_list[0]
        assert first_call[0][1] == AgentStatus.ACTIVE
        assert first_call[0][2] == StateTransition.ACTIVATE
        
        # Second transition: WAITING
        second_call = mock_state_manager.transition_agent_state.call_args_list[1]
        assert second_call[0][1] == AgentStatus.WAITING
        assert second_call[0][2] == StateTransition.PAUSE
        
        # Verify ALL LTMC tools were called - MANDATORY
        
        # 1. pattern_action - MANDATORY Tool 5 (called twice: functions and classes)
        assert mock_pattern.call_count == 2
        pattern_calls = mock_pattern.call_args_list
        
        # First call: extract_functions
        functions_call = pattern_calls[0]
        assert functions_call[1]['action'] == 'extract_functions'
        assert functions_call[1]['conversation_id'] == 'analysis_test_conv'
        assert functions_call[1]['role'] == 'system'
        
        # Second call: extract_classes
        classes_call = pattern_calls[1]
        assert classes_call[1]['action'] == 'extract_classes'
        assert classes_call[1]['conversation_id'] == 'analysis_test_conv'
        assert classes_call[1]['role'] == 'system'
        
        # 2. unix_action - MANDATORY Tool 4
        mock_unix.assert_called_once()
        unix_call = mock_unix.call_args
        assert unix_call[1]['action'] == 'tree'
        assert unix_call[1]['conversation_id'] == 'analysis_test_conv'
        assert unix_call[1]['role'] == 'system'
        
        # 3. memory_action - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'legacy_analysis_' in memory_call[1]['file_name']
        assert 'legacy_analysis' in memory_call[1]['tags']
        
        # 4. graph_action - MANDATORY Tool 8
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'legacy_analyzer_' in graph_call[1]['source_entity']
        assert graph_call[1]['target_entity'] == 'legacy_mcp_tools'
        assert graph_call[1]['relationship'] == 'discovered_legacy_tools'
    
    @patch('ltms.coordination.legacy_code_analysis_engine.pattern_action')
    def test_analyze_legacy_code_exception_handling(self, mock_pattern):
        """Test analysis exception handling"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateTransition
        
        # Setup pattern_action to fail
        mock_pattern.side_effect = Exception("Pattern analysis service unavailable")
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "exception_test_task"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test exception handling
        result = engine.analyze_legacy_code()
        
        # Should handle gracefully and return failure result
        assert result['success'] is False
        assert 'error' in result
        assert len(result['legacy_decorators']) == 0
        
        # Verify error state transition
        error_call = mock_state_manager.transition_agent_state.call_args_list[-1]
        assert error_call[0][1] == AgentStatus.ERROR
        assert error_call[0][2] == StateTransition.FAIL
    
    def test_process_legacy_decorators_identification(self):
        """Test legacy decorator processing functionality"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test functions with legacy decorators
        test_functions = [
            {
                'name': 'legacy_function_1',
                'decorators': ['@mcp.tool', '@some_other'],
                'file': '/test/legacy1.py',
                'line': 10,
                'signature': 'def legacy_function_1()'
            },
            {
                'name': 'modern_function',
                'decorators': ['@modern_decorator'],
                'file': '/test/modern.py', 
                'line': 20,
                'signature': 'def modern_function()'
            },
            {
                'name': 'legacy_function_2',
                'decorators': ['@mcp.tool'],
                'file': '/test/legacy2.py',
                'line': 30,
                'signature': 'def legacy_function_2(arg1)'
            }
        ]
        
        # Process legacy decorators
        engine._process_legacy_decorators(test_functions)
        
        # Verify only legacy functions were identified
        assert len(engine.legacy_decorators) == 2
        
        # Verify first legacy function
        legacy_1 = engine.legacy_decorators[0]
        assert legacy_1['name'] == 'legacy_function_1'
        assert '@mcp.tool' in legacy_1['decorators']
        assert legacy_1['file'] == '/test/legacy1.py'
        assert legacy_1['line'] == 10
        
        # Verify second legacy function
        legacy_2 = engine.legacy_decorators[1]
        assert legacy_2['name'] == 'legacy_function_2'
        assert legacy_2['file'] == '/test/legacy2.py'
        assert legacy_2['line'] == 30
    
    def test_map_functional_tools_generation(self):
        """Test functional tools mapping functionality"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test functional tools mapping
        engine._map_functional_tools()
        
        # Verify all consolidated tools are mapped
        expected_tools = [
            'memory_action', 'todo_action', 'chat_action', 'unix_action',
            'pattern_action', 'blueprint_action', 'cache_action', 'graph_action',
            'documentation_action', 'sync_action', 'config_action'
        ]
        
        assert len(engine.functional_tools) == len(expected_tools)
        
        # Verify each tool is properly mapped
        tool_names = [tool['name'] for tool in engine.functional_tools]
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Verify tool structure
        sample_tool = engine.functional_tools[0]
        assert 'name' in sample_tool
        assert 'file' in sample_tool
        assert 'type' in sample_tool
        assert 'status' in sample_tool
        assert sample_tool['type'] == 'functional_replacement'
        assert sample_tool['status'] == 'active'
    
    def test_create_analysis_report_generation(self):
        """Test analysis report creation functionality"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        engine.agent_id = "test_analyzer"
        
        # Setup test data
        engine.legacy_decorators = [
            {'name': 'func1', 'file': '/test1.py', 'line': 10},
            {'name': 'func2', 'file': '/test2.py', 'line': 20}
        ]
        engine.functional_tools = [
            {'name': 'tool1'}, {'name': 'tool2'}, {'name': 'tool3'}
        ]
        
        # Create analysis report
        engine._create_analysis_report()
        
        # Verify report structure
        report = engine.analysis_report
        assert 'total_legacy_decorators' in report
        assert 'total_functional_tools' in report
        assert 'removal_recommendations' in report
        assert 'analysis_agent' in report
        assert 'analysis_timestamp' in report
        
        # Verify counts
        assert report['total_legacy_decorators'] == 2
        assert report['total_functional_tools'] == 3
        
        # Verify recommendations
        assert len(report['removal_recommendations']) == 2
        assert 'Remove func1 from /test1.py:10' in report['removal_recommendations']
        assert 'Remove func2 from /test2.py:20' in report['removal_recommendations']
        
        # Verify metadata
        assert report['analysis_agent'] == "test_analyzer"
        assert isinstance(report['analysis_timestamp'], str)
    
    @patch('ltms.coordination.legacy_code_analysis_engine.pattern_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.unix_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.memory_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.graph_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_graph, mock_memory, mock_unix, mock_pattern):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_pattern.return_value = {'success': True, 'functions': []}
        mock_unix.return_value = {'success': True, 'tree': 'comprehensive_structure'}
        mock_memory.return_value = {'success': True, 'stored_id': 'ltmc_memory_789'}
        mock_graph.return_value = {'success': True, 'relationship_id': 'ltmc_graph_101'}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "ltmc_comprehensive_analysis"
        mock_coordinator.conversation_id = "ltmc_comprehensive_analysis_conv"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test comprehensive analysis
        result = engine.analyze_legacy_code()
        
        # Verify success
        assert result['success'] is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. pattern_action - MANDATORY Tool 5 (extract_functions and extract_classes)
        assert mock_pattern.call_count == 2
        pattern_calls = mock_pattern.call_args_list
        actions = [call[1]['action'] for call in pattern_calls]
        assert 'extract_functions' in actions
        assert 'extract_classes' in actions
        
        # 2. unix_action - MANDATORY Tool 4 (tree structure)
        mock_unix.assert_called_once()
        unix_call = mock_unix.call_args
        assert unix_call[1]['action'] == 'tree'
        assert unix_call[1]['conversation_id'] == 'ltmc_comprehensive_analysis_conv'
        
        # 3. memory_action - MANDATORY Tool 1 (store analysis)
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'ltmc_comprehensive_analysis' in memory_call[1]['file_name']
        
        # 4. graph_action - MANDATORY Tool 8 (link relationships)
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'ltmc_comprehensive_analysis' in graph_call[1]['source_entity']
    
    @patch('ltms.coordination.legacy_code_analysis_engine.memory_action')
    def test_memory_storage_structure_validation(self, mock_memory):
        """Test memory storage document structure"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        mock_memory.return_value = {'success': True, 'stored_id': 'validation_test'}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "memory_structure_test"
        mock_coordinator.conversation_id = "memory_structure_conv"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        engine.legacy_decorators = [{'test': 'data'}]
        engine.functional_tools = [{'test': 'tool'}]
        engine.analysis_report = {'test': 'report'}
        
        # Mock other LTMC tools to focus on memory
        with patch.multiple(
            'ltms.coordination.legacy_code_analysis_engine',
            pattern_action=Mock(return_value={'functions': []}),
            unix_action=Mock(return_value={'tree': 'test'}),
            graph_action=Mock(return_value={'success': True})
        ):
            result = engine.analyze_legacy_code()
        
        # Verify memory was called
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        
        # Parse stored document
        stored_content = memory_call[1]['content']
        document = json.loads(stored_content)
        
        # Verify document structure
        required_fields = [
            'agent_id', 'analysis_timestamp', 'legacy_decorators',
            'functional_tools', 'analysis_report', 'file_structure', 'coordination_task'
        ]
        for field in required_fields:
            assert field in document
        
        # Verify values
        assert document['coordination_task'] == 'memory_structure_test'
        assert document['agent_id'] == engine.agent_id


class TestLegacyCodeAnalysisEngineIntegration:
    """Test LegacyCodeAnalysisEngine integration scenarios"""
    
    def test_integration_with_coordinator_and_state_manager(self):
        """Test integration with coordinator and state manager components"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test that all components are properly integrated
        assert engine.coordinator == mock_coordinator
        assert engine.state_manager == mock_state_manager
        assert isinstance(engine.legacy_decorators, list)
        assert isinstance(engine.functional_tools, list)
        assert isinstance(engine.analysis_report, dict)
    
    @patch('ltms.coordination.legacy_code_analysis_engine.pattern_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.unix_action') 
    @patch('ltms.coordination.legacy_code_analysis_engine.memory_action')
    @patch('ltms.coordination.legacy_code_analysis_engine.graph_action')
    def test_end_to_end_analysis_workflow(self, mock_graph, mock_memory, mock_unix, mock_pattern):
        """Test complete analysis workflow with all processing steps"""
        from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
        
        # Setup comprehensive test data
        mock_pattern.return_value = {
            'success': True,
            'functions': [
                {
                    'name': 'e2e_legacy_function',
                    'decorators': ['@mcp.tool'],
                    'file': '/e2e/test.py',
                    'line': 100,
                    'signature': 'def e2e_legacy_function()'
                }
            ]
        }
        mock_unix.return_value = {'success': True, 'tree': 'e2e_file_structure'}
        mock_memory.return_value = {'success': True, 'stored_id': 'e2e_memory'}
        mock_graph.return_value = {'success': True, 'relationship_id': 'e2e_graph'}
        
        mock_coordinator = Mock()
        mock_coordinator.task_id = "e2e_analysis"
        mock_coordinator.conversation_id = "e2e_analysis_conv"
        
        mock_state_manager = Mock()
        mock_state_manager.transition_agent_state.return_value = True
        
        engine = LegacyCodeAnalysisEngine(mock_coordinator, mock_state_manager)
        
        # Test complete workflow
        result = engine.analyze_legacy_code()
        
        # Verify complete workflow succeeded
        assert result['success'] is True
        
        # Verify all processing steps were executed
        assert len(result['legacy_decorators']) == 1
        assert len(result['functional_tools']) > 0
        assert 'total_legacy_decorators' in result['analysis_report']
        
        # Verify integration between all components
        decorator = result['legacy_decorators'][0]
        assert decorator['name'] == 'e2e_legacy_function'
        assert decorator['identified_by'] == engine.agent_id


# Pytest fixtures for analysis engine testing
@pytest.fixture
def mock_analysis_dependencies():
    """Fixture providing mock dependencies for analysis engine testing"""
    mock_coordinator = Mock()
    mock_coordinator.task_id = "fixture_analysis_task"
    mock_coordinator.conversation_id = "fixture_analysis_conv"
    
    mock_state_manager = Mock()
    mock_state_manager.transition_agent_state.return_value = True
    
    return {
        'coordinator': mock_coordinator,
        'state_manager': mock_state_manager
    }

@pytest.fixture
def legacy_code_analysis_engine(mock_analysis_dependencies):
    """Fixture providing LegacyCodeAnalysisEngine instance"""
    from ltms.coordination.legacy_code_analysis_engine import LegacyCodeAnalysisEngine
    
    deps = mock_analysis_dependencies
    return LegacyCodeAnalysisEngine(deps['coordinator'], deps['state_manager'])

@pytest.fixture
def mock_all_ltmc_analysis_tools():
    """Fixture providing mocks for all LTMC tools used in analysis engine"""
    with patch.multiple(
        'ltms.coordination.legacy_code_analysis_engine',
        pattern_action=Mock(return_value={'success': True, 'functions': []}),
        unix_action=Mock(return_value={'success': True, 'tree': 'fixture_structure'}),
        memory_action=Mock(return_value={'success': True, 'stored_id': 'fixture_memory'}),
        graph_action=Mock(return_value={'success': True, 'relationship_id': 'fixture_graph'})
    ) as mocks:
        yield mocks