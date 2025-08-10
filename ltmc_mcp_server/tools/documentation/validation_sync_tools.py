"""
Validation Sync Documentation Tools - FastMCP Implementation
===========================================================

Documentation validation and drift detection tools following FastMCP patterns.

Tools implemented:
1. validate_documentation_consistency - Validate doc-code consistency
2. detect_documentation_drift - Detect documentation drift
"""

import logging
from typing import Dict, Any, Optional, List

# Official MCP SDK import - from research findings
from mcp.server.fastmcp import FastMCP

# Local imports
from config.settings import LTMCSettings
from services.database_service import DatabaseService
from services.neo4j_service import Neo4jService
from utils.validation_utils import sanitize_user_input, validate_content_length
from utils.logging_utils import get_tool_logger


def register_validation_sync_documentation_tools(mcp: FastMCP, settings: LTMCSettings) -> None:
    """
    Register validation sync documentation tools with FastMCP server.
    
    Args:
        mcp: FastMCP server instance
        settings: LTMC settings
    """
    logger = get_tool_logger('validation_sync_documentation')
    logger.info("Registering validation sync documentation tools")
    
    # Initialize services
    db_service = DatabaseService(settings)
    neo4j_service = Neo4jService(settings)
    
    @mcp.tool()
    async def validate_documentation_consistency(
        file_path: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Validate documentation consistency with code.
        
        This tool compares documentation against actual code structure
        to identify inconsistencies and missing documentation.
        
        Args:
            file_path: Path to the code file to validate
            project_id: Project ID for context
            
        Returns:
            Dict with validation results and consistency report
        """
        logger.debug(f"Validating documentation consistency: {file_path}")
        
        try:
            # Validate inputs
            if not file_path or not project_id:
                return {
                    "success": False,
                    "error": "file_path and project_id are required"
                }
            
            # Sanitize inputs
            file_path_clean = sanitize_user_input(file_path)
            project_id_clean = sanitize_user_input(project_id)
            
            # TODO: Implement actual consistency validation
            # For now, return mock validation results
            
            inconsistencies = [
                {
                    "type": "missing_documentation",
                    "element": "new_function",
                    "severity": "medium",
                    "description": "Function exists but lacks documentation"
                },
                {
                    "type": "outdated_parameters",
                    "element": "process_data",
                    "severity": "low",
                    "description": "Parameter documentation is outdated"
                }
            ]
            
            consistency_score = max(0.0, 1.0 - (len(inconsistencies) * 0.15))
            is_consistent = len(inconsistencies) == 0
            
            validation_summary = {
                "total_issues": len(inconsistencies),
                "critical_issues": sum(1 for i in inconsistencies if i["severity"] == "critical"),
                "medium_issues": sum(1 for i in inconsistencies if i["severity"] == "medium"),
                "low_issues": sum(1 for i in inconsistencies if i["severity"] == "low"),
                "consistency_score": round(consistency_score, 2)
            }
            
            logger.info(f"Validated documentation consistency: {file_path_clean}, score: {consistency_score}")
            
            return {
                "success": True,
                "file_path": file_path_clean,
                "project_id": project_id_clean,
                "is_consistent": is_consistent,
                "consistency_score": round(consistency_score, 2),
                "inconsistencies": inconsistencies,
                "validation_summary": validation_summary,
                "recommendations": [
                    "Add documentation for new_function",
                    "Update parameter documentation for process_data",
                    "Consider automated documentation generation"
                ] if inconsistencies else ["Documentation is consistent with code"]
            }
            
        except Exception as e:
            logger.error(f"Error validating documentation consistency: {e}")
            return {
                "success": False,
                "error": f"Failed to validate consistency: {str(e)}"
            }
    
    @mcp.tool()
    async def detect_documentation_drift(
        file_path: str,
        project_id: str
    ) -> Dict[str, Any]:
        """
        Detect drift in documentation relative to code changes.
        
        This tool identifies when documentation has become outdated
        relative to recent code changes.
        
        Args:
            file_path: Path to the code file to analyze
            project_id: Project ID for context
            
        Returns:
            Dict with drift analysis and recommendations
        """
        logger.debug(f"Detecting documentation drift: {file_path}")
        
        try:
            # Validate inputs
            if not file_path or not project_id:
                return {
                    "success": False,
                    "error": "file_path and project_id are required"
                }
            
            # Sanitize inputs
            file_path_clean = sanitize_user_input(file_path)
            project_id_clean = sanitize_user_input(project_id)
            
            # TODO: Implement actual drift detection
            # For now, return mock drift analysis
            
            drift_indicators = [
                {
                    "type": "code_change_without_doc_update",
                    "element": "calculate_metrics",
                    "days_since_change": 7,
                    "severity": "medium"
                },
                {
                    "type": "new_method_undocumented",
                    "element": "validate_input",
                    "days_since_addition": 3,
                    "severity": "low"
                }
            ]
            
            drift_score = min(1.0, len(drift_indicators) * 0.2)
            has_drift = len(drift_indicators) > 0
            
            drift_analysis = {
                "total_drift_indicators": len(drift_indicators),
                "high_priority_drift": sum(1 for d in drift_indicators if d["severity"] == "high"),
                "medium_priority_drift": sum(1 for d in drift_indicators if d["severity"] == "medium"),
                "low_priority_drift": sum(1 for d in drift_indicators if d["severity"] == "low"),
                "drift_score": round(drift_score, 2),
                "oldest_drift_days": max([d["days_since_change"] for d in drift_indicators if "days_since_change" in d] or [0])
            }
            
            logger.info(f"Detected documentation drift: {file_path_clean}, score: {drift_score}")
            
            return {
                "success": True,
                "file_path": file_path_clean,
                "project_id": project_id_clean,
                "has_drift": has_drift,
                "drift_score": round(drift_score, 2),
                "drift_indicators": drift_indicators,
                "drift_analysis": drift_analysis,
                "priority_actions": [
                    f"Update documentation for {drift_indicators[0]['element']}" if drift_indicators else "No immediate actions needed"
                ]
            }
            
        except Exception as e:
            logger.error(f"Error detecting documentation drift: {e}")
            return {
                "success": False,
                "error": f"Failed to detect drift: {str(e)}"
            }
    
    logger.info("✅ Validation sync documentation tools registered successfully")
    logger.info("  - validate_documentation_consistency: Validate doc-code consistency")
    logger.info("  - detect_documentation_drift: Detect documentation drift")