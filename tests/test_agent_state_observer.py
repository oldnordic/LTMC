"""
Comprehensive TDD tests for agent_state_observer module.
Tests the AgentStateObserver class that will be extracted from agent_state_manager.py.

Following TDD methodology: Tests written FIRST before implementation.
"""

import pytest
from typing import Callable, List, Dict, Any
from unittest.mock import Mock, MagicMock


class TestAgentStateObserver:
    """Test AgentStateObserver class - extracted from agent_state_manager.py observer methods"""
    
    def test_agent_state_observer_creation(self):
        """Test AgentStateObserver class can be instantiated"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Should initialize with empty observers storage
        assert hasattr(observer_system, 'observers')
        assert isinstance(observer_system.observers, dict)
        assert len(observer_system.observers) == 0
    
    def test_register_observer_method_exists(self):
        """Test that register_observer method exists and is callable"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        assert hasattr(observer_system, 'register_observer')
        assert callable(observer_system.register_observer)
    
    def test_notify_observers_method_exists(self):
        """Test that notify_observers method exists and is callable"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        assert hasattr(observer_system, 'notify_observers')
        assert callable(observer_system.notify_observers)
    
    def test_register_observer_for_specific_agent(self):
        """Test registering observer for a specific agent"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Create mock observer
        mock_observer = Mock()
        
        # Register observer for specific agent
        observer_system.register_observer("agent_1", mock_observer)
        
        # Verify observer is stored
        assert "agent_1" in observer_system.observers
        assert len(observer_system.observers["agent_1"]) == 1
        assert mock_observer in observer_system.observers["agent_1"]
    
    def test_register_observer_for_global_wildcard(self):
        """Test registering global observer using '*' wildcard"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Create mock observer
        global_observer = Mock()
        
        # Register global observer
        observer_system.register_observer("*", global_observer)
        
        # Verify global observer is stored
        assert "*" in observer_system.observers
        assert len(observer_system.observers["*"]) == 1
        assert global_observer in observer_system.observers["*"]
    
    def test_register_multiple_observers_same_agent(self):
        """Test registering multiple observers for the same agent"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Create multiple mock observers
        observer_1 = Mock()
        observer_2 = Mock()
        observer_3 = Mock()
        
        # Register multiple observers for same agent
        observer_system.register_observer("agent_1", observer_1)
        observer_system.register_observer("agent_1", observer_2)
        observer_system.register_observer("agent_1", observer_3)
        
        # Verify all observers are stored
        assert len(observer_system.observers["agent_1"]) == 3
        assert observer_1 in observer_system.observers["agent_1"]
        assert observer_2 in observer_system.observers["agent_1"]
        assert observer_3 in observer_system.observers["agent_1"]
    
    def test_register_observers_multiple_agents(self):
        """Test registering observers for multiple different agents"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Create observers for different agents
        agent1_observer = Mock()
        agent2_observer = Mock()
        global_observer = Mock()
        
        # Register observers
        observer_system.register_observer("agent_1", agent1_observer)
        observer_system.register_observer("agent_2", agent2_observer)
        observer_system.register_observer("*", global_observer)
        
        # Verify separate storage
        assert len(observer_system.observers) == 3
        assert agent1_observer in observer_system.observers["agent_1"]
        assert agent2_observer in observer_system.observers["agent_2"]
        assert global_observer in observer_system.observers["*"]
    
    def test_notify_observers_specific_agent_only(self):
        """Test notifying observers for specific agent only"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Create and register observers
        agent1_observer = Mock()
        agent2_observer = Mock()
        
        observer_system.register_observer("agent_1", agent1_observer)
        observer_system.register_observer("agent_2", agent2_observer)
        
        # Notify observers for agent_1 transition
        observer_system.notify_observers(
            "agent_1",
            AgentStatus.INITIALIZING,
            AgentStatus.ACTIVE
        )
        
        # Verify only agent_1 observer was called
        agent1_observer.assert_called_once_with(
            "agent_1",
            AgentStatus.INITIALIZING,
            AgentStatus.ACTIVE
        )
        
        # Verify agent_2 observer was NOT called
        agent2_observer.assert_not_called()
    
    def test_notify_observers_global_wildcard(self):
        """Test that global observers (*) are notified for any agent"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Register global observer
        global_observer = Mock()
        observer_system.register_observer("*", global_observer)
        
        # Notify for any agent transition
        observer_system.notify_observers(
            "any_agent",
            AgentStatus.ACTIVE,
            AgentStatus.COMPLETED
        )
        
        # Verify global observer was called
        global_observer.assert_called_once_with(
            "any_agent",
            AgentStatus.ACTIVE,
            AgentStatus.COMPLETED
        )
    
    def test_notify_observers_both_specific_and_global(self):
        """Test that both specific and global observers are notified"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Register both specific and global observers
        specific_observer = Mock()
        global_observer = Mock()
        
        observer_system.register_observer("target_agent", specific_observer)
        observer_system.register_observer("*", global_observer)
        
        # Notify for target_agent transition
        observer_system.notify_observers(
            "target_agent",
            AgentStatus.WAITING,
            AgentStatus.ACTIVE
        )
        
        # Verify both observers were called
        specific_observer.assert_called_once_with(
            "target_agent",
            AgentStatus.WAITING,
            AgentStatus.ACTIVE
        )
        
        global_observer.assert_called_once_with(
            "target_agent",
            AgentStatus.WAITING,
            AgentStatus.ACTIVE
        )
    
    def test_notify_observers_multiple_specific_observers(self):
        """Test notifying multiple observers for the same agent"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Register multiple observers for same agent
        observer_1 = Mock()
        observer_2 = Mock()
        observer_3 = Mock()
        
        observer_system.register_observer("test_agent", observer_1)
        observer_system.register_observer("test_agent", observer_2)
        observer_system.register_observer("test_agent", observer_3)
        
        # Notify observers
        observer_system.notify_observers(
            "test_agent",
            AgentStatus.ERROR,
            AgentStatus.ACTIVE
        )
        
        # Verify all observers were called
        for observer in [observer_1, observer_2, observer_3]:
            observer.assert_called_once_with(
                "test_agent",
                AgentStatus.ERROR,
                AgentStatus.ACTIVE
            )
    
    def test_notify_observers_no_observers_registered(self):
        """Test notifying when no observers are registered (should not crash)"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Should not raise exception when no observers registered
        observer_system.notify_observers(
            "nonexistent_agent",
            AgentStatus.ACTIVE,
            AgentStatus.COMPLETED
        )
        
        # Should complete successfully
        assert True
    
    def test_notify_observers_error_handling(self):
        """Test that observer errors don't crash notification system"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Create observer that raises exception
        failing_observer = Mock(side_effect=Exception("Observer error"))
        working_observer = Mock()
        
        observer_system.register_observer("test_agent", failing_observer)
        observer_system.register_observer("test_agent", working_observer)
        
        # Should not raise exception despite failing observer
        observer_system.notify_observers(
            "test_agent",
            AgentStatus.ACTIVE,
            AgentStatus.COMPLETED
        )
        
        # Verify both observers were called despite error
        failing_observer.assert_called_once()
        working_observer.assert_called_once()
    
    def test_notify_observers_correct_parameter_types(self):
        """Test that observers receive correct parameter types"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Register observer that validates parameter types
        def type_checking_observer(agent_id, from_status, to_status):
            assert isinstance(agent_id, str)
            assert isinstance(from_status, AgentStatus)
            assert isinstance(to_status, AgentStatus)
            assert from_status != to_status  # Should be different statuses
        
        observer_system.register_observer("test_agent", type_checking_observer)
        
        # Should not raise assertion errors
        observer_system.notify_observers(
            "test_agent",
            AgentStatus.INITIALIZING,
            AgentStatus.ACTIVE
        )
    
    def test_notify_observers_with_all_agent_statuses(self):
        """Test notification system works with all possible AgentStatus values"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Track all status combinations called
        called_transitions = []
        
        def tracking_observer(agent_id, from_status, to_status):
            called_transitions.append((from_status, to_status))
        
        observer_system.register_observer("test_agent", tracking_observer)
        
        # Test with various status transitions
        test_transitions = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE),
            (AgentStatus.ACTIVE, AgentStatus.WAITING),
            (AgentStatus.WAITING, AgentStatus.COMPLETED),
            (AgentStatus.ACTIVE, AgentStatus.ERROR),
            (AgentStatus.ERROR, AgentStatus.INITIALIZING),
            (AgentStatus.ACTIVE, AgentStatus.HANDOFF),
            (AgentStatus.HANDOFF, AgentStatus.COMPLETED)
        ]
        
        for from_status, to_status in test_transitions:
            observer_system.notify_observers("test_agent", from_status, to_status)
        
        # Verify all transitions were processed
        assert len(called_transitions) == len(test_transitions)
        assert called_transitions == test_transitions
    
    def test_observer_function_signature_validation(self):
        """Test that observer functions can have various valid signatures"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Test different valid observer signatures
        
        # Standard function
        def standard_observer(agent_id, from_status, to_status):
            pass
        
        # Lambda function
        lambda_observer = lambda agent_id, from_status, to_status: None
        
        # Method of a class
        class ObserverClass:
            def observer_method(self, agent_id, from_status, to_status):
                pass
        
        obj = ObserverClass()
        method_observer = obj.observer_method
        
        # Register all types
        observer_system.register_observer("test_agent", standard_observer)
        observer_system.register_observer("test_agent", lambda_observer)
        observer_system.register_observer("test_agent", method_observer)
        
        # Should work with all observer types
        observer_system.notify_observers(
            "test_agent",
            AgentStatus.ACTIVE,
            AgentStatus.COMPLETED
        )
        
        # Verify all were stored
        assert len(observer_system.observers["test_agent"]) == 3


class TestAgentStateObserverIntegration:
    """Test integration scenarios for AgentStateObserver"""
    
    def test_observer_system_realistic_workflow(self):
        """Test observer system in realistic state transition workflow"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Track agent lifecycle
        lifecycle_events = []
        
        def lifecycle_tracker(agent_id, from_status, to_status):
            lifecycle_events.append({
                "agent": agent_id,
                "transition": f"{from_status.value} → {to_status.value}",
                "timestamp": "test_time"
            })
        
        # Register lifecycle tracker
        observer_system.register_observer("workflow_agent", lifecycle_tracker)
        
        # Simulate realistic agent workflow
        workflow_steps = [
            (AgentStatus.INITIALIZING, AgentStatus.ACTIVE),
            (AgentStatus.ACTIVE, AgentStatus.WAITING),
            (AgentStatus.WAITING, AgentStatus.ACTIVE),
            (AgentStatus.ACTIVE, AgentStatus.COMPLETED)
        ]
        
        for from_status, to_status in workflow_steps:
            observer_system.notify_observers("workflow_agent", from_status, to_status)
        
        # Verify complete workflow was tracked
        assert len(lifecycle_events) == 4
        assert lifecycle_events[0]["transition"] == "initializing → active"
        assert lifecycle_events[1]["transition"] == "active → waiting"
        assert lifecycle_events[2]["transition"] == "waiting → active"
        assert lifecycle_events[3]["transition"] == "active → completed"
    
    def test_observer_system_multiple_agents(self):
        """Test observer system with multiple agents and complex notifications"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        from ltms.coordination.agent_coordination_framework import AgentStatus
        
        observer_system = AgentStateObserver()
        
        # Track notifications per agent
        notifications = {"agent_1": [], "agent_2": [], "global": []}
        
        def agent1_observer(agent_id, from_status, to_status):
            notifications["agent_1"].append((agent_id, from_status, to_status))
        
        def agent2_observer(agent_id, from_status, to_status):
            notifications["agent_2"].append((agent_id, from_status, to_status))
        
        def global_observer(agent_id, from_status, to_status):
            notifications["global"].append((agent_id, from_status, to_status))
        
        # Register observers
        observer_system.register_observer("agent_1", agent1_observer)
        observer_system.register_observer("agent_2", agent2_observer)
        observer_system.register_observer("*", global_observer)
        
        # Notify for agent_1 transition
        observer_system.notify_observers("agent_1", AgentStatus.INITIALIZING, AgentStatus.ACTIVE)
        
        # Notify for agent_2 transition
        observer_system.notify_observers("agent_2", AgentStatus.ACTIVE, AgentStatus.COMPLETED)
        
        # Verify correct notifications
        assert len(notifications["agent_1"]) == 1
        assert len(notifications["agent_2"]) == 1
        assert len(notifications["global"]) == 2  # Notified for both agents
        
        # Verify specific notifications
        assert notifications["agent_1"][0] == ("agent_1", AgentStatus.INITIALIZING, AgentStatus.ACTIVE)
        assert notifications["agent_2"][0] == ("agent_2", AgentStatus.ACTIVE, AgentStatus.COMPLETED)
        
        # Verify global observer received both
        global_notifications = notifications["global"]
        assert ("agent_1", AgentStatus.INITIALIZING, AgentStatus.ACTIVE) in global_notifications
        assert ("agent_2", AgentStatus.ACTIVE, AgentStatus.COMPLETED) in global_notifications
    
    def test_observer_removal_functionality(self):
        """Test removing observers (if implemented)"""
        from ltms.coordination.agent_state_observer import AgentStateObserver
        
        observer_system = AgentStateObserver()
        
        # Register observer
        test_observer = Mock()
        observer_system.register_observer("test_agent", test_observer)
        
        # Verify observer is registered
        assert len(observer_system.observers.get("test_agent", [])) == 1
        
        # Test removal method if it exists
        if hasattr(observer_system, 'remove_observer'):
            observer_system.remove_observer("test_agent", test_observer)
            assert len(observer_system.observers.get("test_agent", [])) == 0


# Pytest fixtures for common test data
@pytest.fixture
def mock_observer():
    """Fixture providing a mock observer function"""
    return Mock()

@pytest.fixture
def observer_system():
    """Fixture providing a fresh AgentStateObserver instance"""
    from ltms.coordination.agent_state_observer import AgentStateObserver
    return AgentStateObserver()

@pytest.fixture
def sample_transition():
    """Fixture providing sample state transition data"""
    from ltms.coordination.agent_coordination_framework import AgentStatus
    return {
        "agent_id": "test_agent",
        "from_status": AgentStatus.ACTIVE,
        "to_status": AgentStatus.COMPLETED
    }