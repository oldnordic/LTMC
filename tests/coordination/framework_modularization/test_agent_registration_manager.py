"""
Comprehensive TDD tests for AgentRegistrationManager extraction.
Tests the agent registration and status management functionality.

Following TDD methodology: Tests written FIRST before extraction.
AgentRegistrationManager will handle agent lifecycle management.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentRegistrationManager:
    """Test AgentRegistrationManager class - to be extracted from agent_coordination_framework.py"""
    
    def test_agent_registration_manager_creation(self):
        """Test AgentRegistrationManager can be instantiated"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        
        manager = AgentRegistrationManager("test_task_123", "test_conv_456")
        
        assert hasattr(manager, 'task_id')
        assert hasattr(manager, 'conversation_id')
        assert hasattr(manager, 'agent_registry')
        assert manager.task_id == "test_task_123"
        assert manager.conversation_id == "test_conv_456"
        assert isinstance(manager.agent_registry, dict)
        assert len(manager.agent_registry) == 0
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    @patch('ltms.coordination.agent_registration_manager.graph_action')
    def test_register_agent_success(self, mock_graph_action, mock_memory_action):
        """Test successful agent registration with LTMC integration"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True, 'doc_id': 123}
        mock_graph_action.return_value = {'success': True}
        
        manager = AgentRegistrationManager("test_task", "test_conv")
        
        # Test agent registration
        result = manager.register_agent(
            agent_id="test_agent_1",
            agent_type="ltmc-test-agent",
            task_scope=["test_tasks", "validation"],
            dependencies=["dependency_agent"],
            outputs=["test_output", "validation_report"]
        )
        
        assert result is True
        assert "test_agent_1" in manager.agent_registry
        
        # Verify registration data
        registration = manager.agent_registry["test_agent_1"]
        assert registration.agent_id == "test_agent_1"
        assert registration.agent_type == "ltmc-test-agent"
        assert registration.status == AgentStatus.INITIALIZING
        assert registration.task_scope == ["test_tasks", "validation"]
        assert registration.dependencies == ["dependency_agent"]
        assert registration.outputs == ["test_output", "validation_report"]
        assert registration.task_id == "test_task"
        assert registration.conversation_id == "test_conv"
        
        # Verify LTMC tools were used
        mock_memory_action.assert_called_once()
        mock_graph_action.assert_called_once()
        
        # Verify memory_action call structure
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'agent_registration_test_agent_1' in memory_call[1]['file_name']
        assert 'agent_registration' in memory_call[1]['tags']
        assert 'test_agent_1' in memory_call[1]['tags']
        
        # Verify graph_action call structure
        graph_call = mock_graph_action.call_args
        assert graph_call[1]['action'] == 'link'
        assert 'coordination_task_test_task' in graph_call[1]['source_entity']
        assert 'agent_test_agent_1' in graph_call[1]['target_entity']
        assert graph_call[1]['relationship'] == 'manages'
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    @patch('ltms.coordination.agent_registration_manager.graph_action')
    def test_register_agent_with_defaults(self, mock_graph_action, mock_memory_action):
        """Test agent registration with default parameters"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True}
        mock_graph_action.return_value = {'success': True}
        
        manager = AgentRegistrationManager("default_task", "default_conv")
        
        # Register agent with minimal parameters
        result = manager.register_agent(
            agent_id="minimal_agent",
            agent_type="ltmc-minimal",
            task_scope=["minimal_task"]
        )
        
        assert result is True
        registration = manager.agent_registry["minimal_agent"]
        assert registration.dependencies == []  # Default empty list
        assert registration.outputs == []       # Default empty list
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    @patch('ltms.coordination.agent_registration_manager.graph_action')
    def test_register_agent_error_handling(self, mock_graph_action, mock_memory_action):
        """Test agent registration handles errors gracefully"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        
        # Setup mocks to fail
        mock_memory_action.side_effect = Exception("Memory storage failed")
        mock_graph_action.return_value = {'success': True}
        
        manager = AgentRegistrationManager("error_task", "error_conv")
        
        # Registration should handle error gracefully
        result = manager.register_agent(
            agent_id="error_agent",
            agent_type="ltmc-error-test",
            task_scope=["error_task"]
        )
        
        assert result is False
        assert "error_agent" not in manager.agent_registry
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    def test_update_agent_status_success(self, mock_memory_action):
        """Test successful agent status updates with LTMC integration"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True, 'doc_id': 456}
        
        manager = AgentRegistrationManager("status_task", "status_conv")
        
        # First register an agent (with mocked LTMC calls)
        with patch('ltms.coordination.agent_registration_manager.graph_action'):
            manager.register_agent(
                agent_id="status_agent",
                agent_type="ltmc-status-test",
                task_scope=["status_test"]
            )
        
        # Reset mock to test status update specifically
        mock_memory_action.reset_mock()
        
        # Test status update
        result = manager.update_agent_status(
            agent_id="status_agent",
            status=AgentStatus.ACTIVE,
            findings={"test_finding": "status_data"}
        )
        
        assert result is True
        
        # Verify status was updated
        registration = manager.agent_registry["status_agent"]
        assert registration.status == AgentStatus.ACTIVE
        assert registration.last_activity is not None
        
        # Verify LTMC memory_action was called for both status and findings
        assert mock_memory_action.call_count == 2
        
        # Verify status update call
        status_call = mock_memory_action.call_args_list[0]
        assert status_call[1]['action'] == 'store'
        assert 'agent_status_status_agent' in status_call[1]['file_name']
        assert 'agent_status' in status_call[1]['tags']
        
        # Verify findings storage call
        findings_call = mock_memory_action.call_args_list[1]
        assert findings_call[1]['action'] == 'store'
        assert 'agent_findings_status_agent' in findings_call[1]['file_name']
        assert 'agent_findings' in findings_call[1]['tags']
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    def test_update_agent_status_without_findings(self, mock_memory_action):
        """Test agent status update without findings"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        mock_memory_action.return_value = {'success': True}
        
        manager = AgentRegistrationManager("no_findings_task", "no_findings_conv")
        
        # Register agent first
        with patch('ltms.coordination.agent_registration_manager.graph_action'):
            manager.register_agent(
                agent_id="no_findings_agent",
                agent_type="ltmc-no-findings",
                task_scope=["no_findings_test"]
            )
        
        # Reset mock
        mock_memory_action.reset_mock()
        
        # Update status without findings
        result = manager.update_agent_status(
            agent_id="no_findings_agent",
            status=AgentStatus.COMPLETED
        )
        
        assert result is True
        
        # Should only have one call (status update, no findings storage)
        assert mock_memory_action.call_count == 1
        status_call = mock_memory_action.call_args
        assert 'agent_status' in status_call[1]['tags']
    
    def test_update_agent_status_unregistered_agent(self):
        """Test status update for unregistered agent fails gracefully"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        manager = AgentRegistrationManager("unregistered_task", "unregistered_conv")
        
        # Try to update status for agent that doesn't exist
        result = manager.update_agent_status(
            agent_id="nonexistent_agent",
            status=AgentStatus.ACTIVE
        )
        
        assert result is False
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    def test_update_agent_status_error_handling(self, mock_memory_action):
        """Test status update handles LTMC errors gracefully"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        manager = AgentRegistrationManager("error_status_task", "error_status_conv")
        
        # Register agent first
        with patch('ltms.coordination.agent_registration_manager.graph_action'):
            with patch('ltms.coordination.agent_registration_manager.memory_action') as reg_mock:
                reg_mock.return_value = {'success': True}
                manager.register_agent(
                    agent_id="error_status_agent",
                    agent_type="ltmc-error-status",
                    task_scope=["error_test"]
                )
        
        # Make memory_action fail for status update
        mock_memory_action.side_effect = Exception("Status update failed")
        
        result = manager.update_agent_status(
            agent_id="error_status_agent",
            status=AgentStatus.ERROR
        )
        
        assert result is False
    
    def test_get_agent_registration(self):
        """Test retrieval of agent registration data"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        manager = AgentRegistrationManager("get_agent_task", "get_agent_conv")
        
        # Register agent first
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            with patch('ltms.coordination.agent_registration_manager.graph_action'):
                manager.register_agent(
                    agent_id="get_test_agent",
                    agent_type="ltmc-get-test",
                    task_scope=["get_test"]
                )
        
        # Test getting registration
        registration = manager.get_agent_registration("get_test_agent")
        
        assert registration is not None
        assert registration.agent_id == "get_test_agent"
        assert registration.agent_type == "ltmc-get-test"
        assert registration.status == AgentStatus.INITIALIZING
    
    def test_get_agent_registration_nonexistent(self):
        """Test getting registration for nonexistent agent returns None"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        
        manager = AgentRegistrationManager("nonexistent_task", "nonexistent_conv")
        
        registration = manager.get_agent_registration("nonexistent_agent")
        assert registration is None
    
    def test_get_all_registrations(self):
        """Test retrieval of all agent registrations"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        
        manager = AgentRegistrationManager("all_agents_task", "all_agents_conv")
        
        # Register multiple agents
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            with patch('ltms.coordination.agent_registration_manager.graph_action'):
                manager.register_agent("agent1", "ltmc-type1", ["task1"])
                manager.register_agent("agent2", "ltmc-type2", ["task2"])
                manager.register_agent("agent3", "ltmc-type3", ["task3"])
        
        all_registrations = manager.get_all_registrations()
        
        assert len(all_registrations) == 3
        assert "agent1" in all_registrations
        assert "agent2" in all_registrations
        assert "agent3" in all_registrations
        assert all_registrations["agent1"].agent_type == "ltmc-type1"
        assert all_registrations["agent2"].agent_type == "ltmc-type2"
        assert all_registrations["agent3"].agent_type == "ltmc-type3"
    
    def test_get_active_agents(self):
        """Test retrieval of only active agents"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        manager = AgentRegistrationManager("active_test_task", "active_test_conv")
        
        # Register agents
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            with patch('ltms.coordination.agent_registration_manager.graph_action'):
                manager.register_agent("active_agent", "ltmc-active", ["active_task"])
                manager.register_agent("completed_agent", "ltmc-completed", ["completed_task"])
                manager.register_agent("error_agent", "ltmc-error", ["error_task"])
        
        # Update statuses
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            manager.update_agent_status("active_agent", AgentStatus.ACTIVE)
            manager.update_agent_status("completed_agent", AgentStatus.COMPLETED)
            manager.update_agent_status("error_agent", AgentStatus.ERROR)
        
        active_agents = manager.get_active_agents()
        
        assert len(active_agents) == 1
        assert "active_agent" in active_agents
        assert active_agents["active_agent"].status == AgentStatus.ACTIVE


class TestAgentRegistrationManagerIntegration:
    """Test AgentRegistrationManager integration scenarios"""
    
    @patch('ltms.coordination.agent_registration_manager.memory_action')
    @patch('ltms.coordination.agent_registration_manager.graph_action') 
    def test_complete_agent_lifecycle(self, mock_graph_action, mock_memory_action):
        """Test complete agent lifecycle from registration to completion"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True}
        mock_graph_action.return_value = {'success': True}
        
        manager = AgentRegistrationManager("lifecycle_task", "lifecycle_conv")
        
        # 1. Register agent
        result = manager.register_agent(
            agent_id="lifecycle_agent",
            agent_type="ltmc-lifecycle-test",
            task_scope=["lifecycle_task"],
            outputs=["lifecycle_output"]
        )
        assert result is True
        
        registration = manager.get_agent_registration("lifecycle_agent")
        assert registration.status == AgentStatus.INITIALIZING
        
        # 2. Activate agent
        result = manager.update_agent_status("lifecycle_agent", AgentStatus.ACTIVE)
        assert result is True
        
        registration = manager.get_agent_registration("lifecycle_agent")
        assert registration.status == AgentStatus.ACTIVE
        
        # 3. Complete agent
        result = manager.update_agent_status(
            "lifecycle_agent", 
            AgentStatus.COMPLETED,
            findings={"lifecycle": "completed_successfully"}
        )
        assert result is True
        
        registration = manager.get_agent_registration("lifecycle_agent")
        assert registration.status == AgentStatus.COMPLETED
        
        # Verify all LTMC calls were made
        assert mock_memory_action.call_count >= 4  # Registration + 2 status updates + findings
        assert mock_graph_action.call_count >= 1   # Registration graph link
    
    def test_multiple_agent_coordination(self):
        """Test coordination of multiple agents with dependencies"""
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        manager = AgentRegistrationManager("multi_agent_task", "multi_agent_conv")
        
        # Register agents with dependencies
        with patch('ltms.coordination.agent_registration_manager.memory_action'):
            with patch('ltms.coordination.agent_registration_manager.graph_action'):
                # Primary agent with no dependencies
                manager.register_agent(
                    agent_id="primary_agent",
                    agent_type="ltmc-primary",
                    task_scope=["analysis"],
                    dependencies=[],
                    outputs=["analysis_report"]
                )
                
                # Secondary agent depending on primary
                manager.register_agent(
                    agent_id="secondary_agent",
                    agent_type="ltmc-secondary",
                    task_scope=["validation"],
                    dependencies=["primary_agent"],
                    outputs=["validation_report"]
                )
                
                # Final agent depending on both
                manager.register_agent(
                    agent_id="final_agent",
                    agent_type="ltmc-final",
                    task_scope=["integration"],
                    dependencies=["primary_agent", "secondary_agent"],
                    outputs=["final_report"]
                )
        
        # Verify all agents registered
        all_registrations = manager.get_all_registrations()
        assert len(all_registrations) == 3
        
        # Verify dependency structure
        assert len(all_registrations["primary_agent"].dependencies) == 0
        assert len(all_registrations["secondary_agent"].dependencies) == 1
        assert len(all_registrations["final_agent"].dependencies) == 2
        assert "primary_agent" in all_registrations["secondary_agent"].dependencies
        assert "primary_agent" in all_registrations["final_agent"].dependencies
        assert "secondary_agent" in all_registrations["final_agent"].dependencies


# Pytest fixtures for registration manager testing
@pytest.fixture
def registration_manager():
    """Fixture providing an AgentRegistrationManager instance"""
    from ltms.coordination.agent_registration_manager import AgentRegistrationManager
    return AgentRegistrationManager("fixture_task", "fixture_conv")

@pytest.fixture
def registered_agent_manager():
    """Fixture providing manager with registered agent"""
    from ltms.coordination.agent_registration_manager import AgentRegistrationManager
    
    manager = AgentRegistrationManager("registered_task", "registered_conv")
    
    with patch('ltms.coordination.agent_registration_manager.memory_action'):
        with patch('ltms.coordination.agent_registration_manager.graph_action'):
            manager.register_agent(
                agent_id="fixture_agent",
                agent_type="ltmc-fixture",
                task_scope=["fixture_task"],
                outputs=["fixture_output"]
            )
    
    return manager

@pytest.fixture
def mock_ltmc_tools():
    """Fixture providing mocked LTMC tools"""
    with patch('ltms.coordination.agent_registration_manager.memory_action') as mock_memory:
        with patch('ltms.coordination.agent_registration_manager.graph_action') as mock_graph:
            mock_memory.return_value = {'success': True, 'doc_id': 999}
            mock_graph.return_value = {'success': True}
            yield {
                'memory_action': mock_memory,
                'graph_action': mock_graph
            }