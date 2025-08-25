"""
Comprehensive TDD tests for Workflow Phase Executor extraction.
Tests workflow phase execution and LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
WorkflowPhaseExecutor will handle execute_coordinated_legacy_removal phases.
MANDATORY: Uses ALL required LTMC tools (all 11 tools for comprehensive workflow execution).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestWorkflowPhaseExecutor:
    """Test WorkflowPhaseExecutor class - to be extracted from legacy_removal_workflow.py"""
    
    def test_workflow_phase_executor_creation(self):
        """Test WorkflowPhaseExecutor can be instantiated"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_workflow_orchestrator = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, mock_state_manager, mock_workflow_orchestrator,
            mock_analyzer, mock_validator, "test_workflow_id", "test_conversation_id"
        )
        
        assert hasattr(executor, 'coordinator')
        assert hasattr(executor, 'state_manager')
        assert hasattr(executor, 'workflow_orchestrator')
        assert hasattr(executor, 'analyzer')
        assert hasattr(executor, 'validator')
        assert hasattr(executor, 'workflow_id')
        assert hasattr(executor, 'conversation_id')
        assert executor.workflow_id == "test_workflow_id"
    
    @patch('ltms.coordination.workflow_phase_executor.todo_action')
    @patch('ltms.coordination.workflow_phase_executor.chat_action')
    def test_execute_phase_1_agent_initialization(self, mock_chat, mock_todo):
        """Test Phase 1: Agent Initialization and Workflow Setup"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup LTMC tool mocks - MANDATORY
        mock_todo.return_value = {'success': True, 'task_id': 'phase1_task'}
        mock_chat.return_value = {'success': True}
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_workflow_orchestrator = Mock()
        mock_analyzer = Mock()
        mock_analyzer.initialize_agent.return_value = True
        mock_analyzer.agent_id = "test_analyzer"
        mock_validator = Mock()
        mock_validator.initialize_agent.return_value = True
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, mock_state_manager, mock_workflow_orchestrator,
            mock_analyzer, mock_validator, "phase1_workflow", "phase1_conv"
        )
        
        # Test Phase 1 execution
        result = executor.execute_phase_1_agent_initialization()
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 1
        assert result['agents_initialized'] == 2
        
        # Verify agents were initialized
        mock_analyzer.initialize_agent.assert_called_once()
        mock_validator.initialize_agent.assert_called_once()
        
        # Verify LTMC tools were called - MANDATORY
        # 1. todo_action - MANDATORY Tool 2
        mock_todo.assert_called_once()
        todo_call = mock_todo.call_args
        assert todo_call[1]['action'] == 'add'
        assert 'Execute coordinated legacy removal workflow' in todo_call[1]['content']
        
        # 2. chat_action - MANDATORY Tool 3
        mock_chat.assert_called_once()
        chat_call = mock_chat.call_args
        assert chat_call[1]['action'] == 'log'
        assert 'Phase 1 Complete' in chat_call[1]['message']
    
    def test_execute_phase_2_legacy_analysis(self):
        """Test Phase 2: Legacy Code Analysis"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_coordinator.coordinate_agent_handoff.return_value = True
        
        mock_analyzer = Mock()
        mock_analyzer.analyze_legacy_code.return_value = {
            'success': True,
            'legacy_decorators': [{'name': 'test_func'}],
            'functional_tools': [{'name': 'test_tool'}]
        }
        mock_analyzer.send_analysis_to_next_agent.return_value = True
        mock_analyzer.agent_id = "test_analyzer"
        
        mock_validator = Mock()
        mock_validator.agent_id = "test_validator"
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, Mock(), Mock(),
            mock_analyzer, mock_validator, "phase2_workflow", "phase2_conv"
        )
        
        # Test Phase 2 execution
        result = executor.execute_phase_2_legacy_analysis()
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 2
        assert 'analysis_results' in result
        
        # Verify analysis workflow
        mock_analyzer.analyze_legacy_code.assert_called_once()
        mock_coordinator.coordinate_agent_handoff.assert_called_once()
        mock_analyzer.send_analysis_to_next_agent.assert_called_once_with("safety_validator")
        
        # Verify handoff parameters
        handoff_call = mock_coordinator.coordinate_agent_handoff.call_args
        assert handoff_call[0][0] == "test_analyzer"  # from_agent
        assert handoff_call[0][1] == "test_validator"  # to_agent
        assert 'analysis_results' in handoff_call[0][2]  # handoff_data
    
    @patch('ltms.coordination.workflow_phase_executor.graph_action')
    def test_execute_phase_3_safety_validation(self, mock_graph):
        """Test Phase 3: Safety Validation and Risk Assessment"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup LTMC graph tool mock - MANDATORY
        mock_graph.return_value = {'success': True, 'relationship_id': 'validation_123'}
        
        # Setup mocks
        mock_validator = Mock()
        mock_validator.validate_removal_safety.return_value = {
            'success': True,
            'validation_report': {
                'safety_score': 85.5,
                'risk_level': 'LOW',
                'removal_recommendation': 'PROCEED'
            }
        }
        
        executor = WorkflowPhaseExecutor(
            Mock(), Mock(), Mock(),
            Mock(), mock_validator, "phase3_workflow", "phase3_conv"
        )
        
        # Test analysis data
        analysis_result = {
            'success': True,
            'legacy_decorators': [{'name': 'test_legacy'}]
        }
        
        # Test Phase 3 execution
        result = executor.execute_phase_3_safety_validation(analysis_result)
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 3
        assert 'validation_results' in result
        
        # Verify validation workflow
        mock_validator.validate_removal_safety.assert_called_once_with(analysis_result)
        
        # Verify LTMC graph tool - MANDATORY Tool 8
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'workflow_phase3_workflow' in graph_call[1]['source_entity']
        assert graph_call[1]['target_entity'] == 'legacy_removal_validation'
        assert graph_call[1]['relationship'] == 'completed_validation'
        assert graph_call[1]['properties']['safety_score'] == 85.5
    
    def test_execute_phase_4_removal_planning(self):
        """Test Phase 4: Removal Plan Creation and Task Management"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup mocks
        mock_validator = Mock()
        mock_validator.create_removal_plan.return_value = {
            'success': True,
            'tasks_created': 15,
            'execution_strategy': 'sequential_with_validation'
        }
        
        executor = WorkflowPhaseExecutor(
            Mock(), Mock(), Mock(),
            Mock(), mock_validator, "phase4_workflow", "phase4_conv"
        )
        
        # Test Phase 4 execution
        result = executor.execute_phase_4_removal_planning()
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 4
        assert 'removal_plan' in result
        assert result['removal_plan']['tasks_created'] == 15
        
        # Verify planning workflow
        mock_validator.create_removal_plan.assert_called_once()
    
    @patch('ltms.coordination.workflow_phase_executor.documentation_action')
    @patch('ltms.coordination.workflow_phase_executor.sync_action')
    @patch('ltms.coordination.workflow_phase_executor.cache_action')
    def test_execute_phase_5_documentation(self, mock_cache, mock_sync, mock_doc):
        """Test Phase 5: Documentation Generation and Synchronization"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup LTMC tool mocks - MANDATORY
        mock_doc.return_value = {'success': True, 'docs_generated': 'api_docs.md'}
        mock_sync.return_value = {'success': True, 'files_synced': 25}
        mock_cache.return_value = {'success': True, 'cache_cleared': True}
        
        executor = WorkflowPhaseExecutor(
            Mock(), Mock(), Mock(),
            Mock(), Mock(), "phase5_workflow", "phase5_conv"
        )
        
        # Test Phase 5 execution
        result = executor.execute_phase_5_documentation()
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 5
        assert 'documentation_results' in result
        
        # Verify LTMC tools were called - MANDATORY
        
        # 1. documentation_action - MANDATORY Tool 9
        mock_doc.assert_called_once()
        doc_call = mock_doc.call_args
        assert doc_call[1]['action'] == 'generate_api_docs'
        assert doc_call[1]['conversation_id'] == 'phase5_conv'
        assert doc_call[1]['role'] == 'system'
        
        # 2. sync_action - MANDATORY Tool 10
        mock_sync.assert_called_once()
        sync_call = mock_sync.call_args
        assert sync_call[1]['action'] == 'code'
        assert sync_call[1]['conversation_id'] == 'phase5_conv'
        assert sync_call[1]['role'] == 'system'
        
        # 3. cache_action - MANDATORY Tool 7
        mock_cache.assert_called_once()
        cache_call = mock_cache.call_args
        assert cache_call[1]['action'] == 'flush'
        assert cache_call[1]['conversation_id'] == 'phase5_conv'
        assert cache_call[1]['role'] == 'system'
    
    @patch('ltms.coordination.workflow_phase_executor.memory_action')
    def test_execute_phase_6_completion(self, mock_memory):
        """Test Phase 6: Workflow Completion and Results Compilation"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup LTMC memory tool mock - MANDATORY
        mock_memory.return_value = {'success': True, 'doc_id': 456}
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_coordinator.get_coordination_summary.return_value = {'agents': 2, 'messages': 10}
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {'transitions': 15}
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, mock_state_manager, Mock(),
            Mock(), Mock(), "phase6_workflow", "phase6_conv"
        )
        
        # Test data for compilation
        analysis_result = {'success': True, 'legacy_decorators': [{'name': 'test'}]}
        validation_result = {
            'success': True,
            'validation_report': {'safety_score': 90, 'removal_recommendation': 'PROCEED'}
        }
        removal_plan = {'success': True, 'tasks_created': 20}
        
        # Test Phase 6 execution
        result = executor.execute_phase_6_completion(analysis_result, validation_result, removal_plan)
        
        # Verify success
        assert result['success'] is True
        assert result['phase'] == 6
        assert 'workflow_results' in result
        assert 'report_storage' in result
        
        # Verify workflow results structure
        workflow_results = result['workflow_results']
        assert workflow_results['workflow_id'] == 'phase6_workflow'
        assert workflow_results['workflow_status'] == 'COMPLETED'
        assert workflow_results['phases_completed'] == 6
        assert workflow_results['ltmc_tools_used'] == 11
        
        # Verify LTMC memory tool - MANDATORY Tool 1
        mock_memory.assert_called_once()
        memory_call = mock_memory.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'coordinated_legacy_removal_workflow_report' in memory_call[1]['file_name']
        assert 'workflow_complete' in memory_call[1]['tags']
        
        # Verify coordination summary integration
        mock_coordinator.get_coordination_summary.assert_called_once()
        mock_state_manager.get_performance_metrics.assert_called_once()
    
    def test_execute_phase_failure_handling(self):
        """Test phase execution failure handling"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup mocks for failure scenario
        mock_analyzer = Mock()
        mock_analyzer.initialize_agent.return_value = False  # Failure
        mock_validator = Mock()
        mock_validator.initialize_agent.return_value = True
        
        executor = WorkflowPhaseExecutor(
            Mock(), Mock(), Mock(),
            mock_analyzer, mock_validator, "failure_workflow", "failure_conv"
        )
        
        # Test failure handling in Phase 1
        with patch('ltms.coordination.workflow_phase_executor.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            
            result = executor.execute_phase_1_agent_initialization()
        
        # Verify failure handling
        assert result['success'] is False
        assert 'Agent initialization failed' in result['error']
        assert result['phase'] == 1
    
    @patch('ltms.coordination.workflow_phase_executor.todo_action')
    @patch('ltms.coordination.workflow_phase_executor.chat_action')
    @patch('ltms.coordination.workflow_phase_executor.graph_action')
    @patch('ltms.coordination.workflow_phase_executor.documentation_action')
    @patch('ltms.coordination.workflow_phase_executor.sync_action')
    @patch('ltms.coordination.workflow_phase_executor.cache_action')
    @patch('ltms.coordination.workflow_phase_executor.memory_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_memory, mock_cache, mock_sync, 
                                          mock_doc, mock_graph, mock_chat, mock_todo):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_todo.return_value = {'success': True, 'task_id': 'ltmc_comprehensive'}
        mock_chat.return_value = {'success': True}
        mock_graph.return_value = {'success': True, 'relationship_id': 'ltmc_graph'}
        mock_doc.return_value = {'success': True, 'docs': 'comprehensive'}
        mock_sync.return_value = {'success': True, 'sync': 'complete'}
        mock_cache.return_value = {'success': True, 'cache': 'cleared'}
        mock_memory.return_value = {'success': True, 'doc_id': 789}
        
        # Setup comprehensive mocks
        mock_coordinator = Mock()
        mock_coordinator.coordinate_agent_handoff.return_value = True
        mock_coordinator.get_coordination_summary.return_value = {'comprehensive': True}
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {'comprehensive': True}
        
        mock_analyzer = Mock()
        mock_analyzer.initialize_agent.return_value = True
        mock_analyzer.analyze_legacy_code.return_value = {'success': True, 'legacy_decorators': []}
        mock_analyzer.send_analysis_to_next_agent.return_value = True
        mock_analyzer.agent_id = "ltmc_analyzer"
        
        mock_validator = Mock()
        mock_validator.initialize_agent.return_value = True
        mock_validator.validate_removal_safety.return_value = {
            'success': True, 'validation_report': {'safety_score': 95}
        }
        mock_validator.create_removal_plan.return_value = {'success': True, 'tasks_created': 30}
        mock_validator.agent_id = "ltmc_validator"
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, mock_state_manager, Mock(),
            mock_analyzer, mock_validator, "ltmc_comprehensive", "ltmc_comprehensive_conv"
        )
        
        # Test comprehensive phase execution
        phase_1 = executor.execute_phase_1_agent_initialization()
        phase_2 = executor.execute_phase_2_legacy_analysis()
        phase_3 = executor.execute_phase_3_safety_validation(phase_2['analysis_results'])
        phase_5 = executor.execute_phase_5_documentation()
        phase_6 = executor.execute_phase_6_completion(
            phase_2['analysis_results'], phase_3['validation_results'], {'success': True}
        )
        
        # Verify all phases succeeded
        assert phase_1['success'] is True
        assert phase_2['success'] is True
        assert phase_3['success'] is True
        assert phase_5['success'] is True
        assert phase_6['success'] is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. todo_action - MANDATORY Tool 2
        mock_todo.assert_called()
        
        # 2. chat_action - MANDATORY Tool 3
        mock_chat.assert_called()
        
        # 3. graph_action - MANDATORY Tool 8
        mock_graph.assert_called()
        
        # 4. documentation_action - MANDATORY Tool 9
        mock_doc.assert_called()
        
        # 5. sync_action - MANDATORY Tool 10
        mock_sync.assert_called()
        
        # 6. cache_action - MANDATORY Tool 7
        mock_cache.assert_called()
        
        # 7. memory_action - MANDATORY Tool 1
        mock_memory.assert_called()


class TestWorkflowPhaseExecutorIntegration:
    """Test WorkflowPhaseExecutor integration scenarios"""
    
    def test_integration_with_agents_and_coordination(self):
        """Test integration with agents and coordination framework"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup integration test
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_workflow_orchestrator = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, mock_state_manager, mock_workflow_orchestrator,
            mock_analyzer, mock_validator, "integration_test", "integration_conv"
        )
        
        # Test that all components are properly integrated
        assert executor.coordinator == mock_coordinator
        assert executor.state_manager == mock_state_manager
        assert executor.analyzer == mock_analyzer
        assert executor.validator == mock_validator
    
    def test_phase_to_phase_data_flow(self):
        """Test data flow between phases"""
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        
        # Setup mocks for data flow test
        mock_analyzer = Mock()
        analysis_data = {
            'success': True,
            'legacy_decorators': [{'name': 'flow_test_func'}],
            'functional_tools': [{'name': 'flow_test_tool'}]
        }
        mock_analyzer.analyze_legacy_code.return_value = analysis_data
        mock_analyzer.send_analysis_to_next_agent.return_value = True
        
        mock_validator = Mock()
        validation_data = {
            'success': True,
            'validation_report': {'safety_score': 88, 'risk_level': 'LOW'}
        }
        mock_validator.validate_removal_safety.return_value = validation_data
        
        mock_coordinator = Mock()
        mock_coordinator.coordinate_agent_handoff.return_value = True
        
        executor = WorkflowPhaseExecutor(
            mock_coordinator, Mock(), Mock(),
            mock_analyzer, mock_validator, "data_flow_test", "data_flow_conv"
        )
        
        # Test data flow
        phase_2_result = executor.execute_phase_2_legacy_analysis()
        phase_3_result = executor.execute_phase_3_safety_validation(phase_2_result['analysis_results'])
        
        # Verify data flows correctly between phases
        assert phase_2_result['analysis_results'] == analysis_data
        assert phase_3_result['validation_results'] == validation_data
        
        # Verify validator received analysis data
        mock_validator.validate_removal_safety.assert_called_once_with(analysis_data)


# Pytest fixtures for workflow phase executor testing
@pytest.fixture
def mock_executor_dependencies():
    """Fixture providing mock dependencies for phase executor testing"""
    mock_coordinator = Mock()
    mock_coordinator.coordinate_agent_handoff.return_value = True
    mock_coordinator.get_coordination_summary.return_value = {'test': True}
    
    mock_state_manager = Mock()
    mock_state_manager.get_performance_metrics.return_value = {'metrics': True}
    
    mock_workflow_orchestrator = Mock()
    
    mock_analyzer = Mock()
    mock_analyzer.initialize_agent.return_value = True
    mock_analyzer.analyze_legacy_code.return_value = {'success': True, 'legacy_decorators': []}
    mock_analyzer.send_analysis_to_next_agent.return_value = True
    mock_analyzer.agent_id = "fixture_analyzer"
    
    mock_validator = Mock()
    mock_validator.initialize_agent.return_value = True
    mock_validator.validate_removal_safety.return_value = {'success': True, 'validation_report': {}}
    mock_validator.create_removal_plan.return_value = {'success': True, 'tasks_created': 10}
    mock_validator.agent_id = "fixture_validator"
    
    return {
        'coordinator': mock_coordinator,
        'state_manager': mock_state_manager,
        'workflow_orchestrator': mock_workflow_orchestrator,
        'analyzer': mock_analyzer,
        'validator': mock_validator
    }

@pytest.fixture
def workflow_phase_executor(mock_executor_dependencies):
    """Fixture providing WorkflowPhaseExecutor instance"""
    from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
    
    deps = mock_executor_dependencies
    return WorkflowPhaseExecutor(
        deps['coordinator'], deps['state_manager'], deps['workflow_orchestrator'],
        deps['analyzer'], deps['validator'], "fixture_workflow", "fixture_conv"
    )