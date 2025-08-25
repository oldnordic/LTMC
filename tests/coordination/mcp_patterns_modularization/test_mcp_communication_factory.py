"""
Comprehensive TDD tests for MCP Communication Factory extraction.
Tests factory functions and public API for MCP communication patterns.

Following TDD methodology: Tests written FIRST before extraction.
Factory functions will provide clean public API for common MCP communication patterns.
"""

import pytest
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch
import uuid


class TestMCPCommunicationFactory:
    """Test MCP Communication Factory functions - to be extracted from mcp_communication_patterns.py"""
    
    def test_create_request_response_message(self):
        """Test create_request_response_message factory function"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        from ltms.coordination.mcp_message_models import CommunicationProtocol, MessagePriority
        
        # Create request-response message
        message = create_request_response_message(
            sender="factory_sender",
            recipient="factory_recipient",
            request_type="factory_request",
            request_data={"factory": "test_data", "request": "info"},
            conversation_id="factory_conv",
            task_id="factory_task"
        )
        
        # Verify message structure
        assert message.sender_agent_id == "factory_sender"
        assert message.recipient_agent_id == "factory_recipient"
        assert message.protocol == CommunicationProtocol.REQUEST_RESPONSE
        assert message.priority == MessagePriority.NORMAL
        assert message.message_type == "factory_request"
        assert message.payload == {"factory": "test_data", "request": "info"}
        assert message.conversation_id == "factory_conv"
        assert message.task_id == "factory_task"
        assert message.requires_ack is True
        assert message.correlation_id is not None
        assert message.timestamp is not None
        
        # Verify message ID is generated
        assert message.message_id is not None
        assert len(message.message_id) > 0
    
    def test_create_request_response_message_unique_ids(self):
        """Test create_request_response_message generates unique IDs"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        # Create multiple messages
        message1 = create_request_response_message(
            sender="unique_sender_1",
            recipient="unique_recipient_1",
            request_type="unique_request_1",
            request_data={"unique": 1},
            conversation_id="unique_conv",
            task_id="unique_task"
        )
        
        message2 = create_request_response_message(
            sender="unique_sender_2",
            recipient="unique_recipient_2",
            request_type="unique_request_2",
            request_data={"unique": 2},
            conversation_id="unique_conv",
            task_id="unique_task"
        )
        
        # Verify unique IDs
        assert message1.message_id != message2.message_id
        assert message1.correlation_id != message2.correlation_id
        
        # Verify timestamps are different (at least slightly)
        assert message1.timestamp != message2.timestamp
    
    def test_create_request_response_message_all_fields(self):
        """Test create_request_response_message with all possible data types"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        # Create message with complex data
        complex_request_data = {
            "string_field": "test_string",
            "number_field": 42,
            "boolean_field": True,
            "null_field": None,
            "array_field": [1, 2, 3, "array_item"],
            "nested_object": {
                "nested_string": "nested_value",
                "nested_number": 3.14,
                "deeply_nested": {
                    "deep_field": "deep_value"
                }
            }
        }
        
        message = create_request_response_message(
            sender="complex_sender",
            recipient="complex_recipient",
            request_type="complex_request",
            request_data=complex_request_data,
            conversation_id="complex_conv",
            task_id="complex_task"
        )
        
        # Verify complex payload is preserved
        assert message.payload == complex_request_data
        assert message.payload["nested_object"]["deeply_nested"]["deep_field"] == "deep_value"
        assert message.payload["array_field"] == [1, 2, 3, "array_item"]
        assert message.payload["boolean_field"] is True
        assert message.payload["null_field"] is None
    
    def test_create_broadcast_message(self):
        """Test create_broadcast_message factory function"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        from ltms.coordination.mcp_message_models import CommunicationProtocol, MessagePriority
        
        # Create broadcast message
        message = create_broadcast_message(
            sender="broadcast_sender",
            message_type="broadcast_announcement",
            broadcast_data={"announcement": "broadcast_test", "priority": "normal"},
            conversation_id="broadcast_conv",
            task_id="broadcast_task"
        )
        
        # Verify broadcast message structure
        assert message.sender_agent_id == "broadcast_sender"
        assert message.recipient_agent_id is None  # Broadcast has no specific recipient
        assert message.protocol == CommunicationProtocol.BROADCAST
        assert message.priority == MessagePriority.NORMAL
        assert message.message_type == "broadcast_announcement"
        assert message.payload == {"announcement": "broadcast_test", "priority": "normal"}
        assert message.conversation_id == "broadcast_conv"
        assert message.task_id == "broadcast_task"
        assert message.requires_ack is False
        assert message.timestamp is not None
        
        # Verify message ID is generated
        assert message.message_id is not None
        assert len(message.message_id) > 0
    
    def test_create_broadcast_message_unique_ids(self):
        """Test create_broadcast_message generates unique IDs"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        # Create multiple broadcast messages
        broadcast1 = create_broadcast_message(
            sender="broadcast_sender_1",
            message_type="broadcast_1",
            broadcast_data={"broadcast": 1},
            conversation_id="broadcast_conv",
            task_id="broadcast_task"
        )
        
        broadcast2 = create_broadcast_message(
            sender="broadcast_sender_2",
            message_type="broadcast_2",
            broadcast_data={"broadcast": 2},
            conversation_id="broadcast_conv",
            task_id="broadcast_task"
        )
        
        # Verify unique IDs
        assert broadcast1.message_id != broadcast2.message_id
        assert broadcast1.timestamp != broadcast2.timestamp
    
    def test_create_broadcast_message_complex_data(self):
        """Test create_broadcast_message with complex broadcast data"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        # Create broadcast with complex data
        complex_broadcast_data = {
            "event_type": "system_notification",
            "severity": "high",
            "affected_services": ["service_a", "service_b", "service_c"],
            "metadata": {
                "timestamp": "2025-08-24T10:30:00Z",
                "source": "monitoring_system",
                "details": {
                    "error_code": 500,
                    "error_message": "Service degradation detected"
                }
            },
            "action_required": True
        }
        
        message = create_broadcast_message(
            sender="monitoring_agent",
            message_type="system_alert",
            broadcast_data=complex_broadcast_data,
            conversation_id="monitoring_conv",
            task_id="monitoring_task"
        )
        
        # Verify complex broadcast data is preserved
        assert message.payload == complex_broadcast_data
        assert message.payload["affected_services"] == ["service_a", "service_b", "service_c"]
        assert message.payload["metadata"]["details"]["error_code"] == 500
        assert message.payload["action_required"] is True
    
    def test_create_broadcast_message_empty_data(self):
        """Test create_broadcast_message with empty broadcast data"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        # Create broadcast with empty data
        message = create_broadcast_message(
            sender="empty_broadcast_sender",
            message_type="empty_broadcast",
            broadcast_data={},
            conversation_id="empty_conv",
            task_id="empty_task"
        )
        
        # Verify empty data is handled correctly
        assert message.payload == {}
        assert message.message_type == "empty_broadcast"
        assert message.sender_agent_id == "empty_broadcast_sender"


class TestMCPCommunicationFactoryIntegration:
    """Test MCP Communication Factory integration with other components"""
    
    def test_factory_messages_work_with_message_broker(self):
        """Test factory-created messages work with LTMCMessageBroker"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message, create_broadcast_message
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        # Create messages using factory functions
        request_message = create_request_response_message(
            sender="factory_integration_sender",
            recipient="factory_integration_recipient",
            request_type="integration_test",
            request_data={"integration": "test"},
            conversation_id="integration_conv",
            task_id="integration_task"
        )
        
        broadcast_message = create_broadcast_message(
            sender="factory_integration_broadcaster",
            message_type="integration_broadcast",
            broadcast_data={"broadcast": "integration_test"},
            conversation_id="integration_conv",
            task_id="integration_task"
        )
        
        # Test with message broker
        broker = LTMCMessageBroker("integration_conv")
        
        with patch('ltms.coordination.mcp_message_broker.memory_action') as mock_memory:
            with patch('ltms.coordination.mcp_message_broker.graph_action') as mock_graph:
                mock_memory.return_value = {'success': True}
                mock_graph.return_value = {'success': True}
                
                # Send factory-created messages
                request_result = broker.send_message(request_message)
                broadcast_result = broker.send_message(broadcast_message)
                
                assert request_result is True
                assert broadcast_result is True
                
                # Verify both messages were stored
                assert mock_memory.call_count == 2
                assert mock_graph.call_count == 2
    
    def test_factory_messages_work_with_workflow_orchestrator(self):
        """Test factory functions can be used within workflow contexts"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        from ltms.coordination.mcp_message_models import CommunicationProtocol, MessagePriority
        
        # Create workflow orchestrator
        orchestrator = WorkflowOrchestrator("factory_workflow", "factory_workflow_conv")
        
        # Create message using factory (simulating what orchestrator might do)
        workflow_message = create_request_response_message(
            sender="workflow_orchestrator",
            recipient="target_agent",
            request_type="workflow_task",
            request_data={
                "workflow_id": "factory_workflow",
                "step_id": "factory_test_step",
                "task_description": "Test factory integration"
            },
            conversation_id="factory_workflow_conv",
            task_id="factory_workflow"
        )
        
        # Verify message is compatible with workflow context
        assert workflow_message.protocol == CommunicationProtocol.REQUEST_RESPONSE
        assert workflow_message.priority == MessagePriority.NORMAL
        assert workflow_message.sender_agent_id == "workflow_orchestrator"
        assert workflow_message.conversation_id == "factory_workflow_conv"
        assert workflow_message.task_id == "factory_workflow"
        assert workflow_message.payload["workflow_id"] == "factory_workflow"
    
    def test_factory_messages_serialization_compatibility(self):
        """Test factory-created messages are compatible with serialization"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message, create_broadcast_message
        from dataclasses import asdict
        
        # Create messages using factory
        request_message = create_request_response_message(
            sender="serialization_sender",
            recipient="serialization_recipient",
            request_type="serialization_test",
            request_data={"serialization": "test_data"},
            conversation_id="serialization_conv",
            task_id="serialization_task"
        )
        
        broadcast_message = create_broadcast_message(
            sender="serialization_broadcaster",
            message_type="serialization_broadcast",
            broadcast_data={"broadcast_serialization": "test"},
            conversation_id="serialization_conv",
            task_id="serialization_task"
        )
        
        # Test serialization to dict
        request_dict = asdict(request_message)
        broadcast_dict = asdict(broadcast_message)
        
        assert isinstance(request_dict, dict)
        assert isinstance(broadcast_dict, dict)
        
        # Test JSON serialization (with enum handling)
        request_for_json = asdict(request_message)
        request_for_json['protocol'] = request_message.protocol.value
        request_for_json['priority'] = request_message.priority.value
        
        broadcast_for_json = asdict(broadcast_message)
        broadcast_for_json['protocol'] = broadcast_message.protocol.value
        broadcast_for_json['priority'] = broadcast_message.priority.value
        
        # Should serialize to JSON without errors
        request_json = json.dumps(request_for_json)
        broadcast_json = json.dumps(broadcast_for_json)
        
        assert isinstance(request_json, str)
        assert isinstance(broadcast_json, str)
        
        # Verify key data is preserved in JSON
        assert "serialization_sender" in request_json
        assert "request_response" in request_json
        assert "serialization_broadcaster" in broadcast_json
        assert "broadcast" in broadcast_json


class TestMCPCommunicationFactoryUsagePatterns:
    """Test common usage patterns for MCP Communication Factory"""
    
    def test_request_response_pattern_usage(self):
        """Test typical request-response pattern usage"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        from ltms.coordination.mcp_message_models import MCPResponse
        
        # Agent A requests analysis from Agent B
        analysis_request = create_request_response_message(
            sender="planning_agent",
            recipient="analysis_agent",
            request_type="dependency_analysis",
            request_data={
                "scope": "full_codebase",
                "analysis_type": "dependency_mapping",
                "output_format": "graph"
            },
            conversation_id="planning_session_123",
            task_id="architecture_planning"
        )
        
        # Verify request structure for typical usage
        assert analysis_request.message_type == "dependency_analysis"
        assert analysis_request.requires_ack is True
        assert analysis_request.correlation_id is not None
        
        # Agent B creates response (simulated)
        analysis_response = MCPResponse(
            original_message=analysis_request,
            response_payload={
                "analysis_complete": True,
                "dependency_graph": {"nodes": 15, "edges": 23},
                "critical_dependencies": ["database", "cache", "auth"]
            },
            success=True
        )
        
        # Verify response correlation
        assert analysis_response.original_message_id == analysis_request.message_id
        assert analysis_response.sender_agent_id == "analysis_agent"
        assert analysis_response.recipient_agent_id == "planning_agent"
    
    def test_broadcast_pattern_usage(self):
        """Test typical broadcast pattern usage"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        # System status broadcast
        status_broadcast = create_broadcast_message(
            sender="system_monitor",
            message_type="system_status_update",
            broadcast_data={
                "timestamp": "2025-08-24T10:30:00Z",
                "overall_status": "healthy",
                "services": {
                    "database": "online",
                    "cache": "online",
                    "api": "online",
                    "worker_pool": "online"
                },
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "active_connections": 1247
                }
            },
            conversation_id="system_monitoring",
            task_id="continuous_monitoring"
        )
        
        # Verify broadcast structure for typical usage
        assert status_broadcast.recipient_agent_id is None
        assert status_broadcast.requires_ack is False
        assert status_broadcast.payload["overall_status"] == "healthy"
        assert status_broadcast.payload["services"]["database"] == "online"
    
    def test_emergency_broadcast_pattern(self):
        """Test emergency broadcast pattern usage"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        # Emergency system alert
        emergency_broadcast = create_broadcast_message(
            sender="security_monitor",
            message_type="security_alert",
            broadcast_data={
                "alert_level": "critical",
                "alert_type": "unauthorized_access_attempt",
                "source_ip": "192.168.1.100",
                "target_service": "user_database",
                "action_taken": "blocked_ip",
                "requires_immediate_attention": True,
                "recommended_actions": [
                    "review_access_logs",
                    "verify_user_accounts",
                    "check_firewall_rules"
                ]
            },
            conversation_id="security_monitoring",
            task_id="security_incident_123"
        )
        
        # Verify emergency broadcast structure
        assert emergency_broadcast.payload["alert_level"] == "critical"
        assert emergency_broadcast.payload["requires_immediate_attention"] is True
        assert len(emergency_broadcast.payload["recommended_actions"]) == 3
    
    def test_coordination_request_pattern(self):
        """Test coordination request pattern usage"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        # Agent coordination request
        coordination_request = create_request_response_message(
            sender="orchestration_agent",
            recipient="task_agent",
            request_type="task_coordination",
            request_data={
                "coordination_id": "coord_456",
                "task_assignment": {
                    "task_type": "code_analysis",
                    "priority": "high",
                    "deadline": "2025-08-24T18:00:00Z"
                },
                "dependencies": ["data_preparation_complete"],
                "expected_outputs": ["analysis_report", "recommendations"],
                "collaboration_context": {
                    "other_agents": ["data_agent", "validation_agent"],
                    "shared_resources": ["analysis_database", "temp_storage"]
                }
            },
            conversation_id="multi_agent_coordination",
            task_id="complex_analysis_pipeline"
        )
        
        # Verify coordination request structure
        assert coordination_request.payload["coordination_id"] == "coord_456"
        assert coordination_request.payload["task_assignment"]["priority"] == "high"
        assert "data_preparation_complete" in coordination_request.payload["dependencies"]
        assert len(coordination_request.payload["expected_outputs"]) == 2
    
    def test_workflow_handoff_pattern(self):
        """Test workflow handoff pattern using factory functions"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        # Workflow handoff message
        handoff_message = create_request_response_message(
            sender="analysis_agent",
            recipient="implementation_agent",
            request_type="workflow_handoff",
            request_data={
                "handoff_type": "task_completion",
                "completed_task": "architecture_analysis",
                "results": {
                    "analysis_complete": True,
                    "architecture_patterns": ["mvc", "repository", "factory"],
                    "recommendations": {
                        "database": "postgresql",
                        "cache": "redis",
                        "message_queue": "rabbitmq"
                    }
                },
                "next_phase": "implementation",
                "context_transfer": {
                    "design_documents": ["arch_doc_v2.md", "db_schema.sql"],
                    "dependencies": ["database_setup", "cache_configuration"],
                    "timeline": "2_weeks"
                }
            },
            conversation_id="development_workflow",
            task_id="project_implementation"
        )
        
        # Verify handoff message structure
        assert handoff_message.payload["handoff_type"] == "task_completion"
        assert handoff_message.payload["results"]["analysis_complete"] is True
        assert handoff_message.payload["next_phase"] == "implementation"
        assert len(handoff_message.payload["context_transfer"]["design_documents"]) == 2


class TestMCPCommunicationFactoryEdgeCases:
    """Test edge cases and error handling for MCP Communication Factory"""
    
    def test_create_request_response_message_empty_data(self):
        """Test create_request_response_message with empty request data"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        message = create_request_response_message(
            sender="empty_data_sender",
            recipient="empty_data_recipient",
            request_type="empty_request",
            request_data={},
            conversation_id="empty_data_conv",
            task_id="empty_data_task"
        )
        
        # Should handle empty data gracefully
        assert message.payload == {}
        assert message.message_type == "empty_request"
        assert message.requires_ack is True
    
    def test_create_request_response_message_none_values(self):
        """Test create_request_response_message handles None values in data"""
        from ltms.coordination.mcp_communication_factory import create_request_response_message
        
        request_data_with_none = {
            "valid_field": "valid_value",
            "null_field": None,
            "nested_with_null": {
                "valid_nested": "nested_value",
                "null_nested": None
            }
        }
        
        message = create_request_response_message(
            sender="none_values_sender",
            recipient="none_values_recipient",
            request_type="none_values_test",
            request_data=request_data_with_none,
            conversation_id="none_values_conv",
            task_id="none_values_task"
        )
        
        # Should preserve None values
        assert message.payload["null_field"] is None
        assert message.payload["nested_with_null"]["null_nested"] is None
        assert message.payload["valid_field"] == "valid_value"
    
    def test_create_broadcast_message_none_values(self):
        """Test create_broadcast_message handles None values in broadcast data"""
        from ltms.coordination.mcp_communication_factory import create_broadcast_message
        
        broadcast_data_with_none = {
            "status": "unknown",
            "last_update": None,
            "services": {
                "service_a": "online",
                "service_b": None
            }
        }
        
        message = create_broadcast_message(
            sender="none_broadcast_sender",
            message_type="none_broadcast_test",
            broadcast_data=broadcast_data_with_none,
            conversation_id="none_broadcast_conv",
            task_id="none_broadcast_task"
        )
        
        # Should preserve None values in broadcast
        assert message.payload["last_update"] is None
        assert message.payload["services"]["service_b"] is None
        assert message.payload["status"] == "unknown"


# Pytest fixtures for factory testing
@pytest.fixture
def sample_request_data():
    """Fixture providing sample request data for testing"""
    return {
        "analysis_type": "comprehensive",
        "scope": ["frontend", "backend", "database"],
        "priority": "high",
        "deadline": "2025-08-25T12:00:00Z",
        "requirements": {
            "performance": True,
            "security": True,
            "scalability": False
        },
        "metadata": {
            "requester": "project_manager",
            "project_id": "proj_123"
        }
    }

@pytest.fixture
def sample_broadcast_data():
    """Fixture providing sample broadcast data for testing"""
    return {
        "event_type": "system_maintenance",
        "scheduled_time": "2025-08-24T23:00:00Z",
        "duration": "2_hours",
        "affected_services": ["api", "database", "cache"],
        "impact": "service_unavailable",
        "notification_level": "all_users",
        "preparation_required": True,
        "contact_info": {
            "support_email": "support@example.com",
            "emergency_phone": "+1-555-0123"
        }
    }

@pytest.fixture
def factory_test_identifiers():
    """Fixture providing test identifiers for factory functions"""
    return {
        "sender": "test_sender_agent",
        "recipient": "test_recipient_agent",
        "conversation_id": "factory_test_conversation",
        "task_id": "factory_test_task",
        "message_type": "factory_test_message"
    }