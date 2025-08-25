"""
Comprehensive TDD tests for Workflow Initialization extraction.
Tests workflow setup and coordination framework integration.

Following TDD methodology: Tests written FIRST before extraction.
WorkflowInitialization will handle __init__ and framework setup.
MANDATORY: Uses ALL required LTMC tools (chat_action, todo_action for setup logging).
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestWorkflowInitialization:
    """Test WorkflowInitialization class - to be extracted from legacy_removal_workflow.py"""
    
    def test_workflow_initialization_creation(self):
        """Test WorkflowInitialization can be instantiated"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        assert hasattr(initialization, 'workflow_id')
        assert hasattr(initialization, 'conversation_id')
        assert hasattr(initialization, 'coordinator')
        assert hasattr(initialization, 'state_manager')
        assert hasattr(initialization, 'workflow_orchestrator')
        assert hasattr(initialization, 'analyzer')
        assert hasattr(initialization, 'validator')
        assert hasattr(initialization, 'workflow_results')
        
        # Verify ID generation
        assert initialization.workflow_id.startswith("legacy_removal_workflow_")
        assert initialization.conversation_id.startswith("legacy_removal_")
        assert isinstance(initialization.workflow_results, dict)
    
    @patch('ltms.coordination.workflow_initialization.chat_action')
    @patch('ltms.coordination.workflow_initialization.todo_action')
    def test_initialize_workflow_success(self, mock_todo, mock_chat):
        """Test successful workflow initialization with LTMC tools integration"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        # Setup LTMC tool mocks - MANDATORY
        mock_todo.return_value = {'success': True, 'task_id': 'workflow_init_task'}
        mock_chat.return_value = {'success': True}
        
        initialization = WorkflowInitialization()
        
        # Mock agent initialization
        initialization.analyzer.initialize_agent = Mock(return_value=True)
        initialization.validator.initialize_agent = Mock(return_value=True)
        
        # Test initialization
        result = initialization.initialize_workflow()
        
        # Verify success
        assert result['success'] is True
        assert 'workflow_id' in result
        assert 'conversation_id' in result
        assert result['agents_initialized'] == 2
        
        # Verify agents were initialized
        initialization.analyzer.initialize_agent.assert_called_once()
        initialization.validator.initialize_agent.assert_called_once()
        
        # Verify LTMC tools were called - MANDATORY
        
        # 1. todo_action - MANDATORY Tool 2
        mock_todo.assert_called_once()
        todo_call = mock_todo.call_args
        assert todo_call[1]['action'] == 'add'
        assert 'Execute coordinated legacy removal workflow' in todo_call[1]['content']
        assert todo_call[1]['conversation_id'] == initialization.conversation_id
        assert todo_call[1]['role'] == 'system'
        
        # 2. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Phase 1 Complete: All agents initialized' in chat_call[1]['message']
        assert chat_call[1]['conversation_id'] == initialization.conversation_id
        assert chat_call[1]['role'] == 'system'
    
    def test_initialize_workflow_analyzer_failure(self):
        """Test workflow initialization when analyzer fails"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Mock analyzer failure
        initialization.analyzer.initialize_agent = Mock(return_value=False)
        initialization.validator.initialize_agent = Mock(return_value=True)
        
        # Test initialization failure
        with patch('ltms.coordination.workflow_initialization.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            
            result = initialization.initialize_workflow()
        
        # Verify failure
        assert result['success'] is False
        assert 'Agent initialization failed' in result['error']
        
        # Verify both agents were attempted
        initialization.analyzer.initialize_agent.assert_called_once()
        initialization.validator.initialize_agent.assert_called_once()
    
    def test_initialize_workflow_validator_failure(self):
        """Test workflow initialization when validator fails"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Mock validator failure
        initialization.analyzer.initialize_agent = Mock(return_value=True)
        initialization.validator.initialize_agent = Mock(return_value=False)
        
        # Test initialization failure
        with patch('ltms.coordination.workflow_initialization.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            
            result = initialization.initialize_workflow()
        
        # Verify failure
        assert result['success'] is False
        assert 'Agent initialization failed' in result['error']
    
    def test_initialize_workflow_exception_handling(self):
        """Test workflow initialization exception handling"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Mock exception during initialization
        initialization.analyzer.initialize_agent = Mock(side_effect=Exception("Analyzer service unavailable"))
        initialization.validator.initialize_agent = Mock(return_value=True)
        
        # Test exception handling
        with patch('ltms.coordination.workflow_initialization.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            
            result = initialization.initialize_workflow()
        
        # Should handle gracefully and return failure
        assert result['success'] is False
        assert 'Analyzer service unavailable' in result['error']
    
    def test_workflow_id_generation_uniqueness(self):
        """Test workflow ID generation produces unique IDs"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        # Create multiple instances
        init_1 = WorkflowInitialization()
        time.sleep(0.01)  # Ensure different timestamps
        init_2 = WorkflowInitialization()
        
        # Verify uniqueness
        assert init_1.workflow_id != init_2.workflow_id
        assert init_1.conversation_id != init_2.conversation_id
        
        # Verify format consistency
        assert init_1.workflow_id.startswith("legacy_removal_workflow_")
        assert init_2.workflow_id.startswith("legacy_removal_workflow_")
        assert init_1.conversation_id.startswith("legacy_removal_")
        assert init_2.conversation_id.startswith("legacy_removal_")
    
    def test_coordination_framework_setup(self):
        """Test coordination framework components are properly set up"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Verify coordinator setup
        assert hasattr(initialization.coordinator, 'task_id')
        assert hasattr(initialization.coordinator, 'conversation_id')
        
        # Verify state manager integration
        assert hasattr(initialization.state_manager, 'coordination_id')
        
        # Verify workflow orchestrator
        assert hasattr(initialization.workflow_orchestrator, 'workflow_id')
        assert hasattr(initialization.workflow_orchestrator, 'conversation_id')
        
        # Verify agent setup
        assert hasattr(initialization.analyzer, 'agent_id')
        assert hasattr(initialization.validator, 'agent_id')
    
    @patch('ltms.coordination.workflow_initialization.chat_action')
    @patch('ltms.coordination.workflow_initialization.todo_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_todo, mock_chat):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_todo.return_value = {'success': True, 'task_id': 'ltmc_comprehensive_task'}
        mock_chat.return_value = {'success': True}
        
        initialization = WorkflowInitialization()
        
        # Mock agent initialization
        initialization.analyzer.initialize_agent = Mock(return_value=True)
        initialization.validator.initialize_agent = Mock(return_value=True)
        
        # Test comprehensive initialization
        result = initialization.initialize_workflow()
        
        # Verify success
        assert result['success'] is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. todo_action - MANDATORY Tool 2
        mock_todo.assert_called_once()
        todo_call = mock_todo.call_args
        assert todo_call[1]['action'] == 'add'
        assert todo_call[1]['conversation_id'] == initialization.conversation_id
        assert todo_call[1]['role'] == 'system'
        
        # 2. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert chat_call[1]['conversation_id'] == initialization.conversation_id
        assert chat_call[1]['role'] == 'system'
    
    def test_workflow_results_initialization(self):
        """Test workflow results storage is properly initialized"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Verify initial state
        assert isinstance(initialization.workflow_results, dict)
        assert len(initialization.workflow_results) == 0
        
        # Verify can be updated
        test_data = {"test": "data", "initialization": True}
        initialization.workflow_results.update(test_data)
        
        assert initialization.workflow_results["test"] == "data"
        assert initialization.workflow_results["initialization"] is True
    
    def test_agent_reference_integration(self):
        """Test agent references are properly integrated"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Verify agents have proper coordination context
        assert initialization.analyzer.coordinator == initialization.coordinator
        assert initialization.analyzer.state_manager == initialization.state_manager
        assert initialization.validator.coordinator == initialization.coordinator
        assert initialization.validator.state_manager == initialization.state_manager
        
        # Verify agent IDs are distinct
        assert initialization.analyzer.agent_id != initialization.validator.agent_id
    
    def test_conversation_id_workflow_id_relationship(self):
        """Test conversation ID and workflow ID relationship"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Verify relationship
        assert initialization.workflow_id in initialization.conversation_id
        assert initialization.conversation_id.startswith("legacy_removal_")
        
        # Verify consistency across components
        assert initialization.coordinator.task_id == initialization.workflow_id
        assert initialization.workflow_orchestrator.workflow_id == initialization.workflow_id
        assert initialization.workflow_orchestrator.conversation_id == initialization.conversation_id


class TestWorkflowInitializationIntegration:
    """Test WorkflowInitialization integration scenarios"""
    
    def test_integration_with_coordination_framework(self):
        """Test integration with complete coordination framework"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Test that all coordination components are properly integrated
        assert initialization.coordinator is not None
        assert initialization.state_manager is not None
        assert initialization.workflow_orchestrator is not None
        
        # Test component relationships
        assert hasattr(initialization.state_manager, 'coordinator')
        assert initialization.workflow_orchestrator.workflow_id == initialization.workflow_id
    
    @patch('ltms.coordination.workflow_initialization.chat_action')
    @patch('ltms.coordination.workflow_initialization.todo_action')
    def test_end_to_end_initialization_workflow(self, mock_todo, mock_chat):
        """Test complete initialization workflow with all components"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        # Setup mocks
        mock_todo.return_value = {'success': True}
        mock_chat.return_value = {'success': True}
        
        initialization = WorkflowInitialization()
        
        # Mock successful agent initialization
        initialization.analyzer.initialize_agent = Mock(return_value=True)
        initialization.validator.initialize_agent = Mock(return_value=True)
        
        # Test complete workflow
        result = initialization.initialize_workflow()
        
        # Verify complete workflow succeeded
        assert result['success'] is True
        assert result['agents_initialized'] == 2
        
        # Verify all steps were executed
        mock_todo.assert_called_once()
        initialization.analyzer.initialize_agent.assert_called_once()
        initialization.validator.initialize_agent.assert_called_once()
        mock_chat.assert_called_once()
    
    def test_workflow_state_consistency(self):
        """Test workflow state consistency across initialization"""
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        
        initialization = WorkflowInitialization()
        
        # Test state consistency
        workflow_id = initialization.workflow_id
        conversation_id = initialization.conversation_id
        
        # Verify IDs remain consistent
        assert initialization.workflow_id == workflow_id
        assert initialization.conversation_id == conversation_id
        assert initialization.coordinator.task_id == workflow_id


# Pytest fixtures for workflow initialization testing
@pytest.fixture
def workflow_initialization():
    """Fixture providing WorkflowInitialization instance"""
    from ltms.coordination.workflow_initialization import WorkflowInitialization
    
    return WorkflowInitialization()

@pytest.fixture
def mock_all_ltmc_workflow_init_tools():
    """Fixture providing mocks for all LTMC tools used in workflow initialization"""
    with patch.multiple(
        'ltms.coordination.workflow_initialization',
        todo_action=Mock(return_value={'success': True, 'task_id': 'fixture_task'}),
        chat_action=Mock(return_value={'success': True})
    ) as mocks:
        yield mocks

@pytest.fixture
def mock_successful_agents(workflow_initialization):
    """Fixture providing workflow with successfully initialized agents"""
    workflow_initialization.analyzer.initialize_agent = Mock(return_value=True)
    workflow_initialization.validator.initialize_agent = Mock(return_value=True)
    return workflow_initialization