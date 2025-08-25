"""
Comprehensive TDD tests for agent_state_models module.
Tests all components that will be extracted from agent_state_manager.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


class TestStateTransition:
    """Test StateTransition enum - extracted from agent_state_manager.py lines 42-51"""
    
    def test_state_transition_enum_values(self):
        """Test that StateTransition has all expected enum values"""
        # Import will be updated after extraction
        from ltms.coordination.agent_state_models import StateTransition
        
        expected_values = {
            'INITIALIZE': 'initialize',
            'ACTIVATE': 'activate', 
            'PAUSE': 'pause',
            'RESUME': 'resume',
            'COMPLETE': 'complete',
            'FAIL': 'fail',
            'HANDOFF': 'handoff',
            'RETRY': 'retry'
        }
        
        for attr_name, expected_value in expected_values.items():
            assert hasattr(StateTransition, attr_name)
            assert getattr(StateTransition, attr_name).value == expected_value
    
    def test_state_transition_enum_count(self):
        """Test that StateTransition has exactly 8 values"""
        from ltms.coordination.agent_state_models import StateTransition
        
        assert len(StateTransition) == 8
    
    def test_state_transition_string_representation(self):
        """Test string representation of StateTransition values"""
        from ltms.coordination.agent_state_models import StateTransition
        
        assert str(StateTransition.INITIALIZE) == "StateTransition.INITIALIZE"
        assert StateTransition.ACTIVATE.value == "activate"
    
    def test_state_transition_comparison(self):
        """Test StateTransition enum comparison"""
        from ltms.coordination.agent_state_models import StateTransition
        
        assert StateTransition.INITIALIZE == StateTransition.INITIALIZE
        assert StateTransition.ACTIVATE != StateTransition.PAUSE
    
    def test_state_transition_iteration(self):
        """Test iterating over StateTransition enum"""
        from ltms.coordination.agent_state_models import StateTransition
        
        transitions = list(StateTransition)
        assert len(transitions) == 8
        assert StateTransition.INITIALIZE in transitions


class TestStateSnapshot:
    """Test StateSnapshot dataclass - extracted from agent_state_manager.py lines 54-65"""
    
    def test_state_snapshot_creation(self):
        """Test StateSnapshot dataclass creation with required fields"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        timestamp = datetime.now(timezone.utc).isoformat()
        snapshot = StateSnapshot(
            agent_id="test_agent",
            status=AgentStatus.ACTIVE,
            state_data={"key": "value"},
            timestamp=timestamp,
            task_id="test_task",
            conversation_id="test_conversation"
        )
        
        assert snapshot.agent_id == "test_agent"
        assert snapshot.status == AgentStatus.ACTIVE
        assert snapshot.state_data == {"key": "value"}
        assert snapshot.timestamp == timestamp
        assert snapshot.task_id == "test_task"
        assert snapshot.conversation_id == "test_conversation"
    
    def test_state_snapshot_default_snapshot_id(self):
        """Test that StateSnapshot generates default snapshot_id"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        snapshot = StateSnapshot(
            agent_id="test_agent",
            status=AgentStatus.INITIALIZING,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation"
        )
        
        # Should generate UUID as string
        assert isinstance(snapshot.snapshot_id, str)
        assert len(snapshot.snapshot_id) == 36  # UUID string length
        assert '-' in snapshot.snapshot_id
        
        # Test UUID uniqueness
        snapshot2 = StateSnapshot(
            agent_id="test_agent2",
            status=AgentStatus.INITIALIZING,
            state_data={},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation"
        )
        assert snapshot.snapshot_id != snapshot2.snapshot_id
    
    def test_state_snapshot_default_metadata(self):
        """Test that StateSnapshot has default empty metadata dict"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        snapshot = StateSnapshot(
            agent_id="test_agent",
            status=AgentStatus.WAITING,
            state_data={"test": True},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task", 
            conversation_id="test_conversation"
        )
        
        assert isinstance(snapshot.metadata, dict)
        assert snapshot.metadata == {}
        
        # Test that we can add to metadata
        snapshot.metadata["custom"] = "value"
        assert snapshot.metadata["custom"] == "value"
    
    def test_state_snapshot_with_custom_metadata(self):
        """Test StateSnapshot with custom metadata"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        custom_metadata = {"version": "1.0", "created_by": "test"}
        
        snapshot = StateSnapshot(
            agent_id="test_agent",
            status=AgentStatus.COMPLETED,
            state_data={"result": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation",
            metadata=custom_metadata
        )
        
        assert snapshot.metadata == custom_metadata
        assert snapshot.metadata["version"] == "1.0"
        assert snapshot.metadata["created_by"] == "test"
    
    def test_state_snapshot_serialization(self):
        """Test StateSnapshot can be converted to dict (for JSON storage)"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        snapshot = StateSnapshot(
            agent_id="serialization_test",
            status=AgentStatus.ERROR,
            state_data={"error": "test error"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation",
            metadata={"error_code": 500}
        )
        
        # Test dataclass to dict conversion
        snapshot_dict = asdict(snapshot)
        
        assert isinstance(snapshot_dict, dict)
        assert snapshot_dict["agent_id"] == "serialization_test"
        assert snapshot_dict["status"] == AgentStatus.ERROR  # Enum preserved
        assert snapshot_dict["state_data"]["error"] == "test error"
        assert snapshot_dict["metadata"]["error_code"] == 500
    
    def test_state_snapshot_required_fields(self):
        """Test that StateSnapshot requires all non-default fields"""
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Should raise TypeError if required fields missing
        with pytest.raises(TypeError):
            StateSnapshot()
        
        with pytest.raises(TypeError):
            StateSnapshot(agent_id="test")
        
        with pytest.raises(TypeError):
            StateSnapshot(
                agent_id="test",
                status=AgentStatus.ACTIVE
                # Missing required fields
            )


class TestStateTransitionLog:
    """Test StateTransitionLog dataclass - extracted from agent_state_manager.py lines 67-79"""
    
    def test_state_transition_log_creation(self):
        """Test StateTransitionLog dataclass creation with required fields"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        timestamp = datetime.now(timezone.utc).isoformat()
        log = StateTransitionLog(
            agent_id="test_agent",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            timestamp=timestamp,
            success=True
        )
        
        assert log.agent_id == "test_agent"
        assert log.from_status == AgentStatus.INITIALIZING
        assert log.to_status == AgentStatus.ACTIVE
        assert log.transition_type == StateTransition.ACTIVATE
        assert log.timestamp == timestamp
        assert log.success is True
    
    def test_state_transition_log_default_fields(self):
        """Test StateTransitionLog default fields"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        log = StateTransitionLog(
            agent_id="test_agent",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.COMPLETED,
            transition_type=StateTransition.COMPLETE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
        # Test default values
        assert log.error_message is None
        assert isinstance(log.transition_data, dict)
        assert log.transition_data == {}
        assert isinstance(log.log_id, str)
        assert len(log.log_id) == 36  # UUID string length
    
    def test_state_transition_log_with_error(self):
        """Test StateTransitionLog with error information"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        error_msg = "Validation failed: invalid transition"
        
        log = StateTransitionLog(
            agent_id="error_agent",
            from_status=AgentStatus.WAITING,
            to_status=AgentStatus.ERROR,
            transition_type=StateTransition.FAIL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False,
            error_message=error_msg
        )
        
        assert log.success is False
        assert log.error_message == error_msg
    
    def test_state_transition_log_with_transition_data(self):
        """Test StateTransitionLog with custom transition_data"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        transition_data = {
            "previous_task": "analysis",
            "new_task": "reporting",
            "handoff_data": {"results": ["item1", "item2"]}
        }
        
        log = StateTransitionLog(
            agent_id="handoff_agent",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.HANDOFF,
            transition_type=StateTransition.HANDOFF,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True,
            transition_data=transition_data
        )
        
        assert log.transition_data == transition_data
        assert log.transition_data["previous_task"] == "analysis"
        assert log.transition_data["handoff_data"]["results"] == ["item1", "item2"]
    
    def test_state_transition_log_unique_ids(self):
        """Test that StateTransitionLog generates unique log_id values"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        log1 = StateTransitionLog(
            agent_id="agent1",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            timestamp=timestamp,
            success=True
        )
        
        log2 = StateTransitionLog(
            agent_id="agent2",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            timestamp=timestamp,
            success=True
        )
        
        # log_id should be unique even for similar transitions
        assert log1.log_id != log2.log_id
        assert isinstance(log1.log_id, str)
        assert isinstance(log2.log_id, str)
    
    def test_state_transition_log_serialization(self):
        """Test StateTransitionLog can be converted to dict for storage"""
        from ltms.coordination.agent_state_models import StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        log = StateTransitionLog(
            agent_id="serialize_test",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.ERROR,
            transition_type=StateTransition.FAIL,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=False,
            error_message="Test serialization error",
            transition_data={"context": "unit_test"}
        )
        
        log_dict = asdict(log)
        
        assert isinstance(log_dict, dict)
        assert log_dict["agent_id"] == "serialize_test"
        assert log_dict["from_status"] == AgentStatus.ACTIVE
        assert log_dict["to_status"] == AgentStatus.ERROR
        assert log_dict["transition_type"] == StateTransition.FAIL
        assert log_dict["success"] is False
        assert log_dict["error_message"] == "Test serialization error"
        assert log_dict["transition_data"]["context"] == "unit_test"
    
    def test_state_transition_log_required_fields(self):
        """Test that StateTransitionLog requires all non-default fields"""
        from ltms.coordination.agent_state_models import StateTransitionLog
        
        # Should raise TypeError if required fields missing
        with pytest.raises(TypeError):
            StateTransitionLog()
        
        with pytest.raises(TypeError):
            StateTransitionLog(agent_id="test")
        
        # Should work with all required fields
        from ltms.coordination.agent_state_models import StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        log = StateTransitionLog(
            agent_id="complete_test",
            from_status=AgentStatus.ACTIVE,
            to_status=AgentStatus.COMPLETED,
            transition_type=StateTransition.COMPLETE,
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=True
        )
        
        assert log.agent_id == "complete_test"


class TestAgentStateModelsIntegration:
    """Test integration between all agent_state_models components"""
    
    def test_state_snapshot_with_transition_log_integration(self):
        """Test that StateSnapshot and StateTransitionLog work together"""
        from ltms.coordination.agent_state_models import StateSnapshot, StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create initial snapshot
        initial_snapshot = StateSnapshot(
            agent_id="integration_test",
            status=AgentStatus.INITIALIZING,
            state_data={"phase": "setup"},
            timestamp=timestamp,
            task_id="integration_task",
            conversation_id="integration_conversation"
        )
        
        # Create transition log for moving to active
        transition_log = StateTransitionLog(
            agent_id="integration_test",
            from_status=AgentStatus.INITIALIZING,
            to_status=AgentStatus.ACTIVE,
            transition_type=StateTransition.ACTIVATE,
            timestamp=timestamp,
            success=True,
            transition_data={"snapshot_id": initial_snapshot.snapshot_id}
        )
        
        # Verify integration
        assert initial_snapshot.agent_id == transition_log.agent_id
        assert transition_log.from_status == initial_snapshot.status
        assert transition_log.transition_data["snapshot_id"] == initial_snapshot.snapshot_id
    
    def test_all_enum_combinations(self):
        """Test various StateTransition enum combinations with AgentStatus"""
        from ltms.coordination.agent_state_models import StateTransition, StateTransitionLog
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Test common transition combinations
        valid_combinations = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE, StateTransition.ACTIVATE),
            (AgentStatus.ACTIVE, AgentStatus.COMPLETED, StateTransition.COMPLETE),
            (AgentStatus.ACTIVE, AgentStatus.ERROR, StateTransition.FAIL),
            (AgentStatus.WAITING, AgentStatus.ACTIVE, StateTransition.RESUME),
            (AgentStatus.ACTIVE, AgentStatus.HANDOFF, StateTransition.HANDOFF)
        ]
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for from_status, to_status, transition_type in valid_combinations:
            log = StateTransitionLog(
                agent_id=f"combo_test_{from_status.value}",
                from_status=from_status,
                to_status=to_status,
                transition_type=transition_type,
                timestamp=timestamp,
                success=True
            )
            
            assert log.from_status == from_status
            assert log.to_status == to_status
            assert log.transition_type == transition_type
    
    def test_json_serialization_compatibility(self):
        """Test that all components can be JSON serialized"""
        from ltms.coordination.agent_state_models import StateSnapshot, StateTransitionLog, StateTransition
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        snapshot = StateSnapshot(
            agent_id="json_test",
            status=AgentStatus.ACTIVE,
            state_data={"json_compatible": True, "number": 42},
            timestamp=timestamp,
            task_id="json_task",
            conversation_id="json_conversation",
            metadata={"serialization_test": True}
        )
        
        # Convert to dict for JSON compatibility (enums need special handling)
        snapshot_dict = asdict(snapshot)
        snapshot_dict["status"] = snapshot_dict["status"].value  # Convert enum to string
        
        # Should be JSON serializable
        json_str = json.dumps(snapshot_dict)
        parsed_back = json.loads(json_str)
        
        assert parsed_back["agent_id"] == "json_test"
        assert parsed_back["status"] == "active"
        assert parsed_back["state_data"]["json_compatible"] is True
        assert parsed_back["metadata"]["serialization_test"] is True


# Pytest configuration and fixtures
@pytest.fixture
def sample_agent_id():
    """Fixture providing a sample agent ID"""
    return "test_agent_" + str(uuid.uuid4())[:8]

@pytest.fixture 
def sample_timestamp():
    """Fixture providing a sample timestamp"""
    return datetime.now(timezone.utc).isoformat()

@pytest.fixture
def sample_state_data():
    """Fixture providing sample state data"""
    return {
        "current_task": "testing",
        "progress": 50,
        "context": {"test_mode": True}
    }