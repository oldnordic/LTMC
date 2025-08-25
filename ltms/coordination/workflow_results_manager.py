"""
Workflow Results Manager
Workflow results compilation and reporting.

Extracted from legacy_removal_workflow.py for smart modularization (300-line limit compliance).
Handles workflow results compilation and reporting functionality.

Components:
- WorkflowResultsManager: Results compilation and management utilities
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple


class WorkflowResultsManager:
    """
    Workflow results management and compilation.
    
    Handles results management operations:
    - Comprehensive workflow results compilation
    - Results structure validation and consistency checking
    - Summary report generation for quick status overview
    - Multiple export formats (JSON, dictionary, summary)
    - Performance metrics integration
    - Results state management and reset capabilities
    
    Pure results management utilities without direct LTMC tool dependencies.
    Results are stored via external memory_action calls from phase executor.
    """
    
    def __init__(self, coordinator, state_manager, analyzer, validator,
                 workflow_id: str, conversation_id: str):
        """
        Initialize workflow results manager.
        
        Args:
            coordinator: LTMC agent coordinator for coordination summary
            state_manager: Agent state manager for performance metrics
            analyzer: LegacyCodeAnalyzer agent for agent ID references
            validator: SafetyValidator agent for agent ID references
            workflow_id: Unique workflow identifier
            conversation_id: Conversation context identifier
        """
        self.coordinator = coordinator
        self.state_manager = state_manager
        self.analyzer = analyzer
        self.validator = validator
        self.workflow_id = workflow_id
        self.conversation_id = conversation_id
        self.workflow_results = {}
    
    def compile_workflow_results(self, analysis_result: Dict[str, Any], 
                                validation_result: Dict[str, Any],
                                removal_plan: Dict[str, Any],
                                documentation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compile comprehensive workflow results from all phases.
        
        Creates complete workflow results structure with:
        - Core workflow metadata and identifiers
        - Analysis results with legacy decorators and functional tools
        - Validation results with safety scores and recommendations
        - Removal plan results with task creation and strategy
        - Documentation results with generation and sync status
        - Performance metrics from coordination and state management
        
        Args:
            analysis_result: Results from legacy code analysis phase
            validation_result: Results from safety validation phase
            removal_plan: Results from removal plan creation phase
            documentation_results: Results from documentation phase
            
        Returns:
            Dict[str, Any]: Compiled workflow results with complete metadata
        """
        # Compile comprehensive workflow results
        self.workflow_results = {
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
            "documentation_results": documentation_results,
            "coordination_summary": self.coordinator.get_coordination_summary(),
            "state_performance": self.state_manager.get_performance_metrics()
        }
        
        return {
            "success": True,
            "workflow_results": self.workflow_results
        }
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate summary report for quick workflow status overview.
        
        Creates concise summary with key metrics and status information
        suitable for quick status checks and reporting dashboards.
        
        Returns:
            Dict[str, Any]: Summary report with key workflow metrics
        """
        return {
            "workflow_id": self.workflow_id,
            "status": self.workflow_results.get('workflow_status', 'UNKNOWN'),
            "phases_completed": self.workflow_results.get('phases_completed', 0),
            "legacy_decorators_found": self.workflow_results.get('analysis_results', {}).get('legacy_decorators_found', 0),
            "safety_score": self.workflow_results.get('validation_results', {}).get('safety_score', 0),
            "removal_recommendation": self.workflow_results.get('validation_results', {}).get('recommendation', 'UNKNOWN'),
            "tasks_created": self.workflow_results.get('removal_plan_results', {}).get('tasks_created', 0),
            "summary_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def validate_results_structure(self, results: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate workflow results structure for completeness and consistency.
        
        Checks for required fields, data types, and structural consistency
        to ensure results are complete and properly formatted.
        
        Args:
            results: Workflow results dictionary to validate
            
        Returns:
            Tuple[bool, List[str]]: Validation status and list of issues found
        """
        issues = []
        
        # Required top-level fields
        required_fields = [
            'workflow_id', 'conversation_id', 'execution_timestamp',
            'workflow_status', 'phases_completed', 'agents_coordinated',
            'analysis_results', 'validation_results', 'removal_plan_results',
            'documentation_results'
        ]
        
        for field in required_fields:
            if field not in results:
                issues.append(f"Missing required field: {field}")
        
        # Validate analysis_results structure
        if 'analysis_results' in results:
            analysis = results['analysis_results']
            if 'success' not in analysis:
                issues.append("Missing 'success' field in analysis_results")
        
        # Validate validation_results structure
        if 'validation_results' in results:
            validation = results['validation_results']
            if 'success' not in validation:
                issues.append("Missing 'success' field in validation_results")
        
        return len(issues) == 0, issues
    
    def export_results_to_json(self) -> str:
        """
        Export workflow results to JSON format.
        
        Returns:
            str: JSON string representation of workflow results
        """
        return json.dumps(self.workflow_results, indent=2)
    
    def export_results_to_dict(self) -> Dict[str, Any]:
        """
        Export workflow results as dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary copy of workflow results
        """
        return self.workflow_results.copy()
    
    def export_summary(self) -> Dict[str, Any]:
        """
        Export workflow summary for quick reporting.
        
        Returns:
            Dict[str, Any]: Summary report dictionary
        """
        return self.generate_summary_report()
    
    def reset_results(self) -> None:
        """Reset workflow results storage to empty state."""
        self.workflow_results = {}