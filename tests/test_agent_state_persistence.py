"""
Comprehensive TDD tests for agent_state_persistence module.
Tests the AgentStatePersistence class that will be extracted from agent_state_manager.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock


class TestAgentStatePersistence:
    """Test AgentStatePersistence class - extracted from agent_state_manager.py lines 419-494"""
    
    def test_agent_state_persistence_creation(self):
        """Test AgentStatePersistence class can be instantiated"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        
        assert persistence.coordination_id == "test_coordination"
        assert persistence.conversation_id == "test_conversation"
    
    def test_persist_state_checkpoint_method_exists(self):
        """Test that persist_state_checkpoint method exists and is callable"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        
        assert hasattr(persistence, 'persist_state_checkpoint')
        assert callable(persistence.persist_state_checkpoint)
    
    def test_restore_from_checkpoint_method_exists(self):
        """Test that restore_from_checkpoint method exists and is callable"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        
        assert hasattr(persistence, 'restore_from_checkpoint')
        assert callable(persistence.restore_from_checkpoint)
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_persist_state_checkpoint_empty_states(self, mock_memory_action):
        """Test persisting checkpoint with no agent states"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.persist_state_checkpoint({}, {"test_metric": 42})
        
        assert result is True
        assert mock_memory_action.called
        
        # Verify memory_action was called with correct structure
        call_args = mock_memory_action.call_args
        assert call_args[1]['action'] == 'store'
        assert 'state_checkpoint_' in call_args[1]['file_name']
        
        # Verify checkpoint data structure
        checkpoint_content = json.loads(call_args[1]['content'])
        assert checkpoint_content['checkpoint_action'] == 'state_checkpoint'
        assert checkpoint_content['coordination_id'] == 'test_coordination'
        assert checkpoint_content['total_agents'] == 0
        assert checkpoint_content['agent_states'] == {}
        assert checkpoint_content['performance_metrics'] == {"test_metric": 42}
        assert 'checkpoint_id' in checkpoint_content
        assert 'timestamp' in checkpoint_content
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_persist_state_checkpoint_with_agents(self, mock_memory_action):
        """Test persisting checkpoint with multiple agent states"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        # Create test snapshots
        snapshot1 = StateSnapshot(
            agent_id="agent1",
            status=AgentStatus.ACTIVE,
            state_data={"task": "analysis"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation",
            metadata={"priority": "high"}
        )
        
        snapshot2 = StateSnapshot(
            agent_id="agent2",
            status=AgentStatus.COMPLETED,
            state_data={"result": "success"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation"
        )
        
        agent_states = {
            "agent1": snapshot1,
            "agent2": snapshot2
        }
        
        performance_metrics = {
            "state_transitions": 5,
            "validation_errors": 0,
            "average_transition_time": 0.05
        }
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.persist_state_checkpoint(agent_states, performance_metrics)
        
        assert result is True
        assert mock_memory_action.called
        
        # Verify checkpoint structure with agents
        call_args = mock_memory_action.call_args
        checkpoint_content = json.loads(call_args[1]['content'])
        
        assert checkpoint_content['total_agents'] == 2
        assert len(checkpoint_content['agent_states']) == 2
        assert 'agent1' in checkpoint_content['agent_states']
        assert 'agent2' in checkpoint_content['agent_states']
        
        # Verify agent1 data
        agent1_data = checkpoint_content['agent_states']['agent1']
        assert agent1_data['agent_id'] == 'agent1'
        assert agent1_data['status'] == 'active'
        assert agent1_data['state_data'] == {"task": "analysis"}
        assert agent1_data['metadata'] == {"priority": "high"}
        
        # Verify agent2 data
        agent2_data = checkpoint_content['agent_states']['agent2']
        assert agent2_data['agent_id'] == 'agent2'
        assert agent2_data['status'] == 'completed'
        assert agent2_data['state_data'] == {"result": "success"}
        
        # Verify performance metrics
        assert checkpoint_content['performance_metrics']['state_transitions'] == 5
        assert checkpoint_content['performance_metrics']['validation_errors'] == 0
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_persist_state_checkpoint_memory_failure(self, mock_memory_action):
        """Test persist_state_checkpoint handles memory_action failure"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to simulate failure
        mock_memory_action.return_value = {'success': False, 'error': 'Storage failed'}
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.persist_state_checkpoint({}, {})
        
        assert result is False
        assert mock_memory_action.called
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_persist_state_checkpoint_exception_handling(self, mock_memory_action):
        """Test persist_state_checkpoint handles exceptions gracefully"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to raise exception
        mock_memory_action.side_effect = Exception("Memory system error")
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.persist_state_checkpoint({}, {})
        
        assert result is False
        assert mock_memory_action.called
    
    def test_persist_state_checkpoint_file_naming(self):
        """Test that checkpoint files are named correctly"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        with patch('ltms.coordination.agent_state_persistence.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            persistence = AgentStatePersistence("test_coord_123", "test_conversation")
            persistence.persist_state_checkpoint({}, {})
            
            call_args = mock_memory.call_args
            filename = call_args[1]['file_name']
            
            assert filename.startswith('state_checkpoint_test_coord_123_')
            assert filename.endswith('.json')
            # Should include timestamp
            assert len(filename.split('_')) >= 4
    
    def test_persist_state_checkpoint_tags(self):
        """Test that checkpoint is tagged correctly for LTMC"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        with patch('ltms.coordination.agent_state_persistence.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            persistence = AgentStatePersistence("test_coordination", "test_conversation")
            persistence.persist_state_checkpoint({}, {})
            
            call_args = mock_memory.call_args
            tags = call_args[1]['tags']
            
            assert 'state_checkpoint' in tags
            assert 'test_coordination' in tags
            assert 'checkpoint' in tags
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_no_checkpoints(self, mock_memory_action):
        """Test restore_from_checkpoint when no checkpoints exist"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to return no documents
        mock_memory_action.return_value = {'success': True, 'documents': []}
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.restore_from_checkpoint("any_timestamp")
        
        assert result is False
        assert mock_memory_action.called
        
        # Verify query structure
        call_args = mock_memory_action.call_args
        assert call_args[1]['action'] == 'retrieve'
        assert 'state_checkpoint' in call_args[1]['query']
        assert 'test_coordination' in call_args[1]['query']
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_memory_failure(self, mock_memory_action):
        """Test restore_from_checkpoint handles memory_action failure"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to simulate retrieval failure
        mock_memory_action.return_value = {'success': False, 'error': 'Retrieval failed'}
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.restore_from_checkpoint("timestamp")
        
        assert result is False
        assert mock_memory_action.called
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_successful(self, mock_memory_action):
        """Test successful restoration from checkpoint"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Create mock checkpoint data
        checkpoint_data = {
            "checkpoint_action": "state_checkpoint",
            "coordination_id": "test_coordination",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_agents": 2,
            "agent_states": {
                "agent1": {
                    "agent_id": "agent1",
                    "status": "active",
                    "state_data": {"task": "testing"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": "test_task",
                    "conversation_id": "test_conversation",
                    "snapshot_id": "test-uuid-1",
                    "metadata": {"test": True}
                },
                "agent2": {
                    "agent_id": "agent2",
                    "status": "completed",
                    "state_data": {"result": "success"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": "test_task",
                    "conversation_id": "test_conversation",
                    "snapshot_id": "test-uuid-2",
                    "metadata": {}
                }
            },
            "performance_metrics": {"transitions": 3},
            "checkpoint_id": "checkpoint-uuid"
        }
        
        # Setup mock to return checkpoint
        mock_memory_action.return_value = {
            'success': True,
            'documents': [
                {'content': json.dumps(checkpoint_data)}
            ]
        }
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        restored_states = persistence.restore_from_checkpoint("timestamp")
        
        assert isinstance(restored_states, dict)
        assert len(restored_states) == 2
        assert 'agent1' in restored_states
        assert 'agent2' in restored_states
        
        # Verify restored StateSnapshot objects
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        agent1_snapshot = restored_states['agent1']
        assert isinstance(agent1_snapshot, StateSnapshot)
        assert agent1_snapshot.agent_id == "agent1"
        assert agent1_snapshot.status == AgentStatus.ACTIVE
        assert agent1_snapshot.state_data == {"task": "testing"}
        assert agent1_snapshot.metadata == {"test": True}
        
        agent2_snapshot = restored_states['agent2']
        assert isinstance(agent2_snapshot, StateSnapshot)
        assert agent2_snapshot.agent_id == "agent2"
        assert agent2_snapshot.status == AgentStatus.COMPLETED
        assert agent2_snapshot.state_data == {"result": "success"}
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_partial_failure(self, mock_memory_action):
        """Test restoration with some agents failing to restore"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Create checkpoint with invalid data for one agent
        checkpoint_data = {
            "checkpoint_action": "state_checkpoint",
            "coordination_id": "test_coordination",
            "agent_states": {
                "valid_agent": {
                    "agent_id": "valid_agent",
                    "status": "active",
                    "state_data": {"task": "testing"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": "test_task",
                    "conversation_id": "test_conversation",
                    "snapshot_id": "valid-uuid",
                    "metadata": {}
                },
                "invalid_agent": {
                    # Missing required fields to cause StateSnapshot creation to fail
                    "agent_id": "invalid_agent",
                    "status": "active"
                    # Missing other required fields
                }
            }
        }
        
        mock_memory_action.return_value = {
            'success': True,
            'documents': [{'content': json.dumps(checkpoint_data)}]
        }
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        restored_states = persistence.restore_from_checkpoint("timestamp")
        
        # Should return partial success with only valid agent restored
        assert isinstance(restored_states, dict)
        assert len(restored_states) == 1
        assert 'valid_agent' in restored_states
        assert 'invalid_agent' not in restored_states
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_malformed_json(self, mock_memory_action):
        """Test restore_from_checkpoint handles malformed JSON gracefully"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to return invalid JSON
        mock_memory_action.return_value = {
            'success': True,
            'documents': [{'content': 'invalid json content {'}]
        }
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.restore_from_checkpoint("timestamp")
        
        assert result is False or isinstance(result, dict)  # Should handle gracefully
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_restore_from_checkpoint_exception_handling(self, mock_memory_action):
        """Test restore_from_checkpoint handles exceptions gracefully"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        
        # Setup mock to raise exception
        mock_memory_action.side_effect = Exception("Memory system error")
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        result = persistence.restore_from_checkpoint("timestamp")
        
        assert result is False
        assert mock_memory_action.called


class TestAgentStatePersistenceIntegration:
    """Test integration scenarios for AgentStatePersistence"""
    
    @patch('ltms.coordination.agent_state_persistence.memory_action')
    def test_round_trip_persistence(self, mock_memory_action):
        """Test complete checkpoint → restore cycle"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Create test data
        original_snapshot = StateSnapshot(
            agent_id="roundtrip_test",
            status=AgentStatus.ACTIVE,
            state_data={"complex": {"nested": "data"}, "list": [1, 2, 3]},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="test_task",
            conversation_id="test_conversation",
            metadata={"roundtrip": True}
        )
        
        agent_states = {"roundtrip_test": original_snapshot}
        performance_metrics = {"test_metric": 100}
        
        # Setup mock to capture checkpoint and return it for restore
        checkpoint_content = None
        
        def mock_memory_side_effect(*args, **kwargs):
            nonlocal checkpoint_content
            if kwargs['action'] == 'store':
                checkpoint_content = kwargs['content']
                return {'success': True}
            elif kwargs['action'] == 'retrieve':
                return {
                    'success': True,
                    'documents': [{'content': checkpoint_content}] if checkpoint_content else []
                }
        
        mock_memory_action.side_effect = mock_memory_side_effect
        
        persistence = AgentStatePersistence("test_coordination", "test_conversation")
        
        # Test checkpoint creation
        checkpoint_result = persistence.persist_state_checkpoint(agent_states, performance_metrics)
        assert checkpoint_result is True
        assert checkpoint_content is not None
        
        # Test restoration
        restored_states = persistence.restore_from_checkpoint("timestamp")
        
        assert isinstance(restored_states, dict)
        assert len(restored_states) == 1
        assert 'roundtrip_test' in restored_states
        
        restored_snapshot = restored_states['roundtrip_test']
        
        # Verify data integrity through round-trip
        assert restored_snapshot.agent_id == original_snapshot.agent_id
        assert restored_snapshot.status == original_snapshot.status
        assert restored_snapshot.state_data == original_snapshot.state_data
        assert restored_snapshot.metadata == original_snapshot.metadata
        assert restored_snapshot.task_id == original_snapshot.task_id
        assert restored_snapshot.conversation_id == original_snapshot.conversation_id
    
    def test_persistence_with_all_agent_statuses(self):
        """Test persistence works with all possible AgentStatus values"""
        from ltms.coordination.agent_state_persistence import AgentStatePersistence
        from ltms.coordination.agent_state_models import StateSnapshot
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        # Create snapshots for all status types
        all_statuses = list(AgentStatus)
        agent_states = {}
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        for i, status in enumerate(all_statuses):
            agent_id = f"agent_{status.value}"
            snapshot = StateSnapshot(
                agent_id=agent_id,
                status=status,
                state_data={"status_test": status.value},
                timestamp=timestamp,
                task_id="status_test_task",
                conversation_id="status_test_conversation"
            )
            agent_states[agent_id] = snapshot
        
        with patch('ltms.coordination.agent_state_persistence.memory_action') as mock_memory:
            mock_memory.return_value = {'success': True}
            
            persistence = AgentStatePersistence("test_coordination", "test_conversation")
            result = persistence.persist_state_checkpoint(agent_states, {})
            
            assert result is True
            
            # Verify checkpoint includes all statuses
            call_args = mock_memory.call_args
            checkpoint_content = json.loads(call_args[1]['content'])
            
            assert checkpoint_content['total_agents'] == len(all_statuses)
            
            for status in all_statuses:
                agent_id = f"agent_{status.value}"
                assert agent_id in checkpoint_content['agent_states']
                assert checkpoint_content['agent_states'][agent_id]['status'] == status.value


# Pytest fixtures for common test data
@pytest.fixture
def sample_agent_states():
    """Fixture providing sample agent states for testing"""
    from ltms.coordination.agent_state_models import StateSnapshot
    from ltms.coordination.agent_coordination_framework import AgentStatus
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    return {
        "test_agent_1": StateSnapshot(
            agent_id="test_agent_1",
            status=AgentStatus.ACTIVE,
            state_data={"task": "analysis", "progress": 0.5},
            timestamp=timestamp,
            task_id="fixture_task",
            conversation_id="fixture_conversation"
        ),
        "test_agent_2": StateSnapshot(
            agent_id="test_agent_2", 
            status=AgentStatus.COMPLETED,
            state_data={"result": "success", "output": {"key": "value"}},
            timestamp=timestamp,
            task_id="fixture_task",
            conversation_id="fixture_conversation"
        )
    }

@pytest.fixture
def sample_performance_metrics():
    """Fixture providing sample performance metrics"""
    return {
        "state_transitions": 10,
        "validation_errors": 1,
        "recovery_attempts": 0,
        "successful_handoffs": 3,
        "average_transition_time": 0.025
    }