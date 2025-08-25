"""
Comprehensive TDD tests for SafetyValidator class.
Tests the agent that will be extracted from legacy_removal_coordinated_agents.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


class TestSafetyValidator:
    """Test SafetyValidator agent class - to be extracted from legacy_removal_coordinated_agents.py"""
    
    def test_safety_validator_creation(self):
        """Test SafetyValidator class can be instantiated with coordinator and state manager"""
        from ltms.coordination.safety_validator import SafetyValidator
        from ltms.coordination.agent_coordination_framework import LTMCAgentCoordinator
        from ltms.coordination.agent_state_manager import LTMCAgentStateManager
        
        coordinator = Mock(spec=LTMCAgentCoordinator)
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock(spec=LTMCAgentStateManager)
        
        validator = SafetyValidator(coordinator, state_manager)
        
        assert validator.agent_id == "safety_validator"
        assert validator.agent_type == "ltmc-safety-validator"
        assert validator.coordinator == coordinator
        assert validator.state_manager == state_manager
        assert hasattr(validator, 'message_broker')
        assert hasattr(validator, 'validation_report')
        assert hasattr(validator, 'safety_checks')
        assert hasattr(validator, 'removal_plan')
        assert isinstance(validator.validation_report, dict)
        assert isinstance(validator.safety_checks, list)
        assert isinstance(validator.removal_plan, dict)
    
    def test_initialize_agent_method_exists(self):
        """Test that initialize_agent method exists and is callable"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        validator = SafetyValidator(coordinator, state_manager)
        
        assert hasattr(validator, 'initialize_agent')
        assert callable(validator.initialize_agent)
    
    def test_validate_removal_safety_method_exists(self):
        """Test that validate_removal_safety method exists and is callable"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        validator = SafetyValidator(coordinator, state_manager)
        
        assert hasattr(validator, 'validate_removal_safety')
        assert callable(validator.validate_removal_safety)
    
    @patch('ltms.coordination.safety_validator.chat_action')
    @patch('ltms.coordination.safety_validator.memory_action')
    def test_initialize_agent_successful_registration(self, mock_memory_action, mock_chat_action):
        """Test successful agent initialization and registration"""
        from ltms.coordination.safety_validator import SafetyValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        state_manager.create_agent_state.return_value = True
        
        mock_chat_action.return_value = {'success': True}
        mock_memory_action.return_value = {'success': True}
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Test initialization
        result = validator.initialize_agent()
        
        # Verify successful initialization
        assert result is True
        
        # Verify coordinator registration was called correctly
        coordinator.register_agent.assert_called_once_with(
            "safety_validator",
            "ltmc-safety-validator",
            task_scope=["safety_validation", "dependency_analysis", "removal_planning"],
            dependencies=["legacy_code_analyzer"],
            outputs=["safety_report", "removal_plan", "validation_results"]
        )
        
        # Verify state manager create_agent_state was called
        state_manager.create_agent_state.assert_called_once()
        call_args = state_manager.create_agent_state.call_args
        assert call_args[0][0] == "safety_validator"  # agent_id
        assert call_args[0][1] == AgentStatus.INITIALIZING  # status
        
        # Verify state data structure
        state_data = call_args[0][2]
        assert state_data["agent_id"] == "safety_validator"
        assert state_data["task_scope"] == ["safety_validation", "dependency_analysis", "removal_planning"]
        assert state_data["current_task"] == "initialization"
        
        # Verify LTMC tools were used
        assert mock_chat_action.called
    
    def test_initialize_agent_coordinator_registration_failure(self):
        """Test initialization handles coordinator registration failure"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        # Setup coordinator to fail registration
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = False
        
        state_manager = Mock()
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Test initialization
        result = validator.initialize_agent()
        
        # Should return False on registration failure
        assert result is False
        
        # State manager should not be called if registration fails
        state_manager.create_agent_state.assert_not_called()
    
    @patch('ltms.coordination.safety_validator.blueprint_action')
    @patch('ltms.coordination.safety_validator.pattern_action')
    @patch('ltms.coordination.safety_validator.memory_action')
    def test_validate_removal_safety_dependency_analysis(self, mock_memory_action, mock_pattern_action, mock_blueprint_action):
        """Test safety validation with dependency analysis"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        # Setup mock responses for LTMC tools
        mock_pattern_action.return_value = {
            'success': True,
            'dependencies': [
                {'name': 'legacy_tool_1', 'used_by': ['module_a.py', 'module_b.py']},
                {'name': 'legacy_tool_2', 'used_by': []}
            ]
        }
        
        mock_blueprint_action.return_value = {
            'success': True,
            'dependencies': [
                {'source': 'legacy_tool_1', 'target': 'memory_action', 'confidence': 0.95}
            ]
        }
        
        mock_memory_action.return_value = {'success': True, 'doc_id': 456}
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Sample analysis data from LegacyCodeAnalyzer
        analysis_data = {
            'legacy_decorators': [
                {'name': 'legacy_tool_1', 'file': 'legacy.py', 'line': 10},
                {'name': 'legacy_tool_2', 'file': 'legacy.py', 'line': 20}
            ],
            'functional_tools': [
                {'name': 'memory_action', 'file': 'consolidated.py'}
            ]
        }
        
        # Test validation
        result = validator.validate_removal_safety(analysis_data)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'validation_report' in result
        assert 'safety_checks' in result
        assert 'removal_recommendations' in result
        
        # Verify LTMC tools were used
        assert mock_pattern_action.called
        assert mock_blueprint_action.called
        assert mock_memory_action.called
    
    @patch('ltms.coordination.safety_validator.unix_action')
    @patch('ltms.coordination.safety_validator.pattern_action')
    def test_validate_removal_safety_usage_scanning(self, mock_pattern_action, mock_unix_action):
        """Test that safety validation scans for legacy tool usage"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        # Setup mocks for usage scanning
        mock_unix_action.return_value = {
            'success': True,
            'files': ['module_a.py', 'module_b.py', 'test_module.py']
        }
        
        mock_pattern_action.return_value = {
            'success': True,
            'usages': [
                {'file': 'module_a.py', 'line': 45, 'usage': 'legacy_tool_1()'},
                {'file': 'test_module.py', 'line': 12, 'usage': 'legacy_tool_1()'}
            ]
        }
        
        with patch('ltms.coordination.safety_validator.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            validator = SafetyValidator(coordinator, state_manager)
            
            analysis_data = {
                'legacy_decorators': [
                    {'name': 'legacy_tool_1', 'file': 'legacy.py'}
                ]
            }
            
            result = validator.validate_removal_safety(analysis_data)
            
            # Verify usage scanning was performed
            assert mock_unix_action.called
            assert mock_pattern_action.called
            
            # Verify safety analysis identified usage
            assert result['success'] is True
            assert len(validator.safety_checks) > 0
    
    @patch('ltms.coordination.safety_validator.memory_action')
    def test_validate_removal_safety_creates_safety_report(self, mock_memory_action):
        """Test that validation creates comprehensive safety report in LTMC"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_memory_action.return_value = {'success': True, 'doc_id': 789}
        
        with patch('ltms.coordination.safety_validator.pattern_action') as mock_pattern:
            mock_pattern.return_value = {'success': True, 'dependencies': []}
            
            with patch('ltms.coordination.safety_validator.unix_action') as mock_unix:
                mock_unix.return_value = {'success': True, 'files': []}
                
                validator = SafetyValidator(coordinator, state_manager)
                
                analysis_data = {
                    'legacy_decorators': [
                        {'name': 'test_tool', 'file': 'test.py'}
                    ]
                }
                
                validator.validate_removal_safety(analysis_data)
                
                # Verify memory_action was called for storing safety report
                assert mock_memory_action.called
                
                # Check for safety report storage
                storage_calls = [call for call in mock_memory_action.call_args_list if call[1].get('action') == 'store']
                assert len(storage_calls) > 0
                
                storage_call = storage_calls[0]
                assert 'safety_validation' in storage_call[1]['file_name']
                assert 'safety_validation' in storage_call[1]['tags']
    
    def test_create_removal_plan_method_exists(self):
        """Test that create_removal_plan method exists and is callable"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        validator = SafetyValidator(coordinator, state_manager)
        
        assert hasattr(validator, 'create_removal_plan')
        assert callable(validator.create_removal_plan)
    
    @patch('ltms.coordination.safety_validator.todo_action')
    @patch('ltms.coordination.safety_validator.blueprint_action')
    def test_create_removal_plan_generates_tasks(self, mock_blueprint_action, mock_todo_action):
        """Test that create_removal_plan generates structured removal tasks"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_blueprint_action.return_value = {'success': True}
        mock_todo_action.return_value = {'success': True, 'task_id': 'removal_task_1'}
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Set up validation results
        validator.safety_checks = [
            {'tool': 'legacy_tool_1', 'safe_to_remove': True, 'replacement': 'memory_action'},
            {'tool': 'legacy_tool_2', 'safe_to_remove': False, 'dependencies': ['module_x']}
        ]
        
        result = validator.create_removal_plan()
        
        # Verify removal plan structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'removal_plan' in result
        assert 'tasks_created' in result
        
        # Verify LTMC tools were used
        assert mock_blueprint_action.called
        assert mock_todo_action.called
    
    @patch('ltms.coordination.safety_validator.graph_action')
    def test_validate_removal_safety_creates_graph_relationships(self, mock_graph_action):
        """Test that validation creates knowledge graph relationships"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_graph_action.return_value = {'success': True}
        
        with patch('ltms.coordination.safety_validator.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            with patch('ltms.coordination.safety_validator.pattern_action') as mock_pattern:
                mock_pattern.return_value = {'success': True, 'dependencies': []}
                
                validator = SafetyValidator(coordinator, state_manager)
                
                analysis_data = {
                    'legacy_decorators': [
                        {'name': 'test_tool', 'file': 'test.py'}
                    ]
                }
                
                validator.validate_removal_safety(analysis_data)
                
                # Verify graph relationships were created
                assert mock_graph_action.called
                
                graph_calls = mock_graph_action.call_args_list
                link_calls = [call for call in graph_calls if call[1].get('action') == 'link']
                assert len(link_calls) > 0
    
    def test_message_broker_integration(self):
        """Test that validator properly integrates with message broker"""
        from ltms.coordination.safety_validator import SafetyValidator
        from ltms.coordination.mcp_communication_patterns import LTMCMessageBroker
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Verify message broker is created
        assert hasattr(validator, 'message_broker')
        assert isinstance(validator.message_broker, LTMCMessageBroker)
        assert validator.message_broker.conversation_id == "test_conversation"
    
    @patch('ltms.coordination.safety_validator.cache_action')
    def test_validate_removal_safety_uses_caching(self, mock_cache_action):
        """Test that validation uses caching for performance"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        
        mock_cache_action.return_value = {'success': True, 'cached': False}
        
        with patch('ltms.coordination.safety_validator.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            with patch('ltms.coordination.safety_validator.pattern_action') as mock_pattern:
                mock_pattern.return_value = {'success': True, 'dependencies': []}
                
                validator = SafetyValidator(coordinator, state_manager)
                
                analysis_data = {
                    'legacy_decorators': [{'name': 'test_tool', 'file': 'test.py'}]
                }
                
                validator.validate_removal_safety(analysis_data)
                
                # Verify caching was used
                assert mock_cache_action.called
    
    def test_validate_removal_safety_error_handling(self):
        """Test validation handles errors gracefully"""
        from ltms.coordination.safety_validator import SafetyValidator
        
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        state_manager = Mock()
        state_manager.transition_agent_state = Mock()
        
        # Setup pattern_action to fail
        with patch('ltms.coordination.safety_validator.pattern_action') as mock_pattern:
            mock_pattern.side_effect = Exception("Analysis failed")
            
            validator = SafetyValidator(coordinator, state_manager)
            
            analysis_data = {'legacy_decorators': []}
            
            result = validator.validate_removal_safety(analysis_data)
            
            # Should handle error gracefully
            assert result['success'] is False
            assert 'error' in result
            
            # Should transition to error state
            state_manager.transition_agent_state.assert_called()


class TestSafetyValidatorIntegration:
    """Test integration scenarios for SafetyValidator"""
    
    @patch('ltms.coordination.safety_validator.memory_action')
    @patch('ltms.coordination.safety_validator.blueprint_action')
    @patch('ltms.coordination.safety_validator.pattern_action')
    @patch('ltms.coordination.safety_validator.unix_action')
    @patch('ltms.coordination.safety_validator.chat_action')
    def test_complete_validation_workflow(self, mock_chat, mock_unix, mock_pattern, mock_blueprint, mock_memory):
        """Test complete safety validation workflow"""
        from ltms.coordination.safety_validator import SafetyValidator
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup comprehensive mocks
        coordinator = Mock()
        coordinator.conversation_id = "test_conversation"
        coordinator.register_agent.return_value = True
        
        state_manager = Mock()
        state_manager.create_agent_state.return_value = True
        
        mock_chat.return_value = {'success': True}
        mock_memory.return_value = {'success': True, 'doc_id': 999}
        mock_unix.return_value = {'success': True, 'files': ['test.py']}
        mock_pattern.return_value = {'success': True, 'dependencies': [], 'usages': []}
        mock_blueprint.return_value = {'success': True, 'dependencies': []}
        
        validator = SafetyValidator(coordinator, state_manager)
        
        # Test complete workflow
        init_result = validator.initialize_agent()
        assert init_result is True
        
        analysis_data = {
            'legacy_decorators': [
                {'name': 'legacy_tool_1', 'file': 'legacy.py', 'line': 10}
            ],
            'functional_tools': [
                {'name': 'memory_action', 'file': 'consolidated.py'}
            ]
        }
        
        validation_result = validator.validate_removal_safety(analysis_data)
        assert validation_result['success'] is True
        
        removal_plan = validator.create_removal_plan()
        assert removal_plan['success'] is True
        
        # Verify all LTMC tools were used appropriately
        assert mock_chat.called
        assert mock_unix.called
        assert mock_pattern.called
        assert mock_blueprint.called
        assert mock_memory.called


# Pytest fixtures for common test data
@pytest.fixture
def mock_coordinator():
    """Fixture providing a mock LTMCAgentCoordinator"""
    coordinator = Mock()
    coordinator.conversation_id = "test_conversation"
    coordinator.register_agent.return_value = True
    return coordinator

@pytest.fixture
def mock_state_manager():
    """Fixture providing a mock LTMCAgentStateManager"""
    state_manager = Mock()
    state_manager.create_agent_state.return_value = True
    return state_manager

@pytest.fixture
def validator_instance(mock_coordinator, mock_state_manager):
    """Fixture providing a SafetyValidator instance"""
    from ltms.coordination.safety_validator import SafetyValidator
    return SafetyValidator(mock_coordinator, mock_state_manager)

@pytest.fixture
def sample_analysis_data():
    """Fixture providing sample analysis data from LegacyCodeAnalyzer"""
    return {
        'legacy_decorators': [
            {
                'name': 'legacy_memory_tool',
                'file': 'ltms/tools/legacy.py',
                'line': 45,
                'decorators': ['@mcp.tool'],
                'signature': 'def legacy_memory_tool(action: str) -> dict'
            }
        ],
        'functional_tools': [
            {
                'name': 'memory_action',
                'file': 'ltms/tools/consolidated.py',
                'type': 'functional_replacement',
                'status': 'active'
            }
        ],
        'analysis_report': {
            'total_legacy_decorators': 1,
            'total_functional_tools': 1
        }
    }

@pytest.fixture
def sample_safety_checks():
    """Fixture providing sample safety check results"""
    return [
        {
            'tool': 'legacy_memory_tool',
            'safe_to_remove': True,
            'replacement': 'memory_action',
            'confidence': 0.95,
            'dependencies': [],
            'usage_count': 3
        }
    ]