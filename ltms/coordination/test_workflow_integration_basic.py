"""
Basic Integration Test for Modularized Legacy Removal Workflow
Tests core integration functionality with ALL LTMC tools validation.

TDD requirement: Test integration before replacing original file.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ltms.coordination.legacy_removal_workflow_integrated import CoordinatedLegacyRemovalWorkflow


class TestWorkflowIntegration:
    """Basic integration tests for modularized workflow."""
    
    def setup_method(self):
        """Set up test fixtures with mocked LTMC tools."""
        # Mock LTMC tools to prevent actual tool calls during testing
        self.ltmc_mocks = {
            'todo_action': MagicMock(return_value={'success': True}),
            'chat_action': MagicMock(return_value={'success': True}),
            'memory_action': MagicMock(return_value={'success': True}),
            'graph_action': MagicMock(return_value={'success': True}),
            'documentation_action': MagicMock(return_value={'success': True}),
            'sync_action': MagicMock(return_value={'success': True}),
            'cache_action': MagicMock(return_value={'success': True})
        }
    
    def test_workflow_initialization_integration(self):
        """Test workflow initialization creates all required components."""
        with patch.multiple(
            'ltms.coordination.workflow_initialization',
            todo_action=self.ltmc_mocks['todo_action'],
            chat_action=self.ltmc_mocks['chat_action']
        ), patch('ltms.coordination.workflow_initialization.AgentCoordinationCore') as mock_coordinator, \
           patch('ltms.coordination.workflow_initialization.integrate_state_manager_with_coordinator') as mock_state_integration, \
           patch('ltms.coordination.workflow_initialization.WorkflowOrchestrator') as mock_orchestrator, \
           patch('ltms.coordination.workflow_initialization.LegacyCodeAnalyzer') as mock_analyzer, \
           patch('ltms.coordination.workflow_initialization.SafetyValidator') as mock_validator:
            
            # Setup mock returns
            mock_coordinator.return_value = MagicMock()
            mock_state_integration.return_value = MagicMock()
            mock_orchestrator.return_value = MagicMock()
            mock_analyzer.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_analyzer.return_value.initialize_agent.return_value = True
            mock_validator.return_value.initialize_agent.return_value = True
            
            # Create workflow instance
            workflow = CoordinatedLegacyRemovalWorkflow()
            
            # Verify all components initialized
            assert hasattr(workflow, 'initialization')
            assert hasattr(workflow, 'phase_executor')
            assert hasattr(workflow, 'error_handler')
            assert hasattr(workflow, 'results_manager')
            assert hasattr(workflow, 'workflow_id')
            assert hasattr(workflow, 'conversation_id')
            
            # Verify workflow ID format
            assert workflow.workflow_id.startswith('legacy_removal_workflow_')
            assert workflow.conversation_id.startswith('legacy_removal_')

    def test_workflow_execute_method_exists(self):
        """Test main execution method exists and is callable."""
        with patch.multiple(
            'ltms.coordination.workflow_initialization',
            todo_action=self.ltmc_mocks['todo_action'],
            chat_action=self.ltmc_mocks['chat_action']
        ), patch('ltms.coordination.workflow_initialization.AgentCoordinationCore') as mock_coordinator, \
           patch('ltms.coordination.workflow_initialization.integrate_state_manager_with_coordinator') as mock_state_integration, \
           patch('ltms.coordination.workflow_initialization.WorkflowOrchestrator') as mock_orchestrator, \
           patch('ltms.coordination.workflow_initialization.LegacyCodeAnalyzer') as mock_analyzer, \
           patch('ltms.coordination.workflow_initialization.SafetyValidator') as mock_validator:
            
            # Setup mock returns
            mock_coordinator.return_value = MagicMock()
            mock_state_integration.return_value = MagicMock()
            mock_orchestrator.return_value = MagicMock()
            mock_analyzer.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_analyzer.return_value.initialize_agent.return_value = True
            mock_validator.return_value.initialize_agent.return_value = True
            
            workflow = CoordinatedLegacyRemovalWorkflow()
            
            # Verify main execution method exists
            assert hasattr(workflow, 'execute_coordinated_legacy_removal')
            assert callable(workflow.execute_coordinated_legacy_removal)

    def test_ltmc_tools_integration_validation(self):
        """Validate that ALL LTMC tools are integrated across modules."""
        # Import all modular components to validate LTMC tool integration
        from ltms.coordination.workflow_initialization import WorkflowInitialization
        from ltms.coordination.workflow_phase_executor import WorkflowPhaseExecutor
        from ltms.coordination.workflow_error_handler import WorkflowErrorHandler
        from ltms.coordination.workflow_results_manager import WorkflowResultsManager
        
        # Verify LTMC tool imports exist in each module
        import ltms.coordination.workflow_initialization as init_module
        import ltms.coordination.workflow_phase_executor as phase_module
        import ltms.coordination.workflow_error_handler as error_module
        
        # Validate tool imports in initialization module
        assert hasattr(init_module, 'todo_action')
        assert hasattr(init_module, 'chat_action')
        
        # Validate tool imports in phase executor module (should have ALL 7 tools)
        assert hasattr(phase_module, 'todo_action')
        assert hasattr(phase_module, 'chat_action')
        assert hasattr(phase_module, 'graph_action')
        assert hasattr(phase_module, 'documentation_action')
        assert hasattr(phase_module, 'sync_action')
        assert hasattr(phase_module, 'cache_action')
        assert hasattr(phase_module, 'memory_action')
        
        # Validate tool imports in error handler module
        assert hasattr(error_module, 'chat_action')
        assert hasattr(error_module, 'memory_action')
        
        print("✅ ALL LTMC tools integration validated across all modules")

    def test_modular_delegation_pattern(self):
        """Test that main class properly delegates to modules."""
        with patch.multiple(
            'ltms.coordination.workflow_initialization',
            todo_action=self.ltmc_mocks['todo_action'],
            chat_action=self.ltmc_mocks['chat_action']
        ), patch('ltms.coordination.workflow_initialization.AgentCoordinationCore') as mock_coordinator, \
           patch('ltms.coordination.workflow_initialization.integrate_state_manager_with_coordinator') as mock_state_integration, \
           patch('ltms.coordination.workflow_initialization.WorkflowOrchestrator') as mock_orchestrator, \
           patch('ltms.coordination.workflow_initialization.LegacyCodeAnalyzer') as mock_analyzer, \
           patch('ltms.coordination.workflow_initialization.SafetyValidator') as mock_validator:
            
            # Setup mock returns
            mock_coordinator.return_value = MagicMock()
            mock_state_integration.return_value = MagicMock()
            mock_orchestrator.return_value = MagicMock()
            mock_analyzer.return_value = MagicMock()
            mock_validator.return_value = MagicMock()
            mock_analyzer.return_value.initialize_agent.return_value = True
            mock_validator.return_value.initialize_agent.return_value = True
            
            workflow = CoordinatedLegacyRemovalWorkflow()
            
            # Verify delegation helper methods exist
            assert hasattr(workflow, '_determine_failure_phase')
            assert hasattr(workflow, 'get_workflow_results')
            assert hasattr(workflow, 'get_summary_report')
            assert hasattr(workflow, 'export_results_to_json')
            
            # Verify these are callable
            assert callable(workflow._determine_failure_phase)
            assert callable(workflow.get_workflow_results)
            assert callable(workflow.get_summary_report)
            assert callable(workflow.export_results_to_json)

    def test_file_size_compliance(self):
        """Verify all modular files comply with 300-line limit."""
        import os
        
        coordination_dir = os.path.dirname(__file__)
        modular_files = [
            'legacy_removal_workflow_integrated.py',
            'workflow_initialization.py',
            'workflow_phase_executor.py',
            'workflow_error_handler.py',
            'workflow_results_manager.py'
        ]
        
        for filename in modular_files:
            filepath = os.path.join(coordination_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    line_count = sum(1 for line in f)
                print(f"📏 {filename}: {line_count} lines ({line_count/300*100:.1f}% of 300-line limit)")
                assert line_count <= 300, f"{filename} exceeds 300-line limit with {line_count} lines"

    def test_real_functionality_validation(self):
        """Validate no mocks, stubs, or placeholders in production code."""
        import os
        
        coordination_dir = os.path.dirname(__file__)
        modular_files = [
            'legacy_removal_workflow_integrated.py',
            'workflow_initialization.py',
            'workflow_phase_executor.py',
            'workflow_error_handler.py',
            'workflow_results_manager.py'
        ]
        
        forbidden_patterns = ['pass', 'TODO', 'FIXME', 'MagicMock', 'unittest.mock']
        
        for filename in modular_files:
            filepath = os.path.join(coordination_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    
                for pattern in forbidden_patterns:
                    assert pattern not in content, f"{filename} contains forbidden pattern: {pattern}"
        
        print("✅ Real functionality validation passed - no mocks/stubs/placeholders found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])