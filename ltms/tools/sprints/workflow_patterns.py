from ltms.tools.coordination.coordination_actions import CoordinationTools
"""
Sprint Workflow Pattern Implementation for LTMC.
Provides workflow state management and coordination patterns for professional sprint management.

File: ltms/tools/sprints/workflow_patterns.py
Lines: ~280 (under 300 limit)
Purpose: Sprint workflow state management, pattern templates, and LTMC coordination integration
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path

from ..coordination.coordination_actions import coordination_action

logger = logging.getLogger(__name__)


class SprintWorkflowManager:
    """Manages sprint workflow states and coordination patterns with LTMC integration."""
    
    def __init__(self):
        self.coordination_dir = Path("/home/feanor/Projects/ltmc/.ltmc-coordination")
        self.templates_file = self.coordination_dir / "sprint-workflow-templates.json"
        self.workflow_states_dir = self.coordination_dir / "workflow-states"
        
        # Load workflow templates
        self.templates = self._load_workflow_templates()
    
    def _load_workflow_templates(self) -> Dict[str, Any]:
        """Load sprint workflow templates from configuration file."""
        try:
            if self.templates_file.exists():
                with open(self.templates_file, 'r') as f:
                    data = json.load(f)
                    return data.get('sprint_workflow_templates', {})
            else:
                logger.warning(f"Workflow templates file not found: {self.templates_file}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load workflow templates: {e}")
            return {}
    
    async def create_sprint_workflow(self, sprint_id: str, sprint_name: str, 
                                   workflow_type: str = "standard_sprint_workflow",
                                   created_by: str = None) -> Dict[str, Any]:
        """Create a new sprint workflow with proper state initialization."""
        coordination_tools = CoordinationTools()
        try:
            workflow_id = f"sprint_{sprint_id}_{workflow_type}"
            
            # Get workflow template
            template = self.templates.get(workflow_type)
            if not template:
                return {"success": False, "error": f"Unknown workflow type: {workflow_type}"}
            
            # Create coordination workflow
            coord_result = await coordination_tools("create_workflow",
                workflow_id=workflow_id,
                description=f"Sprint coordination for {sprint_name} using {template['template_name']}",
                agent_id=created_by or 'system'
            )
            
            if coord_result.get('success'):
                # Initialize with proper workflow state structure
                workflow_state = {
                    "workflow_id": workflow_id,
                    "sprint_id": sprint_id,
                    "sprint_name": sprint_name,
                    "workflow_type": workflow_type,
                    "template_name": template['template_name'],
                    "description": f"Sprint workflow for {sprint_name}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by": created_by or 'system',
                    "current_state": "initialized",
                    "workflow_config": {
                        "default_duration_days": template.get('default_duration_days'),
                        "available_states": list(template['states'].keys()),
                        "automation_enabled": True
                    },
                    "states": [
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "previous_state": None,
                            "new_state": "initialized",
                            "agent_id": created_by or 'system',
                            "metadata": {
                                "workflow_type": workflow_type,
                                "template_applied": template['template_name']
                            }
                        }
                    ],
                    "state_definitions": template['states'],
                    "coordination_patterns": self.templates.get('coordination_patterns', {})
                }
                
                # Save enhanced workflow state
                state_file = self.workflow_states_dir / f"{workflow_id}_state.json"
                with open(state_file, 'w') as f:
                    json.dump(workflow_state, f, indent=2)
                
                return {
                    "success": True,
                    "workflow_id": workflow_id,
                    "workflow_type": workflow_type,
                    "current_state": "initialized",
                    "available_transitions": template['states']['initialized']['transitions']
                }
            else:
                return {"success": False, "error": "Failed to create coordination workflow"}
                
        except Exception as e:
            logger.error(f"Failed to create sprint workflow: {e}")
            return {"success": False, "error": str(e)}
    
    async def transition_workflow_state(self, workflow_id: str, new_state: str, 
                                      agent_id: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transition a workflow to a new state with validation and automation."""
        coordination_tools = CoordinationTools()
        try:
            # Load current workflow state
            state_file = self.workflow_states_dir / f"{workflow_id}_state.json"
            if not state_file.exists():
                return {"success": False, "error": f"Workflow {workflow_id} not found"}
            
            with open(state_file, 'r') as f:
                workflow_state = json.load(f)
            
            current_state = workflow_state.get('current_state')
            state_definitions = workflow_state.get('state_definitions', {})
            
            # Validate transition
            if current_state not in state_definitions:
                return {"success": False, "error": f"Invalid current state: {current_state}"}
            
            allowed_transitions = state_definitions[current_state].get('transitions', [])
            if new_state not in allowed_transitions:
                return {"success": False, "error": f"Invalid transition from {current_state} to {new_state}"}
            
            # Perform state transition
            workflow_state['current_state'] = new_state
            workflow_state['states'].append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "previous_state": current_state,
                "new_state": new_state,
                "agent_id": agent_id or 'system',
                "metadata": metadata or {}
            })
            
            # Save updated state
            with open(state_file, 'w') as f:
                json.dump(workflow_state, f, indent=2)
            
            # Execute automation if configured
            await self._execute_state_automation(workflow_id, new_state, workflow_state)
            
            # Update coordination system
            await coordination_tools("update_status",
                workflow_id=workflow_id,
                status=new_state,
                agent_id=agent_id or 'system'
            )
            
            return {
                "success": True,
                "previous_state": current_state,
                "new_state": new_state,
                "available_transitions": state_definitions.get(new_state, {}).get('transitions', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to transition workflow state: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_state_automation(self, workflow_id: str, state: str, 
                                      workflow_state: Dict[str, Any]) -> None:
        """Execute automated actions for a workflow state."""
        try:
            state_definitions = workflow_state.get('state_definitions', {})
            automation = state_definitions.get(state, {}).get('automation', {})
            
            if not automation:
                return
            
            # Send notifications
            if 'notifications' in automation:
                await self._send_state_notifications(workflow_id, state, workflow_state, 
                                                   automation['notifications'])
            
            # Auto-transition if configured
            if automation.get('auto_transition'):
                # Implement auto-transition logic based on conditions
                pass
            
            # Update metrics if configured
            if automation.get('velocity_tracking') or automation.get('burndown_tracking'):
                await self._update_sprint_metrics(workflow_id, state, workflow_state)
            
        except Exception as e:
            logger.error(f"Failed to execute state automation: {e}")
    
    async def _send_state_notifications(self, workflow_id: str, state: str, 
                                      workflow_state: Dict[str, Any], 
                                      notification_targets: List[str]) -> None:
        """Send notifications for workflow state changes."""
        coordination_tools = CoordinationTools()
        try:
            # Get notification template
            templates = self.templates.get('notification_templates', {})
            
            # Map state to notification template
            template_mapping = {
                'active': 'sprint_start',
                'completed': 'sprint_completion',
                'blocked': 'blocker_alert'
            }
            
            template_name = template_mapping.get(state)
            if not template_name or template_name not in templates:
                return
            
            template = templates[template_name]
            
            # Create notification context
            context = {
                'sprint_name': workflow_state.get('sprint_name', ''),
                'workflow_id': workflow_id,
                'state': state,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            # Store notification request in coordination system
            await coordination_tools("store_analysis",
                agent_id='sprint_notification_system',
                analysis_data={
                    'notification_type': template_name,
                    'subject': template['subject'],
                    'message': template['template'],
                    'context': context,
                    'targets': notification_targets
                },
                target_agent='notification_dispatcher',
                instructions=f"Send {template_name} notification for {workflow_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to send state notifications: {e}")
    
    async def _update_sprint_metrics(self, workflow_id: str, state: str, 
                                   workflow_state: Dict[str, Any]) -> None:
        """Update sprint metrics based on state changes."""
        coordination_tools = CoordinationTools()
        try:
            sprint_id = workflow_state.get('sprint_id')
            if not sprint_id:
                return
            
            # Store metrics update request
            await coordination_tools("store_analysis",
                agent_id='sprint_metrics_system',
                analysis_data={
                    'metric_update': 'state_transition',
                    'sprint_id': sprint_id,
                    'workflow_id': workflow_id,
                    'new_state': state,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                },
                target_agent='metrics_processor',
                instructions=f"Update sprint metrics for {sprint_id} state change to {state}"
            )
            
        except Exception as e:
            logger.error(f"Failed to update sprint metrics: {e}")
    
    def get_workflow_state(self, workflow_id: str) -> Dict[str, Any]:
        """Get current workflow state and available actions."""
        try:
            state_file = self.workflow_states_dir / f"{workflow_id}_state.json"
            if not state_file.exists():
                return {"success": False, "error": f"Workflow {workflow_id} not found"}
            
            with open(state_file, 'r') as f:
                workflow_state = json.load(f)
            
            current_state = workflow_state.get('current_state')
            state_definitions = workflow_state.get('state_definitions', {})
            current_state_def = state_definitions.get(current_state, {})
            
            return {
                "success": True,
                "workflow_id": workflow_id,
                "current_state": current_state,
                "state_description": current_state_def.get('description', ''),
                "required_actions": current_state_def.get('required_actions', []),
                "available_transitions": current_state_def.get('transitions', []),
                "automation": current_state_def.get('automation', {}),
                "workflow_history": workflow_state.get('states', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to get workflow state: {e}")
            return {"success": False, "error": str(e)}
    
    def list_available_workflow_types(self) -> Dict[str, Any]:
        """List all available workflow types and their descriptions."""
        workflow_types = {}
        
        for workflow_type, template in self.templates.items():
            # Skip non-workflow template items (metadata and configuration sections)
            if workflow_type in ['coordination_patterns', 'notification_templates', 'description', 'created_at', 'created_by']:
                continue
            
            # Only process dictionary templates (actual workflow definitions)
            if not isinstance(template, dict):
                continue
                
            workflow_types[workflow_type] = {
                "template_name": template.get('template_name', ''),
                "description": template.get('description', ''),
                "default_duration_days": template.get('default_duration_days'),
                "states": list(template.get('states', {}).keys())
            }
        
        return {
            "success": True,
            "available_workflows": workflow_types
        }


# Global workflow manager instance
_workflow_manager = None

def get_workflow_manager() -> SprintWorkflowManager:
    """Get or create global workflow manager instance."""
    global _workflow_manager
    if _workflow_manager is None:
        _workflow_manager = SprintWorkflowManager()
    return _workflow_manager