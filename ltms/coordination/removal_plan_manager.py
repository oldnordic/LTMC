"""
Removal Plan Manager
Plan creation and management with comprehensive LTMC tool integration.

Extracted from safety_validator.py for smart modularization (300-line limit compliance).
Handles removal plan creation using blueprint_action, todo_action, and memory_action.

Components:
- RemovalPlanManager: Complete plan creation with ALL required LTMC tools
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import LTMC tools - MANDATORY
from ltms.tools.consolidated import (
    blueprint_action,   # Tool 6 - Blueprint management - MANDATORY
    todo_action,        # Tool 2 - Todo management - MANDATORY  
    memory_action       # Tool 1 - Memory operations - MANDATORY
)


class RemovalPlanManager:
    """
    Removal plan manager with comprehensive LTMC tool integration.
    
    Uses ALL required LTMC tools for complete plan creation:
    - blueprint_action (Tool 6): Create project blueprint for legacy removal
    - todo_action (Tool 2): Create individual removal tasks
    - memory_action (Tool 1): Store complete removal plan
    
    Integrates with validation results to create executable removal plans.
    """
    
    def __init__(self, core):
        """
        Initialize removal plan manager with core validator.
        
        Args:
            core: SafetyValidationCore instance providing validation context
        """
        self.core = core
    
    def create_removal_plan(self) -> Dict[str, Any]:
        """
        Create comprehensive legacy removal plan based on validation results.
        
        Uses ALL LTMC tools to create executable removal plan including
        project blueprint, individual tasks, and persistent storage.
        
        Returns:
            Dict[str, Any]: Plan creation results with LTMC tool integration
        """
        try:
            # Verify validation report exists
            if not hasattr(self.core, 'validation_report') or not self.core.validation_report:
                return {
                    "success": False,
                    "error": "Must complete validation before creating removal plan",
                    "tasks_created": 0,
                    "blueprint_created": False,
                    "storage_result": {}
                }
            
            validation_report = self.core.validation_report
            safety_score = validation_report.get('safety_score', 0)
            recommendation = validation_report.get('removal_recommendation', 'REQUIRES_REVIEW')
            risk_level = validation_report.get('risk_level', 'HIGH')
            
            # Create blueprint using blueprint_action (Tool 6) - MANDATORY
            blueprint_result = blueprint_action(
                action="create",
                project_name="legacy_removal_execution_plan",
                description=f"Comprehensive legacy @mcp.tool decorator removal plan (Safety: {safety_score:.1f}%, Risk: {risk_level})",
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            blueprint_id = blueprint_result.get('blueprint_id') if blueprint_result.get('success') else None
            blueprint_created = blueprint_result.get('success', False)
            
            # Define removal tasks sequence
            removal_tasks = [
                "Backup current LTMC system state",
                "Create comprehensive test coverage for consolidated tools", 
                "Identify and update import statements referencing legacy decorators",
                "Remove legacy @mcp.tool decorated functions",
                "Update MCP server configuration",
                "Run comprehensive test suite",
                "Validate LTMC system functionality",
                "Update documentation"
            ]
            
            # Create tasks using todo_action (Tool 2) - MANDATORY
            created_tasks = []
            tasks_created = 0
            
            # Only create tasks for approved/caution scenarios
            if recommendation in ['APPROVED', 'APPROVED_WITH_CAUTION']:
                for i, task_description in enumerate(removal_tasks, 1):
                    task_result = todo_action(
                        action="add",
                        task=f"Legacy Removal Task {i}: {task_description}",
                        tags=[
                            "legacy_removal",
                            "mcp_tool_cleanup", 
                            self.core.coordinator.task_id,
                            risk_level.lower()
                        ],
                        conversation_id=self.core.coordinator.conversation_id,
                        role="system"
                    )
                    
                    if task_result.get('success'):
                        created_tasks.append({
                            "task_id": task_result.get('task_id'),
                            "description": task_description,
                            "sequence": i,
                            "status": "pending"
                        })
                        tasks_created += 1
            
            # Create complete removal plan
            plan_timestamp = datetime.now(timezone.utc).isoformat()
            
            self.core.removal_plan = {
                "plan_timestamp": plan_timestamp,
                "coordinator_task": self.core.coordinator.task_id,
                "validation_basis": {
                    "safety_score": safety_score,
                    "recommendation": recommendation,
                    "risk_level": risk_level
                },
                "removal_tasks": created_tasks,
                "execution_strategy": "sequential_with_validation",
                "rollback_plan": "System backup allows complete restoration if issues arise",
                "success_criteria": [
                    "All legacy @mcp.tool decorators removed",
                    "LTMC system fully functional with consolidated tools",
                    "All tests passing", 
                    "Documentation updated"
                ],
                "blueprint_id": blueprint_id
            }
            
            # Store removal plan using memory_action (Tool 1) - MANDATORY
            plan_filename = f"legacy_removal_plan_{self.core.coordinator.task_id}_{int(time.time())}.json"
            storage_result = memory_action(
                action="store",
                file_name=plan_filename,
                content=json.dumps(self.core.removal_plan, indent=2),
                tags=[
                    "removal_plan",
                    "legacy_removal", 
                    self.core.coordinator.task_id,
                    recommendation.lower(),
                    risk_level.lower()
                ],
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            print(f"✅ Removal plan created: {tasks_created} tasks, Blueprint: {blueprint_created}, Risk: {risk_level}")
            
            return {
                "success": True,
                "removal_plan": self.core.removal_plan,
                "tasks_created": tasks_created,
                "blueprint_created": blueprint_created,
                "storage_result": storage_result
            }
            
        except Exception as e:
            error_msg = f"Removal plan creation failed: {e}"
            print(f"❌ {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "tasks_created": 0,
                "blueprint_created": False,
                "storage_result": {}
            }