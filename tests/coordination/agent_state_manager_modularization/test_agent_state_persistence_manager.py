"""
Comprehensive TDD tests for Agent State Persistence Manager extraction.
Tests checkpoint and persistence operations with LTMC tools integration.

Following TDD methodology: Tests written FIRST before extraction.
AgentStatePersistenceManager will handle checkpoints and transition history.
MANDATORY: Uses ALL required LTMC tools (cache_action for performance optimization).
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock


class TestAgentStatePersistenceManager:
    """Test AgentStatePersistenceManager class - to be extracted from agent_state_manager.py"""
    
    def test_agent_state_persistence_manager_creation(self):
        """Test AgentStatePersistenceManager can be instantiated"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        # Mock dependencies
        mock_core = Mock()
        mock_persistence = Mock()
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        assert hasattr(persistence_manager, 'core')
        assert hasattr(persistence_manager, 'persistence')
        assert hasattr(persistence_manager, 'logging')
        assert persistence_manager.core == mock_core
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_persist_state_checkpoint_success(self, mock_cache):
        """Test successful state checkpoint creation with LTMC cache integration"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup LTMC cache tool mock - MANDATORY
        mock_cache.return_value = {'success': True, 'cache_key': 'checkpoint_123'}
        
        # Setup state snapshots
        snapshot_1 = StateSnapshot(
            agent_id="checkpoint_agent_1",
            status=AgentStatus.ACTIVE,
            state_data={"task": "running"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="checkpoint_test",
            conversation_id="checkpoint_conv",
            metadata={"version": "1.0"}
        )
        
        snapshot_2 = StateSnapshot(
            agent_id="checkpoint_agent_2",
            status=AgentStatus.WAITING,
            state_data={"task": "queued"},
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_id="checkpoint_test",
            conversation_id="checkpoint_conv",
            metadata={"version": "1.0"}
        )
        
        # Setup core with agent states
        mock_core = Mock()
        mock_core.coordination_id = "checkpoint_test"
        mock_core.conversation_id = "checkpoint_conv"
        mock_core.agent_states = {
            "checkpoint_agent_1": snapshot_1,
            "checkpoint_agent_2": snapshot_2
        }
        
        # Setup persistence
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = True
        
        mock_logging = Mock()
        
        # Test performance metrics
        performance_metrics = {
            "state_transitions": 10,
            "recovery_attempts": 2,
            "validation_errors": 1
        }
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test checkpoint creation
        result = persistence_manager.persist_state_checkpoint(performance_metrics)
        
        # Verify success
        assert result is True
        
        # Verify persistence system was called
        mock_persistence.persist_state_checkpoint.assert_called_once()
        checkpoint_call = mock_persistence.persist_state_checkpoint.call_args
        assert checkpoint_call[0][0] == mock_core.agent_states  # agent_states
        assert checkpoint_call[0][1] == performance_metrics  # performance_metrics
        
        # Verify LTMC cache was called - MANDATORY
        mock_cache.assert_called_once()
        cache_call = mock_cache.call_args
        assert cache_call[1]['action'] == 'stats'
        assert cache_call[1]['conversation_id'] == 'checkpoint_conv'
        assert cache_call[1]['role'] == 'system'
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_persist_state_checkpoint_failure(self, mock_cache):
        """Test checkpoint creation when persistence fails"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        # Setup cache
        mock_cache.return_value = {'success': True}
        
        mock_core = Mock()
        mock_core.agent_states = {}
        
        # Setup persistence to fail
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = False
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test failed checkpoint
        result = persistence_manager.persist_state_checkpoint({})
        
        # Verify failure
        assert result is False
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_restore_from_checkpoint_success(self, mock_cache):
        """Test successful checkpoint restoration with LTMC cache integration"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        from ltms.coordination.agent_coordination_models import AgentStatus
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup LTMC cache tool mock - MANDATORY
        mock_cache.return_value = {'success': True, 'cache_stats': {'hits': 10, 'misses': 2}}
        
        # Setup restored state data
        restored_snapshot = StateSnapshot(
            agent_id="restored_agent",
            status=AgentStatus.COMPLETED,
            state_data={"task": "finished"},
            timestamp="2025-08-24T10:30:00Z",
            task_id="restore_test",
            conversation_id="restore_conv",
            metadata={"restored": True}
        )
        
        restored_states = {"restored_agent": restored_snapshot}
        
        mock_core = Mock()
        mock_core.coordination_id = "restore_test"
        mock_core.conversation_id = "restore_conv"
        mock_core.agent_states = {}
        
        # Setup persistence to return restored states
        mock_persistence = Mock()
        mock_persistence.restore_from_checkpoint.return_value = restored_states
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test restoration
        checkpoint_timestamp = "2025-08-24T10:30:00Z"
        result = persistence_manager.restore_from_checkpoint(checkpoint_timestamp)
        
        # Verify success
        assert result is True
        
        # Verify persistence system was called
        mock_persistence.restore_from_checkpoint.assert_called_once_with(checkpoint_timestamp)
        
        # Verify core states were updated
        mock_core.agent_states.update.assert_called_once_with(restored_states)
        
        # Verify LTMC cache was called - MANDATORY
        mock_cache.assert_called_once()
        cache_call = mock_cache.call_args
        assert cache_call[1]['action'] == 'stats'
        assert cache_call[1]['conversation_id'] == 'restore_conv'
        assert cache_call[1]['role'] == 'system'
    
    def test_restore_from_checkpoint_no_data(self):
        """Test checkpoint restoration when no data is found"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        mock_core = Mock()
        
        # Setup persistence to return None (no checkpoint found)
        mock_persistence = Mock()
        mock_persistence.restore_from_checkpoint.return_value = None
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test restoration with no data
        result = persistence_manager.restore_from_checkpoint("nonexistent_timestamp")
        
        # Verify failure
        assert result is False
        
        # Verify core states were not updated
        mock_core.agent_states.update.assert_not_called()
    
    def test_get_state_transition_history(self):
        """Test retrieval of state transition history"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        from ltms.coordination.agent_state_models import StateTransitionLog
        
        # Setup mock transition history
        transition_log = StateTransitionLog(
            agent_id="history_agent",
            from_status="INITIALIZING",
            to_status="ACTIVE",
            transition_type="ACTIVATE",
            success=True,
            timestamp="2025-08-24T10:30:00Z",
            coordination_id="history_test",
            conversation_id="history_conv",
            error_message=None,
            transition_data={"test": True}
        )
        
        history = [transition_log]
        
        mock_core = Mock()
        mock_persistence = Mock()
        
        # Setup logging to return history
        mock_logging = Mock()
        mock_logging.get_transition_history.return_value = history
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test history retrieval
        result = persistence_manager.get_state_transition_history("history_agent")
        
        # Verify result
        assert result == history
        assert len(result) == 1
        assert result[0].agent_id == "history_agent"
        
        # Verify logging was called
        mock_logging.get_transition_history.assert_called_once_with("history_agent")
    
    def test_get_state_transition_history_empty(self):
        """Test transition history retrieval for agent with no history"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        mock_core = Mock()
        mock_persistence = Mock()
        
        # Setup logging to return empty history
        mock_logging = Mock()
        mock_logging.get_transition_history.return_value = []
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test empty history retrieval
        result = persistence_manager.get_state_transition_history("no_history_agent")
        
        # Verify empty result
        assert result == []
        assert len(result) == 0
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_exception_handling_during_checkpoint(self, mock_cache):
        """Test exception handling during checkpoint operations"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        # Setup cache to fail
        mock_cache.side_effect = Exception("Cache service unavailable")
        
        mock_core = Mock()
        mock_core.agent_states = {}
        
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = True
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test checkpoint with cache exception
        result = persistence_manager.persist_state_checkpoint({})
        
        # Should handle gracefully but still return result from persistence
        assert result is True  # persistence succeeded despite cache failure
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_ltmc_tools_comprehensive_usage(self, mock_cache):
        """Test comprehensive LTMC tools usage - MANDATORY ALL TOOLS"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        # Setup ALL LTMC tool mocks - MANDATORY
        mock_cache.return_value = {'success': True, 'stats': {'operations': 100}}
        
        mock_core = Mock()
        mock_core.coordination_id = "ltmc_comprehensive"
        mock_core.conversation_id = "ltmc_comprehensive_conv"
        mock_core.agent_states = {"ltmc_agent": "test_snapshot"}
        
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = True
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test comprehensive checkpoint creation
        performance_metrics = {"ltmc_test": True}
        result = persistence_manager.persist_state_checkpoint(performance_metrics)
        
        # Verify success
        assert result is True
        
        # Verify ALL required LTMC tools were used - MANDATORY
        
        # 1. cache_action - MANDATORY Tool 7
        mock_cache.assert_called_once()
        cache_call = mock_cache.call_args
        assert cache_call[1]['action'] == 'stats'
        assert cache_call[1]['conversation_id'] == 'ltmc_comprehensive_conv'
        assert cache_call[1]['role'] == 'system'
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_cache_optimization_during_operations(self, mock_cache):
        """Test cache optimization features during persistence operations"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        # Setup cache with performance stats
        mock_cache.return_value = {
            'success': True,
            'stats': {
                'hits': 85,
                'misses': 15,
                'hit_ratio': 0.85,
                'memory_usage': '2.5MB'
            }
        }
        
        mock_core = Mock()
        mock_core.coordination_id = "cache_optimization"
        mock_core.conversation_id = "cache_optimization_conv"
        mock_core.agent_states = {
            "cached_agent_1": "snapshot_1",
            "cached_agent_2": "snapshot_2"
        }
        
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = True
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test checkpoint with cache optimization
        result = persistence_manager.persist_state_checkpoint({"cache_test": True})
        
        # Verify success and cache usage
        assert result is True
        mock_cache.assert_called_once()
        
        # Verify cache stats were retrieved for optimization
        cache_call = mock_cache.call_args
        assert cache_call[1]['action'] == 'stats'


class TestAgentStatePersistenceManagerIntegration:
    """Test AgentStatePersistenceManager integration scenarios"""
    
    def test_integration_with_core_persistence_logging(self):
        """Test integration with core, persistence, and logging components"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        
        mock_core = Mock()
        mock_persistence = Mock()
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test that all components are properly integrated
        assert persistence_manager.core == mock_core
        assert persistence_manager.persistence == mock_persistence
        assert persistence_manager.logging == mock_logging
    
    @patch('ltms.coordination.agent_state_persistence_manager.cache_action')
    def test_end_to_end_checkpoint_restoration_cycle(self, mock_cache):
        """Test complete checkpoint and restoration cycle"""
        from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
        from ltms.coordination.agent_state_models import StateSnapshot
        
        # Setup cache
        mock_cache.return_value = {'success': True}
        
        # Create test snapshot
        test_snapshot = StateSnapshot(
            agent_id="cycle_agent",
            status="ACTIVE",
            state_data={"cycle": "test"},
            timestamp="2025-08-24T10:30:00Z",
            task_id="cycle_test",
            conversation_id="cycle_conv",
            metadata={"cycle_test": True}
        )
        
        initial_states = {"cycle_agent": test_snapshot}
        
        mock_core = Mock()
        mock_core.coordination_id = "cycle_test"
        mock_core.conversation_id = "cycle_conv"
        mock_core.agent_states = initial_states.copy()
        
        mock_persistence = Mock()
        mock_persistence.persist_state_checkpoint.return_value = True
        mock_persistence.restore_from_checkpoint.return_value = initial_states
        
        mock_logging = Mock()
        
        persistence_manager = AgentStatePersistenceManager(mock_core, mock_persistence, mock_logging)
        
        # Test checkpoint creation
        checkpoint_result = persistence_manager.persist_state_checkpoint({"test": True})
        assert checkpoint_result is True
        
        # Clear states to simulate loss
        mock_core.agent_states.clear()
        
        # Test restoration
        restore_result = persistence_manager.restore_from_checkpoint("2025-08-24T10:30:00Z")
        assert restore_result is True
        
        # Verify restoration called core update
        mock_core.agent_states.update.assert_called_once_with(initial_states)


# Pytest fixtures for persistence manager testing
@pytest.fixture
def mock_persistence_dependencies():
    """Fixture providing mock dependencies for persistence manager testing"""
    mock_core = Mock()
    mock_core.coordination_id = "fixture_persistence_coord"
    mock_core.conversation_id = "fixture_persistence_conv"
    mock_core.agent_states = {}
    
    mock_persistence = Mock()
    mock_persistence.persist_state_checkpoint.return_value = True
    mock_persistence.restore_from_checkpoint.return_value = None
    
    mock_logging = Mock()
    mock_logging.get_transition_history.return_value = []
    
    return {
        'core': mock_core,
        'persistence': mock_persistence,
        'logging': mock_logging
    }

@pytest.fixture
def agent_state_persistence_manager(mock_persistence_dependencies):
    """Fixture providing AgentStatePersistenceManager instance"""
    from ltms.coordination.agent_state_persistence_manager import AgentStatePersistenceManager
    
    deps = mock_persistence_dependencies
    return AgentStatePersistenceManager(deps['core'], deps['persistence'], deps['logging'])

@pytest.fixture
def mock_all_ltmc_persistence_tools():
    """Fixture providing mocks for all LTMC tools used in persistence manager"""
    with patch.multiple(
        'ltms.coordination.agent_state_persistence_manager',
        cache_action=Mock(return_value={'success': True, 'stats': {'hits': 100}})
    ) as mocks:
        yield mocks