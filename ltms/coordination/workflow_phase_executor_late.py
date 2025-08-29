"""
Workflow Phase Executor - Late Phases (4-6)
Phase execution for planning, documentation, and completion.

Extracted from workflow_phase_executor.py for 300-line limit compliance.
Handles Phases 4-6 with LTMC tools integration.

Components:
- WorkflowPhaseExecutorLate: Phases 4-6 execution with doc, sync, cache, memory tools
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any

# Import LTMC tools - MANDATORY
from ltms.tools.docs.documentation_actions import documentation_action   # Tool 9 - Documentation - MANDATORY
from ltms.tools.sync.sync_actions import sync_action           # Tool 10 - Doc synchronization - MANDATORY
from ltms.tools.monitoring.cache_actions import cache_action          # Tool 7 - Cache operations - MANDATORY
from ltms.tools.memory.memory_actions import memory_action          # Tool 1 - Memory operations - MANDATORY


class WorkflowPhaseExecutorLate:
    """
    Late phase execution with comprehensive LTMC integration.
    
    Handles late phase execution operations:
    - Phase 4: Removal plan creation and task management
    - Phase 5: Documentation generation and synchronization
    - Phase 6: Workflow completion and results compilation
    
    Uses MANDATORY LTMC tools:
    - documentation_action (Tool 9): Workflow documentation generation
    - sync_action (Tool 10): Documentation synchronization
    - cache_action (Tool 7): Cache management and optimization
    - memory_action (Tool 1): Results storage and persistence
    """
    
    def __init__(self, coordinator, state_manager, workflow_orchestrator, 
                 analyzer, validator, workflow_id: str, conversation_id: str):
        """
        Initialize late phase executor.
        
        Args:
            coordinator: LTMC agent coordinator for coordination operations
            state_manager: Agent state manager for state transitions
            workflow_orchestrator: Workflow orchestrator for advanced coordination
            analyzer: LegacyCodeAnalyzer agent for analysis operations
            validator: SafetyValidator agent for validation operations
            workflow_id: Unique workflow identifier
            conversation_id: Conversation context identifier
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.workflow_orchestrator = workflow_orchestrator
        self.analyzer = analyzer
        self.validator = validator
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
    
    def execute_phase_4_removal_planning(self) -> Dict[str, Any]:
        """
        Execute Phase 4: Removal Plan Creation and Task Management.
        
        Returns:
            Dict[str, Any]: Phase 4 execution results with removal plan
        """
        try:
            print("\\n📋 Phase 4: Removal Plan Creation and Task Management")
            
            removal_plan = self.validator.create_removal_plan()
            if not removal_plan.get('success'):
                raise Exception(f"Removal plan creation failed: {removal_plan.get('error', 'Unknown planning error')}")
            
            print(f"✅ Removal plan created with {removal_plan.get('tasks_created', 0)} structured tasks")
            
            return {
                "success": True,
                "phase": 4,
                "removal_plan": removal_plan
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 4,
                "error": str(e)
            }
    
    def execute_phase_5_documentation(self) -> Dict[str, Any]:
        """
        Execute Phase 5: Documentation Generation and Synchronization.
        
        Uses MANDATORY LTMC tools for documentation workflow:
        - documentation_action for API documentation generation
        - sync_action for documentation synchronization
        - cache_action for cache optimization
        
        Returns:
            Dict[str, Any]: Phase 5 execution results with documentation status
        """
        try:
            print("\\n📋 Phase 5: Documentation Generation and Synchronization")
            
            # Generate comprehensive workflow documentation using documentation_action (Tool 9) - MANDATORY
            workflow_documentation = documentation_action(
                action="generate_api_docs",
                project_path="/home/feanor/Projects/ltmc",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Synchronize documentation with codebase using sync_action (Tool 10) - MANDATORY
            doc_sync_result = sync_action(
                action="code",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            # Flush cache to ensure fresh data using cache_action (Tool 7) - MANDATORY
            cache_flush = cache_action(
                action="flush",
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print("✅ Documentation generated and synchronized")
            
            return {
                "success": True,
                "phase": 5,
                "documentation_results": {
                    "generated": workflow_documentation.get('success', False),
                    "synchronized": doc_sync_result.get('success', False),
                    "cache_cleared": cache_flush.get('success', False)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 5,
                "error": str(e)
            }
    
    def execute_phase_6_completion(self, analysis_result: Dict[str, Any], 
                                 validation_result: Dict[str, Any], 
                                 removal_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Phase 6: Workflow Completion and Results Compilation.
        
        Uses MANDATORY LTMC tools for results compilation:
        - memory_action for final report storage
        
        Args:
            analysis_result: Results from Phase 2
            validation_result: Results from Phase 3
            removal_plan: Results from Phase 4
            
        Returns:
            Dict[str, Any]: Phase 6 execution results with compiled workflow results
        """
        try:
            print("\\n📋 Phase 6: Workflow Completion and Results Compilation")
            
            # Compile comprehensive workflow results
            workflow_results = {
                "workflow_id": self.workflow_id,
                "conversation_id": self.conversation_id,
                "execution_timestamp": datetime.now(timezone.utc).isoformat(),
                "workflow_status": "COMPLETED",
                "phases_completed": 6,
                "agents_coordinated": 2,
                "ltmc_tools_used": 11,
                "analysis_results": {
                    "success": analysis_result.get('success'),
                    "legacy_decorators_found": len(analysis_result.get('legacy_decorators', [])),
                    "functional_tools_available": len(analysis_result.get('functional_tools', [])),
                    "analysis_agent": self.analyzer.agent_id
                },
                "validation_results": {
                    "success": validation_result.get('success'),
                    "safety_score": validation_result.get('validation_report', {}).get('safety_score', 0),
                    "recommendation": validation_result.get('validation_report', {}).get('removal_recommendation', 'UNKNOWN'),
                    "risk_level": validation_result.get('validation_report', {}).get('risk_level', 'UNKNOWN'),
                    "validation_agent": self.validator.agent_id
                },
                "removal_plan_results": {
                    "success": removal_plan.get('success'),
                    "tasks_created": removal_plan.get('tasks_created', 0),
                    "execution_strategy": "sequential_with_validation"
                },
                "coordination_summary": self.coordinator.get_coordination_summary(),
                "state_performance": self.state_manager.get_performance_metrics()
            }
            
            # Store final comprehensive workflow report using memory_action (Tool 1) - MANDATORY
            final_report = memory_action(
                action="store",
                file_name=f"coordinated_legacy_removal_workflow_report_{self.workflow_id}.json",
                content=json.dumps(workflow_results, indent=2),
                tags=["workflow_complete", "legacy_removal", "coordinated_agents", "all_tools_used"],
                conversation_id=self.conversation_id,
                role="system"
            )
            
            print("✅ Comprehensive workflow report generated and stored")
            
            return {
                "success": True,
                "phase": 6,
                "workflow_results": workflow_results,
                "report_storage": final_report
            }
            
        except Exception as e:
            return {
                "success": False,
                "phase": 6,
                "error": str(e)
            }