"""
Coordination Reporting and Finalization
Coordination summary generation and finalization operations.

Extracted from agent_coordination_core.py for 300-line limit compliance.
Handles coordination reporting, summary generation, and finalization.

Components:
- CoordinationReporting: Reporting and finalization with LTMC memory integration
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

# LTMC MCP tool imports for real functionality
from ltms.tools.memory.memory_actions import memory_action


class CoordinationReporting:
    """
    Coordination reporting and finalization with comprehensive LTMC integration.
    
    Handles coordination reporting operations:
    - Comprehensive coordination summary generation
    - Final coordination report compilation and storage
    - Coordination duration calculation
    - LTMC memory storage for reports and summaries
    
    Uses MANDATORY LTMC tools:
    - memory_action (Tool 1): Report storage and coordination data retrieval
    """
    
    def __init__(self, task_id: str, conversation_id: str, task_description: str):
        """
        Initialize coordination reporting.
        
        Args:
            task_id: Task identifier for coordination context
            conversation_id: Conversation context identifier
            task_description: Description of coordination task
        """
        self.task_id = task_id
        self.conversation_id = conversation_id
        self.task_description = task_description
    
    def get_coordination_summary(self, coordination_state: Dict[str, Any], 
                                registration_manager) -> Dict[str, Any]:
        """
        Get comprehensive summary of coordination state.
        
        Uses MANDATORY LTMC tools for data retrieval:
        - memory_action for coordination data retrieval
        
        Args:
            coordination_state: Current coordination state
            registration_manager: Agent registration manager for agent data
            
        Returns:
            Dict containing comprehensive coordination summary
        """
        try:
            # Retrieve all coordination data from LTMC using memory_action (Tool 1) - MANDATORY
            summary_query = memory_action(
                action="retrieve",
                query=f"coordination task_id:{self.task_id}",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Get registration summary from registration manager
            registration_summary = registration_manager.get_registration_summary()
            
            summary = {
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "task_description": self.task_description,
                "registered_agents": registration_summary["active_agent_ids"] + registration_summary["completed_agent_ids"],
                "agent_statuses": {
                    agent_id: reg.status.value 
                    for agent_id, reg in registration_manager.get_all_registrations().items()
                },
                "findings_count": len(coordination_state["agent_findings"]),
                "coordination_state": coordination_state,
                "ltmc_documents": summary_query.get('total_found', 0) if summary_query.get('success') else 0,
                "registration_summary": registration_summary
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ Failed to get coordination summary: {e}")
            return {"error": str(e)}
    
    def finalize_coordination(self, coordination_state: Dict[str, Any], 
                             registration_manager) -> Dict[str, Any]:
        """
        Finalize coordination and store complete results.
        
        Uses MANDATORY LTMC tools for report storage:
        - memory_action for final report persistence
        
        Args:
            coordination_state: Current coordination state
            registration_manager: Agent registration manager for agent data
            
        Returns:
            Dict containing final coordination report
        """
        try:
            # Get final registration summary
            registration_summary = registration_manager.get_registration_summary()
            
            # Generate final coordination report
            final_report = {
                "coordination_completed": True,
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "task_description": self.task_description,
                "total_agents": registration_summary["total_agents"],
                "successful_agents": len(registration_summary["completed_agent_ids"]),
                "total_findings": len(coordination_state["agent_findings"]),
                "coordination_duration": self._calculate_duration(registration_manager),
                "agent_summary": {
                    agent_id: {
                        "type": reg.agent_type,
                        "status": reg.status.value,
                        "task_scope": reg.task_scope,
                        "outputs": reg.outputs
                    } for agent_id, reg in registration_manager.get_all_registrations().items()
                },
                "finalization_timestamp": datetime.now(timezone.utc).isoformat(),
                "registration_summary": registration_summary
            }
            
            # Store final report in LTMC using memory_action (Tool 1) - MANDATORY
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on coordination final report context and results
            finalization_timestamp = final_report["finalization_timestamp"].replace(':', '_').replace('-', '_')
            total_agents = final_report["total_agents"]
            successful_agents = final_report["successful_agents"]
            total_findings = final_report["total_findings"]
            success_rate = f"{int((successful_agents/total_agents)*100)}pct" if total_agents > 0 else "0pct"
            task_description_clean = self.task_description.replace(' ', '_').replace('/', '_').lower()[:15]  # Truncate long descriptions
            dynamic_final_report_file_name = f"coordination_final_report_{self.task_id}_{task_description_clean}_{total_agents}agents_{success_rate}success_{total_findings}findings_{finalization_timestamp}.md"
            
            memory_action(
                action="store",
                file_name=dynamic_final_report_file_name,
                content=f"# Final Coordination Report\n\n{json.dumps(final_report, indent=2)}",
                tags=["coordination_complete", "final_report", self.task_id],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print(f"✅ Coordination finalized successfully for task: {self.task_id}")
            return final_report
            
        except Exception as e:
            print(f"❌ Failed to finalize coordination: {e}")
            return {"error": str(e)}
    
    def _calculate_duration(self, registration_manager) -> str:
        """
        Calculate coordination duration using registration manager data.
        
        Args:
            registration_manager: Agent registration manager for timing data
            
        Returns:
            str: Formatted duration string
        """
        try:
            registration_summary = registration_manager.get_registration_summary()
            
            if registration_summary["total_agents"] == 0:
                return "0 seconds"
            
            all_registrations = registration_manager.get_all_registrations()
            start_times = [reg.start_time for reg in all_registrations.values()]
            end_times = [reg.last_activity for reg in all_registrations.values()]
            
            if start_times and end_times:
                start = min(start_times)
                end = max(end_times)
                
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                
                duration = end_dt - start_dt
                return str(duration)
            
            return "unknown"
            
        except Exception as e:
            print(f"⚠️ Failed to calculate duration: {e}")
            return "calculation_failed"
    
    def generate_interim_report(self, coordination_state: Dict[str, Any], 
                               registration_manager) -> Dict[str, Any]:
        """
        Generate interim coordination report.
        
        Args:
            coordination_state: Current coordination state
            registration_manager: Agent registration manager for agent data
            
        Returns:
            Dict containing interim report data
        """
        try:
            registration_summary = registration_manager.get_registration_summary()
            
            interim_report = {
                "report_type": "interim",
                "task_id": self.task_id,
                "conversation_id": self.conversation_id,
                "task_description": self.task_description,
                "active_agents": len(registration_summary["active_agent_ids"]),
                "completed_agents": len(registration_summary["completed_agent_ids"]),
                "total_findings": len(coordination_state["agent_findings"]),
                "current_agent": coordination_state.get("current_agent"),
                "elapsed_duration": self._calculate_duration(registration_manager),
                "report_timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            return interim_report
            
        except Exception as e:
            print(f"❌ Failed to generate interim report: {e}")
            return {"error": str(e)}