"""
Comprehensive TDD tests for CoordinatedLegacyRemovalWorkflow class.
Tests the workflow orchestrator that will be extracted from legacy_removal_coordinated_agents.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List


class TestCoordinatedLegacyRemovalWorkflow:
    """Test CoordinatedLegacyRemovalWorkflow class - to be extracted from legacy_removal_coordinated_agents.py"""
    
    def test_workflow_creation(self):
        """Test CoordinatedLegacyRemovalWorkflow class can be instantiated"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        assert hasattr(workflow, 'workflow_id')
        assert hasattr(workflow, 'conversation_id')
        assert hasattr(workflow, 'coordinator')
        assert hasattr(workflow, 'state_manager')
        assert hasattr(workflow, 'workflow_orchestrator')
        assert hasattr(workflow, 'analyzer')
        assert hasattr(workflow, 'validator')
        assert hasattr(workflow, 'workflow_results')
        assert isinstance(workflow.workflow_results, dict)
        assert workflow.workflow_id.startswith('legacy_removal_workflow_')
        assert workflow.conversation_id.startswith('legacy_removal_')
    
    def test_execute_coordinated_legacy_removal_method_exists(self):
        """Test that execute_coordinated_legacy_removal method exists and is callable"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        assert hasattr(workflow, 'execute_coordinated_legacy_removal')
        assert callable(workflow.execute_coordinated_legacy_removal)
    
    @patch('ltms.coordination.legacy_removal_workflow.todo_action')
    @patch('ltms.coordination.legacy_removal_workflow.memory_action')
    def test_workflow_initialization_with_ltmc_tools(self, mock_memory_action, mock_todo_action):
        """Test workflow properly initializes and uses LTMC tools"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup mocks
        mock_todo_action.return_value = {'success': True, 'task_id': 'workflow_task_1'}
        mock_memory_action.return_value = {'success': True, 'doc_id': 555}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Verify framework components are properly initialized
        assert hasattr(workflow.coordinator, 'task_id')
        assert hasattr(workflow.state_manager, 'coordination_id')
        assert hasattr(workflow.analyzer, 'agent_id')
        assert hasattr(workflow.validator, 'agent_id')
        assert workflow.analyzer.agent_id == "legacy_code_analyzer"
        assert workflow.validator.agent_id == "safety_validator"
    
    @patch('ltms.coordination.legacy_removal_workflow.documentation_action')
    @patch('ltms.coordination.legacy_removal_workflow.sync_action')
    @patch('ltms.coordination.legacy_removal_workflow.memory_action')
    @patch('ltms.coordination.legacy_removal_workflow.todo_action')
    def test_execute_coordinated_legacy_removal_agent_initialization(self, mock_todo, mock_memory, mock_sync, mock_doc):
        """Test that workflow properly initializes all agents"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup mocks
        mock_todo.return_value = {'success': True}
        mock_memory.return_value = {'success': True}
        mock_sync.return_value = {'success': True}
        mock_doc.return_value = {'success': True}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock agent initialization
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        # Test workflow execution
        result = workflow.execute_coordinated_legacy_removal()
        
        # Verify agents were initialized
        workflow.analyzer.initialize_agent.assert_called_once()
        workflow.validator.initialize_agent.assert_called_once()
        
        # Verify LTMC tools were used
        assert mock_todo.called
        assert mock_memory.called
    
    @patch('ltms.coordination.legacy_removal_workflow.graph_action')
    @patch('ltms.coordination.legacy_removal_workflow.chat_action')
    def test_execute_coordinated_legacy_removal_analysis_phase(self, mock_chat, mock_graph):
        """Test workflow analysis phase with agent coordination"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup mocks
        mock_chat.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock agent methods
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        analysis_results = {
            'success': True,
            'legacy_decorators': [{'name': 'test_tool', 'file': 'test.py'}],
            'functional_tools': [{'name': 'memory_action'}],
            'analysis_report': {'total_legacy_decorators': 1}
        }
        workflow.analyzer.analyze_legacy_code = Mock(return_value=analysis_results)
        workflow.analyzer.send_analysis_to_next_agent = Mock(return_value=True)
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Verify analysis was performed
                workflow.analyzer.analyze_legacy_code.assert_called_once()
                workflow.analyzer.send_analysis_to_next_agent.assert_called_with("safety_validator")
                
                # Verify LTMC tools used for coordination
                assert mock_chat.called
                assert mock_graph.called
    
    def test_execute_coordinated_legacy_removal_validation_phase(self):
        """Test workflow validation phase with safety checks"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock agent initialization
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        # Mock analysis results
        analysis_results = {
            'success': True,
            'legacy_decorators': [{'name': 'legacy_tool', 'file': 'legacy.py'}]
        }
        workflow.analyzer.analyze_legacy_code = Mock(return_value=analysis_results)
        workflow.analyzer.send_analysis_to_next_agent = Mock(return_value=True)
        
        # Mock validation results
        validation_results = {
            'success': True,
            'validation_report': {
                'safety_score': 95.0,
                'removal_recommendation': 'APPROVED',
                'risk_level': 'LOW'
            }
        }
        workflow.validator.validate_removal_safety = Mock(return_value=validation_results)
        workflow.validator.create_removal_plan = Mock(return_value={'success': True, 'tasks_created': 5})
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Verify validation was performed
                workflow.validator.validate_removal_safety.assert_called_once()
                workflow.validator.create_removal_plan.assert_called_once()
                
                # Verify analysis results were passed to validator
                call_args = workflow.validator.validate_removal_safety.call_args[0][0]
                assert 'legacy_decorators' in call_args
    
    @patch('ltms.coordination.legacy_removal_workflow.documentation_action')
    @patch('ltms.coordination.legacy_removal_workflow.sync_action')
    def test_execute_coordinated_legacy_removal_documentation_phase(self, mock_sync, mock_doc):
        """Test workflow documentation and synchronization phase"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup mocks
        mock_sync.return_value = {'success': True, 'synchronized': 3}
        mock_doc.return_value = {'success': True, 'documentation_updated': True}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock successful agent workflow
        self._setup_successful_agent_mocks(workflow)
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Verify documentation tools were used
                assert mock_sync.called
                assert mock_doc.called
                
                # Check sync_action was called for documentation synchronization
                sync_calls = mock_sync.call_args_list
                assert any(call[1].get('action') == 'code' for call in sync_calls)
    
    @patch('ltms.coordination.legacy_removal_workflow.cache_action')
    def test_execute_coordinated_legacy_removal_cache_management(self, mock_cache):
        """Test workflow cache management and cleanup"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup cache mock
        mock_cache.return_value = {'success': True, 'cache_cleared': True}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock successful agent workflow
        self._setup_successful_agent_mocks(workflow)
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Verify cache management was performed
                assert mock_cache.called
                
                # Check for cache flush operation
                cache_calls = mock_cache.call_args_list
                assert any(call[1].get('action') == 'flush' for call in cache_calls)
    
    def test_execute_coordinated_legacy_removal_error_handling(self):
        """Test workflow error handling and rollback mechanisms"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock agent initialization failure
        workflow.analyzer.initialize_agent = Mock(return_value=False)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Should handle initialization failure gracefully
                assert result['success'] is False
                assert 'error' in result
                assert 'initialization_failed' in result['error'] or 'Agent initialization failed' in result['error']
    
    def test_execute_coordinated_legacy_removal_analysis_failure_handling(self):
        """Test workflow handles analysis failure gracefully"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock successful initialization but failed analysis
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        workflow.analyzer.analyze_legacy_code = Mock(return_value={'success': False, 'error': 'Analysis failed'})
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True}
                
                result = workflow.execute_coordinated_legacy_removal()
                
                # Should handle analysis failure
                assert result['success'] is False
                assert 'error' in result
    
    def test_workflow_orchestrator_integration(self):
        """Test integration with WorkflowOrchestrator"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        from ltms.coordination.mcp_communication_patterns import WorkflowOrchestrator
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Verify workflow orchestrator is properly initialized
        assert hasattr(workflow, 'workflow_orchestrator')
        assert isinstance(workflow.workflow_orchestrator, WorkflowOrchestrator)
        assert workflow.workflow_orchestrator.workflow_id == workflow.workflow_id
        assert workflow.workflow_orchestrator.conversation_id == workflow.conversation_id
    
    def test_agent_coordination_integration(self):
        """Test proper integration with agent coordination framework"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        from ltms.coordination.agent_coordination_framework import LTMCAgentCoordinator
        from ltms.coordination.agent_state_manager import LTMCAgentStateManager
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Verify coordination framework integration
        assert isinstance(workflow.coordinator, LTMCAgentCoordinator)
        assert isinstance(workflow.state_manager, LTMCAgentStateManager)
        
        # Verify agents are properly initialized with coordination framework
        assert workflow.analyzer.coordinator == workflow.coordinator
        assert workflow.analyzer.state_manager == workflow.state_manager
        assert workflow.validator.coordinator == workflow.coordinator
        assert workflow.validator.state_manager == workflow.state_manager
    
    def test_workflow_results_structure(self):
        """Test that workflow results have proper structure"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock successful complete workflow
        self._setup_successful_agent_mocks(workflow)
        
        with patch('ltms.coordination.legacy_removal_workflow.todo_action') as mock_todo:
            mock_todo.return_value = {'success': True}
            with patch('ltms.coordination.legacy_removal_workflow.memory_action') as mock_memory:
                mock_memory.return_value = {'success': True, 'doc_id': 999}
                with patch('ltms.coordination.legacy_removal_workflow.sync_action') as mock_sync:
                    mock_sync.return_value = {'success': True}
                    with patch('ltms.coordination.legacy_removal_workflow.documentation_action') as mock_doc:
                        mock_doc.return_value = {'success': True}
                        
                        result = workflow.execute_coordinated_legacy_removal()
                        
                        # Verify result structure
                        assert isinstance(result, dict)
                        assert 'success' in result
                        assert 'workflow_id' in result
                        assert 'phases_completed' in result
                        assert 'analysis_results' in result
                        assert 'validation_results' in result
    
    def _setup_successful_agent_mocks(self, workflow):
        """Helper method to setup successful agent mocks"""
        # Mock agent initialization
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        # Mock successful analysis
        analysis_results = {
            'success': True,
            'legacy_decorators': [{'name': 'legacy_tool', 'file': 'legacy.py'}],
            'functional_tools': [{'name': 'memory_action'}],
            'analysis_report': {'total_legacy_decorators': 1}
        }
        workflow.analyzer.analyze_legacy_code = Mock(return_value=analysis_results)
        workflow.analyzer.send_analysis_to_next_agent = Mock(return_value=True)
        
        # Mock successful validation
        validation_results = {
            'success': True,
            'validation_report': {
                'safety_score': 95.0,
                'removal_recommendation': 'APPROVED'
            }
        }
        workflow.validator.validate_removal_safety = Mock(return_value=validation_results)
        workflow.validator.create_removal_plan = Mock(return_value={'success': True, 'tasks_created': 5})


class TestCoordinatedLegacyRemovalWorkflowIntegration:
    """Test integration scenarios for CoordinatedLegacyRemovalWorkflow"""
    
    @patch('ltms.coordination.legacy_removal_workflow.documentation_action')
    @patch('ltms.coordination.legacy_removal_workflow.sync_action')
    @patch('ltms.coordination.legacy_removal_workflow.cache_action')
    @patch('ltms.coordination.legacy_removal_workflow.graph_action')
    @patch('ltms.coordination.legacy_removal_workflow.chat_action')
    @patch('ltms.coordination.legacy_removal_workflow.memory_action')
    @patch('ltms.coordination.legacy_removal_workflow.todo_action')
    def test_complete_workflow_with_all_ltmc_tools(self, mock_todo, mock_memory, mock_chat, mock_graph, mock_cache, mock_sync, mock_doc):
        """Test complete workflow uses all LTMC tools appropriately"""
        from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
        
        # Setup all LTMC tool mocks
        mock_todo.return_value = {'success': True, 'task_id': 'workflow_task'}
        mock_memory.return_value = {'success': True, 'doc_id': 888}
        mock_chat.return_value = {'success': True}
        mock_graph.return_value = {'success': True}
        mock_cache.return_value = {'success': True}
        mock_sync.return_value = {'success': True, 'synchronized': 5}
        mock_doc.return_value = {'success': True, 'updated': True}
        
        workflow = CoordinatedLegacyRemovalWorkflow()
        
        # Mock successful agent workflow
        workflow.analyzer.initialize_agent = Mock(return_value=True)
        workflow.validator.initialize_agent = Mock(return_value=True)
        
        analysis_results = {
            'success': True,
            'legacy_decorators': [{'name': 'test_legacy', 'file': 'test.py'}],
            'functional_tools': [{'name': 'memory_action'}]
        }
        workflow.analyzer.analyze_legacy_code = Mock(return_value=analysis_results)
        workflow.analyzer.send_analysis_to_next_agent = Mock(return_value=True)
        
        validation_results = {
            'success': True,
            'validation_report': {'safety_score': 90.0, 'removal_recommendation': 'APPROVED'}
        }
        workflow.validator.validate_removal_safety = Mock(return_value=validation_results)
        workflow.validator.create_removal_plan = Mock(return_value={'success': True})
        
        # Execute complete workflow
        result = workflow.execute_coordinated_legacy_removal()
        
        # Verify all LTMC tools were used
        assert mock_todo.called  # Task management
        assert mock_memory.called  # Memory storage
        assert mock_chat.called  # Agent communication
        assert mock_graph.called  # Knowledge graph
        assert mock_cache.called  # Cache management
        assert mock_sync.called  # Documentation sync
        assert mock_doc.called  # Documentation generation
        
        # Verify workflow success
        assert result['success'] is True
        assert 'workflow_id' in result
        assert 'phases_completed' in result


# Pytest fixtures for common test data
@pytest.fixture
def workflow_instance():
    """Fixture providing a CoordinatedLegacyRemovalWorkflow instance"""
    from ltms.coordination.legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow
    return CoordinatedLegacyRemovalWorkflow()

@pytest.fixture
def sample_analysis_results():
    """Fixture providing sample analysis results from LegacyCodeAnalyzer"""
    return {
        'success': True,
        'legacy_decorators': [
            {
                'name': 'legacy_memory_tool',
                'file': 'ltms/tools/legacy.py',
                'line': 45,
                'decorators': ['@mcp.tool']
            }
        ],
        'functional_tools': [
            {
                'name': 'memory_action',
                'file': 'ltms/tools/consolidated.py',
                'type': 'functional_replacement'
            }
        ],
        'analysis_report': {
            'total_legacy_decorators': 1,
            'total_functional_tools': 1
        }
    }

@pytest.fixture
def sample_validation_results():
    """Fixture providing sample validation results from SafetyValidator"""
    return {
        'success': True,
        'validation_report': {
            'safety_score': 95.0,
            'removal_recommendation': 'APPROVED',
            'risk_level': 'LOW',
            'validation_timestamp': '2025-08-24T10:30:00Z'
        },
        'safety_checks': [
            {'check': 'functional_tools_available', 'status': 'PASS'},
            {'check': 'configuration_valid', 'status': 'PASS'}
        ]
    }

@pytest.fixture
def successful_workflow_mocks():
    """Fixture providing mocks for successful workflow execution"""
    return {
        'todo_action': {'success': True, 'task_id': 'test_task'},
        'memory_action': {'success': True, 'doc_id': 777},
        'chat_action': {'success': True},
        'graph_action': {'success': True},
        'cache_action': {'success': True},
        'sync_action': {'success': True, 'synchronized': 3},
        'documentation_action': {'success': True, 'updated': True}
    }