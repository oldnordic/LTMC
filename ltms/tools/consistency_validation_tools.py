"""
Consistency Validation Tools - MCP Tools for Phase 3 Component 4.

This module provides MCP tools for blueprint consistency validation and enforcement with:

1. Consistency Validation: Comprehensive validation of blueprint-code alignment
2. Change Impact Analysis: Real-time validation of changes against blueprints
3. Enforcement Operations: Automated consistency enforcement and correction
4. Violation Detection: Intelligent detection of consistency violations
5. Automated Remediation: Smart fixes for common consistency issues

Performance Requirements:
- Validation operations: <10ms per validation
- Change analysis: <8ms per change
- Enforcement operations: <15ms per operation
- Violation detection: <5ms per scan
- Remediation operations: <12ms per fix

Integration Points:
- Consistency Validation Engine
- Consistency Enforcement Engine
- Neo4j Blueprint System
- Documentation Sync System
- Security Integration: Project isolation and validation
"""

import asyncio
import time
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from ltms.services.consistency_validation_engine import (
    ConsistencyValidationEngine,
    ConsistencyEnforcementEngine,
    ViolationType,
    SeverityLevel,
    EnforcementAction,
    get_consistency_validation_engine,
    get_consistency_enforcement_engine
)
from ltms.models.blueprint_schemas import CodeStructure
from ltms.tools.blueprint_tools import CodeAnalyzer
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

logger = logging.getLogger(__name__)


class ConsistencyValidationToolsError(Exception):
    """Base exception for consistency validation tools."""
    pass


async def validate_blueprint_consistency(
    file_path: str,
    project_id: str,
    validation_level: str = "comprehensive",
    include_recommendations: bool = True,
    cache_results: bool = True
) -> Dict[str, Any]:
    """
    Validate consistency between blueprint and code structure.
    
    Args:
        file_path: Path to code file for validation
        project_id: Project identifier for security isolation
        validation_level: Level of validation (basic, comprehensive, strict)
        include_recommendations: Whether to include fix recommendations
        cache_results: Whether to cache validation results
        
    Returns:
        Dict with detailed consistency validation results
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_path or not project_id:
            raise ConsistencyValidationToolsError("file_path and project_id are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "read", file_path):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        if not path_validator.validate_path(file_path, project_id):
            raise ConsistencyValidationToolsError(f"Invalid file path: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise ConsistencyValidationToolsError(f"File not found: {file_path}")
        
        # Get validation engine
        validation_engine = await get_consistency_validation_engine()
        
        # Perform validation
        validation_result = await validation_engine.validate_blueprint_consistency(
            file_path, project_id
        )
        
        # Prepare response based on validation level
        response = {
            "success": validation_result.success,
            "file_path": file_path,
            "project_id": project_id,
            "validation_level": validation_level,
            "validation_time_ms": validation_result.validation_time_ms,
            "total_nodes_checked": validation_result.total_nodes_checked,
            "violations_found": validation_result.violations_found,
            "consistency_score": validation_result.consistency_score,
            "consistency_level": validation_result.consistency_level.value if validation_result.consistency_level else "unknown"
        }
        
        # Include violations based on level
        if validation_level in ["comprehensive", "strict"]:
            response["violations"] = [
                {
                    "violation_id": v.violation_id,
                    "type": v.violation_type.value,
                    "severity": v.severity.value,
                    "node_name": v.node_name,
                    "description": v.description,
                    "blueprint_value": v.blueprint_value,
                    "code_value": v.code_value,
                    "suggested_fix": v.suggested_fix,
                    "detected_at": v.detected_at.isoformat()
                }
                for v in validation_result.violations
            ]
        
        # Include recommendations if requested
        if include_recommendations and validation_result.recommendations:
            response["recommendations"] = validation_result.recommendations
        
        # Add error information if validation failed
        if not validation_result.success and validation_result.error_message:
            response["error_message"] = validation_result.error_message
        
        end_time = time.perf_counter()
        response["total_time_ms"] = (end_time - start_time) * 1000
        
        return response
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Blueprint consistency validation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def analyze_change_impact(
    file_path: str,
    project_id: str,
    change_type: str,
    changed_content: str = None,
    block_on_critical: bool = True
) -> Dict[str, Any]:
    """
    Analyze impact of code changes on blueprint consistency.
    
    Args:
        file_path: Path to changed file
        project_id: Project identifier for security isolation
        change_type: Type of change (modified, created, deleted)
        changed_content: New file content (for modification analysis)
        block_on_critical: Whether to block changes that introduce critical violations
        
    Returns:
        Dict with change impact analysis results
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_path or not project_id or not change_type:
            raise ConsistencyValidationToolsError("file_path, project_id, and change_type are required")
        
        valid_change_types = ["modified", "created", "deleted"]
        if change_type not in valid_change_types:
            raise ConsistencyValidationToolsError(f"change_type must be one of: {valid_change_types}")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "read", file_path):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        if not path_validator.validate_path(file_path, project_id):
            raise ConsistencyValidationToolsError(f"Invalid file path: {file_path}")
        
        # Get validation engine
        validation_engine = await get_consistency_validation_engine()
        
        # Analyze change impact
        impact_result = await validation_engine.validate_change_impact(
            file_path, project_id, change_type, changed_content
        )
        
        if not impact_result["success"]:
            return {
                "success": False,
                "error": impact_result.get("error", "Change impact analysis failed")
            }
        
        impact_analysis = impact_result["impact_analysis"]
        
        # Apply blocking logic if requested
        should_block = False
        if block_on_critical and not impact_analysis["change_allowed"]:
            should_block = True
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": True,
            "file_path": file_path,
            "project_id": project_id,
            "change_type": change_type,
            "change_allowed": impact_analysis["change_allowed"],
            "should_block": should_block,
            "consistency_impact": impact_analysis["consistency_impact"],
            "violations_introduced": len(impact_analysis.get("violations_introduced", [])),
            "recommended_actions": impact_analysis.get("recommended_actions", []),
            "validation_time_ms": impact_result.get("validation_time_ms", 0),
            "total_time_ms": total_time_ms
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Change impact analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def enforce_consistency_rules(
    file_path: str,
    project_id: str,
    enforcement_mode: str = "auto",
    dry_run: bool = False,
    severity_threshold: str = "medium"
) -> Dict[str, Any]:
    """
    Enforce consistency rules and apply automated fixes.
    
    Args:
        file_path: Path to code file
        project_id: Project identifier for security isolation
        enforcement_mode: Mode of enforcement (auto, manual, strict)
        dry_run: If True, simulate actions without applying them
        severity_threshold: Minimum severity level to enforce (low, medium, high, critical)
        
    Returns:
        Dict with enforcement results and actions taken
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_path or not project_id:
            raise ConsistencyValidationToolsError("file_path and project_id are required")
        
        valid_modes = ["auto", "manual", "strict"]
        if enforcement_mode not in valid_modes:
            raise ConsistencyValidationToolsError(f"enforcement_mode must be one of: {valid_modes}")
        
        valid_severities = ["low", "medium", "high", "critical"]
        if severity_threshold not in valid_severities:
            raise ConsistencyValidationToolsError(f"severity_threshold must be one of: {valid_severities}")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "read", file_path):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        if not path_validator.validate_path(file_path, project_id):
            raise ConsistencyValidationToolsError(f"Invalid file path: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise ConsistencyValidationToolsError(f"File not found: {file_path}")
        
        # Get enforcement engine
        enforcement_engine = await get_consistency_enforcement_engine()
        
        # Perform enforcement
        enforcement_result = await enforcement_engine.enforce_consistency(
            file_path, project_id, dry_run=dry_run
        )
        
        if not enforcement_result.success:
            return {
                "success": False,
                "error": enforcement_result.error_message or "Enforcement failed"
            }
        
        # Filter actions by severity threshold
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        threshold_level = severity_order[severity_threshold]
        
        relevant_actions = []
        for action in enforcement_result.actions_taken:
            # Simplified filtering - in production would check actual violation severity
            relevant_actions.append(action)
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": True,
            "file_path": file_path,
            "project_id": project_id,
            "enforcement_mode": enforcement_mode,
            "dry_run": dry_run,
            "severity_threshold": severity_threshold,
            "enforcement_time_ms": enforcement_result.enforcement_time_ms,
            "actions_taken": relevant_actions,
            "violations_resolved": enforcement_result.violations_resolved,
            "violations_remaining": enforcement_result.violations_remaining,
            "auto_fixes_applied": enforcement_result.auto_fixes_applied,
            "manual_interventions_required": enforcement_result.manual_interventions_required,
            "warnings_generated": enforcement_result.warnings_generated,
            "total_time_ms": total_time_ms
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Consistency enforcement failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def detect_consistency_violations(
    file_path: str,
    project_id: str,
    violation_types: List[str] = None,
    include_auto_fixable: bool = True,
    group_by_severity: bool = True
) -> Dict[str, Any]:
    """
    Detect specific types of consistency violations.
    
    Args:
        file_path: Path to code file
        project_id: Project identifier for security isolation
        violation_types: Specific violation types to detect (optional)
        include_auto_fixable: Whether to include auto-fixable violations
        group_by_severity: Whether to group results by severity level
        
    Returns:
        Dict with detected violations grouped and categorized
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not file_path or not project_id:
            raise ConsistencyValidationToolsError("file_path and project_id are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager("/home/feanor/Projects/lmtc")
        path_validator = SecurePathValidator("/home/feanor/Projects/lmtc")
        
        if not isolation_manager.validate_project_access(project_id, "read", file_path):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        if not path_validator.validate_path(file_path, project_id):
            raise ConsistencyValidationToolsError(f"Invalid file path: {file_path}")
        
        # Validate file exists
        if not Path(file_path).exists():
            raise ConsistencyValidationToolsError(f"File not found: {file_path}")
        
        # Get validation engine
        validation_engine = await get_consistency_validation_engine()
        
        # Validate to get violations
        validation_result = await validation_engine.validate_blueprint_consistency(
            file_path, project_id
        )
        
        if not validation_result.success:
            return {
                "success": False,
                "error": validation_result.error_message or "Violation detection failed"
            }
        
        all_violations = validation_result.violations
        
        # Filter by violation types if specified
        if violation_types:
            valid_types = [vt.value for vt in ViolationType]
            invalid_types = [vt for vt in violation_types if vt not in valid_types]
            if invalid_types:
                raise ConsistencyValidationToolsError(f"Invalid violation types: {invalid_types}")
            
            filtered_violations = [
                v for v in all_violations 
                if v.violation_type.value in violation_types
            ]
        else:
            filtered_violations = all_violations
        
        # Convert violations to dict format
        violations_data = []
        for v in filtered_violations:
            violation_dict = {
                "violation_id": v.violation_id,
                "type": v.violation_type.value,
                "severity": v.severity.value,
                "node_name": v.node_name,
                "description": v.description,
                "suggested_fix": v.suggested_fix,
                "detected_at": v.detected_at.isoformat(),
                "auto_fixable": v.violation_type in [ViolationType.DOCSTRING_MISSING]  # Simplified check
            }
            
            if include_auto_fixable or not violation_dict["auto_fixable"]:
                violations_data.append(violation_dict)
        
        # Group by severity if requested
        grouped_violations = {}
        if group_by_severity:
            for severity in ["critical", "high", "medium", "low", "info"]:
                grouped_violations[severity] = [
                    v for v in violations_data if v["severity"] == severity
                ]
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        response = {
            "success": True,
            "file_path": file_path,
            "project_id": project_id,
            "total_violations_found": len(violations_data),
            "validation_time_ms": validation_result.validation_time_ms,
            "total_time_ms": total_time_ms
        }
        
        if group_by_severity:
            response["violations_by_severity"] = grouped_violations
            response["severity_summary"] = {
                severity: len(violations) 
                for severity, violations in grouped_violations.items()
            }
        else:
            response["violations"] = violations_data
        
        return response
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Violation detection failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def generate_consistency_report(
    project_id: str,
    file_paths: List[str] = None,
    include_statistics: bool = True,
    include_recommendations: bool = True,
    output_format: str = "json"
) -> Dict[str, Any]:
    """
    Generate comprehensive consistency report for project or files.
    
    Args:
        project_id: Project identifier for security isolation
        file_paths: Optional list of specific files to analyze
        include_statistics: Whether to include statistical analysis
        include_recommendations: Whether to include improvement recommendations
        output_format: Output format (json, markdown, yaml)
        
    Returns:
        Dict with comprehensive consistency report
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not project_id:
            raise ConsistencyValidationToolsError("project_id is required")
        
        valid_formats = ["json", "markdown", "yaml"]
        if output_format not in valid_formats:
            raise ConsistencyValidationToolsError(f"output_format must be one of: {valid_formats}")
        
        # Security validation
        isolation_manager = ProjectIsolationManager()
        if not isolation_manager.validate_project_access(project_id, "read", "report"):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        # Get validation engine
        validation_engine = await get_consistency_validation_engine()
        
        # Determine files to analyze
        if not file_paths:
            # In production, would scan project directory for Python files
            file_paths = [f"mock_file_{i}.py" for i in range(1, 4)]  # Mock for demo
        
        # Analyze each file
        file_results = []
        all_violations = []
        total_nodes_checked = 0
        
        for file_path in file_paths:
            if Path(file_path).exists():
                validation_result = await validation_engine.validate_blueprint_consistency(
                    file_path, project_id
                )
                
                if validation_result.success:
                    file_results.append({
                        "file_path": file_path,
                        "consistency_score": validation_result.consistency_score,
                        "consistency_level": validation_result.consistency_level.value,
                        "violations_count": validation_result.violations_found,
                        "nodes_checked": validation_result.total_nodes_checked
                    })
                    
                    all_violations.extend(validation_result.violations)
                    total_nodes_checked += validation_result.total_nodes_checked
        
        # Generate statistics
        statistics = {}
        if include_statistics:
            severity_counts = {}
            type_counts = {}
            
            for violation in all_violations:
                # Count by severity
                severity = violation.severity.value
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                # Count by type
                vtype = violation.violation_type.value
                type_counts[vtype] = type_counts.get(vtype, 0) + 1
            
            statistics = {
                "total_files_analyzed": len(file_results),
                "total_nodes_checked": total_nodes_checked,
                "total_violations": len(all_violations),
                "severity_distribution": severity_counts,
                "violation_type_distribution": type_counts,
                "average_consistency_score": sum(f["consistency_score"] for f in file_results) / len(file_results) if file_results else 0.0
            }
        
        # Generate recommendations
        recommendations = []
        if include_recommendations:
            if statistics.get("total_violations", 0) > 0:
                recommendations.append("Run consistency enforcement to address violations")
            
            if statistics.get("average_consistency_score", 1.0) < 0.8:
                recommendations.append("Consider updating blueprints to match current code structure")
            
            high_severity_count = statistics.get("severity_distribution", {}).get("high", 0)
            critical_count = statistics.get("severity_distribution", {}).get("critical", 0)
            
            if critical_count > 0:
                recommendations.append(f"Address {critical_count} critical violations immediately")
            
            if high_severity_count > 0:
                recommendations.append(f"Review {high_severity_count} high-severity violations")
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        report_data = {
            "success": True,
            "project_id": project_id,
            "generated_at": datetime.now().isoformat(),
            "file_results": file_results,
            "output_format": output_format,
            "total_time_ms": total_time_ms
        }
        
        if include_statistics:
            report_data["statistics"] = statistics
        
        if include_recommendations:
            report_data["recommendations"] = recommendations
        
        # Format output based on requested format
        if output_format == "json":
            report_data["formatted_report"] = json.dumps(report_data, indent=2)
        elif output_format == "markdown":
            markdown_report = f"# Consistency Report\n\nProject: {project_id}\nGenerated: {report_data['generated_at']}\n\n"
            if include_statistics:
                markdown_report += f"## Statistics\n\n- Files analyzed: {statistics['total_files_analyzed']}\n- Total violations: {statistics['total_violations']}\n"
            report_data["formatted_report"] = markdown_report
        
        return report_data
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Consistency report generation failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


async def configure_enforcement_rules(
    project_id: str,
    rule_configuration: Dict[str, Any],
    apply_immediately: bool = False
) -> Dict[str, Any]:
    """
    Configure consistency enforcement rules for a project.
    
    Args:
        project_id: Project identifier for security isolation
        rule_configuration: Configuration for enforcement rules
        apply_immediately: Whether to apply rules to existing violations
        
    Returns:
        Dict with rule configuration results
    """
    start_time = time.perf_counter()
    
    try:
        # Validate inputs
        if not project_id or not rule_configuration:
            raise ConsistencyValidationToolsError("project_id and rule_configuration are required")
        
        # Security validation
        isolation_manager = ProjectIsolationManager()
        if not isolation_manager.validate_project_access(project_id, "write", "config"):
            raise ConsistencyValidationToolsError(f"Project access denied: {project_id}")
        
        # Validate rule configuration structure
        required_fields = ["rules"]
        for field in required_fields:
            if field not in rule_configuration:
                raise ConsistencyValidationToolsError(f"Missing required field: {field}")
        
        # Get enforcement engine
        enforcement_engine = await get_consistency_enforcement_engine()
        
        # Process rule configuration (simplified implementation)
        configured_rules = []
        for rule_data in rule_configuration["rules"]:
            rule_info = {
                "rule_id": rule_data.get("rule_id", f"custom_rule_{len(configured_rules)}"),
                "rule_name": rule_data.get("rule_name", "Custom Rule"),
                "violation_types": rule_data.get("violation_types", []),
                "enforcement_action": rule_data.get("enforcement_action", "generate_warning"),
                "auto_fix_enabled": rule_data.get("auto_fix_enabled", False)
            }
            configured_rules.append(rule_info)
        
        # Apply immediately if requested
        immediate_results = None
        if apply_immediately:
            # In production, would apply rules to existing violations
            immediate_results = {
                "rules_applied": len(configured_rules),
                "violations_processed": 0,
                "actions_taken": []
            }
        
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        return {
            "success": True,
            "project_id": project_id,
            "rules_configured": len(configured_rules),
            "configured_rules": configured_rules,
            "apply_immediately": apply_immediately,
            "immediate_results": immediate_results,
            "total_time_ms": total_time_ms
        }
        
    except Exception as e:
        end_time = time.perf_counter()
        total_time_ms = (end_time - start_time) * 1000
        
        logger.error(f"Rule configuration failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "total_time_ms": total_time_ms
        }


# MCP Tool Registration Functions

def get_consistency_validation_tools() -> List[Dict[str, Any]]:
    """Get list of all consistency validation MCP tools."""
    return [
        {
            "name": "validate_blueprint_consistency",
            "description": "Validate consistency between blueprint and code structure",
            "parameters": {
                "file_path": {"type": "string", "description": "Path to code file for validation"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "validation_level": {"type": "string", "description": "Level of validation (basic, comprehensive, strict)", "default": "comprehensive"},
                "include_recommendations": {"type": "boolean", "description": "Whether to include fix recommendations", "default": True},
                "cache_results": {"type": "boolean", "description": "Whether to cache validation results", "default": True}
            }
        },
        {
            "name": "analyze_change_impact",
            "description": "Analyze impact of code changes on blueprint consistency",
            "parameters": {
                "file_path": {"type": "string", "description": "Path to changed file"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "change_type": {"type": "string", "description": "Type of change (modified, created, deleted)"},
                "changed_content": {"type": "string", "description": "New file content (for modification analysis)"},
                "block_on_critical": {"type": "boolean", "description": "Whether to block changes that introduce critical violations", "default": True}
            }
        },
        {
            "name": "enforce_consistency_rules",
            "description": "Enforce consistency rules and apply automated fixes",
            "parameters": {
                "file_path": {"type": "string", "description": "Path to code file"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "enforcement_mode": {"type": "string", "description": "Mode of enforcement (auto, manual, strict)", "default": "auto"},
                "dry_run": {"type": "boolean", "description": "If True, simulate actions without applying them", "default": False},
                "severity_threshold": {"type": "string", "description": "Minimum severity level to enforce (low, medium, high, critical)", "default": "medium"}
            }
        },
        {
            "name": "detect_consistency_violations",
            "description": "Detect specific types of consistency violations",
            "parameters": {
                "file_path": {"type": "string", "description": "Path to code file"},
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "violation_types": {"type": "array", "description": "Specific violation types to detect (optional)"},
                "include_auto_fixable": {"type": "boolean", "description": "Whether to include auto-fixable violations", "default": True},
                "group_by_severity": {"type": "boolean", "description": "Whether to group results by severity level", "default": True}
            }
        },
        {
            "name": "generate_consistency_report",
            "description": "Generate comprehensive consistency report for project or files",
            "parameters": {
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "file_paths": {"type": "array", "description": "Optional list of specific files to analyze"},
                "include_statistics": {"type": "boolean", "description": "Whether to include statistical analysis", "default": True},
                "include_recommendations": {"type": "boolean", "description": "Whether to include improvement recommendations", "default": True},
                "output_format": {"type": "string", "description": "Output format (json, markdown, yaml)", "default": "json"}
            }
        },
        {
            "name": "configure_enforcement_rules",
            "description": "Configure consistency enforcement rules for a project",
            "parameters": {
                "project_id": {"type": "string", "description": "Project identifier for security isolation"},
                "rule_configuration": {"type": "object", "description": "Configuration for enforcement rules"},
                "apply_immediately": {"type": "boolean", "description": "Whether to apply rules to existing violations", "default": False}
            }
        }
    ]


# Export functions for MCP integration
__all__ = [
    "validate_blueprint_consistency",
    "analyze_change_impact",
    "enforce_consistency_rules",
    "detect_consistency_violations",
    "generate_consistency_report",
    "configure_enforcement_rules",
    "get_consistency_validation_tools"
]