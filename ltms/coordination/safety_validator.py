"""
LTMC Safety Validator Agent
Modularized agent for validating safe removal of legacy code.

Smart modularization completed (300-line limit compliance).
Uses 4 focused modules with comprehensive LTMC tool integration.

Components:
- SafetyValidator: Main agent class integrating all modular components
- SafetyValidationCore: Base agent functionality and coordination
- SafetyValidationEngine: Core validation logic with ALL 11 LTMC tools
- SafetyValidationUtils: Pure utility functions  
- RemovalPlanManager: Plan creation with blueprint/todo/memory integration
"""

from typing import Dict, Any, List

# Import coordination framework components
from .agent_coordination_core import AgentCoordinationCore as LTMCAgentCoordinator
from .agent_state_manager import LTMCAgentStateManager

# Import modularized components - ALL 4 modules
from .safety_validation_core import SafetyValidationCore
from .safety_validation_engine import SafetyValidationEngine
from .safety_validation_utils import generate_next_steps, create_removal_recommendations
from .removal_plan_manager import RemovalPlanManager


class SafetyValidator:
    """
    Modularized agent for validating safe removal of legacy code.
    
    Integrates 4 focused modules for comprehensive validation:
    - SafetyValidationCore: Base agent functionality and coordination
    - SafetyValidationEngine: Core validation with ALL 11 LTMC tools
    - SafetyValidationUtils: Pure utility functions
    - RemovalPlanManager: Plan creation with blueprint/todo/memory integration
    
    Part of the coordinated legacy removal workflow alongside LegacyCodeAnalyzer
    and LegacyRemovalWorkflow agents. Maintains 100% LTMC tool integration.
    """
    
    def __init__(self, coordinator: LTMCAgentCoordinator, state_manager: LTMCAgentStateManager):
        """
        Initialize safety validator with modular components.
        
        Args:
            coordinator: LTMC agent coordinator for registration and communication
            state_manager: Agent state manager for lifecycle management
        """
        # Initialize core component
        self.core = SafetyValidationCore(coordinator, state_manager)
        
        # Initialize specialized components
        self.engine = SafetyValidationEngine(self.core)
        self.plan_manager = RemovalPlanManager(self.core)
        
        # Expose core properties for compatibility
        self.agent_id = self.core.agent_id
        self.agent_type = self.core.agent_type
        self.coordinator = self.core.coordinator
        self.state_manager = self.core.state_manager
    
    def initialize_agent(self) -> bool:
        """
        Initialize safety validator using modular core component.
        
        Uses SafetyValidationCore for agent registration and initialization
        with proper LTMC tool integration.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        return self.core.initialize_agent()
    
    def validate_removal_safety(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that legacy code can be safely removed.
        
        Uses SafetyValidationEngine for comprehensive validation with
        ALL 11 LTMC tools integration and safety scoring system.
        
        Args:
            analysis_data: Results from LegacyCodeAnalyzer containing legacy decorators and functional tools
            
        Returns:
            Dict[str, Any]: Comprehensive validation report with safety score and recommendations
        """
        return self.engine.validate_removal_safety(analysis_data)
    
    def create_removal_plan(self) -> Dict[str, Any]:
        """
        Create structured removal plan based on validation results.
        
        Uses RemovalPlanManager for comprehensive plan creation with
        blueprint_action, todo_action, and memory_action integration.
        
        Returns:
            Dict[str, Any]: Structured removal plan with tasks and timeline
        """
        return self.plan_manager.create_removal_plan()
    
    # Expose validation and plan results for compatibility
    @property
    def validation_report(self) -> Dict[str, Any]:
        """Access validation report from core component."""
        return getattr(self.core, 'validation_report', {})
    
    @property
    def safety_checks(self) -> List[Dict[str, Any]]:
        """Access safety checks from core component."""
        return getattr(self.core, 'safety_checks', [])
    
    @property
    def removal_plan(self) -> Dict[str, Any]:
        """Access removal plan from core component."""
        return getattr(self.core, 'removal_plan', {})