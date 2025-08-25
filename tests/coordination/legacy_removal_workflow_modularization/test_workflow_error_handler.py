"""
Comprehensive TDD tests for Workflow Error Handler extraction.
Tests error handling, rollback, and recovery mechanisms.

Following TDD methodology: Tests written FIRST before extraction.
WorkflowErrorHandler will handle exception management and error reporting.
MANDATORY: Uses ALL required LTMC tools (chat_action, memory_action for error logging).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestWorkflowErrorHandler:
    """Test WorkflowErrorHandler class - to be extracted from legacy_removal_workflow.py"""
    
    def test_workflow_error_handler_creation(self):
        """Test WorkflowErrorHandler can be instantiated"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        handler = WorkflowErrorHandler(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "test_workflow_id", "test_conversation_id"
        )
        
        assert hasattr(handler, 'coordinator')
        assert hasattr(handler, 'state_manager')
        assert hasattr(handler, 'analyzer')
        assert hasattr(handler, 'validator')
        assert hasattr(handler, 'workflow_id')
        assert hasattr(handler, 'conversation_id')
        assert handler.workflow_id == "test_workflow_id"
        assert handler.conversation_id == "test_conversation_id"
    
    @patch('ltms.coordination.workflow_error_handler.chat_action')
    @patch('ltms.coordination.workflow_error_handler.memory_action')
    def test_handle_workflow_error_success(self, mock_memory, mock_chat):
        """Test successful workflow error handling with LTMC tools integration"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Setup LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        mock_memory.return_value = {'success': True, 'doc_id': 123}
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "test_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "test_validator"
        
        handler = WorkflowErrorHandler(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "error_workflow_id", "error_conversation_id"
        )
        
        # Test error handling
        test_exception = Exception("Test workflow failure")
        result = handler.handle_workflow_error(test_exception, "test_phase")
        
        # Verify error handling response
        assert result['success'] is False
        assert result['workflow_id'] == "error_workflow_id"
        assert 'error' in result
        assert 'error_report' in result
        assert 'Test workflow failure' in result['error']
        
        # Verify error report structure
        error_report = result['error_report']
        assert error_report['workflow_id'] == "error_workflow_id"
        assert error_report['error_message'] == "Coordinated legacy removal workflow failed: Test workflow failure"
        assert error_report['workflow_status'] == "FAILED"
        assert error_report['error_phase'] == "test_phase"
        assert 'error_timestamp' in error_report
        
        # Verify LTMC tools were called - MANDATORY
        
        # 1. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'failed' in chat_call[1]['message']
        assert 'error_workflow_id' in chat_call[1]['message']
        assert chat_call[1]['conversation_id'] == 'error_conversation_id'
        assert chat_call[1]['role'] == 'system'
        
        # 2. memory_action - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'workflow_error_report_' in memory_call[1]['file_name']
        assert 'workflow_error' in memory_call[1]['tags']
        assert 'legacy_removal' in memory_call[1]['tags']
    
    def test_determine_failure_phase_agent_initialization(self):
        """Test failure phase detection for agent initialization phase"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Setup mocks for agent initialization failure
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.return_value = None  # Agent not found
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "init_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "init_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "init_failure_workflow", "init_failure_conv"
        )
        
        # Test failure phase detection
        phase = handler.determine_failure_phase()
        
        # Verify correct phase detection
        assert phase == "agent_initialization"
        
        # Verify state manager was queried for analyzer
        mock_state_manager.get_agent_state.assert_called_with("init_analyzer")
    
    def test_determine_failure_phase_legacy_analysis(self):
        """Test failure phase detection for legacy analysis phase"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup analyzer in error state
        error_snapshot = StateSnapshot(
            agent_id="analysis_analyzer",
            status=AgentStatus.ERROR,
            state_data={"error": "Analysis failed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="analysis_failure_test",
            conversation_id="analysis_failure_conv",
            metadata={"phase": "legacy_analysis"}
        )
        
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.return_value = error_snapshot
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "analysis_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "analysis_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "analysis_failure_workflow", "analysis_failure_conv"
        )
        
        # Test failure phase detection
        phase = handler.determine_failure_phase()
        
        # Verify correct phase detection
        assert phase == "legacy_analysis"
    
    def test_determine_failure_phase_safety_validation(self):
        """Test failure phase detection for safety validation phase"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup analyzer in active state (passed) but validator in error state
        active_snapshot = StateSnapshot(
            agent_id="validation_analyzer",
            status=AgentStatus.ACTIVE,
            state_data={"analysis": "completed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="validation_failure_test",
            conversation_id="validation_failure_conv",
            metadata={"phase": "analysis_complete"}
        )
        
        error_snapshot = StateSnapshot(
            agent_id="validation_validator",
            status=AgentStatus.ERROR,
            state_data={"error": "Validation failed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="validation_failure_test",
            conversation_id="validation_failure_conv",
            metadata={"phase": "safety_validation"}
        )
        
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.side_effect = [active_snapshot, error_snapshot]
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "validation_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "validation_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "validation_failure_workflow", "validation_failure_conv"
        )
        
        # Test failure phase detection
        phase = handler.determine_failure_phase()
        
        # Verify correct phase detection
        assert phase == "safety_validation"
        
        # Verify both agents were checked
        assert mock_state_manager.get_agent_state.call_count == 2
    
    def test_determine_failure_phase_workflow_coordination(self):
        """Test failure phase detection for workflow coordination phase"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup both agents in active state (coordination failure)
        active_snapshot_1 = StateSnapshot(
            agent_id="coord_analyzer",
            status=AgentStatus.ACTIVE,
            state_data={"coordination": "active"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="coord_failure_test",
            conversation_id="coord_failure_conv",
            metadata={"phase": "coordination"}
        )
        
        active_snapshot_2 = StateSnapshot(
            agent_id="coord_validator",
            status=AgentStatus.ACTIVE,
            state_data={"coordination": "active"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="coord_failure_test",
            conversation_id="coord_failure_conv",
            metadata={"phase": "coordination"}
        )
        
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.side_effect = [active_snapshot_1, active_snapshot_2]
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "coord_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "coord_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "coord_failure_workflow", "coord_failure_conv"
        )
        
        # Test failure phase detection
        phase = handler.determine_failure_phase()
        
        # Verify correct phase detection (both agents active = coordination failure)
        assert phase == "workflow_coordination"
    
    def test_determine_failure_phase_unknown(self):
        """Test failure phase detection when state detection fails"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Setup state manager to raise exception
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.side_effect = Exception("State manager unavailable")
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "unknown_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "unknown_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "unknown_failure_workflow", "unknown_failure_conv"
        )
        
        # Test failure phase detection with exception
        phase = handler.determine_failure_phase()
        
        # Verify unknown phase when detection fails
        assert phase == "unknown_phase"
    
    @patch('ltms.coordination.workflow_error_handler.chat_action')
    @patch('ltms.coordination.workflow_error_handler.memory_action')
    def test_handle_multiple_error_types(self, mock_memory, mock_chat):
        """Test handling different types of errors"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Setup LTMC tool mocks
        mock_chat.return_value = {'success': True}
        mock_memory.return_value = {'success': True, 'doc_id': 456}
        
        handler = WorkflowErrorHandler(
            Mock(), Mock(), Mock(), Mock(),
            "multi_error_workflow", "multi_error_conv"
        )
        
        # Test different error types
        errors_to_test = [
            ValueError("Invalid parameter"),
            ConnectionError("Service unavailable"),
            TimeoutError("Operation timed out"),
            RuntimeError("Runtime failure"),
            KeyError("Missing configuration key")
        ]
        
        for error in errors_to_test:
            result = handler.handle_workflow_error(error, "multi_error_phase")
            
            # Verify each error is handled properly
            assert result['success'] is False
            assert 'error' in result
            assert str(error) in result['error']
            assert result['workflow_id'] == "multi_error_workflow"
    
    @patch('ltms.coordination.workflow_error_handler.chat_action')
    @patch('ltms.coordination.workflow_error_handler.memory_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_memory, mock_chat):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_chat.return_value = {'success': True}
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        
        handler = WorkflowErrorHandler(
            Mock(), Mock(), Mock(), Mock(),
            "ltmc_comprehensive_error", "ltmc_comprehensive_error_conv"
        )
        
        # Test comprehensive error handling
        comprehensive_error = Exception("LTMC comprehensive error test")
        result = handler.handle_workflow_error(comprehensive_error, "ltmc_comprehensive_phase")
        
        # Verify error handling success
        assert result['success'] is False
        assert 'LTMC comprehensive error test' in result['error']
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert chat_call[1]['conversation_id'] == 'ltmc_comprehensive_error_conv'
        assert chat_call[1]['role'] == 'system'
        assert 'ltmc_comprehensive_error' in chat_call[1]['message']
        
        # 2. memory_action - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert memory_call[1]['conversation_id'] == 'ltmc_comprehensive_error_conv'
        assert memory_call[1]['role'] == 'system'
        assert 'workflow_error_report_ltmc_comprehensive_error' in memory_call[1]['file_name']
    
    def test_error_report_structure_validation(self):
        """Test error report structure includes all required fields"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        handler = WorkflowErrorHandler(
            Mock(), Mock(), Mock(), Mock(),
            "structure_validation_workflow", "structure_validation_conv"
        )
        
        # Test error report generation
        test_error = Exception("Structure validation error")
        
        with patch('ltms.coordination.workflow_error_handler.chat_action') as mock_chat, \
             patch('ltms.coordination.workflow_error_handler.memory_action') as mock_memory:
            
            mock_chat.return_value = {'success': True}
            mock_memory.return_value = {'success': True}
            
            result = handler.handle_workflow_error(test_error, "structure_validation_phase")
        
        # Verify error report structure
        error_report = result['error_report']
        
        required_fields = [
            'workflow_id', 'error_timestamp', 'error_message',
            'workflow_status', 'error_phase'
        ]
        
        for field in required_fields:
            assert field in error_report, f"Missing required field: {field}"
        
        # Verify field values
        assert error_report['workflow_id'] == "structure_validation_workflow"
        assert error_report['workflow_status'] == "FAILED"
        assert error_report['error_phase'] == "structure_validation_phase"
        assert 'Structure validation error' in error_report['error_message']
        
        # Verify timestamp format
        timestamp = error_report['error_timestamp']
        # Should not raise exception
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_error_handler_state_isolation(self):
        """Test error handler maintains proper state isolation"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        # Create two separate handler instances
        handler_1 = WorkflowErrorHandler(
            Mock(), Mock(), Mock(), Mock(),
            "isolation_workflow_1", "isolation_conv_1"
        )
        
        handler_2 = WorkflowErrorHandler(
            Mock(), Mock(), Mock(), Mock(),
            "isolation_workflow_2", "isolation_conv_2"
        )
        
        # Test different errors in each
        error_1 = Exception("Isolation error 1")
        error_2 = Exception("Isolation error 2")
        
        with patch('ltms.coordination.workflow_error_handler.chat_action') as mock_chat, \
             patch('ltms.coordination.workflow_error_handler.memory_action') as mock_memory:
            
            mock_chat.return_value = {'success': True}
            mock_memory.return_value = {'success': True}
            
            result_1 = handler_1.handle_workflow_error(error_1, "isolation_phase_1")
            result_2 = handler_2.handle_workflow_error(error_2, "isolation_phase_2")
        
        # Verify isolation
        assert result_1['workflow_id'] == "isolation_workflow_1"
        assert result_2['workflow_id'] == "isolation_workflow_2"
        
        assert 'Isolation error 1' in result_1['error']
        assert 'Isolation error 2' in result_2['error']
        
        assert result_1['error_report']['error_phase'] == "isolation_phase_1"
        assert result_2['error_report']['error_phase'] == "isolation_phase_2"
        
        # Verify no cross-contamination
        assert 'Isolation error 2' not in result_1['error']
        assert 'Isolation error 1' not in result_2['error']


class TestWorkflowErrorHandlerIntegration:
    """Test WorkflowErrorHandler integration scenarios"""
    
    def test_integration_with_state_manager_and_agents(self):
        """Test integration with state manager and agent components"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        handler = WorkflowErrorHandler(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "integration_test", "integration_conv"
        )
        
        # Test that all components are properly integrated
        assert handler.coordinator == mock_coordinator
        assert handler.state_manager == mock_state_manager
        assert handler.analyzer == mock_analyzer
        assert handler.validator == mock_validator
    
    def test_error_recovery_workflow_integration(self):
        """Test error handler integration with recovery workflows"""
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup state manager with recovery scenario
        recovery_snapshot = StateSnapshot(
            agent_id="recovery_analyzer",
            status=AgentStatus.ERROR,
            state_data={"recovery": "needed"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="recovery_test",
            conversation_id="recovery_conv",
            metadata={"recovery_attempts": 0}
        )
        
        mock_state_manager = Mock()
        mock_state_manager.get_agent_state.return_value = recovery_snapshot
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "recovery_analyzer"
        mock_validator = Mock()
        mock_validator.agent_id = "recovery_validator"
        
        handler = WorkflowErrorHandler(
            Mock(), mock_state_manager, mock_analyzer, mock_validator,
            "recovery_workflow", "recovery_conv"
        )
        
        # Test error handling with recovery context
        recovery_error = Exception("Recoverable error")
        
        with patch('ltms.coordination.workflow_error_handler.chat_action') as mock_chat, \
             patch('ltms.coordination.workflow_error_handler.memory_action') as mock_memory:
            
            mock_chat.return_value = {'success': True}
            mock_memory.return_value = {'success': True}
            
            result = handler.handle_workflow_error(recovery_error, "recovery_phase")
        
        # Verify error handling includes recovery context
        assert result['success'] is False
        assert result['error_report']['error_phase'] == "legacy_analysis"  # Based on agent state
        
        # Verify state manager was queried for recovery planning
        mock_state_manager.get_agent_state.assert_called_with("recovery_analyzer")


# Pytest fixtures for workflow error handler testing
@pytest.fixture
def mock_error_handler_dependencies():
    """Fixture providing mock dependencies for error handler testing"""
    mock_coordinator = Mock()
    
    mock_state_manager = Mock()
    mock_state_manager.get_agent_state.return_value = None
    
    mock_analyzer = Mock()
    mock_analyzer.agent_id = "fixture_analyzer"
    
    mock_validator = Mock()
    mock_validator.agent_id = "fixture_validator"
    
    return {
        'coordinator': mock_coordinator,
        'state_manager': mock_state_manager,
        'analyzer': mock_analyzer,
        'validator': mock_validator
    }

@pytest.fixture
def workflow_error_handler(mock_error_handler_dependencies):
    """Fixture providing WorkflowErrorHandler instance"""
    from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
    
    deps = mock_error_handler_dependencies
    return WorkflowErrorHandler(
        deps['coordinator'], deps['state_manager'], deps['analyzer'], deps['validator'],
        "fixture_workflow", "fixture_conv"
    )

@pytest.fixture
def mock_all_ltmc_error_tools():
    """Fixture providing mocks for all LTMC tools used in error handler"""
    with patch.multiple(
        'ltms.coordination.workflow_error_handler',
        chat_action=Mock(return_value={'success': True}),
        memory_action=Mock(return_value={'success': True, 'doc_id': 999})
    ) as mocks:
        yield mocks