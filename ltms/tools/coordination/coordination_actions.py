"""
Agent Coordination management tools for LTMC MCP server.
Provides external file-based coordination to solve parallel isolation problem.

File: ltms/tools/coordination/coordination_actions.py
Lines: ~290 (under 300 limit)
Purpose: Agent handoff, workflow state management, and cross-agent coordination
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from ..core.mcp_base import MCPToolBase
from ..core.config import get_tool_config

logger = logging.getLogger(__name__)


class CoordinationTools(MCPToolBase):
    """Agent coordination tools with external file-based state management.
    
    Solves parallel isolation problem by using persistent file coordination
    instead of agent memory sharing. Based on TaskMaster design patterns.
    """
    
    def __init__(self):
        super().__init__("CoordinationTools")
        self.config = get_tool_config()
        self.coordination_dir = Path("/home/feanor/Projects/ltmc/.ltmc-coordination")
        self._ensure_coordination_directories()
    
    def _ensure_coordination_directories(self):
        """Ensure all coordination directories exist."""
        subdirs = ["agent-handoffs", "workflow-states", "shared-context", "coordination-history"]
        for subdir in subdirs:
            (self.coordination_dir / subdir).mkdir(parents=True, exist_ok=True)
    
    def get_valid_actions(self) -> List[str]:
        """Get list of valid coordination actions."""
        return [
            'store_analysis', 
            'retrieve_handoff', 
            'update_status', 
            'list_pending',
            'create_workflow',
            'store_handoff',
            'get_workflow_state',
            'log_coordination_activity'
        ]
    
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute coordination management action."""
        if action == 'store_analysis':
            return await self._action_store_analysis(**params)
        elif action == 'retrieve_handoff':
            return await self._action_retrieve_handoff(**params)
        elif action == 'update_status':
            return await self._action_update_status(**params)
        elif action == 'list_pending':
            return await self._action_list_pending(**params)
        elif action == 'create_workflow':
            return await self._action_create_workflow(**params)
        elif action == 'store_handoff':
            return await self._action_store_handoff(**params)
        elif action == 'get_workflow_state':
            return await self._action_get_workflow_state(**params)
        elif action == 'log_coordination_activity':
            return await self._action_log_coordination_activity(**params)
        else:
            return self._create_error_response(f"Unknown coordination action: {action}")
    
    async def _action_store_analysis(self, agent_id: str, analysis_data: Dict[str, Any], 
                                   target_agent: Optional[str] = None, **params) -> Dict[str, Any]:
        """Store analysis results for agent handoff."""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            
            # Store in shared-context for general access
            context_file = self.coordination_dir / "shared-context" / f"analysis_{agent_id}_{timestamp}.json"
            
            analysis_record = {
                "agent_id": agent_id,
                "timestamp": timestamp,
                "analysis_data": analysis_data,
                "target_agent": target_agent,
                "status": "available",
                "metadata": params
            }
            
            with open(context_file, 'w') as f:
                json.dump(analysis_record, f, indent=2)
            
            # If target agent specified, create handoff file
            handoff_id = None
            if target_agent:
                handoff_id = f"{agent_id}_to_{target_agent}_{timestamp}"
                handoff_file = self.coordination_dir / "agent-handoffs" / f"{handoff_id}.json"
                
                handoff_record = {
                    "handoff_id": handoff_id,
                    "source_agent": agent_id,
                    "target_agent": target_agent,
                    "timestamp": timestamp,
                    "context": analysis_data,
                    "instructions": params.get("instructions", "Process the provided analysis"),
                    "validation_criteria": params.get("validation_criteria", []),
                    "status": "pending"
                }
                
                with open(handoff_file, 'w') as f:
                    json.dump(handoff_record, f, indent=2)
            
            # Log the activity
            await self._log_activity("analysis_stored", {
                "agent_id": agent_id,
                "target_agent": target_agent,
                "handoff_id": handoff_id,
                "context_file": str(context_file)
            })
            
            return self._create_success_response({
                "analysis_stored": True,
                "agent_id": agent_id,
                "context_file": str(context_file),
                "handoff_created": handoff_id is not None,
                "handoff_id": handoff_id,
                "timestamp": timestamp
            })
            
        except Exception as e:
            return self._create_error_response(f'Store analysis failed: {str(e)}')
    
    async def _action_retrieve_handoff(self, target_agent: str, **params) -> Dict[str, Any]:
        """Retrieve pending handoff for specific agent."""
        try:
            handoffs_dir = self.coordination_dir / "agent-handoffs"
            pending_handoffs = []
            
            # Find handoffs for target agent
            for handoff_file in handoffs_dir.glob(f"*_to_{target_agent}_*.json"):
                try:
                    with open(handoff_file, 'r') as f:
                        handoff_data = json.load(f)
                    
                    if handoff_data.get("status") == "pending":
                        handoff_data["file_path"] = str(handoff_file)
                        pending_handoffs.append(handoff_data)
                except Exception as e:
                    logger.warning(f"Failed to read handoff file {handoff_file}: {e}")
            
            # Sort by timestamp (most recent first)
            pending_handoffs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Log the retrieval
            await self._log_activity("handoff_retrieved", {
                "target_agent": target_agent,
                "handoffs_found": len(pending_handoffs)
            })
            
            return self._create_success_response({
                "target_agent": target_agent,
                "pending_handoffs": pending_handoffs,
                "handoff_count": len(pending_handoffs),
                "has_pending": len(pending_handoffs) > 0
            })
            
        except Exception as e:
            return self._create_error_response(f'Retrieve handoff failed: {str(e)}')
    
    async def _action_update_status(self, workflow_id: str, status: str, 
                                  agent_id: Optional[str] = None, **params) -> Dict[str, Any]:
        """Update workflow state with new status."""
        try:
            workflow_file = self.coordination_dir / "workflow-states" / f"{workflow_id}_state.json"
            
            # Load existing state or create new
            if workflow_file.exists():
                with open(workflow_file, 'r') as f:
                    workflow_state = json.load(f)
            else:
                workflow_state = {
                    "workflow_id": workflow_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "states": [],
                    "current_state": "initialized"
                }
            
            # Add state transition
            transition = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_state": workflow_state.get("current_state"),
                "new_state": status,
                "agent_id": agent_id,
                "metadata": params
            }
            
            workflow_state["states"].append(transition)
            workflow_state["current_state"] = status
            workflow_state["last_updated"] = transition["timestamp"]
            
            # Save updated state
            with open(workflow_file, 'w') as f:
                json.dump(workflow_state, f, indent=2)
            
            # Log the activity
            await self._log_activity("status_updated", {
                "workflow_id": workflow_id,
                "status": status,
                "agent_id": agent_id
            })
            
            return self._create_success_response({
                "workflow_id": workflow_id,
                "status_updated": True,
                "previous_state": transition["previous_state"],
                "new_state": status,
                "timestamp": transition["timestamp"]
            })
            
        except Exception as e:
            return self._create_error_response(f'Update status failed: {str(e)}')
    
    async def _action_list_pending(self, agent_id: Optional[str] = None, **params) -> Dict[str, Any]:
        """List all pending handoffs, optionally filtered by agent."""
        try:
            handoffs_dir = self.coordination_dir / "agent-handoffs"
            pending_handoffs = []
            
            # Scan all handoff files
            for handoff_file in handoffs_dir.glob("*.json"):
                try:
                    with open(handoff_file, 'r') as f:
                        handoff_data = json.load(f)
                    
                    if handoff_data.get("status") == "pending":
                        # Filter by agent if specified
                        if agent_id and handoff_data.get("target_agent") != agent_id:
                            continue
                        
                        handoff_data["file_path"] = str(handoff_file)
                        pending_handoffs.append(handoff_data)
                except Exception as e:
                    logger.warning(f"Failed to read handoff file {handoff_file}: {e}")
            
            # Sort by timestamp
            pending_handoffs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            return self._create_success_response({
                "pending_handoffs": pending_handoffs,
                "total_pending": len(pending_handoffs),
                "filtered_by_agent": agent_id
            })
            
        except Exception as e:
            return self._create_error_response(f'List pending failed: {str(e)}')
    
    async def _action_create_workflow(self, workflow_id: str, description: str = "", 
                                    agent_id: Optional[str] = None, **params) -> Dict[str, Any]:
        """Initialize new coordination workflow."""
        try:
            workflow_file = self.coordination_dir / "workflow-states" / f"{workflow_id}_state.json"
            
            # Check if workflow already exists
            if workflow_file.exists():
                return self._create_error_response(f"Workflow {workflow_id} already exists")
            
            # Create initial workflow state
            workflow_state = {
                "workflow_id": workflow_id,
                "description": description,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": agent_id,
                "current_state": "initialized",
                "states": [{
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "previous_state": None,
                    "new_state": "initialized",
                    "agent_id": agent_id,
                    "metadata": params
                }]
            }
            
            with open(workflow_file, 'w') as f:
                json.dump(workflow_state, f, indent=2)
            
            # Log the activity
            await self._log_activity("workflow_created", {
                "workflow_id": workflow_id,
                "created_by": agent_id
            })
            
            return self._create_success_response({
                "workflow_created": True,
                "workflow_id": workflow_id,
                "initial_state": "initialized",
                "created_at": workflow_state["created_at"]
            })
            
        except Exception as e:
            return self._create_error_response(f'Create workflow failed: {str(e)}')
    
    async def _action_store_handoff(self, source_agent: str, target_agent: str,
                                  context: Dict[str, Any], instructions: str = "",
                                  validation_criteria: List[str] = None, **params) -> Dict[str, Any]:
        """Store agent handoff with complete context."""
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            handoff_id = f"{source_agent}_to_{target_agent}_{timestamp}"
            handoff_file = self.coordination_dir / "agent-handoffs" / f"{handoff_id}.json"
            
            handoff_record = {
                "handoff_id": handoff_id,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "timestamp": timestamp,
                "context": context,
                "instructions": instructions,
                "validation_criteria": validation_criteria or [],
                "status": "pending",
                "metadata": params
            }
            
            with open(handoff_file, 'w') as f:
                json.dump(handoff_record, f, indent=2)
            
            # Log the activity
            await self._log_activity("handoff_stored", {
                "handoff_id": handoff_id,
                "source_agent": source_agent,
                "target_agent": target_agent
            })
            
            return self._create_success_response({
                "handoff_stored": True,
                "handoff_id": handoff_id,
                "source_agent": source_agent,
                "target_agent": target_agent,
                "timestamp": timestamp
            })
            
        except Exception as e:
            return self._create_error_response(f'Store handoff failed: {str(e)}')
    
    async def _action_get_workflow_state(self, workflow_id: str, **params) -> Dict[str, Any]:
        """Get current workflow state and history."""
        try:
            workflow_file = self.coordination_dir / "workflow-states" / f"{workflow_id}_state.json"
            
            if not workflow_file.exists():
                return self._create_error_response(f"Workflow {workflow_id} not found")
            
            with open(workflow_file, 'r') as f:
                workflow_state = json.load(f)
            
            return self._create_success_response({
                "workflow_found": True,
                "workflow_id": workflow_id,
                "current_state": workflow_state.get("current_state"),
                "state_history": workflow_state.get("states", []),
                "created_at": workflow_state.get("created_at"),
                "last_updated": workflow_state.get("last_updated")
            })
            
        except Exception as e:
            return self._create_error_response(f'Get workflow state failed: {str(e)}')
    
    async def _action_log_coordination_activity(self, activity_type: str, 
                                              activity_data: Dict[str, Any], **params) -> Dict[str, Any]:
        """Log coordination activity for audit trail."""
        try:
            return await self._log_activity(activity_type, activity_data)
            
        except Exception as e:
            return self._create_error_response(f'Log activity failed: {str(e)}')
    
    async def _log_activity(self, activity_type: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to log coordination activities."""
        try:
            date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
            log_file = self.coordination_dir / "coordination-history" / f"{date_str}_{activity_type}_log.json"
            
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_type": activity_type,
                "activity_data": activity_data
            }
            
            # Append to existing log or create new
            log_entries = []
            if log_file.exists():
                with open(log_file, 'r') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        log_entries = existing_data
                    elif isinstance(existing_data, dict):
                        log_entries = [existing_data]
            
            log_entries.append(log_entry)
            
            with open(log_file, 'w') as f:
                json.dump(log_entries, f, indent=2)
            
            return self._create_success_response({
                "activity_logged": True,
                "activity_type": activity_type,
                "log_file": str(log_file),
                "timestamp": log_entry["timestamp"]
            })
            
        except Exception as e:
            logger.error(f"Failed to log coordination activity: {e}")
            return self._create_error_response(f'Activity logging failed: {str(e)}')


# Create global instance for backward compatibility
async def coordination_action(action: str, **params) -> Dict[str, Any]:
    """Agent coordination operations (backward compatibility).
    
    Actions: store_analysis, retrieve_handoff, update_status, list_pending, 
            create_workflow, store_handoff, get_workflow_state, log_coordination_activity
    """
    coordination_tools = CoordinationTools()
    return await coordination_tools(action, **params)