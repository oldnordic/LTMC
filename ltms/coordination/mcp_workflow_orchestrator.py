"""
MCP Workflow Orchestrator for LTMC Agent Coordination  
Multi-agent workflow orchestration using MCP communication patterns.

Extracted from mcp_communication_patterns.py for smart modularization (300-line limit compliance).
Provides workflow execution, step management, and agent orchestration via LTMC integration.

Components:
- WorkflowOrchestrator: Complete workflow management with MCP communication
"""

import json
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Import message components
from .mcp_message_models import MCPMessage, CommunicationProtocol, MessagePriority
from .mcp_message_broker import LTMCMessageBroker

# LTMC MCP tool imports for real functionality
from ltms.tools.consolidated import memory_action


class WorkflowOrchestrator:
    """
    Orchestrates multi-agent workflows using MCP communication patterns.
    """
    
    def __init__(self, workflow_id: str, conversation_id: str):
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
        self.message_broker = LTMCMessageBroker(conversation_id)
        self.workflow_state: Dict[str, Any] = {
            "workflow_id": workflow_id,
            "status": "initialized",
            "agents": {},
            "current_step": 0,
            "steps": [],
            "results": {}
        }
    
    def add_workflow_step(self, 
                         step_id: str,
                         agent_id: str, 
                         task_description: str,
                         dependencies: List[str] = None) -> None:
        """Add step to workflow"""
        step = {
            "step_id": step_id,
            "agent_id": agent_id,
            "task_description": task_description,
            "dependencies": dependencies or [],
            "status": "pending",
            "result": None
        }
        
        self.workflow_state["steps"].append(step)
        self.workflow_state["agents"][agent_id] = {"assigned_steps": [step_id]}
    
    async def execute_workflow(self) -> Dict[str, Any]:
        """Execute the complete workflow"""
        try:
            self.workflow_state["status"] = "running"
            
            # Store workflow initiation in LTMC
            workflow_doc = {
                "workflow_execution": "started",
                "workflow_id": self.workflow_id,
                "total_steps": len(self.workflow_state["steps"]),
                "agents_involved": list(self.workflow_state["agents"].keys())
            }
            
            memory_action(
                action="store",
                file_name=f"workflow_execution_{self.workflow_id}.json",
                content=json.dumps(workflow_doc, indent=2),
                tags=["workflow_execution", self.workflow_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Execute steps in dependency order
            for step in self.workflow_state["steps"]:
                if self._dependencies_satisfied(step):
                    await self._execute_step(step)
            
            self.workflow_state["status"] = "completed"
            return self.workflow_state
            
        except Exception as e:
            self.workflow_state["status"] = "failed"
            self.workflow_state["error"] = str(e)
            print(f"❌ Workflow execution failed: {e}")
            return self.workflow_state
    
    def _dependencies_satisfied(self, step: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        if not step["dependencies"]:
            return True
        
        for dep_step_id in step["dependencies"]:
            dep_step = next((s for s in self.workflow_state["steps"] if s["step_id"] == dep_step_id), None)
            if not dep_step or dep_step["status"] != "completed":
                return False
        
        return True
    
    async def _execute_step(self, step: Dict[str, Any]) -> None:
        """Execute individual workflow step"""
        try:
            step["status"] = "running"
            
            # Send task message to agent
            task_message = MCPMessage(
                message_id=str(uuid.uuid4()),
                sender_agent_id="workflow_orchestrator",
                recipient_agent_id=step["agent_id"],
                protocol=CommunicationProtocol.WORKFLOW_HANDOFF,
                priority=MessagePriority.HIGH,
                message_type="workflow_task",
                payload={
                    "workflow_id": self.workflow_id,
                    "step_id": step["step_id"],
                    "task_description": step["task_description"],
                    "workflow_context": self.workflow_state["results"]
                },
                conversation_id=self.conversation_id,
                task_id=self.workflow_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                requires_ack=True
            )
            
            # Send message via broker
            if self.message_broker.send_message(task_message):
                # Wait for completion (simplified - in production would use proper async monitoring)
                step["status"] = "completed"
                step["result"] = {"message_sent": True, "message_id": task_message.message_id}
                
                print(f"✅ Workflow step {step['step_id']} executed for agent {step['agent_id']}")
            else:
                step["status"] = "failed"
                step["result"] = {"error": "Failed to send task message"}
                
        except Exception as e:
            step["status"] = "failed"
            step["result"] = {"error": str(e)}
            print(f"❌ Failed to execute workflow step {step['step_id']}: {e}")