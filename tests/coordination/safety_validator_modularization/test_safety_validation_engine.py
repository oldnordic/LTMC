"""
Comprehensive TDD tests for Safety Validation Engine extraction.
Tests comprehensive validation logic, LTMC tool integration, and safety scoring.

Following TDD methodology: Tests written FIRST before extraction.
SafetyValidationEngine will handle core validation with all 11 LTMC tools.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestSafetyValidationEngine:
    """Test SafetyValidationEngine class - to be extracted from safety_validator.py"""
    
    def test_safety_validation_engine_creation(self):
        """Test SafetyValidationEngine can be instantiated"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        # Mock core validator
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        assert hasattr(engine, 'core')
        assert engine.core == mock_core
    
    @patch('ltms.coordination.safety_validation_engine.config_action')
    @patch('ltms.coordination.safety_validation_engine.cache_action')
    @patch('ltms.coordination.safety_validation_engine.graph_action')
    @patch('ltms.coordination.safety_validation_engine.blueprint_action')
    @patch('ltms.coordination.safety_validation_engine.pattern_action')
    @patch('ltms.coordination.safety_validation_engine.memory_action')
    def test_validate_removal_safety_success(self, mock_memory, mock_pattern, mock_blueprint, 
                                           mock_graph, mock_cache, mock_config):
        """Test successful safety validation with all LTMC tools"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_manager import StateTransition
        
        # Setup mocks for all LTMC tools (Tools 5-11)
        mock_config.return_value = {'success': True, 'valid': True}
        mock_cache.return_value = {'success': True, 'status': 'healthy'}
        mock_graph.return_value = {'success': True, 'results': []}
        mock_blueprint.return_value = {'success': True, 'summary': 'complexity_ok'}
        mock_pattern.return_value = {'success': True, 'functions': []}
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        
        # Mock core validator
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "validation_test"
        mock_core.coordinator.conversation_id = "validation_conv"
        mock_core.state_manager = Mock()
        mock_core.state_manager.transition_agent_state.return_value = True
        
        engine = SafetyValidationEngine(mock_core)
        
        # Test analysis data with sufficient functional tools
        analysis_data = {
            'legacy_decorators': [
                {'name': 'memory_tool', 'file': '/test.py', 'line': 1},
                {'name': 'chat_tool', 'file': '/test2.py', 'line': 2}
            ],
            'functional_tools': [
                {'name': 'memory_action'}, {'name': 'chat_action'}, {'name': 'todo_action'},
                {'name': 'unix_action'}, {'name': 'pattern_action'}, {'name': 'blueprint_action'},
                {'name': 'cache_action'}, {'name': 'graph_action'}, {'name': 'documentation_action'},
                {'name': 'sync_action'}, {'name': 'config_action'}
            ],
            'analysis_report': {'analysis_timestamp': '2025-08-24T10:30:00Z'}
        }
        
        # Test validation
        result = engine.validate_removal_safety(analysis_data)
        
        # Verify successful validation
        assert result['success'] is True
        assert 'validation_report' in result
        assert 'safety_checks' in result
        assert 'removal_recommendations' in result
        
        validation_report = result['validation_report']
        assert validation_report['safety_score'] == 100.0  # All checks should pass
        assert validation_report['removal_recommendation'] == "APPROVED"
        assert validation_report['risk_level'] == "LOW"
        
        # Verify all LTMC tools were called
        mock_config.assert_called_once()
        mock_cache.assert_called_once()
        mock_graph.assert_called_once()
        mock_blueprint.assert_called_once()
        mock_pattern.assert_called_once()
        mock_memory.assert_called_once()
        
        # Verify state transitions
        assert mock_core.state_manager.transition_agent_state.call_count == 2  # ACTIVE, then COMPLETED
    
    @patch('ltms.coordination.safety_validation_engine.config_action')
    @patch('ltms.coordination.safety_validation_engine.cache_action')
    @patch('ltms.coordination.safety_validation_engine.graph_action')
    @patch('ltms.coordination.safety_validation_engine.blueprint_action')
    @patch('ltms.coordination.safety_validation_engine.pattern_action')
    @patch('ltms.coordination.safety_validation_engine.memory_action')
    def test_validate_removal_safety_partial_failures(self, mock_memory, mock_pattern, mock_blueprint,
                                                     mock_graph, mock_cache, mock_config):
        """Test safety validation with some tool failures"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        # Setup mocks with some failures
        mock_config.return_value = {'success': False, 'error': 'Config invalid'}
        mock_cache.return_value = {'success': True, 'status': 'healthy'}
        mock_graph.return_value = {'success': False, 'error': 'Graph unavailable'}
        mock_blueprint.return_value = {'success': True, 'summary': 'complexity_ok'}
        mock_pattern.return_value = {'success': True, 'functions': []}
        mock_memory.return_value = {'success': True, 'doc_id': 790}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "partial_failure_test"
        mock_core.coordinator.conversation_id = "partial_failure_conv"
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        # Test with insufficient functional tools
        analysis_data = {
            'legacy_decorators': [],
            'functional_tools': [
                {'name': 'memory_action'}, {'name': 'chat_action'}  # Only 2 tools
            ]
        }
        
        result = engine.validate_removal_safety(analysis_data)
        
        # Should still succeed but with lower score
        assert result['success'] is True
        validation_report = result['validation_report']
        
        # Safety score should be reduced due to failures
        assert validation_report['safety_score'] < 100.0
        assert validation_report['removal_recommendation'] in ["APPROVED_WITH_CAUTION", "REQUIRES_REVIEW"]
        assert validation_report['risk_level'] in ["MEDIUM", "HIGH"]
        
        # Verify failed checks
        safety_checks = result['safety_checks']
        failed_checks = [check for check in safety_checks if check['status'] == 'FAIL']
        assert len(failed_checks) >= 2  # At least config and functional_tools
    
    @patch('ltms.coordination.safety_validation_engine.config_action')
    @patch('ltms.coordination.safety_validation_engine.cache_action')
    @patch('ltms.coordination.safety_validation_engine.graph_action')
    @patch('ltms.coordination.safety_validation_engine.blueprint_action')
    @patch('ltms.coordination.safety_validation_engine.pattern_action')
    @patch('ltms.coordination.safety_validation_engine.memory_action')
    def test_validate_removal_safety_scoring_system(self, mock_memory, mock_pattern, mock_blueprint,
                                                   mock_graph, mock_cache, mock_config):
        """Test safety validation scoring system logic"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        # Setup mocks for specific scoring scenarios
        mock_config.return_value = {'success': True}
        mock_cache.return_value = {'success': True}
        mock_graph.return_value = {'success': False}  # 1 failure
        mock_blueprint.return_value = {'success': False}  # 1 failure
        mock_pattern.return_value = {'success': True}
        mock_memory.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "scoring_test"
        mock_core.coordinator.conversation_id = "scoring_conv"
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        # Analysis data with exactly 11 functional tools
        analysis_data = {
            'functional_tools': [{'name': f'tool_{i}'} for i in range(11)]
        }
        
        result = engine.validate_removal_safety(analysis_data)
        
        # Should have 4/6 checks passed = 66.7% score
        validation_report = result['validation_report']
        expected_score = (4.0 / 6.0) * 100  # 4 passed out of 6 total checks
        assert abs(validation_report['safety_score'] - expected_score) < 1.0
        
        # Score < 75% should be REQUIRES_REVIEW
        assert validation_report['removal_recommendation'] == "REQUIRES_REVIEW"
        assert validation_report['risk_level'] == "HIGH"
    
    @patch('ltms.coordination.safety_validation_engine.config_action')
    def test_validate_removal_safety_exception_handling(self, mock_config):
        """Test safety validation exception handling"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_manager import StateTransition
        
        # Setup mock to raise exception
        mock_config.side_effect = Exception("LTMC tool failure")
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        result = engine.validate_removal_safety({})
        
        # Should handle exception gracefully
        assert result['success'] is False
        assert 'error' in result
        assert "LTMC tool failure" in result['error']
        
        # Should transition to ERROR state
        mock_core.state_manager.transition_agent_state.assert_called_once()
        error_call = mock_core.state_manager.transition_agent_state.call_args
        assert error_call[0][1] == AgentStatus.ERROR
        assert error_call[0][2] == StateTransition.FAIL
    
    @patch('ltms.coordination.safety_validation_engine.config_action')
    @patch('ltms.coordination.safety_validation_engine.cache_action') 
    @patch('ltms.coordination.safety_validation_engine.graph_action')
    @patch('ltms.coordination.safety_validation_engine.blueprint_action')
    @patch('ltms.coordination.safety_validation_engine.pattern_action')
    @patch('ltms.coordination.safety_validation_engine.memory_action')
    def test_validate_removal_safety_comprehensive_checks(self, mock_memory, mock_pattern, mock_blueprint,
                                                        mock_graph, mock_cache, mock_config):
        """Test all safety checks are properly implemented"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        # Setup all mocks to succeed
        mock_config.return_value = {'success': True}
        mock_cache.return_value = {'success': True, 'status': 'healthy'}
        mock_graph.return_value = {'success': True}
        mock_blueprint.return_value = {'success': True, 'summary': 'analysis_complete'}
        mock_pattern.return_value = {'success': True}
        mock_memory.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "comprehensive_test"
        mock_core.coordinator.conversation_id = "comprehensive_conv"
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        analysis_data = {'functional_tools': [{'name': f'tool_{i}'} for i in range(11)]}
        result = engine.validate_removal_safety(analysis_data)
        
        # Verify all expected safety checks are present
        safety_checks = result['safety_checks']
        check_names = [check['check'] for check in safety_checks]
        
        expected_checks = [
            'functional_tools_available',
            'configuration_valid',
            'cache_healthy',
            'dependency_analysis_complete',
            'complexity_within_bounds',
            'usage_patterns_analyzed'
        ]
        
        for expected_check in expected_checks:
            assert expected_check in check_names
        
        # Verify all checks passed
        for check in safety_checks:
            assert check['status'] == 'PASS'
            assert 'description' in check
            assert 'details' in check
    
    @patch('ltms.coordination.safety_validation_engine.memory_action')
    @patch('ltms.coordination.safety_validation_engine.graph_action')
    def test_ltmc_storage_integration(self, mock_graph, mock_memory):
        """Test LTMC storage integration for validation reports"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        # Mock successful storage operations
        mock_memory.return_value = {'success': True, 'doc_id': 999}
        mock_graph.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "storage_test"
        mock_core.coordinator.conversation_id = "storage_conv"
        mock_core.state_manager = Mock()
        
        # Mock other tools to avoid complications
        with patch('ltms.coordination.safety_validation_engine.config_action', return_value={'success': True}):
            with patch('ltms.coordination.safety_validation_engine.cache_action', return_value={'success': True}):
                with patch('ltms.coordination.safety_validation_engine.blueprint_action', return_value={'success': True}):
                    with patch('ltms.coordination.safety_validation_engine.pattern_action', return_value={'success': True}):
                        
                        engine = SafetyValidationEngine(mock_core)
                        analysis_data = {'functional_tools': [{'name': f'tool_{i}'} for i in range(11)]}
                        
                        result = engine.validate_removal_safety(analysis_data)
        
        # Verify LTMC storage was called correctly
        mock_memory.assert_called()
        storage_call = None
        for call in mock_memory.call_args_list:
            if call[1]['action'] == 'store' and 'safety_validation_report_' in call[1]['file_name']:
                storage_call = call
                break
        
        assert storage_call is not None
        assert 'safety_validation' in storage_call[1]['tags']
        assert 'storage_test' in storage_call[1]['tags']
        assert storage_call[1]['conversation_id'] == 'storage_conv'
        
        # Verify graph relationship creation
        mock_graph.assert_called()
        graph_calls = [call for call in mock_graph.call_args_list if call[1]['action'] == 'link']
        assert len(graph_calls) >= 1
        
        graph_call = graph_calls[0]
        assert 'safety_validation_' in graph_call[1]['source_entity']
        assert graph_call[1]['relationship'] == 'validates_safety_of'
        assert 'safety_score' in graph_call[1]['properties']
    
    def test_validation_report_structure(self):
        """Test validation report contains all required fields"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "report_test"
        mock_core.state_manager = Mock()
        
        # Mock all LTMC tools
        with patch('ltms.coordination.safety_validation_engine.config_action', return_value={'success': True}):
            with patch('ltms.coordination.safety_validation_engine.cache_action', return_value={'success': True}):
                with patch('ltms.coordination.safety_validation_engine.graph_action', return_value={'success': True}):
                    with patch('ltms.coordination.safety_validation_engine.blueprint_action', return_value={'success': True}):
                        with patch('ltms.coordination.safety_validation_engine.pattern_action', return_value={'success': True}):
                            with patch('ltms.coordination.safety_validation_engine.memory_action', return_value={'success': True}):
                                
                                engine = SafetyValidationEngine(mock_core)
                                analysis_data = {
                                    'legacy_decorators': [{'name': 'test_tool'}],
                                    'functional_tools': [{'name': f'tool_{i}'} for i in range(11)],
                                    'analysis_report': {'analysis_timestamp': '2025-08-24T10:30:00Z'}
                                }
                                
                                result = engine.validate_removal_safety(analysis_data)
        
        # Verify report structure
        validation_report = result['validation_report']
        
        required_fields = [
            'validation_timestamp', 'agent_id', 'coordinator_task', 'safety_score',
            'risk_level', 'removal_recommendation', 'safety_checks', 
            'analysis_input_summary', 'validation_tools_used', 'next_steps'
        ]
        
        for field in required_fields:
            assert field in validation_report, f"Missing required field: {field}"
        
        # Verify field types and values
        assert isinstance(validation_report['validation_timestamp'], str)
        assert validation_report['agent_id'] == "safety_validator"
        assert isinstance(validation_report['safety_score'], float)
        assert validation_report['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
        assert validation_report['removal_recommendation'] in ['APPROVED', 'APPROVED_WITH_CAUTION', 'REQUIRES_REVIEW']
        assert isinstance(validation_report['safety_checks'], list)
        assert isinstance(validation_report['validation_tools_used'], list)
        assert isinstance(validation_report['next_steps'], list)


class TestSafetyValidationEngineIntegration:
    """Test SafetyValidationEngine integration scenarios"""
    
    def test_integration_with_safety_validation_core(self):
        """Test SafetyValidationEngine integration with SafetyValidationCore"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Create integrated system
        mock_coordinator = Mock()
        mock_coordinator.task_id = "integration_test"
        mock_coordinator.conversation_id = "integration_conv"
        mock_state_manager = Mock()
        
        core = SafetyValidationCore(mock_coordinator, mock_state_manager)
        engine = SafetyValidationEngine(core)
        
        # Verify integration
        assert engine.core == core
        assert engine.core.coordinator == mock_coordinator
        assert engine.core.state_manager == mock_state_manager
    
    def test_integration_with_ltmc_tools_comprehensive(self):
        """Test comprehensive integration with all LTMC tools"""
        from ltms.coordination.safety_validation_engine import SafetyValidationEngine
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "ltmc_integration"
        mock_core.coordinator.conversation_id = "ltmc_conv"
        mock_core.state_manager = Mock()
        
        engine = SafetyValidationEngine(mock_core)
        
        # Track all LTMC tool calls
        ltmc_tools = [
            'config_action', 'cache_action', 'graph_action', 
            'blueprint_action', 'pattern_action', 'memory_action'
        ]
        
        with patch.multiple(
            'ltms.coordination.safety_validation_engine',
            config_action=Mock(return_value={'success': True}),
            cache_action=Mock(return_value={'success': True}),
            graph_action=Mock(return_value={'success': True}),
            blueprint_action=Mock(return_value={'success': True}),
            pattern_action=Mock(return_value={'success': True}),
            memory_action=Mock(return_value={'success': True})
        ) as mocks:
            
            analysis_data = {'functional_tools': [{'name': f'tool_{i}'} for i in range(11)]}
            result = engine.validate_removal_safety(analysis_data)
            
            # Verify all tools were called
            for tool_name in ltmc_tools:
                assert mocks[tool_name].called, f"LTMC tool {tool_name} was not called"
            
            assert result['success'] is True


# Pytest fixtures for engine testing
@pytest.fixture
def mock_core():
    """Fixture providing mock SafetyValidationCore for engine testing"""
    core = Mock()
    core.agent_id = "safety_validator"
    core.coordinator = Mock()
    core.coordinator.task_id = "fixture_task"
    core.coordinator.conversation_id = "fixture_conv"
    core.state_manager = Mock()
    return core

@pytest.fixture
def safety_validation_engine(mock_core):
    """Fixture providing SafetyValidationEngine instance"""
    from ltms.coordination.safety_validation_engine import SafetyValidationEngine
    return SafetyValidationEngine(mock_core)

@pytest.fixture
def sample_analysis_data():
    """Fixture providing sample analysis data for validation testing"""
    return {
        'legacy_decorators': [
            {'name': 'memory_tool', 'file': '/ltmc/memory.py', 'line': 42},
            {'name': 'chat_tool', 'file': '/ltmc/chat.py', 'line': 28}
        ],
        'functional_tools': [
            {'name': 'memory_action'}, {'name': 'chat_action'}, {'name': 'todo_action'},
            {'name': 'unix_action'}, {'name': 'pattern_action'}, {'name': 'blueprint_action'},
            {'name': 'cache_action'}, {'name': 'graph_action'}, {'name': 'documentation_action'},
            {'name': 'sync_action'}, {'name': 'config_action'}
        ],
        'analysis_report': {
            'analysis_timestamp': '2025-08-24T10:30:00Z',
            'total_decorators': 2,
            'total_tools': 11
        }
    }

@pytest.fixture
def mock_all_ltmc_tools():
    """Fixture providing mocks for all LTMC tools used in validation"""
    with patch.multiple(
        'ltms.coordination.safety_validation_engine',
        config_action=Mock(return_value={'success': True}),
        cache_action=Mock(return_value={'success': True, 'status': 'healthy'}),
        graph_action=Mock(return_value={'success': True}),
        blueprint_action=Mock(return_value={'success': True, 'summary': 'ok'}),
        pattern_action=Mock(return_value={'success': True}),
        memory_action=Mock(return_value={'success': True, 'doc_id': 888})
    ) as mocks:
        yield mocks