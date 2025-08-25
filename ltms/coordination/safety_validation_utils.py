"""
Safety Validation Utility Functions
Pure utility functions for safety validation logic.

Extracted from safety_validator.py for smart modularization (300-line limit compliance).
Provides helper functions, recommendation logic, and utility functions with no LTMC dependencies.

Components:
- generate_next_steps: Generate context-appropriate next steps based on validation results
- create_removal_recommendations: Create specific removal recommendations for legacy decorators  
- find_functional_replacement: Find appropriate functional replacement for legacy tools
"""

from typing import Dict, Any, List


def generate_next_steps(recommendation: str, safety_checks: List[Dict[str, Any]]) -> List[str]:
    """
    Generate context-appropriate next steps based on validation results.
    
    Args:
        recommendation: Validation recommendation (APPROVED, APPROVED_WITH_CAUTION, REQUIRES_REVIEW)
        safety_checks: List of safety check results
        
    Returns:
        List[str]: Context-appropriate next steps
    """
    next_steps = []
    
    if recommendation == "APPROVED":
        next_steps.extend([
            "Proceed with legacy removal execution",
            "Create system backup before removal",
            "Execute removal tasks in sequence"
        ])
    elif recommendation == "APPROVED_WITH_CAUTION":
        next_steps.extend([
            "Review failed safety checks before proceeding",
            "Create comprehensive backup and rollback plan",
            "Execute removal with enhanced monitoring"
        ])
    else:  # REQUIRES_REVIEW or any other case
        next_steps.extend([
            "Address failed safety checks",
            "Perform additional analysis on high-risk components",
            "Re-validate after resolving safety concerns"
        ])
    
    # Add specific recommendations based on failed checks
    for check in safety_checks:
        if check['status'] == 'FAIL':
            if 'functional_tools' in check['check']:
                next_steps.append("Ensure all 11 LTMC consolidated tools are properly implemented")
            elif 'configuration' in check['check']:
                next_steps.append("Fix system configuration issues before proceeding")
    
    return next_steps


def create_removal_recommendations(analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Create specific removal recommendations for each legacy decorator.
    
    Args:
        analysis_data: Analysis results containing legacy decorators and functional tools
        
    Returns:
        List[Dict[str, Any]]: List of removal recommendations
    """
    recommendations = []
    
    legacy_decorators = analysis_data.get('legacy_decorators', [])
    functional_tools = analysis_data.get('functional_tools', [])
    
    for decorator in legacy_decorators:
        # Handle malformed decorator entries
        if not isinstance(decorator, dict) or 'name' not in decorator:
            continue
            
        recommendation = {
            "legacy_tool": decorator.get('name'),
            "file_location": f"{decorator.get('file', 'None')}:{decorator.get('line', 'None')}",
            "action": "remove",
            "replacement": find_functional_replacement(decorator.get('name'), functional_tools),
            "priority": "high" if decorator.get('name') in ['memory_tool', 'chat_tool'] else "medium"
        }
        recommendations.append(recommendation)
    
    return recommendations


def find_functional_replacement(legacy_name: str, functional_tools: List[Dict[str, Any]]) -> str:
    """
    Find the appropriate functional replacement for a legacy tool.
    
    Args:
        legacy_name: Name of the legacy tool to replace
        functional_tools: List of available functional tools
        
    Returns:
        str: Name of the functional replacement
    """
    # Mapping from legacy tools to functional replacements
    name_mappings = {
        'memory_tool': 'memory_action',
        'chat_tool': 'chat_action',
        'todo_tool': 'todo_action',
        'unix_tool': 'unix_action'
    }
    
    return name_mappings.get(legacy_name, 'consolidated_tool')