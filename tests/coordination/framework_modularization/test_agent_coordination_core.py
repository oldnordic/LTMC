"""
Comprehensive TDD tests for AgentCoordinationCore extraction.
Tests the main coordination logic that orchestrates all framework components.

Following TDD methodology: Tests written FIRST before extraction.
AgentCoordinationCore will be the main LTMCAgentCoordinator class with integrated components.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentCoordinationCore:
    """Test AgentCoordinationCore class - to be extracted from agent_coordination_framework.py"""
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_agent_coordination_core_creation(self, mock_memory_action):
        """Test AgentCoordinationCore can be instantiated with LTMC initialization"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        # Setup mock
        mock_memory_action.return_value = {'success': True, 'doc_id': 123}
        
        coordinator = AgentCoordinationCore("Test coordination task", "test_coord_123")
        
        assert hasattr(coordinator, 'task_id')
        assert hasattr(coordinator, 'conversation_id')
        assert hasattr(coordinator, 'task_description')
        assert hasattr(coordinator, 'state')
        assert hasattr(coordinator, 'registration_manager')
        assert hasattr(coordinator, 'message_handler')
        
        assert coordinator.task_id == "test_coord_123"
        assert coordinator.task_description == "Test coordination task"
        assert coordinator.conversation_id.startswith("agent_coord_")
        
        # Verify LTMC initialization was called
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'coordination_init_' in memory_call[1]['file_name']
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_agent_coordination_core_with_custom_id(self, mock_memory_action):
        """Test AgentCoordinationCore with custom coordination ID"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Custom task", "custom_coord_456")
        
        assert coordinator.task_id == "custom_coord_456"
        assert coordinator.conversation_id == "agent_coord_custom_coord_456"
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_register_agent_integration(self, mock_memory_action):
        """Test agent registration through coordination core"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Setup mocks
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Registration test", "reg_test_123")
        
        with patch('ltms.coordination.agent_coordination_core.graph_action') as mock_graph:
            mock_graph.return_value = {'success': True}
            
            # Test agent registration
            result = coordinator.register_agent(
                agent_id="test_integration_agent",
                agent_type="ltmc-integration-test",
                task_scope=["integration_tasks"],
                dependencies=["dep_agent"],
                outputs=["integration_output"]
            )
        
        assert result is True
        
        # Verify agent was added to coordination state
        assert "test_integration_agent" in coordinator.state["active_agents"]
        
        # Verify registration manager was used
        registration = coordinator.registration_manager.get_agent_registration("test_integration_agent")
        assert registration is not None
        assert registration.agent_type == "ltmc-integration-test"
        assert registration.status == AgentStatus.INITIALIZING
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_send_agent_message_integration(self, mock_memory_action):
        """Test message sending through coordination core"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Message test", "msg_test_456")
        
        # Register agents first
        with patch('ltms.coordination.agent_coordination_core.graph_action'):
            coordinator.register_agent("msg_sender", "ltmc-sender", ["send_tasks"])
            coordinator.register_agent("msg_recipient", "ltmc-recipient", ["receive_tasks"])
        
        # Create test message
        message = AgentMessage(
            sender_agent="msg_sender",
            recipient_agent="msg_recipient",
            message_type="test_integration",
            content={"test": "integration_message"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            conversation_id=coordinator.conversation_id,
            task_id=coordinator.task_id
        )
        
        # Reset mock for message sending
        mock_memory_action.reset_mock()
        
        # Test message sending
        result = coordinator.send_agent_message(message)
        
        assert result is True
        
        # Verify message handler was used
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert 'agent_message_msg_sender_to_msg_recipient' in memory_call[1]['file_name']
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_coordinate_agent_handoff(self, mock_memory_action):
        """Test agent handoff coordination functionality"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Handoff test", "handoff_test_789")
        
        # Register agents
        with patch('ltms.coordination.agent_coordination_core.graph_action') as mock_graph:
            mock_graph.return_value = {'success': True}
            
            coordinator.register_agent("handoff_from", "ltmc-sender", ["analysis"])
            coordinator.register_agent("handoff_to", "ltmc-receiver", ["validation"])
            
            # Reset mocks
            mock_memory_action.reset_mock()
            mock_graph.reset_mock()
            
            # Test handoff coordination
            result = coordinator.coordinate_agent_handoff(
                from_agent="handoff_from",
                to_agent="handoff_to",
                handoff_data={"analysis_complete": True, "results": "analysis_data"}
            )
        
        assert result is True
        
        # Verify state was updated
        assert coordinator.state["current_agent"] == "handoff_to"
        
        # Verify agents' status was updated
        from_registration = coordinator.registration_manager.get_agent_registration("handoff_from")
        to_registration = coordinator.registration_manager.get_agent_registration("handoff_to")
        
        assert from_registration.status == AgentStatus.COMPLETED
        assert to_registration.status == AgentStatus.ACTIVE
        
        # Verify handoff message was sent
        assert mock_memory_action.call_count >= 3  # Message + 2 status updates
        
        # Verify graph relationship was created
        mock_graph.assert_called_once()
        graph_call = mock_graph.call_args
        assert graph_call[1]['relationship'] == 'hands_off_to'
        assert 'agent_handoff_from' in graph_call[1]['source_entity']
        assert 'agent_handoff_to' in graph_call[1]['target_entity']
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_get_coordination_summary(self, mock_memory_action):
        """Test coordination summary generation"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        # Setup mock for initialization and summary
        mock_memory_action.return_value = {'success': True, 'total_found': 5}
        
        coordinator = AgentCoordinationCore("Summary test", "summary_test_101")
        
        # Register multiple agents
        with patch('ltms.coordination.agent_coordination_core.graph_action'):
            coordinator.register_agent("summary_agent_1", "ltmc-type-1", ["task1"])
            coordinator.register_agent("summary_agent_2", "ltmc-type-2", ["task2"])
            coordinator.register_agent("summary_agent_3", "ltmc-type-3", ["task3"])
        
        # Add some findings to state
        coordinator.state["agent_findings"].append({
            "agent_id": "summary_agent_1",
            "findings": {"test": "finding_1"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Reset mock for summary query
        mock_memory_action.reset_mock()
        mock_memory_action.return_value = {'success': True, 'total_found': 8}
        
        # Test summary generation
        summary = coordinator.get_coordination_summary()
        
        assert isinstance(summary, dict)
        assert summary["task_id"] == "summary_test_101"
        assert summary["task_description"] == "Summary test"
        assert len(summary["registered_agents"]) == 3
        assert "summary_agent_1" in summary["registered_agents"]
        assert "summary_agent_2" in summary["registered_agents"]
        assert "summary_agent_3" in summary["registered_agents"]
        assert summary["findings_count"] == 1
        assert summary["ltmc_documents"] == 8
        
        # Verify agent statuses are included
        assert "agent_statuses" in summary
        assert len(summary["agent_statuses"]) == 3
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_finalize_coordination(self, mock_memory_action):
        """Test coordination finalization and final report generation"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Finalize test", "finalize_test_202")
        
        # Register and complete some agents
        with patch('ltms.coordination.agent_coordination_core.graph_action'):
            coordinator.register_agent("final_agent_1", "ltmc-final-1", ["final_task_1"])
            coordinator.register_agent("final_agent_2", "ltmc-final-2", ["final_task_2"])
            
            # Update one agent to completed
            coordinator.registration_manager.update_agent_status(
                "final_agent_1", 
                AgentStatus.COMPLETED,
                findings={"finalization": "complete"}
            )
        
        # Add findings to state
        coordinator.state["agent_findings"].append({
            "agent_id": "final_agent_1",
            "findings": {"final": "results"},
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Reset mock for finalization
        mock_memory_action.reset_mock()
        
        # Test finalization
        final_report = coordinator.finalize_coordination()
        
        assert isinstance(final_report, dict)
        assert final_report["coordination_completed"] is True
        assert final_report["task_id"] == "finalize_test_202"
        assert final_report["task_description"] == "Finalize test"
        assert final_report["total_agents"] == 2
        assert final_report["successful_agents"] == 1  # One completed agent
        assert final_report["total_findings"] == 1
        
        # Verify final report was stored in LTMC
        mock_memory_action.assert_called_once()
        memory_call = mock_memory_action.call_args
        assert memory_call[1]['action'] == 'store'
        assert 'coordination_final_report_' in memory_call[1]['file_name']
        assert 'coordination_complete' in memory_call[1]['tags']
        
        # Verify agent summary is included
        assert "agent_summary" in final_report
        assert len(final_report["agent_summary"]) == 2
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_coordination_error_handling(self, mock_memory_action):
        """Test coordination error handling for initialization failure"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        # Setup mock to fail
        mock_memory_action.side_effect = Exception("LTMC initialization failed")
        
        # Should handle initialization error gracefully
        with pytest.raises(Exception) as excinfo:
            coordinator = AgentCoordinationCore("Error test", "error_test_303")
        
        assert "LTMC initialization failed" in str(excinfo.value)
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_retrieve_agent_messages_integration(self, mock_memory_action):
        """Test message retrieval through coordination core"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        # Setup mock for initialization
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Message retrieval test", "msg_retrieve_404")
        
        # Setup mock for message retrieval
        mock_memory_action.return_value = {
            'success': True,
            'documents': [
                {
                    'id': 1,
                    'content': '# Agent Message: sender → retrieve_test_agent\n\n{"message": "test"}'
                }
            ]
        }
        
        # Test message retrieval
        messages = coordinator.retrieve_agent_messages("retrieve_test_agent")
        
        assert isinstance(messages, list)
        assert len(messages) == 1
        assert 'sender → retrieve_test_agent' in messages[0]['parsed_content']
    
    def test_coordination_state_management(self):
        """Test coordination state structure and management"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        
        with patch('ltms.coordination.agent_coordination_core.memory_action'):
            coordinator = AgentCoordinationCore("State test", "state_test_505")
            
            # Verify initial state structure
            assert coordinator.state["task_id"] == "state_test_505"
            assert coordinator.state["primary_task"] == "State test"
            assert isinstance(coordinator.state["active_agents"], list)
            assert isinstance(coordinator.state["agent_findings"], list)
            assert isinstance(coordinator.state["shared_context"], dict)
            assert isinstance(coordinator.state["completion_status"], dict)
            assert isinstance(coordinator.state["coordination_metadata"], dict)
            
            # Test state updates
            coordinator.state["current_agent"] = "state_test_agent"
            coordinator.state["shared_context"]["test_key"] = "test_value"
            
            assert coordinator.state["current_agent"] == "state_test_agent"
            assert coordinator.state["shared_context"]["test_key"] == "test_value"
    
    def test_component_integration(self):
        """Test integration between all coordination components"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_registration_manager import AgentRegistrationManager
        from ltms.coordination.agent_message_handler import AgentMessageHandler
        
        with patch('ltms.coordination.agent_coordination_core.memory_action'):
            coordinator = AgentCoordinationCore("Integration test", "integration_test_606")
            
            # Verify component integration
            assert isinstance(coordinator.registration_manager, AgentRegistrationManager)
            assert isinstance(coordinator.message_handler, AgentMessageHandler)
            
            # Verify components share same task and conversation IDs
            assert coordinator.registration_manager.task_id == coordinator.task_id
            assert coordinator.registration_manager.conversation_id == coordinator.conversation_id
            assert coordinator.message_handler.task_id == coordinator.task_id
            assert coordinator.message_handler.conversation_id == coordinator.conversation_id


class TestAgentCoordinationCoreWorkflows:
    """Test complex coordination workflows with AgentCoordinationCore"""
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_complete_coordination_workflow(self, mock_memory_action):
        """Test complete agent coordination workflow from start to finish"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentMessage, AgentStatus
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Complete workflow test", "workflow_complete_707")
        
        with patch('ltms.coordination.agent_coordination_core.graph_action') as mock_graph:
            mock_graph.return_value = {'success': True}
            
            # 1. Register multiple agents
            coordinator.register_agent("workflow_planner", "ltmc-planner", ["planning"], outputs=["plan"])
            coordinator.register_agent("workflow_executor", "ltmc-executor", ["execution"], dependencies=["workflow_planner"], outputs=["results"])
            
            # 2. Update agent status and add findings
            coordinator.registration_manager.update_agent_status(
                "workflow_planner", 
                AgentStatus.COMPLETED,
                findings={"planning_complete": True, "plan": "execution_plan"}
            )
            
            # 3. Coordinate handoff
            handoff_result = coordinator.coordinate_agent_handoff(
                "workflow_planner",
                "workflow_executor", 
                {"plan": "execution_plan", "ready": True}
            )
            
            assert handoff_result is True
            
            # 4. Complete second agent
            coordinator.registration_manager.update_agent_status(
                "workflow_executor",
                AgentStatus.COMPLETED,
                findings={"execution_complete": True, "results": "workflow_results"}
            )
            
            # 5. Generate summary
            summary = coordinator.get_coordination_summary()
            assert summary["task_id"] == "workflow_complete_707"
            assert len(summary["registered_agents"]) == 2
            
            # 6. Finalize coordination
            final_report = coordinator.finalize_coordination()
            assert final_report["coordination_completed"] is True
            assert final_report["successful_agents"] == 2
    
    @patch('ltms.coordination.agent_coordination_core.memory_action')
    def test_multi_agent_communication_workflow(self, mock_memory_action):
        """Test workflow with multiple agents communicating"""
        from ltms.coordination.agent_coordination_core import AgentCoordinationCore
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        mock_memory_action.return_value = {'success': True}
        
        coordinator = AgentCoordinationCore("Communication workflow", "comm_workflow_808")
        
        with patch('ltms.coordination.agent_coordination_core.graph_action'):
            # Register agents
            coordinator.register_agent("comm_agent_a", "ltmc-comm-a", ["comm_tasks"])
            coordinator.register_agent("comm_agent_b", "ltmc-comm-b", ["comm_tasks"])
            coordinator.register_agent("comm_agent_c", "ltmc-comm-c", ["comm_tasks"])
            
            # Create and send multiple messages
            message_a_to_b = AgentMessage(
                sender_agent="comm_agent_a",
                recipient_agent="comm_agent_b",
                message_type="coordination_request",
                content={"request": "data_from_a"},
                timestamp=datetime.now(timezone.utc).isoformat(),
                conversation_id=coordinator.conversation_id,
                task_id=coordinator.task_id
            )
            
            message_b_to_c = AgentMessage(
                sender_agent="comm_agent_b",
                recipient_agent="comm_agent_c", 
                message_type="coordination_handoff",
                content={"processed_data": "from_b"},
                timestamp=datetime.now(timezone.utc).isoformat(),
                conversation_id=coordinator.conversation_id,
                task_id=coordinator.task_id
            )
            
            # Send messages
            result_1 = coordinator.send_agent_message(message_a_to_b)
            result_2 = coordinator.send_agent_message(message_b_to_c)
            
            assert result_1 is True
            assert result_2 is True
            
            # Verify communication was tracked
            summary = coordinator.get_coordination_summary()
            assert len(summary["registered_agents"]) == 3


# Pytest fixtures for coordination core testing
@pytest.fixture
def coordination_core():
    """Fixture providing an AgentCoordinationCore instance"""
    from ltms.coordination.agent_coordination_core import AgentCoordinationCore
    
    with patch('ltms.coordination.agent_coordination_core.memory_action'):
        return AgentCoordinationCore("Fixture test task", "fixture_coord_999")

@pytest.fixture
def coordination_core_with_agents():
    """Fixture providing coordination core with registered agents"""
    from ltms.coordination.agent_coordination_core import AgentCoordinationCore
    
    with patch('ltms.coordination.agent_coordination_core.memory_action'):
        with patch('ltms.coordination.agent_coordination_core.graph_action'):
            coordinator = AgentCoordinationCore("Fixture with agents", "fixture_agents_888")
            
            coordinator.register_agent("fixture_agent_1", "ltmc-fixture-1", ["fixture_tasks"])
            coordinator.register_agent("fixture_agent_2", "ltmc-fixture-2", ["fixture_tasks"])
            
            return coordinator

@pytest.fixture
def mock_ltmc_integration():
    """Fixture providing complete LTMC tool mocking"""
    with patch('ltms.coordination.agent_coordination_core.memory_action') as mock_memory:
        with patch('ltms.coordination.agent_coordination_core.graph_action') as mock_graph:
            mock_memory.return_value = {'success': True, 'doc_id': 777}
            mock_graph.return_value = {'success': True}
            
            yield {
                'memory_action': mock_memory,
                'graph_action': mock_graph
            }