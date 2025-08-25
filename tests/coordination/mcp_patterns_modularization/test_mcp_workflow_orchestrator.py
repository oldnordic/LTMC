"""
Comprehensive TDD tests for MCP Workflow Orchestrator extraction.
Tests workflow execution, step management, and orchestration functionality.

Following TDD methodology: Tests written FIRST before extraction.
WorkflowOrchestrator will manage multi-agent workflows using MCP communication patterns.
"""

import pytest
import json
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import uuid


class TestWorkflowOrchestrator:
    """Test WorkflowOrchestrator class - to be extracted from mcp_communication_patterns.py"""
    
    def test_workflow_orchestrator_creation(self):
        """Test WorkflowOrchestrator can be instantiated"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("test_workflow_123", "test_conv_456")
        
        assert hasattr(orchestrator, 'workflow_id')
        assert hasattr(orchestrator, 'conversation_id')
        assert hasattr(orchestrator, 'message_broker')
        assert hasattr(orchestrator, 'workflow_state')
        
        assert orchestrator.workflow_id == "test_workflow_123"
        assert orchestrator.conversation_id == "test_conv_456"
        
        # Verify workflow state initialization
        assert isinstance(orchestrator.workflow_state, dict)
        assert orchestrator.workflow_state["workflow_id"] == "test_workflow_123"
        assert orchestrator.workflow_state["status"] == "initialized"
        assert isinstance(orchestrator.workflow_state["agents"], dict)
        assert isinstance(orchestrator.workflow_state["steps"], list)
        assert orchestrator.workflow_state["current_step"] == 0
        assert isinstance(orchestrator.workflow_state["results"], dict)
    
    def test_workflow_orchestrator_message_broker_integration(self):
        """Test WorkflowOrchestrator creates and integrates with LTMCMessageBroker"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        
        orchestrator = WorkflowOrchestrator("broker_test_workflow", "broker_test_conv")
        
        # Verify message broker is created and integrated
        assert isinstance(orchestrator.message_broker, LTMCMessageBroker)
        assert orchestrator.message_broker.conversation_id == "broker_test_conv"
    
    def test_add_workflow_step_single(self):
        """Test adding single workflow step"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("step_test_workflow", "step_test_conv")
        
        # Add workflow step
        orchestrator.add_workflow_step(
            step_id="test_step_1",
            agent_id="test_agent_1",
            task_description="Test task description",
            dependencies=["dep_step_1", "dep_step_2"]
        )
        
        # Verify step was added correctly
        assert len(orchestrator.workflow_state["steps"]) == 1
        
        step = orchestrator.workflow_state["steps"][0]
        assert step["step_id"] == "test_step_1"
        assert step["agent_id"] == "test_agent_1"
        assert step["task_description"] == "Test task description"
        assert step["dependencies"] == ["dep_step_1", "dep_step_2"]
        assert step["status"] == "pending"
        assert step["result"] is None
        
        # Verify agent tracking
        assert "test_agent_1" in orchestrator.workflow_state["agents"]
        assert orchestrator.workflow_state["agents"]["test_agent_1"]["assigned_steps"] == ["test_step_1"]
    
    def test_add_workflow_step_no_dependencies(self):
        """Test adding workflow step with no dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("no_deps_workflow", "no_deps_conv")
        
        # Add step without dependencies
        orchestrator.add_workflow_step(
            step_id="independent_step",
            agent_id="independent_agent",
            task_description="Independent task"
        )
        
        step = orchestrator.workflow_state["steps"][0]
        assert step["dependencies"] == []
        assert step["status"] == "pending"
    
    def test_add_multiple_workflow_steps(self):
        """Test adding multiple workflow steps"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("multi_step_workflow", "multi_step_conv")
        
        # Add multiple steps
        orchestrator.add_workflow_step("step_1", "agent_1", "First task")
        orchestrator.add_workflow_step("step_2", "agent_2", "Second task", ["step_1"])
        orchestrator.add_workflow_step("step_3", "agent_3", "Third task", ["step_1", "step_2"])
        
        # Verify all steps added
        assert len(orchestrator.workflow_state["steps"]) == 3
        assert len(orchestrator.workflow_state["agents"]) == 3
        
        # Verify step dependencies
        step_2 = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_2")
        assert step_2["dependencies"] == ["step_1"]
        
        step_3 = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_3")
        assert step_3["dependencies"] == ["step_1", "step_2"]
    
    def test_add_workflow_step_same_agent_multiple_steps(self):
        """Test adding multiple steps to same agent"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("same_agent_workflow", "same_agent_conv")
        
        # Add multiple steps to same agent
        orchestrator.add_workflow_step("step_a", "multi_task_agent", "Task A")
        orchestrator.add_workflow_step("step_b", "multi_task_agent", "Task B")
        orchestrator.add_workflow_step("step_c", "other_agent", "Task C")
        
        # Verify agent tracking
        assert len(orchestrator.workflow_state["agents"]) == 2
        assert "multi_task_agent" in orchestrator.workflow_state["agents"]
        assert "other_agent" in orchestrator.workflow_state["agents"]
        
        # Note: Current implementation overwrites assigned_steps, so only last step is tracked
        # This might be a bug in the original implementation to fix during extraction
        assert orchestrator.workflow_state["agents"]["multi_task_agent"]["assigned_steps"] == ["step_b"]
        assert orchestrator.workflow_state["agents"]["other_agent"]["assigned_steps"] == ["step_c"]
    
    def test_dependencies_satisfied_no_dependencies(self):
        """Test _dependencies_satisfied with no dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("deps_test_workflow", "deps_test_conv")
        
        # Create step with no dependencies
        step = {
            "step_id": "independent_step",
            "agent_id": "test_agent",
            "task_description": "Independent task",
            "dependencies": [],
            "status": "pending",
            "result": None
        }
        
        # Should be satisfied (no dependencies)
        assert orchestrator._dependencies_satisfied(step) is True
    
    def test_dependencies_satisfied_with_completed_dependencies(self):
        """Test _dependencies_satisfied with completed dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("completed_deps_workflow", "completed_deps_conv")
        
        # Add workflow steps
        orchestrator.add_workflow_step("dep_step_1", "agent_1", "Dependency 1")
        orchestrator.add_workflow_step("dep_step_2", "agent_2", "Dependency 2")
        orchestrator.add_workflow_step("main_step", "agent_3", "Main task", ["dep_step_1", "dep_step_2"])
        
        # Mark dependencies as completed
        for step in orchestrator.workflow_state["steps"]:
            if step["step_id"] in ["dep_step_1", "dep_step_2"]:
                step["status"] = "completed"
        
        # Get main step
        main_step = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "main_step")
        
        # Dependencies should be satisfied
        assert orchestrator._dependencies_satisfied(main_step) is True
    
    def test_dependencies_satisfied_with_incomplete_dependencies(self):
        """Test _dependencies_satisfied with incomplete dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("incomplete_deps_workflow", "incomplete_deps_conv")
        
        # Add workflow steps
        orchestrator.add_workflow_step("incomplete_dep", "agent_1", "Incomplete dependency")
        orchestrator.add_workflow_step("completed_dep", "agent_2", "Completed dependency")
        orchestrator.add_workflow_step("waiting_step", "agent_3", "Waiting task", ["incomplete_dep", "completed_dep"])
        
        # Mark only one dependency as completed
        for step in orchestrator.workflow_state["steps"]:
            if step["step_id"] == "completed_dep":
                step["status"] = "completed"
        
        # Get waiting step
        waiting_step = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "waiting_step")
        
        # Dependencies should NOT be satisfied
        assert orchestrator._dependencies_satisfied(waiting_step) is False
    
    def test_dependencies_satisfied_missing_dependency_step(self):
        """Test _dependencies_satisfied with missing dependency step"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("missing_dep_workflow", "missing_dep_conv")
        
        # Add step that references non-existent dependency
        step = {
            "step_id": "missing_dep_step",
            "agent_id": "test_agent",
            "task_description": "Task with missing dependency",
            "dependencies": ["non_existent_step"],
            "status": "pending",
            "result": None
        }
        
        # Should not be satisfied (missing dependency)
        assert orchestrator._dependencies_satisfied(step) is False
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    def test_execute_step_success(self, mock_memory_action):
        """Test _execute_step successful execution"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("execute_test_workflow", "execute_test_conv")
        
        # Mock message broker send_message
        with patch.object(orchestrator.message_broker, 'send_message', return_value=True) as mock_send:
            # Create test step
            step = {
                "step_id": "execute_test_step",
                "agent_id": "execute_test_agent",
                "task_description": "Test execution task",
                "dependencies": [],
                "status": "pending",
                "result": None
            }
            
            # Execute step (sync call for testing)
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify step was executed successfully
            assert step["status"] == "completed"
            assert step["result"]["message_sent"] is True
            assert "message_id" in step["result"]
            
            # Verify message was sent via broker
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            assert sent_message.sender_agent_id == "workflow_orchestrator"
            assert sent_message.recipient_agent_id == "execute_test_agent"
            assert sent_message.message_type == "workflow_task"
            assert sent_message.payload["workflow_id"] == "execute_test_workflow"
            assert sent_message.payload["step_id"] == "execute_test_step"
            assert sent_message.payload["task_description"] == "Test execution task"
            assert sent_message.requires_ack is True
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    def test_execute_step_message_send_failure(self, mock_memory_action):
        """Test _execute_step when message sending fails"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("fail_execute_workflow", "fail_execute_conv")
        
        # Mock message broker send_message to fail
        with patch.object(orchestrator.message_broker, 'send_message', return_value=False):
            step = {
                "step_id": "fail_execute_step",
                "agent_id": "fail_execute_agent",
                "task_description": "Failing execution task",
                "dependencies": [],
                "status": "pending",
                "result": None
            }
            
            # Execute step
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify step failed
            assert step["status"] == "failed"
            assert step["result"]["error"] == "Failed to send task message"
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    def test_execute_step_exception_handling(self, mock_memory_action):
        """Test _execute_step exception handling"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("exception_workflow", "exception_conv")
        
        # Mock message broker to raise exception
        with patch.object(orchestrator.message_broker, 'send_message', side_effect=Exception("Send message error")):
            step = {
                "step_id": "exception_step",
                "agent_id": "exception_agent",
                "task_description": "Exception task",
                "dependencies": [],
                "status": "pending",
                "result": None
            }
            
            # Execute step should handle exception
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify step failed with error
            assert step["status"] == "failed"
            assert "Send message error" in step["result"]["error"]
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    async def test_execute_workflow_success(self, mock_memory_action):
        """Test complete workflow execution success"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        # Setup mock
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("full_workflow", "full_conv")
        
        # Add workflow steps with dependencies
        orchestrator.add_workflow_step("step_1", "agent_1", "First task")
        orchestrator.add_workflow_step("step_2", "agent_2", "Second task", ["step_1"])
        
        # Mock message broker
        with patch.object(orchestrator.message_broker, 'send_message', return_value=True):
            # Execute workflow
            result = await orchestrator.execute_workflow()
            
            # Verify workflow completion
            assert result["status"] == "completed"
            assert result["workflow_id"] == "full_workflow"
            assert len(result["steps"]) == 2
            
            # Verify all steps completed (simplified - in reality would need proper async coordination)
            for step in result["steps"]:
                assert step["status"] == "completed"
                assert step["result"]["message_sent"] is True
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    async def test_execute_workflow_with_ltmc_storage(self, mock_memory_action):
        """Test workflow execution stores initiation in LTMC"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("ltmc_storage_workflow", "ltmc_storage_conv")
        orchestrator.add_workflow_step("storage_step", "storage_agent", "LTMC storage test")
        
        with patch.object(orchestrator.message_broker, 'send_message', return_value=True):
            result = await orchestrator.execute_workflow()
            
            # Verify LTMC storage was called
            mock_memory_action.assert_called()
            
            # Find the workflow initiation storage call
            storage_calls = [call for call in mock_memory_action.call_args_list if call[1].get('action') == 'store']
            workflow_storage_call = next(call for call in storage_calls if 'workflow_execution_' in call[1]['file_name'])
            
            # Verify workflow storage content
            stored_content = json.loads(workflow_storage_call[1]['content'])
            assert stored_content['workflow_execution'] == "started"
            assert stored_content['workflow_id'] == "ltmc_storage_workflow"
            assert stored_content['total_steps'] == 1
            assert stored_content['agents_involved'] == ["storage_agent"]
            
            # Verify storage tags
            assert 'workflow_execution' in workflow_storage_call[1]['tags']
            assert 'ltmc_storage_workflow' in workflow_storage_call[1]['tags']
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    async def test_execute_workflow_failure_handling(self, mock_memory_action):
        """Test workflow execution handles failures gracefully"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        # Setup mock to fail
        mock_memory_action.side_effect = Exception("LTMC workflow storage failed")
        
        orchestrator = WorkflowOrchestrator("failing_workflow", "failing_conv")
        orchestrator.add_workflow_step("fail_step", "fail_agent", "Failing task")
        
        # Execute workflow should handle exception
        result = await orchestrator.execute_workflow()
        
        # Verify workflow failure
        assert result["status"] == "failed"
        assert "LTMC workflow storage failed" in result["error"]
        assert result["workflow_id"] == "failing_workflow"
    
    def test_workflow_state_management(self):
        """Test workflow state structure and management"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("state_test_workflow", "state_test_conv")
        
        # Verify initial state structure
        state = orchestrator.workflow_state
        assert state["workflow_id"] == "state_test_workflow"
        assert state["status"] == "initialized"
        assert isinstance(state["agents"], dict)
        assert isinstance(state["steps"], list)
        assert state["current_step"] == 0
        assert isinstance(state["results"], dict)
        
        # Test state updates
        state["status"] = "running"
        state["current_step"] = 1
        state["results"]["test_key"] = "test_value"
        
        assert orchestrator.workflow_state["status"] == "running"
        assert orchestrator.workflow_state["current_step"] == 1
        assert orchestrator.workflow_state["results"]["test_key"] == "test_value"


class TestWorkflowOrchestratorIntegration:
    """Test WorkflowOrchestrator integration with other components"""
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    def test_orchestrator_with_message_broker_integration(self, mock_memory_action):
        """Test WorkflowOrchestrator integration with LTMCMessageBroker"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        from ltms.coordination.mcp_message_broker import LTMCMessageBroker
        from ltms.coordination.mcp_message_models import CommunicationProtocol, MessagePriority
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("integration_workflow", "integration_conv")
        
        # Verify message broker integration
        assert isinstance(orchestrator.message_broker, LTMCMessageBroker)
        assert orchestrator.message_broker.conversation_id == "integration_conv"
        
        # Test step execution creates proper MCP messages
        orchestrator.add_workflow_step("integration_step", "integration_agent", "Integration test")
        
        with patch.object(orchestrator.message_broker, 'send_message') as mock_send:
            mock_send.return_value = True
            
            step = orchestrator.workflow_state["steps"][0]
            
            # Execute step
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify message was created and sent correctly
            mock_send.assert_called_once()
            sent_message = mock_send.call_args[0][0]
            
            # Verify MCP message structure
            assert hasattr(sent_message, 'message_id')
            assert hasattr(sent_message, 'protocol')
            assert hasattr(sent_message, 'priority')
            assert sent_message.protocol == CommunicationProtocol.WORKFLOW_HANDOFF
            assert sent_message.priority == MessagePriority.HIGH
            assert sent_message.message_type == "workflow_task"
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    async def test_complex_workflow_execution(self, mock_memory_action):
        """Test complex workflow with multiple agents and dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("complex_workflow", "complex_conv")
        
        # Create complex workflow
        orchestrator.add_workflow_step("analysis", "planner_agent", "Analyze requirements")
        orchestrator.add_workflow_step("design", "architect_agent", "Create design", ["analysis"])
        orchestrator.add_workflow_step("implement", "coder_agent", "Implement solution", ["design"])
        orchestrator.add_workflow_step("test", "tester_agent", "Test implementation", ["implement"])
        orchestrator.add_workflow_step("quality", "enforcer_agent", "Quality validation", ["test"])
        
        with patch.object(orchestrator.message_broker, 'send_message', return_value=True):
            result = await orchestrator.execute_workflow()
            
            # Verify complex workflow structure
            assert result["status"] == "completed"
            assert len(result["steps"]) == 5
            assert len(result["agents"]) == 5
            
            # Verify all agents were involved
            expected_agents = ["planner_agent", "architect_agent", "coder_agent", "tester_agent", "enforcer_agent"]
            actual_agents = list(result["agents"].keys())
            for agent in expected_agents:
                assert agent in actual_agents
    
    def test_workflow_orchestrator_with_message_models(self):
        """Test WorkflowOrchestrator creates proper MCP message models"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        from ltms.coordination.mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
        
        orchestrator = WorkflowOrchestrator("models_test_workflow", "models_test_conv")
        orchestrator.add_workflow_step("models_step", "models_agent", "Test message models")
        
        # Mock the message creation in _execute_step
        with patch.object(orchestrator.message_broker, 'send_message') as mock_send:
            mock_send.return_value = True
            
            step = orchestrator.workflow_state["steps"][0]
            
            # Execute step and capture message
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify MCPMessage was created correctly
            sent_message = mock_send.call_args[0][0]
            assert isinstance(sent_message, MCPMessage)
            assert sent_message.protocol == CommunicationProtocol.WORKFLOW_HANDOFF
            assert sent_message.priority == MessagePriority.HIGH
            assert sent_message.sender_agent_id == "workflow_orchestrator"
            assert sent_message.recipient_agent_id == "models_agent"
            assert sent_message.conversation_id == "models_test_conv"
            assert sent_message.task_id == "models_test_workflow"
            assert sent_message.requires_ack is True
            
            # Verify payload contains workflow context
            payload = sent_message.payload
            assert payload["workflow_id"] == "models_test_workflow"
            assert payload["step_id"] == "models_step"
            assert payload["task_description"] == "Test message models"
            assert "workflow_context" in payload


class TestWorkflowOrchestratorAdvanced:
    """Test advanced WorkflowOrchestrator functionality"""
    
    def test_workflow_dependency_chain_validation(self):
        """Test complex dependency chain validation"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("dependency_chain", "dependency_conv")
        
        # Create dependency chain: A -> B -> C -> D
        orchestrator.add_workflow_step("step_a", "agent_a", "Task A")
        orchestrator.add_workflow_step("step_b", "agent_b", "Task B", ["step_a"])
        orchestrator.add_workflow_step("step_c", "agent_c", "Task C", ["step_b"])
        orchestrator.add_workflow_step("step_d", "agent_d", "Task D", ["step_c"])
        
        # Initially no dependencies satisfied except step_a
        step_a = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_a")
        step_b = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_b")
        step_c = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_c")
        step_d = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "step_d")
        
        assert orchestrator._dependencies_satisfied(step_a) is True  # No dependencies
        assert orchestrator._dependencies_satisfied(step_b) is False  # A not completed
        assert orchestrator._dependencies_satisfied(step_c) is False  # B not completed
        assert orchestrator._dependencies_satisfied(step_d) is False  # C not completed
        
        # Complete step A
        step_a["status"] = "completed"
        assert orchestrator._dependencies_satisfied(step_b) is True  # A completed
        assert orchestrator._dependencies_satisfied(step_c) is False  # B still not completed
        
        # Complete step B
        step_b["status"] = "completed"
        assert orchestrator._dependencies_satisfied(step_c) is True  # B completed
        assert orchestrator._dependencies_satisfied(step_d) is False  # C still not completed
        
        # Complete step C
        step_c["status"] = "completed"
        assert orchestrator._dependencies_satisfied(step_d) is True  # C completed
    
    def test_workflow_multiple_dependencies_per_step(self):
        """Test steps with multiple dependencies"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        orchestrator = WorkflowOrchestrator("multi_deps_workflow", "multi_deps_conv")
        
        # Create workflow with multiple dependencies
        orchestrator.add_workflow_step("prep_a", "agent_a", "Preparation A")
        orchestrator.add_workflow_step("prep_b", "agent_b", "Preparation B")
        orchestrator.add_workflow_step("prep_c", "agent_c", "Preparation C")
        orchestrator.add_workflow_step("main_task", "agent_main", "Main task", ["prep_a", "prep_b", "prep_c"])
        
        main_step = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "main_task")
        
        # Initially not satisfied (no prep steps completed)
        assert orchestrator._dependencies_satisfied(main_step) is False
        
        # Complete partial dependencies
        prep_a = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "prep_a")
        prep_b = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "prep_b")
        prep_c = next(s for s in orchestrator.workflow_state["steps"] if s["step_id"] == "prep_c")
        
        prep_a["status"] = "completed"
        prep_b["status"] = "completed"
        assert orchestrator._dependencies_satisfied(main_step) is False  # Still missing prep_c
        
        # Complete all dependencies
        prep_c["status"] = "completed"
        assert orchestrator._dependencies_satisfied(main_step) is True  # All dependencies satisfied
    
    @patch('ltms.coordination.mcp_workflow_orchestrator.memory_action')
    async def test_workflow_context_propagation(self, mock_memory_action):
        """Test workflow context propagation between steps"""
        from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
        
        mock_memory_action.return_value = {'success': True}
        
        orchestrator = WorkflowOrchestrator("context_workflow", "context_conv")
        orchestrator.add_workflow_step("context_step", "context_agent", "Context propagation test")
        
        # Add results to workflow state
        orchestrator.workflow_state["results"]["step_1_result"] = {"analysis": "complete"}
        orchestrator.workflow_state["results"]["step_2_result"] = {"design": "ready"}
        
        with patch.object(orchestrator.message_broker, 'send_message') as mock_send:
            mock_send.return_value = True
            
            step = orchestrator.workflow_state["steps"][0]
            
            # Execute step
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(orchestrator._execute_step(step))
            
            # Verify workflow context was included in message
            sent_message = mock_send.call_args[0][0]
            workflow_context = sent_message.payload["workflow_context"]
            
            assert "step_1_result" in workflow_context
            assert "step_2_result" in workflow_context
            assert workflow_context["step_1_result"]["analysis"] == "complete"
            assert workflow_context["step_2_result"]["design"] == "ready"


# Pytest fixtures for workflow orchestrator testing
@pytest.fixture
def workflow_orchestrator():
    """Fixture providing WorkflowOrchestrator instance"""
    from ltms.coordination.mcp_workflow_orchestrator import WorkflowOrchestrator
    return WorkflowOrchestrator("fixture_workflow", "fixture_conv")

@pytest.fixture
def simple_workflow_steps():
    """Fixture providing simple workflow step definitions"""
    return [
        {"step_id": "step_1", "agent_id": "agent_1", "task_description": "First task", "dependencies": []},
        {"step_id": "step_2", "agent_id": "agent_2", "task_description": "Second task", "dependencies": ["step_1"]},
        {"step_id": "step_3", "agent_id": "agent_3", "task_description": "Third task", "dependencies": ["step_2"]}
    ]

@pytest.fixture
def complex_workflow_steps():
    """Fixture providing complex workflow with multiple dependencies"""
    return [
        {"step_id": "analysis", "agent_id": "planner", "task_description": "Analyze requirements", "dependencies": []},
        {"step_id": "design", "agent_id": "architect", "task_description": "Create design", "dependencies": ["analysis"]},
        {"step_id": "frontend", "agent_id": "frontend_dev", "task_description": "Implement frontend", "dependencies": ["design"]},
        {"step_id": "backend", "agent_id": "backend_dev", "task_description": "Implement backend", "dependencies": ["design"]},
        {"step_id": "integration", "agent_id": "integrator", "task_description": "Integrate components", "dependencies": ["frontend", "backend"]},
        {"step_id": "testing", "agent_id": "tester", "task_description": "Test system", "dependencies": ["integration"]},
        {"step_id": "deployment", "agent_id": "deployer", "task_description": "Deploy system", "dependencies": ["testing"]}
    ]

@pytest.fixture
def mock_workflow_ltmc_tools():
    """Fixture providing mocked LTMC tools for workflow testing"""
    with patch('ltms.coordination.mcp_workflow_orchestrator.memory_action') as mock_memory:
        mock_memory.return_value = {'success': True, 'doc_id': 888}
        yield {'memory_action': mock_memory}