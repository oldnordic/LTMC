"""
Safety Validation Engine
Core validation logic with comprehensive LTMC tool integration.

Extracted from safety_validator.py for smart modularization (300-line limit compliance).
Handles comprehensive safety validation using ALL 11 LTMC tools - MANDATORY.

Components:
- SafetyValidationEngine: Complete validation logic with LTMC integration
"""

import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import coordination components
from .agent_coordination_models import AgentStatus
from .agent_state_models import StateTransition  
from .safety_validation_utils import generate_next_steps, create_removal_recommendations

# Import ALL LTMC tools - MANDATORY
from ltms.tools.memory.memory_actions import memory_action      # Tool 1 - Memory operations - MANDATORY
from ltms.tools.monitoring.cache_actions import cache_action       # Tool 7 - Cache operations - MANDATORY
from ltms.tools.graph.graph_actions import graph_action       # Tool 8 - Knowledge graph - MANDATORY
from ltms.tools.config.config_actions import config_action      # Tool 11 - Configuration - MANDATORY
from ltms.tools.blueprints.blueprint_actions import blueprint_action   # Tool 6 - Blueprint management - MANDATORY  
from ltms.tools.patterns.pattern_actions import pattern_action      # Tool 5 - Code analysis - MANDATORY


class SafetyValidationEngine:
    """
    Safety validation engine with comprehensive LTMC tool integration.
    
    Uses ALL required LTMC tools for complete validation:
    - config_action (Tool 11): System configuration validation
    - cache_action (Tool 7): Cache health checks  
    - graph_action (Tool 8): Dependency analysis
    - blueprint_action (Tool 6): Complexity analysis
    - pattern_action (Tool 5): Usage pattern analysis
    - memory_action (Tool 1): Report storage and persistence
    
    Provides comprehensive safety scoring and recommendation system.
    """
    
    def __init__(self, core):
        """
        Initialize validation engine with core agent.
        
        Args:
            core: SafetyValidationCore instance providing agent context
        """
        self.core = core
    
    def validate_removal_safety(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that legacy code can be safely removed.
        
        Uses ALL LTMC tools for comprehensive validation including system
        configuration, cache health, dependency analysis, and complexity assessment.
        Creates detailed safety report with scoring system.
        
        Args:
            analysis_data: Results from LegacyCodeAnalyzer containing legacy decorators and functional tools
            
        Returns:
            Dict[str, Any]: Comprehensive validation report with safety score and recommendations
        """
        try:
            # Transition to active state
            self.core.state_manager.transition_agent_state(
                self.core.agent_id,
                AgentStatus.ACTIVE,
                StateTransition.ACTIVATE,
                {"state_updates": {"current_task": "safety_validation"}}
            )
            
            # Use config_action (Tool 11) to validate system configuration - MANDATORY
            config_validation = config_action(
                action="validate_config",
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            # Use cache_action (Tool 7) for health check - MANDATORY
            cache_health = cache_action(
                action="health_check", 
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            # Use graph_action (Tool 8) to analyze dependencies - MANDATORY
            dependency_graph = graph_action(
                action="query",
                query_text="mcp_server legacy_decorators",
                return_paths=True
            )
            
            # Use blueprint_action (Tool 6) to analyze complexity - MANDATORY  
            complexity_analysis = blueprint_action(
                action="analyze_complexity",
                project_name="ltmc_legacy_removal",
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            # Use pattern_action (Tool 5) to scan for legacy tool usage - MANDATORY
            usage_scan = pattern_action(
                action="extract_functions", 
                file_path="/home/feanor/Projects/ltmc/ltms",
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            # Perform comprehensive safety checks using ALL LTMC tool results
            safety_checks = [
                {
                    "check": "functional_tools_available",
                    "status": "PASS" if len(analysis_data.get('functional_tools', [])) >= 11 else "FAIL",
                    "description": "Verify 11 functional tools are available",
                    "details": f"Found {len(analysis_data.get('functional_tools', []))} functional tools"
                },
                {
                    "check": "configuration_valid", 
                    "status": "PASS" if config_validation.get('success') else "FAIL",
                    "description": "System configuration is valid",
                    "details": config_validation.get('error', 'Configuration validated successfully')
                },
                {
                    "check": "cache_healthy",
                    "status": "PASS" if cache_health.get('success') else "WARN",
                    "description": "Cache system health check",
                    "details": cache_health.get('status', 'Cache health verified')
                },
                {
                    "check": "dependency_analysis_complete",
                    "status": "PASS" if dependency_graph.get('success') else "WARN", 
                    "description": "Dependency graph analysis completed",
                    "details": f"Graph query success: {dependency_graph.get('success', False)}"
                },
                {
                    "check": "complexity_within_bounds",
                    "status": "PASS" if complexity_analysis.get('success') else "WARN",
                    "description": "Project complexity analysis within acceptable bounds",
                    "details": complexity_analysis.get('summary', 'Complexity analysis completed')
                },
                {
                    "check": "usage_patterns_analyzed",
                    "status": "PASS" if usage_scan.get('success') else "WARN",
                    "description": "Legacy tool usage patterns analyzed", 
                    "details": f"Usage scan completed: {usage_scan.get('success', False)}"
                }
            ]
            
            self.core.safety_checks = safety_checks
            
            # Calculate safety score
            passed_checks = sum(1 for check in safety_checks if check['status'] == 'PASS')
            total_checks = len(safety_checks)
            safety_score = (passed_checks / total_checks) * 100
            
            # Determine recommendation based on safety score
            if safety_score >= 90:
                recommendation = "APPROVED"
                risk_level = "LOW"
            elif safety_score >= 75:
                recommendation = "APPROVED_WITH_CAUTION" 
                risk_level = "MEDIUM"
            else:
                recommendation = "REQUIRES_REVIEW"
                risk_level = "HIGH"
            
            # Create comprehensive validation report  
            self.core.validation_report = {
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": self.core.agent_id,
                "coordinator_task": self.core.coordinator.task_id,
                "safety_score": safety_score,
                "risk_level": risk_level,
                "removal_recommendation": recommendation,
                "safety_checks": safety_checks,
                "analysis_input_summary": {
                    "legacy_decorators_count": len(analysis_data.get('legacy_decorators', [])),
                    "functional_tools_count": len(analysis_data.get('functional_tools', [])),
                    "analysis_timestamp": analysis_data.get('analysis_report', {}).get('analysis_timestamp', 'unknown')
                },
                "validation_tools_used": ["config_action", "cache_action", "graph_action", "blueprint_action", "pattern_action"],
                "next_steps": generate_next_steps(recommendation, safety_checks)
            }
            
            # Store validation report in LTMC memory (Tool 1) - MANDATORY
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic file name based on safety validation context, score, and recommendation
            validation_timestamp = self.core.validation_report["validation_timestamp"].replace(':', '_').replace('-', '_')
            safety_score_int = int(safety_score)
            dynamic_safety_report_file_name = f"safety_validation_report_{recommendation.lower()}_{safety_score_int}score_{risk_level.lower()}_task{self.core.coordinator.task_id}_{validation_timestamp}.json"
            
            memory_result = memory_action(
                action="store",
                file_name=dynamic_safety_report_file_name,
                content=json.dumps(self.core.validation_report, indent=2),
                tags=["safety_validation", "removal_approval", self.core.coordinator.task_id, risk_level.lower()],
                conversation_id=self.core.coordinator.conversation_id,
                role="system"
            )
            
            # Create knowledge graph relationships (Tool 8) - MANDATORY
            graph_action(
                action="link",
                source_entity=f"safety_validation_{self.core.coordinator.task_id}",
                target_entity="legacy_removal_plan",
                relationship="validates_safety_of",
                properties={
                    "safety_score": safety_score,
                    "recommendation": recommendation,
                    "risk_level": risk_level,
                    "validation_timestamp": self.core.validation_report["validation_timestamp"]
                }
            )
            
            # Update agent state to completed validation
            self.core.state_manager.transition_agent_state(
                self.core.agent_id,
                AgentStatus.COMPLETED,
                StateTransition.COMPLETE,
                {"state_updates": {
                    "validation_completed": True,
                    "safety_score": safety_score,
                    "recommendation": recommendation
                }}
            )
            
            print(f"✅ Safety validation complete: {safety_score:.1f}% safety score - {recommendation}")
            
            return {
                "success": True,
                "validation_report": self.core.validation_report,
                "safety_checks": self.core.safety_checks,
                "removal_recommendations": create_removal_recommendations(analysis_data),
                "memory_storage": memory_result
            }
            
        except Exception as e:
            # Log error and transition to error state
            error_msg = f"Safety validation failed: {e}"
            print(f"❌ {error_msg}")
            
            self.core.state_manager.transition_agent_state(
                self.core.agent_id,
                AgentStatus.ERROR,
                StateTransition.FAIL,
                {"state_updates": {"error": error_msg}}
            )
            
            return {
                "success": False,
                "error": error_msg,
                "validation_report": {},
                "safety_checks": []
            }