"""
Comprehensive TDD tests for Removal Plan Manager extraction.
Tests plan creation, blueprint integration, todo management, and LTMC storage.

Following TDD methodology: Tests written FIRST before extraction.
RemovalPlanManager will handle removal plan creation with LTMC tools integration.
MANDATORY: Uses ALL required LTMC tools (blueprint_action, todo_action, memory_action).
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestRemovalPlanManager:
    """Test RemovalPlanManager class - to be extracted from safety_validator.py"""
    
    def test_removal_plan_manager_creation(self):
        """Test RemovalPlanManager can be instantiated"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Mock core validator with validation report
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "plan_test"
        mock_core.coordinator.conversation_id = "plan_conv"
        mock_core.validation_report = {
            'safety_score': 95.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        
        manager = RemovalPlanManager(mock_core)
        
        assert hasattr(manager, 'core')
        assert manager.core == mock_core
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_create_removal_plan_approved_scenario(self, mock_memory, mock_todo, mock_blueprint):
        """Test removal plan creation for APPROVED scenario with ALL LTMC tools"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks - MANDATORY ALL TOOLS USED
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_123'}
        mock_todo.return_value = {'success': True, 'task_id': 'task_456'}
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        
        # Mock core validator with approved validation
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "approved_plan_test"
        mock_core.coordinator.conversation_id = "approved_plan_conv"
        mock_core.validation_report = {
            'safety_score': 95.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}  # Will be populated
        
        manager = RemovalPlanManager(mock_core)
        
        # Test plan creation
        result = manager.create_removal_plan()
        
        # Verify successful plan creation
        assert result['success'] is True
        assert 'removal_plan' in result
        assert 'tasks_created' in result
        assert 'blueprint_created' in result
        assert 'storage_result' in result
        
        # Verify ALL LTMC tools were called - MANDATORY
        mock_blueprint.assert_called_once()
        blueprint_call = mock_blueprint.call_args
        assert blueprint_call[1]['action'] == 'create'
        assert blueprint_call[1]['project_name'] == 'legacy_removal_execution_plan'
        assert 'legacy @mcp.tool decorator removal' in blueprint_call[1]['description']
        assert blueprint_call[1]['conversation_id'] == 'approved_plan_conv'
        
        # Verify todo_action was called for each task - MANDATORY
        assert mock_todo.call_count == 8  # 8 removal tasks
        for call in mock_todo.call_args_list:
            assert call[1]['action'] == 'add'
            assert 'Legacy Removal Task' in call[1]['task']
            assert 'legacy_removal' in call[1]['tags']
            assert 'approved_plan_test' in call[1]['tags']
            assert call[1]['conversation_id'] == 'approved_plan_conv'
        
        # Verify memory_action was called for storage - MANDATORY
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'legacy_removal_plan_approved_plan_test.json' in memory_call[1]['file_name']
        assert 'removal_plan' in memory_call[1]['tags']
        assert memory_call[1]['conversation_id'] == 'approved_plan_conv'
        
        # Verify plan structure
        removal_plan = result['removal_plan']
        assert removal_plan['coordinator_task'] == 'approved_plan_test'
        assert removal_plan['validation_basis']['safety_score'] == 95.0
        assert removal_plan['validation_basis']['recommendation'] == 'APPROVED'
        assert removal_plan['execution_strategy'] == 'sequential_with_validation'
        assert len(removal_plan['removal_tasks']) == 8
        assert removal_plan['blueprint_id'] == 'bp_123'
        
        # Verify task structure
        for i, task in enumerate(removal_plan['removal_tasks'], 1):
            assert task['task_id'] == 'task_456'
            assert task['sequence'] == i
            assert task['status'] == 'pending'
            assert isinstance(task['description'], str)
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_create_removal_plan_approved_with_caution_scenario(self, mock_memory, mock_todo, mock_blueprint):
        """Test removal plan creation for APPROVED_WITH_CAUTION scenario"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_caution_123'}
        mock_todo.return_value = {'success': True, 'task_id': 'caution_task_456'}
        mock_memory.return_value = {'success': True, 'doc_id': 890}
        
        # Mock core with caution recommendation
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "caution_plan_test"
        mock_core.coordinator.conversation_id = "caution_plan_conv"
        mock_core.validation_report = {
            'safety_score': 80.0,
            'removal_recommendation': 'APPROVED_WITH_CAUTION',
            'risk_level': 'MEDIUM'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should still create plan but with caution
        assert result['success'] is True
        assert result['tasks_created'] == 8  # Same number of tasks
        
        # Verify ALL LTMC tools were called
        mock_blueprint.assert_called_once()
        assert mock_todo.call_count == 8
        mock_memory.assert_called_once()
        
        # Verify plan reflects caution
        removal_plan = result['removal_plan']
        assert removal_plan['validation_basis']['recommendation'] == 'APPROVED_WITH_CAUTION'
        assert removal_plan['validation_basis']['risk_level'] == 'MEDIUM'
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_create_removal_plan_requires_review_scenario(self, mock_memory, mock_todo, mock_blueprint):
        """Test removal plan creation for REQUIRES_REVIEW scenario"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_review_123'}
        mock_todo.return_value = {'success': True, 'task_id': 'review_task_456'}
        mock_memory.return_value = {'success': True, 'doc_id': 991}
        
        # Mock core with review required
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "review_plan_test"
        mock_core.coordinator.conversation_id = "review_plan_conv"
        mock_core.validation_report = {
            'safety_score': 60.0,
            'removal_recommendation': 'REQUIRES_REVIEW',
            'risk_level': 'HIGH'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should not create removal tasks due to high risk
        assert result['success'] is True
        assert result['tasks_created'] == 0  # No tasks created for high-risk scenarios
        
        # Blueprint should still be created - MANDATORY LTMC tool usage
        mock_blueprint.assert_called_once()
        mock_memory.assert_called_once()
        
        # Todo tasks should not be created for REQUIRES_REVIEW
        mock_todo.assert_not_called()
        
        # Plan should reflect high risk status
        removal_plan = result['removal_plan']
        assert removal_plan['validation_basis']['recommendation'] == 'REQUIRES_REVIEW'
        assert removal_plan['validation_basis']['risk_level'] == 'HIGH'
        assert len(removal_plan['removal_tasks']) == 0
    
    def test_create_removal_plan_no_validation_report(self):
        """Test removal plan creation when validation report is missing"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Mock core without validation report
        mock_core = Mock()
        mock_core.validation_report = {}  # Empty validation report
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should fail gracefully
        assert result['success'] is False
        assert 'error' in result
        assert 'Must complete validation before creating removal plan' in result['error']
        assert result['tasks_created'] == 0
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_create_removal_plan_blueprint_failure(self, mock_memory, mock_todo, mock_blueprint):
        """Test removal plan creation when blueprint_action fails"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks with blueprint failure
        mock_blueprint.return_value = {'success': False, 'error': 'Blueprint creation failed'}
        mock_todo.return_value = {'success': True, 'task_id': 'task_789'}
        mock_memory.return_value = {'success': True, 'doc_id': 123}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "blueprint_fail_test"
        mock_core.coordinator.conversation_id = "blueprint_fail_conv"
        mock_core.validation_report = {
            'safety_score': 95.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should succeed despite blueprint failure
        assert result['success'] is True
        assert result['blueprint_created'] is False
        assert result['tasks_created'] == 8  # Tasks still created
        
        # Plan should have None blueprint_id
        removal_plan = result['removal_plan']
        assert removal_plan['blueprint_id'] is None
        
        # ALL other LTMC tools should still be called
        mock_blueprint.assert_called_once()
        assert mock_todo.call_count == 8
        mock_memory.assert_called_once()
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_create_removal_plan_todo_partial_failure(self, mock_memory, mock_todo, mock_blueprint):
        """Test removal plan creation when some todo_action calls fail"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks with partial todo failures
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_partial_123'}
        mock_memory.return_value = {'success': True, 'doc_id': 456}
        
        # Mock todo to succeed for first 3 tasks, fail for rest
        todo_responses = [
            {'success': True, 'task_id': f'task_{i}'} if i <= 3 
            else {'success': False, 'error': f'Task {i} failed'}
            for i in range(1, 9)
        ]
        mock_todo.side_effect = todo_responses
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "todo_partial_fail_test"
        mock_core.coordinator.conversation_id = "todo_partial_fail_conv"
        mock_core.validation_report = {
            'safety_score': 90.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should succeed with partial tasks
        assert result['success'] is True
        assert result['tasks_created'] == 3  # Only successful tasks
        
        # Verify ALL LTMC tools were attempted
        mock_blueprint.assert_called_once()
        assert mock_todo.call_count == 8  # All 8 attempts made
        mock_memory.assert_called_once()
        
        # Plan should contain only successful tasks
        removal_plan = result['removal_plan']
        assert len(removal_plan['removal_tasks']) == 3
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    def test_create_removal_plan_exception_handling(self, mock_blueprint):
        """Test removal plan creation exception handling"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup blueprint to raise exception
        mock_blueprint.side_effect = Exception("LTMC blueprint service unavailable")
        
        mock_core = Mock()
        mock_core.validation_report = {
            'safety_score': 85.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Should handle exception gracefully
        assert result['success'] is False
        assert 'error' in result
        assert 'LTMC blueprint service unavailable' in result['error']
        assert result['tasks_created'] == 0
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_removal_task_structure_validation(self, mock_memory, mock_todo, mock_blueprint):
        """Test that all removal tasks have correct structure"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_structure_test'}
        mock_todo.return_value = {'success': True, 'task_id': 'structure_task'}
        mock_memory.return_value = {'success': True, 'doc_id': 999}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "structure_test"
        mock_core.coordinator.conversation_id = "structure_conv"
        mock_core.validation_report = {
            'safety_score': 100.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Verify all expected tasks are created
        removal_plan = result['removal_plan']
        expected_task_descriptions = [
            "Backup current LTMC system state",
            "Create comprehensive test coverage for consolidated tools",
            "Identify and update import statements referencing legacy decorators", 
            "Remove legacy @mcp.tool decorated functions",
            "Update MCP server configuration",
            "Run comprehensive test suite",
            "Validate LTMC system functionality",
            "Update documentation"
        ]
        
        assert len(removal_plan['removal_tasks']) == len(expected_task_descriptions)
        
        for i, task in enumerate(removal_plan['removal_tasks']):
            # Verify task structure
            required_fields = ['task_id', 'description', 'sequence', 'status']
            for field in required_fields:
                assert field in task
            
            assert task['sequence'] == i + 1
            assert task['status'] == 'pending'
            assert task['task_id'] == 'structure_task'
            
            # Verify description matches expected
            expected_desc = expected_task_descriptions[i]
            assert expected_desc in task['description']
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_removal_plan_complete_structure(self, mock_memory, mock_todo, mock_blueprint):
        """Test complete removal plan structure contains all required fields"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup LTMC tool mocks
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'bp_complete_test'}
        mock_todo.return_value = {'success': True, 'task_id': 'complete_task'}
        mock_memory.return_value = {'success': True, 'doc_id': 777}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "complete_structure_test"
        mock_core.coordinator.conversation_id = "complete_structure_conv"
        mock_core.validation_report = {
            'safety_score': 92.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Verify complete plan structure
        removal_plan = result['removal_plan']
        
        required_fields = [
            'plan_timestamp', 'coordinator_task', 'validation_basis',
            'removal_tasks', 'execution_strategy', 'rollback_plan',
            'success_criteria', 'blueprint_id'
        ]
        
        for field in required_fields:
            assert field in removal_plan, f"Missing required field: {field}"
        
        # Verify validation basis structure
        validation_basis = removal_plan['validation_basis']
        assert validation_basis['safety_score'] == 92.0
        assert validation_basis['recommendation'] == 'APPROVED'
        assert validation_basis['risk_level'] == 'LOW'
        
        # Verify execution strategy
        assert removal_plan['execution_strategy'] == 'sequential_with_validation'
        
        # Verify success criteria
        success_criteria = removal_plan['success_criteria']
        assert isinstance(success_criteria, list)
        assert len(success_criteria) == 4
        expected_criteria = [
            'All legacy @mcp.tool decorators removed',
            'LTMC system fully functional with consolidated tools',
            'All tests passing',
            'Documentation updated'
        ]
        for criterion in expected_criteria:
            assert criterion in success_criteria
        
        # Verify rollback plan
        assert 'backup' in removal_plan['rollback_plan'].lower()
        
        # Verify blueprint integration
        assert removal_plan['blueprint_id'] == 'bp_complete_test'


class TestRemovalPlanManagerIntegration:
    """Test RemovalPlanManager integration with other components"""
    
    def test_integration_with_safety_validation_core(self):
        """Test RemovalPlanManager integration with SafetyValidationCore"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        from ltms.coordination.safety_validation_core import SafetyValidationCore
        
        # Create integrated system
        mock_coordinator = Mock()
        mock_coordinator.task_id = "integration_test"
        mock_coordinator.conversation_id = "integration_conv"
        mock_state_manager = Mock()
        
        core = SafetyValidationCore(mock_coordinator, mock_state_manager)
        core.validation_report = {
            'safety_score': 88.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        
        manager = RemovalPlanManager(core)
        
        # Verify integration
        assert manager.core == core
        assert manager.core.coordinator == mock_coordinator
    
    @patch('ltms.coordination.removal_plan_manager.blueprint_action')
    @patch('ltms.coordination.removal_plan_manager.todo_action')
    @patch('ltms.coordination.removal_plan_manager.memory_action')
    def test_ltmc_tools_integration_comprehensive(self, mock_memory, mock_todo, mock_blueprint):
        """Test comprehensive LTMC tools integration - ALL TOOLS MANDATORY"""
        from ltms.coordination.removal_plan_manager import RemovalPlanManager
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_blueprint.return_value = {'success': True, 'blueprint_id': 'comprehensive_bp'}
        mock_todo.return_value = {'success': True, 'task_id': 'comprehensive_task'}
        mock_memory.return_value = {'success': True, 'doc_id': 555}
        
        mock_core = Mock()
        mock_core.agent_id = "safety_validator"
        mock_core.coordinator = Mock()
        mock_core.coordinator.task_id = "comprehensive_ltmc_test"
        mock_core.coordinator.conversation_id = "comprehensive_ltmc_conv"
        mock_core.validation_report = {
            'safety_score': 94.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW'
        }
        mock_core.removal_plan = {}
        
        manager = RemovalPlanManager(mock_core)
        result = manager.create_removal_plan()
        
        # Verify ALL LTMC tools were used - MANDATORY
        
        # 1. blueprint_action - MANDATORY Tool 6
        mock_blueprint.assert_called_once()
        bp_call = mock_blueprint.call_args
        assert bp_call[1]['action'] == 'create'
        assert bp_call[1]['conversation_id'] == 'comprehensive_ltmc_conv'
        assert bp_call[1]['role'] == 'system'
        
        # 2. todo_action - MANDATORY Tool 2 (8 calls for 8 tasks)
        assert mock_todo.call_count == 8
        for call in mock_todo.call_args_list:
            assert call[1]['action'] == 'add'
            assert call[1]['conversation_id'] == 'comprehensive_ltmc_conv'
            assert call[1]['role'] == 'system'
            assert 'legacy_removal' in call[1]['tags']
            assert 'comprehensive_ltmc_test' in call[1]['tags']
        
        # 3. memory_action - MANDATORY Tool 1 
        mock_memory.assert_called_once()
        mem_call = mock_memory.call_args
        assert mem_call[1]['action'] == 'store'
        assert mem_call[1]['conversation_id'] == 'comprehensive_ltmc_conv'
        assert mem_call[1]['role'] == 'system'
        assert 'removal_plan' in mem_call[1]['tags']
        
        assert result['success'] is True


# Pytest fixtures for plan manager testing
@pytest.fixture
def mock_core_approved():
    """Fixture providing mock core with approved validation"""
    core = Mock()
    core.agent_id = "safety_validator"
    core.coordinator = Mock()
    core.coordinator.task_id = "fixture_approved_task"
    core.coordinator.conversation_id = "fixture_approved_conv"
    core.validation_report = {
        'safety_score': 95.0,
        'removal_recommendation': 'APPROVED',
        'risk_level': 'LOW'
    }
    core.removal_plan = {}
    return core

@pytest.fixture
def mock_core_caution():
    """Fixture providing mock core with caution validation"""
    core = Mock()
    core.agent_id = "safety_validator"
    core.coordinator = Mock()
    core.coordinator.task_id = "fixture_caution_task"
    core.coordinator.conversation_id = "fixture_caution_conv"
    core.validation_report = {
        'safety_score': 78.0,
        'removal_recommendation': 'APPROVED_WITH_CAUTION',
        'risk_level': 'MEDIUM'
    }
    core.removal_plan = {}
    return core

@pytest.fixture
def mock_core_review_required():
    """Fixture providing mock core with review required"""
    core = Mock()
    core.agent_id = "safety_validator"
    core.coordinator = Mock()
    core.coordinator.task_id = "fixture_review_task"
    core.coordinator.conversation_id = "fixture_review_conv"
    core.validation_report = {
        'safety_score': 55.0,
        'removal_recommendation': 'REQUIRES_REVIEW',
        'risk_level': 'HIGH'
    }
    core.removal_plan = {}
    return core

@pytest.fixture
def mock_all_ltmc_plan_tools():
    """Fixture providing mocks for all LTMC tools used in plan creation"""
    with patch.multiple(
        'ltms.coordination.removal_plan_manager',
        blueprint_action=Mock(return_value={'success': True, 'blueprint_id': 'fixture_bp'}),
        todo_action=Mock(return_value={'success': True, 'task_id': 'fixture_task'}),
        memory_action=Mock(return_value={'success': True, 'doc_id': 666})
    ) as mocks:
        yield mocks