"""
Comprehensive TDD tests for Workflow Results Manager extraction.
Tests workflow results compilation and reporting.

Following TDD methodology: Tests written FIRST before extraction.
WorkflowResultsManager will handle workflow results compilation and reporting.
MANDATORY: Uses ALL required LTMC tools for results management and storage.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestWorkflowResultsManager:
    """Test WorkflowResultsManager class - to be extracted from legacy_removal_workflow.py"""
    
    def test_workflow_results_manager_creation(self):
        """Test WorkflowResultsManager can be instantiated"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Mock dependencies
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        manager = WorkflowResultsManager(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "test_workflow_id", "test_conversation_id"
        )
        
        assert hasattr(manager, 'coordinator')
        assert hasattr(manager, 'state_manager')
        assert hasattr(manager, 'analyzer')
        assert hasattr(manager, 'validator')
        assert hasattr(manager, 'workflow_id')
        assert hasattr(manager, 'conversation_id')
        assert hasattr(manager, 'workflow_results')
        assert manager.workflow_id == "test_workflow_id"
        assert isinstance(manager.workflow_results, dict)
    
    def test_compile_workflow_results_comprehensive(self):
        """Test comprehensive workflow results compilation"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Setup mocks with comprehensive data
        mock_coordinator = Mock()
        mock_coordinator.get_coordination_summary.return_value = {
            'agents_coordinated': 2,
            'messages_exchanged': 25,
            'handoffs_completed': 3
        }
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {
            'state_transitions': 45,
            'validation_errors': 2,
            'recovery_attempts': 1
        }
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "comprehensive_analyzer"
        
        mock_validator = Mock()
        mock_validator.agent_id = "comprehensive_validator"
        
        manager = WorkflowResultsManager(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "comprehensive_workflow", "comprehensive_conv"
        )
        
        # Test data for compilation
        analysis_result = {
            'success': True,
            'legacy_decorators': [
                {'name': 'legacy_func_1', 'file': 'test1.py'},
                {'name': 'legacy_func_2', 'file': 'test2.py'}
            ],
            'functional_tools': [
                {'name': 'memory_action', 'status': 'active'},
                {'name': 'chat_action', 'status': 'active'}
            ]
        }
        
        validation_result = {
            'success': True,
            'validation_report': {
                'safety_score': 92.5,
                'removal_recommendation': 'PROCEED_WITH_CAUTION',
                'risk_level': 'MEDIUM'
            }
        }
        
        removal_plan = {
            'success': True,
            'tasks_created': 18,
            'execution_strategy': 'sequential_with_validation'
        }
        
        documentation_results = {
            'generated': True,
            'synchronized': True,
            'cache_cleared': True
        }
        
        # Test comprehensive compilation
        result = manager.compile_workflow_results(
            analysis_result, validation_result, removal_plan, documentation_results
        )
        
        # Verify compilation success
        assert result['success'] is True
        assert 'workflow_results' in result
        
        # Verify workflow results structure
        workflow_results = result['workflow_results']
        
        # Core workflow metadata
        assert workflow_results['workflow_id'] == 'comprehensive_workflow'
        assert workflow_results['conversation_id'] == 'comprehensive_conv'
        assert workflow_results['workflow_status'] == 'COMPLETED'
        assert workflow_results['phases_completed'] == 6
        assert workflow_results['agents_coordinated'] == 2
        assert workflow_results['ltmc_tools_used'] == 11
        
        # Analysis results
        analysis_data = workflow_results['analysis_results']
        assert analysis_data['success'] is True
        assert analysis_data['legacy_decorators_found'] == 2
        assert analysis_data['functional_tools_available'] == 2
        assert analysis_data['analysis_agent'] == 'comprehensive_analyzer'
        
        # Validation results
        validation_data = workflow_results['validation_results']
        assert validation_data['success'] is True
        assert validation_data['safety_score'] == 92.5
        assert validation_data['recommendation'] == 'PROCEED_WITH_CAUTION'
        assert validation_data['risk_level'] == 'MEDIUM'
        assert validation_data['validation_agent'] == 'comprehensive_validator'
        
        # Removal plan results
        plan_data = workflow_results['removal_plan_results']
        assert plan_data['success'] is True
        assert plan_data['tasks_created'] == 18
        assert plan_data['execution_strategy'] == 'sequential_with_validation'
        
        # Documentation results
        doc_data = workflow_results['documentation_results']
        assert doc_data['generated'] is True
        assert doc_data['synchronized'] is True
        assert doc_data['cache_cleared'] is True
        
        # Integration data
        assert workflow_results['coordination_summary'] == mock_coordinator.get_coordination_summary.return_value
        assert workflow_results['state_performance'] == mock_state_manager.get_performance_metrics.return_value
        
        # Verify timestamp
        assert 'execution_timestamp' in workflow_results
        timestamp = workflow_results['execution_timestamp']
        # Should not raise exception
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    def test_compile_workflow_results_failure_scenarios(self):
        """Test workflow results compilation with failure scenarios"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Setup mocks
        mock_coordinator = Mock()
        mock_coordinator.get_coordination_summary.return_value = {'failure_test': True}
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {'failure_test': True}
        
        manager = WorkflowResultsManager(
            Mock(), mock_coordinator, Mock(), Mock(),
            "failure_workflow", "failure_conv"
        )
        
        # Test data with failures
        analysis_result = {
            'success': False,
            'error': 'Analysis failed due to missing files',
            'legacy_decorators': [],
            'functional_tools': []
        }
        
        validation_result = {
            'success': False,
            'error': 'Validation failed due to safety concerns',
            'validation_report': {
                'safety_score': 0,
                'removal_recommendation': 'ABORT',
                'risk_level': 'HIGH'
            }
        }
        
        removal_plan = {
            'success': False,
            'error': 'Cannot create plan due to validation failure',
            'tasks_created': 0
        }
        
        documentation_results = {
            'generated': False,
            'synchronized': False,
            'cache_cleared': False
        }
        
        # Test failure compilation
        result = manager.compile_workflow_results(
            analysis_result, validation_result, removal_plan, documentation_results
        )
        
        # Verify failure compilation
        assert result['success'] is True  # Compilation succeeds even with component failures
        workflow_results = result['workflow_results']
        
        # Verify failure data is properly captured
        assert workflow_results['analysis_results']['success'] is False
        assert workflow_results['validation_results']['success'] is False
        assert workflow_results['removal_plan_results']['success'] is False
        assert workflow_results['documentation_results']['generated'] is False
    
    def test_generate_summary_report(self):
        """Test summary report generation"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "summary_workflow", "summary_conv"
        )
        
        # Setup workflow results
        manager.workflow_results = {
            'workflow_id': 'summary_workflow',
            'workflow_status': 'COMPLETED',
            'phases_completed': 6,
            'analysis_results': {
                'success': True,
                'legacy_decorators_found': 5
            },
            'validation_results': {
                'success': True,
                'safety_score': 88.5,
                'recommendation': 'PROCEED'
            },
            'removal_plan_results': {
                'success': True,
                'tasks_created': 12
            }
        }
        
        # Test summary generation
        summary = manager.generate_summary_report()
        
        # Verify summary structure
        assert summary['workflow_id'] == 'summary_workflow'
        assert summary['status'] == 'COMPLETED'
        assert summary['phases_completed'] == 6
        assert summary['legacy_decorators_found'] == 5
        assert summary['safety_score'] == 88.5
        assert summary['removal_recommendation'] == 'PROCEED'
        assert summary['tasks_created'] == 12
        assert 'summary_timestamp' in summary
    
    def test_validate_results_structure_comprehensive(self):
        """Test comprehensive results structure validation"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "validation_workflow", "validation_conv"
        )
        
        # Test valid structure
        valid_results = {
            'workflow_id': 'validation_workflow',
            'conversation_id': 'validation_conv',
            'execution_timestamp': datetime.now(timezone.utc).isoformat(),
            'workflow_status': 'COMPLETED',
            'phases_completed': 6,
            'agents_coordinated': 2,
            'ltmc_tools_used': 11,
            'analysis_results': {
                'success': True,
                'legacy_decorators_found': 3,
                'functional_tools_available': 11,
                'analysis_agent': 'test_analyzer'
            },
            'validation_results': {
                'success': True,
                'safety_score': 95,
                'recommendation': 'PROCEED',
                'risk_level': 'LOW',
                'validation_agent': 'test_validator'
            },
            'removal_plan_results': {
                'success': True,
                'tasks_created': 8,
                'execution_strategy': 'sequential_with_validation'
            },
            'documentation_results': {
                'generated': True,
                'synchronized': True,
                'cache_cleared': True
            },
            'coordination_summary': {'test': True},
            'state_performance': {'test': True}
        }
        
        # Test validation
        is_valid, issues = manager.validate_results_structure(valid_results)
        
        # Verify validation passes
        assert is_valid is True
        assert len(issues) == 0
    
    def test_validate_results_structure_missing_fields(self):
        """Test results structure validation with missing fields"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "missing_fields_workflow", "missing_fields_conv"
        )
        
        # Test invalid structure (missing required fields)
        invalid_results = {
            'workflow_id': 'missing_fields_workflow',
            # Missing conversation_id, execution_timestamp, etc.
            'workflow_status': 'COMPLETED',
            'analysis_results': {
                # Missing success field
                'legacy_decorators_found': 2
            }
        }
        
        # Test validation
        is_valid, issues = manager.validate_results_structure(invalid_results)
        
        # Verify validation fails
        assert is_valid is False
        assert len(issues) > 0
        
        # Check for expected missing fields
        issues_text = ' '.join(issues)
        assert 'conversation_id' in issues_text or 'missing' in issues_text.lower()
    
    def test_export_results_to_formats(self):
        """Test results export to different formats"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "export_workflow", "export_conv"
        )
        
        # Setup test results
        test_results = {
            'workflow_id': 'export_workflow',
            'status': 'COMPLETED',
            'results': {'test': 'data'}
        }
        manager.workflow_results = test_results
        
        # Test JSON export
        json_export = manager.export_results_to_json()
        assert isinstance(json_export, str)
        parsed_json = json.loads(json_export)
        assert parsed_json['workflow_id'] == 'export_workflow'
        
        # Test dictionary export
        dict_export = manager.export_results_to_dict()
        assert isinstance(dict_export, dict)
        assert dict_export['workflow_id'] == 'export_workflow'
        
        # Test summary export
        summary_export = manager.export_summary()
        assert isinstance(summary_export, dict)
        assert 'workflow_id' in summary_export
    
    def test_results_manager_state_management(self):
        """Test results manager state management"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "state_mgmt_workflow", "state_mgmt_conv"
        )
        
        # Verify initial state
        assert isinstance(manager.workflow_results, dict)
        assert len(manager.workflow_results) == 0
        
        # Test state updates
        test_data = {'test_key': 'test_value', 'status': 'INITIALIZING'}
        manager.workflow_results.update(test_data)
        
        assert manager.workflow_results['test_key'] == 'test_value'
        assert manager.workflow_results['status'] == 'INITIALIZING'
        
        # Test state reset
        manager.reset_results()
        assert len(manager.workflow_results) == 0
    
    def test_performance_metrics_integration(self):
        """Test performance metrics integration"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Setup performance metrics
        mock_coordinator = Mock()
        mock_coordinator.get_coordination_summary.return_value = {
            'total_messages': 50,
            'total_handoffs': 5,
            'coordination_time': '120.5s'
        }
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {
            'state_transitions': 75,
            'average_transition_time': 0.85,
            'error_recoveries': 3
        }
        
        manager = WorkflowResultsManager(
            mock_coordinator, mock_state_manager, Mock(), Mock(),
            "performance_workflow", "performance_conv"
        )
        
        # Test metrics integration
        analysis_result = {'success': True, 'legacy_decorators': [], 'functional_tools': []}
        validation_result = {'success': True, 'validation_report': {'safety_score': 90}}
        removal_plan = {'success': True, 'tasks_created': 5}
        documentation_results = {'generated': True, 'synchronized': True, 'cache_cleared': True}
        
        result = manager.compile_workflow_results(
            analysis_result, validation_result, removal_plan, documentation_results
        )
        
        # Verify performance metrics are included
        workflow_results = result['workflow_results']
        assert 'coordination_summary' in workflow_results
        assert 'state_performance' in workflow_results
        
        # Verify performance data
        coord_summary = workflow_results['coordination_summary']
        assert coord_summary['total_messages'] == 50
        assert coord_summary['total_handoffs'] == 5
        
        state_perf = workflow_results['state_performance']
        assert state_perf['state_transitions'] == 75
        assert state_perf['average_transition_time'] == 0.85


class TestWorkflowResultsManagerIntegration:
    """Test WorkflowResultsManager integration scenarios"""
    
    def test_integration_with_coordination_components(self):
        """Test integration with coordination framework components"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        mock_coordinator = Mock()
        mock_state_manager = Mock()
        mock_analyzer = Mock()
        mock_validator = Mock()
        
        manager = WorkflowResultsManager(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "integration_test", "integration_conv"
        )
        
        # Test that all components are properly integrated
        assert manager.coordinator == mock_coordinator
        assert manager.state_manager == mock_state_manager
        assert manager.analyzer == mock_analyzer
        assert manager.validator == mock_validator
    
    def test_end_to_end_results_workflow(self):
        """Test complete end-to-end results management workflow"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Setup comprehensive mocks
        mock_coordinator = Mock()
        mock_coordinator.get_coordination_summary.return_value = {'e2e': 'coordination'}
        
        mock_state_manager = Mock()
        mock_state_manager.get_performance_metrics.return_value = {'e2e': 'performance'}
        
        mock_analyzer = Mock()
        mock_analyzer.agent_id = "e2e_analyzer"
        
        mock_validator = Mock()
        mock_validator.agent_id = "e2e_validator"
        
        manager = WorkflowResultsManager(
            mock_coordinator, mock_state_manager, mock_analyzer, mock_validator,
            "e2e_workflow", "e2e_conv"
        )
        
        # Test complete workflow
        # 1. Compile results
        analysis_result = {'success': True, 'legacy_decorators': [{'name': 'e2e_func'}], 'functional_tools': []}
        validation_result = {'success': True, 'validation_report': {'safety_score': 85}}
        removal_plan = {'success': True, 'tasks_created': 10}
        documentation_results = {'generated': True, 'synchronized': True, 'cache_cleared': True}
        
        compile_result = manager.compile_workflow_results(
            analysis_result, validation_result, removal_plan, documentation_results
        )
        
        # 2. Generate summary
        summary = manager.generate_summary_report()
        
        # 3. Validate structure
        is_valid, issues = manager.validate_results_structure(compile_result['workflow_results'])
        
        # 4. Export results
        json_export = manager.export_results_to_json()
        dict_export = manager.export_results_to_dict()
        
        # Verify complete workflow
        assert compile_result['success'] is True
        assert 'workflow_results' in compile_result
        assert 'workflow_id' in summary
        assert summary['workflow_id'] == 'e2e_workflow'
        assert is_valid is True
        assert len(issues) == 0
        assert isinstance(json_export, str)
        assert isinstance(dict_export, dict)
    
    def test_results_consistency_across_operations(self):
        """Test results consistency across all manager operations"""
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        manager = WorkflowResultsManager(
            Mock(), Mock(), Mock(), Mock(),
            "consistency_workflow", "consistency_conv"
        )
        
        # Setup consistent test data
        test_workflow_id = "consistency_workflow"
        test_conversation_id = "consistency_conv"
        
        analysis_result = {'success': True, 'legacy_decorators': []}
        validation_result = {'success': True, 'validation_report': {'safety_score': 80}}
        removal_plan = {'success': True, 'tasks_created': 7}
        documentation_results = {'generated': True, 'synchronized': True, 'cache_cleared': True}
        
        # Compile results
        compile_result = manager.compile_workflow_results(
            analysis_result, validation_result, removal_plan, documentation_results
        )
        
        # Test consistency across all operations
        workflow_results = compile_result['workflow_results']
        summary = manager.generate_summary_report()
        json_export = json.loads(manager.export_results_to_json())
        dict_export = manager.export_results_to_dict()
        
        # Verify consistent workflow ID across all operations
        assert workflow_results['workflow_id'] == test_workflow_id
        assert summary['workflow_id'] == test_workflow_id
        assert json_export['workflow_id'] == test_workflow_id
        assert dict_export['workflow_id'] == test_workflow_id
        
        # Verify consistent conversation ID
        assert workflow_results['conversation_id'] == test_conversation_id
        assert json_export['conversation_id'] == test_conversation_id
        assert dict_export['conversation_id'] == test_conversation_id


# Pytest fixtures for workflow results manager testing
@pytest.fixture
def mock_results_manager_dependencies():
    """Fixture providing mock dependencies for results manager testing"""
    mock_coordinator = Mock()
    mock_coordinator.get_coordination_summary.return_value = {'fixture': 'coordination'}
    
    mock_state_manager = Mock()
    mock_state_manager.get_performance_metrics.return_value = {'fixture': 'performance'}
    
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
def workflow_results_manager(mock_results_manager_dependencies):
    """Fixture providing WorkflowResultsManager instance"""
    from ltms.coordination.workflow_results_manager import WorkflowResultsManager
    
    deps = mock_results_manager_dependencies
    return WorkflowResultsManager(
        deps['coordinator'], deps['state_manager'], deps['analyzer'], deps['validator'],
        "fixture_workflow", "fixture_conv"
    )

@pytest.fixture
def sample_workflow_data():
    """Fixture providing sample workflow data for testing"""
    return {
        'analysis_result': {
            'success': True,
            'legacy_decorators': [{'name': 'sample_func'}],
            'functional_tools': [{'name': 'sample_tool'}]
        },
        'validation_result': {
            'success': True,
            'validation_report': {
                'safety_score': 87.5,
                'removal_recommendation': 'PROCEED',
                'risk_level': 'LOW'
            }
        },
        'removal_plan': {
            'success': True,
            'tasks_created': 15,
            'execution_strategy': 'sequential_with_validation'
        },
        'documentation_results': {
            'generated': True,
            'synchronized': True,
            'cache_cleared': True
        }
    }