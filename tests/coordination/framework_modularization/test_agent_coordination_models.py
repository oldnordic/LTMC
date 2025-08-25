"""
Comprehensive TDD tests for AgentCoordinationModels extraction.
Tests the data models that will be extracted from agent_coordination_framework.py.

Following TDD methodology: Tests written FIRST before extraction.
AgentCoordinationModels will contain enums, TypedDict, and dataclasses.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch


class TestAgentStatus:
    """Test AgentStatus enum - to be extracted from agent_coordination_framework.py"""
    
    def test_agent_status_enum_exists(self):
        """Test AgentStatus enum can be imported and has required values"""
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Test all required status values exist
        assert hasattr(AgentStatus, 'INITIALIZING')
        assert hasattr(AgentStatus, 'ACTIVE')
        assert hasattr(AgentStatus, 'WAITING')
        assert hasattr(AgentStatus, 'COMPLETED')
        assert hasattr(AgentStatus, 'ERROR')
        assert hasattr(AgentStatus, 'HANDOFF')
    
    def test_agent_status_values(self):
        """Test AgentStatus enum has correct string values"""
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        assert AgentStatus.INITIALIZING.value == "initializing"
        assert AgentStatus.ACTIVE.value == "active"
        assert AgentStatus.WAITING.value == "waiting"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.HANDOFF.value == "handoff"
    
    def test_agent_status_enum_operations(self):
        """Test AgentStatus enum supports standard enum operations"""
        from ltms.coordination.agent_coordination_models import AgentStatus
        
        # Test enum comparison
        assert AgentStatus.ACTIVE == AgentStatus.ACTIVE
        assert AgentStatus.ACTIVE != AgentStatus.COMPLETED
        
        # Test enum in collections
        status_list = [AgentStatus.ACTIVE, AgentStatus.COMPLETED]
        assert AgentStatus.ACTIVE in status_list
        assert AgentStatus.ERROR not in status_list
        
        # Test string representation
        assert str(AgentStatus.ACTIVE) == "AgentStatus.ACTIVE"


class TestCoordinationState:
    """Test CoordinationState TypedDict - to be extracted from agent_coordination_framework.py"""
    
    def test_coordination_state_typeddict_structure(self):
        """Test CoordinationState TypedDict has correct structure"""
        from ltms.coordination.agent_coordination_models import CoordinationState
        
        # Test that CoordinationState can be imported
        assert CoordinationState is not None
        
        # Test sample CoordinationState creation
        sample_state: CoordinationState = {
            "task_id": "test_task_123",
            "conversation_id": "test_conv_456", 
            "primary_task": "Test task description",
            "active_agents": ["agent1", "agent2"],
            "agent_findings": [{"agent": "agent1", "data": "findings"}],
            "shared_context": {"key": "value"},
            "current_agent": "agent1",
            "next_agent": "agent2",
            "completion_status": {"agent1": True, "agent2": False},
            "coordination_metadata": {"created_at": "2025-08-24T10:30:00Z"}
        }
        
        # Test required fields are present
        assert "task_id" in sample_state
        assert "conversation_id" in sample_state
        assert "primary_task" in sample_state
        assert "active_agents" in sample_state
        assert "agent_findings" in sample_state
        assert "shared_context" in sample_state
        assert "current_agent" in sample_state
        assert "next_agent" in sample_state
        assert "completion_status" in sample_state
        assert "coordination_metadata" in sample_state
    
    def test_coordination_state_type_validation(self):
        """Test CoordinationState field types"""
        from ltms.coordination.agent_coordination_models import CoordinationState
        
        # Test with correct types
        valid_state: CoordinationState = {
            "task_id": "test_task",
            "conversation_id": "test_conv",
            "primary_task": "Test primary task",
            "active_agents": ["agent1"],
            "agent_findings": [{"finding": "data"}],
            "shared_context": {"context": "value"},
            "current_agent": "current",
            "next_agent": "next",
            "completion_status": {"status": True},
            "coordination_metadata": {"meta": "data"}
        }
        
        # Verify types are as expected
        assert isinstance(valid_state["task_id"], str)
        assert isinstance(valid_state["active_agents"], list)
        assert isinstance(valid_state["agent_findings"], list)
        assert isinstance(valid_state["shared_context"], dict)
        assert isinstance(valid_state["completion_status"], dict)
        assert isinstance(valid_state["coordination_metadata"], dict)


class TestAgentMessage:
    """Test AgentMessage dataclass - to be extracted from agent_coordination_framework.py"""
    
    def test_agent_message_dataclass_creation(self):
        """Test AgentMessage dataclass can be created with required fields"""
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="test_recipient",
            message_type="test_message",
            content={"data": "test_content"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="test_conv_123",
            task_id="test_task_456"
        )
        
        assert message.sender_agent == "test_sender"
        assert message.recipient_agent == "test_recipient"
        assert message.message_type == "test_message"
        assert message.content == {"data": "test_content"}
        assert message.timestamp == "2025-08-24T10:30:00Z"
        assert message.conversation_id == "test_conv_123"
        assert message.task_id == "test_task_456"
        assert message.requires_response is False  # Default value
    
    def test_agent_message_with_response_required(self):
        """Test AgentMessage with requires_response parameter"""
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        message = AgentMessage(
            sender_agent="sender",
            recipient_agent="recipient",
            message_type="request",
            content={"request": "data"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="conv_123",
            task_id="task_456",
            requires_response=True
        )
        
        assert message.requires_response is True
    
    def test_agent_message_broadcast(self):
        """Test AgentMessage for broadcast (no specific recipient)"""
        from ltms.coordination.agent_coordination_models import AgentMessage
        
        broadcast_message = AgentMessage(
            sender_agent="broadcast_sender",
            recipient_agent=None,  # Broadcast message
            message_type="broadcast",
            content={"announcement": "broadcast_data"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="broadcast_conv",
            task_id="broadcast_task"
        )
        
        assert broadcast_message.recipient_agent is None
        assert broadcast_message.message_type == "broadcast"
        assert "announcement" in broadcast_message.content
    
    def test_agent_message_serialization(self):
        """Test AgentMessage can be serialized to dictionary"""
        from ltms.coordination.agent_coordination_models import AgentMessage
        from dataclasses import asdict
        
        message = AgentMessage(
            sender_agent="test_sender",
            recipient_agent="test_recipient",
            message_type="serialization_test",
            content={"serialize": "test"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="serialize_conv",
            task_id="serialize_task"
        )
        
        # Test conversion to dictionary
        message_dict = asdict(message)
        
        assert isinstance(message_dict, dict)
        assert message_dict["sender_agent"] == "test_sender"
        assert message_dict["recipient_agent"] == "test_recipient"
        assert message_dict["message_type"] == "serialization_test"
        assert message_dict["content"] == {"serialize": "test"}
        assert message_dict["requires_response"] is False
    
    def test_agent_message_json_serialization(self):
        """Test AgentMessage can be converted to JSON"""
        from ltms.coordination.agent_coordination_models import AgentMessage
        from dataclasses import asdict
        import json
        
        message = AgentMessage(
            sender_agent="json_sender",
            recipient_agent="json_recipient",
            message_type="json_test",
            content={"json_data": "test_value"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="json_conv",
            task_id="json_task"
        )
        
        # Test JSON serialization
        message_json = json.dumps(asdict(message))
        assert isinstance(message_json, str)
        
        # Test JSON deserialization
        message_data = json.loads(message_json)
        assert message_data["sender_agent"] == "json_sender"
        assert message_data["content"]["json_data"] == "test_value"


class TestAgentRegistration:
    """Test AgentRegistration dataclass - to be extracted from agent_coordination_framework.py"""
    
    def test_agent_registration_creation(self):
        """Test AgentRegistration dataclass can be created with all fields"""
        from ltms.coordination.agent_coordination_models import AgentRegistration, AgentStatus
        
        registration = AgentRegistration(
            agent_id="test_agent_123",
            agent_type="ltmc-test-agent",
            status=AgentStatus.INITIALIZING,
            task_scope=["test_task", "validation_task"],
            dependencies=["dependency_agent"],
            outputs=["test_output", "validation_report"],
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:30:05Z",
            conversation_id="reg_conv_123",
            task_id="reg_task_456"
        )
        
        assert registration.agent_id == "test_agent_123"
        assert registration.agent_type == "ltmc-test-agent"
        assert registration.status == AgentStatus.INITIALIZING
        assert registration.task_scope == ["test_task", "validation_task"]
        assert registration.dependencies == ["dependency_agent"]
        assert registration.outputs == ["test_output", "validation_report"]
        assert registration.start_time == "2025-08-24T10:30:00Z"
        assert registration.last_activity == "2025-08-24T10:30:05Z"
        assert registration.conversation_id == "reg_conv_123"
        assert registration.task_id == "reg_task_456"
    
    def test_agent_registration_with_empty_lists(self):
        """Test AgentRegistration with empty dependencies and outputs"""
        from ltms.coordination.agent_coordination_models import AgentRegistration, AgentStatus
        
        registration = AgentRegistration(
            agent_id="independent_agent",
            agent_type="ltmc-independent",
            status=AgentStatus.ACTIVE,
            task_scope=["independent_task"],
            dependencies=[],  # No dependencies
            outputs=[],       # No outputs
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:30:00Z",
            conversation_id="independent_conv",
            task_id="independent_task"
        )
        
        assert len(registration.dependencies) == 0
        assert len(registration.outputs) == 0
        assert isinstance(registration.dependencies, list)
        assert isinstance(registration.outputs, list)
    
    def test_agent_registration_status_updates(self):
        """Test AgentRegistration status can be updated"""
        from ltms.coordination.agent_coordination_models import AgentRegistration, AgentStatus
        
        registration = AgentRegistration(
            agent_id="status_test_agent",
            agent_type="ltmc-status-test",
            status=AgentStatus.INITIALIZING,
            task_scope=["status_task"],
            dependencies=[],
            outputs=["status_output"],
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:30:00Z",
            conversation_id="status_conv",
            task_id="status_task"
        )
        
        # Test status updates
        registration.status = AgentStatus.ACTIVE
        assert registration.status == AgentStatus.ACTIVE
        
        registration.status = AgentStatus.COMPLETED
        assert registration.status == AgentStatus.COMPLETED
        
        # Test last activity update
        new_timestamp = "2025-08-24T10:35:00Z"
        registration.last_activity = new_timestamp
        assert registration.last_activity == new_timestamp
    
    def test_agent_registration_serialization(self):
        """Test AgentRegistration can be serialized"""
        from ltms.coordination.agent_coordination_models import AgentRegistration, AgentStatus
        from dataclasses import asdict
        
        registration = AgentRegistration(
            agent_id="serialize_agent",
            agent_type="ltmc-serializable",
            status=AgentStatus.COMPLETED,
            task_scope=["serialize_task"],
            dependencies=["dep1", "dep2"],
            outputs=["output1", "output2"],
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:35:00Z",
            conversation_id="serialize_conv",
            task_id="serialize_task"
        )
        
        # Test dictionary conversion
        reg_dict = asdict(registration)
        
        assert isinstance(reg_dict, dict)
        assert reg_dict["agent_id"] == "serialize_agent"
        assert reg_dict["agent_type"] == "ltmc-serializable"
        assert reg_dict["status"] == AgentStatus.COMPLETED
        assert reg_dict["task_scope"] == ["serialize_task"]
        assert reg_dict["dependencies"] == ["dep1", "dep2"]
        assert reg_dict["outputs"] == ["output1", "output2"]


class TestAgentCoordinationModelsIntegration:
    """Test integration between all coordination models"""
    
    def test_models_work_together(self):
        """Test all models can be used together in coordination scenario"""
        from ltms.coordination.agent_coordination_models import (
            AgentStatus, CoordinationState, AgentMessage, AgentRegistration
        )
        from dataclasses import asdict
        
        # Create coordination state
        state: CoordinationState = {
            "task_id": "integration_task",
            "conversation_id": "integration_conv",
            "primary_task": "Integration testing",
            "active_agents": ["agent1", "agent2"],
            "agent_findings": [],
            "shared_context": {},
            "current_agent": "agent1",
            "next_agent": "agent2",
            "completion_status": {},
            "coordination_metadata": {"test": "integration"}
        }
        
        # Create agent registration
        registration = AgentRegistration(
            agent_id="agent1",
            agent_type="ltmc-integration-test",
            status=AgentStatus.ACTIVE,
            task_scope=["integration_task"],
            dependencies=[],
            outputs=["integration_output"],
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:30:00Z",
            conversation_id=state["conversation_id"],
            task_id=state["task_id"]
        )
        
        # Create message
        message = AgentMessage(
            sender_agent="agent1",
            recipient_agent="agent2",
            message_type="integration_test",
            content={"integration": "test_data"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id=state["conversation_id"],
            task_id=state["task_id"]
        )
        
        # Test integration
        assert registration.task_id == state["task_id"]
        assert registration.conversation_id == state["conversation_id"]
        assert message.conversation_id == state["conversation_id"]
        assert message.task_id == state["task_id"]
        assert registration.agent_id in state["active_agents"]
        assert registration.status == AgentStatus.ACTIVE
    
    def test_models_json_serialization_integration(self):
        """Test all models can be serialized together"""
        from ltms.coordination.agent_coordination_models import (
            AgentStatus, AgentMessage, AgentRegistration
        )
        from dataclasses import asdict
        import json
        
        registration = AgentRegistration(
            agent_id="json_integration_agent",
            agent_type="ltmc-json-test",
            status=AgentStatus.COMPLETED,
            task_scope=["json_task"],
            dependencies=[],
            outputs=["json_output"],
            start_time="2025-08-24T10:30:00Z",
            last_activity="2025-08-24T10:35:00Z",
            conversation_id="json_conv",
            task_id="json_task"
        )
        
        message = AgentMessage(
            sender_agent="json_integration_agent",
            recipient_agent="recipient",
            message_type="json_integration",
            content={"integration_data": "test"},
            timestamp="2025-08-24T10:30:00Z",
            conversation_id="json_conv",
            task_id="json_task"
        )
        
        # Test combined serialization
        combined_data = {
            "registration": asdict(registration),
            "message": asdict(message)
        }
        
        json_str = json.dumps(combined_data, default=str)  # default=str handles enum
        assert isinstance(json_str, str)
        
        # Test deserialization
        parsed_data = json.loads(json_str)
        assert "registration" in parsed_data
        assert "message" in parsed_data
        assert parsed_data["registration"]["agent_id"] == "json_integration_agent"
        assert parsed_data["message"]["sender_agent"] == "json_integration_agent"


# Pytest fixtures for model testing
@pytest.fixture
def sample_agent_status():
    """Fixture providing sample AgentStatus"""
    from ltms.coordination.agent_coordination_models import AgentStatus
    return AgentStatus.ACTIVE

@pytest.fixture
def sample_coordination_state():
    """Fixture providing sample CoordinationState"""
    from ltms.coordination.agent_coordination_models import CoordinationState
    
    state: CoordinationState = {
        "task_id": "fixture_task",
        "conversation_id": "fixture_conv",
        "primary_task": "Fixture test task",
        "active_agents": ["fixture_agent"],
        "agent_findings": [],
        "shared_context": {"fixture": "data"},
        "current_agent": "fixture_agent",
        "next_agent": None,
        "completion_status": {"fixture_agent": True},
        "coordination_metadata": {"fixture": True}
    }
    return state

@pytest.fixture
def sample_agent_message():
    """Fixture providing sample AgentMessage"""
    from ltms.coordination.agent_coordination_models import AgentMessage
    
    return AgentMessage(
        sender_agent="fixture_sender",
        recipient_agent="fixture_recipient",
        message_type="fixture_message",
        content={"fixture": "content"},
        timestamp="2025-08-24T10:30:00Z",
        conversation_id="fixture_conv",
        task_id="fixture_task"
    )

@pytest.fixture
def sample_agent_registration():
    """Fixture providing sample AgentRegistration"""
    from ltms.coordination.agent_coordination_models import AgentRegistration, AgentStatus
    
    return AgentRegistration(
        agent_id="fixture_agent",
        agent_type="ltmc-fixture",
        status=AgentStatus.ACTIVE,
        task_scope=["fixture_task"],
        dependencies=[],
        outputs=["fixture_output"],
        start_time="2025-08-24T10:30:00Z",
        last_activity="2025-08-24T10:30:00Z",
        conversation_id="fixture_conv",
        task_id="fixture_task"
    )