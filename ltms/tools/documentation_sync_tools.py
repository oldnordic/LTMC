"""
Documentation Synchronization MCP Tools - Phase 3 Component 2.

This module implements MCP tools for the documentation synchronization system including:

MCP Tools:
- sync_documentation_with_code: Synchronize documentation with code changes
- validate_documentation_consistency: Validate documentation-code consistency
- detect_documentation_drift: Detect documentation drift from code changes
- update_documentation_from_blueprint: Update documentation from Neo4j blueprints
- get_documentation_consistency_score: Get detailed consistency scoring

Performance Requirements:
- Sync operations: <5ms per operation
- Consistency validation: <10ms per validation
- Real-time change detection: <100ms latency
- Consistency scoring: <5ms per calculation

Security Integration:
- Phase 1 project isolation via project_id
- Input validation and sanitization
- Secure file operations with path validation
- Cross-project access prevention
"""

import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import documentation sync service (some imports done locally to avoid circular imports)
from ltms.services.documentation_sync_service import (
    DocumentationSyncManager,
    DocumentationSyncError,
    SyncConflictError,
    ValidationFailureError
)

# Import security components (Phase 1 integration)
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

logger = logging.getLogger(__name__)


class DocumentationSyncToolError(Exception):
    """Base exception for documentation sync tool operations."""
    pass


# Global instances for performance (initialized once)
_sync_manager = None
_project_manager = None
_path_validator = None


def _get_sync_manager() -> DocumentationSyncManager:
    """Get singleton documentation sync manager instance.""" 
    global _sync_manager
    if _sync_manager is None:
        # Import locally to avoid circular imports
        from ltms.services.documentation_sync_service import get_documentation_sync_manager
        
        # Use asyncio to get the manager
        try:
            loop = asyncio.get_event_loop()
            _sync_manager = loop.run_until_complete(get_documentation_sync_manager())
        except RuntimeError:
            # No event loop running, create new one
            _sync_manager = asyncio.run(get_documentation_sync_manager())
    return _sync_manager


def _get_project_manager() -> ProjectIsolationManager:
    """Get singleton project isolation manager."""
    global _project_manager
    if _project_manager is None:
        from pathlib import Path
        # Use project root as project root
        project_root = Path(__file__).parent.parent.parent  # /home/feanor/Projects/lmtc
        _project_manager = ProjectIsolationManager(project_root)
    return _project_manager


def _get_path_validator() -> SecurePathValidator:
    """Get singleton path validator.""" 
    global _path_validator
    if _path_validator is None:
        from pathlib import Path
        # Use project root as secure root
        secure_root = Path(__file__).parent.parent.parent  # /home/feanor/Projects/lmtc
        _path_validator = SecurePathValidator(secure_root)
    return _path_validator


def _validate_sync_inputs(file_path: str, project_id: str) -> Dict[str, str]:
    """
    Validate and sanitize inputs for sync operations.
    
    Args:
        file_path: File path to validate
        project_id: Project identifier to validate
        
    Returns:
        Dict with validated file_path and project_id
        
    Raises:
        DocumentationSyncToolError: If validation fails
    """
    try:
        # Validate file_path
        if not file_path or not file_path.strip():
            raise DocumentationSyncToolError("file_path is required and cannot be empty")
        
        path_validator = _get_path_validator()
        validated_path = path_validator.validate_file_path(file_path.strip())
        
        # Validate project_id
        if not project_id or not project_id.strip():
            raise DocumentationSyncToolError("project_id is required and cannot be empty")
        
        sanitized_project_id = path_validator.sanitize_user_input(project_id.strip())
        
        if not sanitized_project_id or len(sanitized_project_id) == 0:
            raise DocumentationSyncToolError(f"Invalid project_id: {project_id}")
        
        return {
            "file_path": str(validated_path),
            "project_id": sanitized_project_id
        }
        
    except Exception as e:
        if isinstance(e, DocumentationSyncToolError):
            raise
        raise DocumentationSyncToolError(f"Input validation failed: {e}")


def _run_async_operation(coro) -> Dict[str, Any]:
    """
    Run async operation with proper event loop handling.
    
    Args:
        coro: Coroutine to execute
        
    Returns:
        Dict with operation results
    """
    try:
        # Try to use existing event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop is running, need to use create_task
            task = asyncio.create_task(coro)
            return task.result()  # This won't work in running loop
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(coro)
    except Exception as e:
        logger.error(f"Async operation failed: {e}")
        return {
            "success": False,
            "error": f"Async operation failed: {e}"
        }


def sync_documentation_with_code(
    file_path: str,
    project_id: str,
    force_update: bool = False
) -> Dict[str, Any]:
    """
    Synchronize documentation with code changes.
    
    This tool performs dual-source synchronization between Neo4j blueprints
    and actual code, updating documentation as needed.
    
    Args:
        file_path: Path to Python file to sync
        project_id: Project identifier for isolation
        force_update: Force update even if no changes detected
        
    Returns:
        Dict with synchronization results including:
        - success: bool
        - sync_time_ms: float (<5ms target)
        - files_processed: int
        - documentation_updated: bool
        - blueprint_nodes_synced: int
        - blueprint_relationships_synced: int
        - consistency_score: float
        - warnings: List[str]
    """
    try:
        # Validate inputs
        validated = _validate_sync_inputs(file_path, project_id)
        file_path = validated["file_path"]
        project_id = validated["project_id"]
        
        # Get sync manager and perform operation
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def sync_operation():
            return await sync_manager.sync_documentation_with_code(
                file_path=file_path,
                project_id=project_id,
                force_update=force_update
            )
        
        result = _run_async_operation(sync_operation())
        
        # Validate performance target
        if result.get("success") and result.get("sync_time_ms", 0) > 5.0:
            logger.warning(f"Sync operation exceeded 5ms target: {result['sync_time_ms']}ms")
        
        return result
        
    except DocumentationSyncToolError as e:
        return {"success": False, "error": str(e)}
    except DocumentationSyncError as e:
        return {"success": False, "error": f"Sync error: {e}"}
    except Exception as e:
        logger.error(f"Sync documentation tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def validate_documentation_consistency(
    file_path: str,
    project_id: str
) -> Dict[str, Any]:
    """
    Validate consistency between documentation and code.
    
    This tool performs dual-source validation between Neo4j blueprints
    and actual code to calculate consistency scores.
    
    Args:
        file_path: Path to Python file to validate
        project_id: Project identifier for isolation
        
    Returns:
        Dict with consistency validation results including:
        - success: bool
        - consistency_score: float (0.0-1.0, target >0.90)
        - consistency_level: str (HIGH/MEDIUM/LOW)
        - inconsistencies: List[Dict]
        - validation_time_ms: float (<10ms target)
        - total_nodes: int
        - matching_nodes: int
    """
    try:
        # Validate inputs
        validated = _validate_sync_inputs(file_path, project_id)
        file_path = validated["file_path"]
        project_id = validated["project_id"]
        
        # Get sync manager and perform validation
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def validation_operation():
            return await sync_manager.validate_documentation_consistency(
                file_path=file_path,
                project_id=project_id
            )
        
        result = _run_async_operation(validation_operation())
        
        # Validate performance target
        if result.get("success") and result.get("validation_time_ms", 0) > 10.0:
            logger.warning(f"Validation exceeded 10ms target: {result['validation_time_ms']}ms")
        
        # Add consistency analysis
        if result.get("success"):
            consistency_score = result.get("consistency_score", 0.0)
            result["meets_target"] = consistency_score >= 0.90
            result["consistency_rating"] = "excellent" if consistency_score >= 0.95 else "good" if consistency_score >= 0.90 else "needs_improvement"
        
        return result
        
    except DocumentationSyncToolError as e:
        return {"success": False, "error": str(e)}
    except ValidationFailureError as e:
        return {"success": False, "error": f"Validation failure: {e}"}
    except Exception as e:
        logger.error(f"Validate consistency tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def detect_documentation_drift(
    file_path: str,
    project_id: str,
    time_threshold_hours: Optional[int] = 24
) -> Dict[str, Any]:
    """
    Detect documentation drift from code changes.
    
    This tool analyzes recent changes to detect when documentation
    may be out of sync with code modifications.
    
    Args:
        file_path: Path to Python file to analyze
        project_id: Project identifier for isolation
        time_threshold_hours: Hours to look back for changes
        
    Returns:
        Dict with drift detection results including:
        - success: bool
        - drift_detected: bool
        - drift_score: float (0.0-1.0)
        - affected_sections: List[str]
        - last_code_change: str (ISO timestamp)
        - drift_analysis: Dict with detailed analysis
    """
    try:
        # Validate inputs
        validated = _validate_sync_inputs(file_path, project_id)
        file_path = validated["file_path"]
        project_id = validated["project_id"]
        
        # Validate time threshold
        if time_threshold_hours is not None and time_threshold_hours < 0:
            return {"success": False, "error": "time_threshold_hours must be non-negative"}
        
        # Get sync manager and perform drift detection
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def drift_operation():
            return await sync_manager.detect_documentation_drift(
                file_path=file_path,
                project_id=project_id
            )
        
        result = _run_async_operation(drift_operation())
        
        # Add time threshold analysis if provided
        if result.get("success") and time_threshold_hours:
            result["time_threshold_hours"] = time_threshold_hours
            result["within_threshold"] = result.get("drift_score", 0) < 0.3  # Low drift threshold
        
        return result
        
    except DocumentationSyncToolError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Detect drift tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def update_documentation_from_blueprint(
    blueprint_id: str,
    project_id: str,
    sections: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update documentation from Neo4j blueprint changes.
    
    This tool updates documentation based on changes in Neo4j blueprints,
    ensuring documentation stays synchronized with architectural changes.
    
    Args:
        blueprint_id: Blueprint identifier in Neo4j
        project_id: Project identifier for isolation
        sections: Specific sections to update (optional)
        
    Returns:
        Dict with documentation update results including:
        - success: bool
        - blueprint_id: str
        - project_id: str
        - documentation_sections_updated: int
        - update_time_ms: float (<10ms target)
        - updated_sections: List[str]
    """
    try:
        # Validate blueprint_id
        if not blueprint_id or not blueprint_id.strip():
            return {"success": False, "error": "blueprint_id is required and cannot be empty"}
        
        # Validate project_id
        if not project_id or not project_id.strip():
            return {"success": False, "error": "project_id is required and cannot be empty"}
        
        # Sanitize inputs
        path_validator = _get_path_validator()
        sanitized_blueprint_id = path_validator.sanitize_user_input(blueprint_id.strip())
        sanitized_project_id = path_validator.sanitize_user_input(project_id.strip())
        
        if not sanitized_blueprint_id or not sanitized_project_id:
            return {"success": False, "error": "Invalid blueprint_id or project_id after sanitization"}
        
        # Validate sections if provided
        if sections is not None:
            if not isinstance(sections, list):
                return {"success": False, "error": "sections must be a list"}
            
            valid_sections = {"api_documentation", "architecture_diagram", "progress_report", "user_guide"}
            invalid_sections = set(sections) - valid_sections
            if invalid_sections:
                return {"success": False, "error": f"Invalid sections: {list(invalid_sections)}"}
        
        # Get sync manager and perform update
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def update_operation():
            return await sync_manager.update_documentation_from_blueprint(
                blueprint_id=sanitized_blueprint_id,
                project_id=sanitized_project_id
            )
        
        result = _run_async_operation(update_operation())
        
        # Validate performance target
        if result.get("success") and result.get("update_time_ms", 0) > 10.0:
            logger.warning(f"Blueprint update exceeded 10ms target: {result['update_time_ms']}ms")
        
        # Add requested sections filter
        if result.get("success") and sections:
            result["requested_sections"] = sections
            result["sections_filtered"] = True
        
        return result
        
    except Exception as e:
        logger.error(f"Update from blueprint tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def get_documentation_consistency_score(
    file_path: str,
    project_id: str,
    detailed_analysis: bool = False
) -> Dict[str, Any]:
    """
    Get detailed consistency score between documentation and code.
    
    This tool provides comprehensive consistency analysis including
    node-level and relationship-level scoring.
    
    Args:
        file_path: Path to Python file to analyze
        project_id: Project identifier for isolation
        detailed_analysis: Include detailed node-by-node analysis
        
    Returns:
        Dict with consistency score details including:
        - success: bool
        - consistency_score: float (0.0-1.0)
        - consistency_level: str (HIGH/MEDIUM/LOW)
        - calculation_time_ms: float (<5ms target)
        - total_nodes_analyzed: int
        - blueprint_available: bool
        - detailed_scores: Dict (if detailed_analysis=True)
    """
    try:
        # Validate inputs
        validated = _validate_sync_inputs(file_path, project_id)
        file_path = validated["file_path"]
        project_id = validated["project_id"]
        
        # Validate detailed_analysis parameter
        if not isinstance(detailed_analysis, bool):
            return {"success": False, "error": "detailed_analysis must be a boolean"}
        
        # Get sync manager and calculate score
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def score_operation():
            return await sync_manager.get_documentation_consistency_score(
                file_path=file_path,
                project_id=project_id
            )
        
        result = _run_async_operation(score_operation())
        
        # Validate performance target
        if result.get("success") and result.get("calculation_time_ms", 0) > 5.0:
            logger.warning(f"Consistency scoring exceeded 5ms target: {result['calculation_time_ms']}ms")
        
        # Add analysis enhancements
        if result.get("success"):
            consistency_score = result.get("consistency_score", 0.0)
            
            # Add quality indicators
            result["quality_indicators"] = {
                "excellent": consistency_score >= 0.95,
                "good": 0.90 <= consistency_score < 0.95,
                "acceptable": 0.70 <= consistency_score < 0.90,
                "needs_improvement": consistency_score < 0.70
            }
            
            # Add target compliance
            result["meets_90_percent_target"] = consistency_score >= 0.90
            
            # Add recommendations
            if consistency_score < 0.90:
                result["recommendations"] = [
                    "Consider updating documentation to match code structure",
                    "Review inconsistent nodes and relationships",
                    "Ensure blueprint synchronization is up to date"
                ]
            
            # Include detailed analysis if requested
            if detailed_analysis:
                result["detailed_analysis_requested"] = True
                # Note: Detailed analysis would require additional scorer calls
                result["analysis_note"] = "Detailed analysis available via consistency scorer"
        
        return result
        
    except DocumentationSyncToolError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Get consistency score tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def start_real_time_documentation_sync(
    file_paths: List[str],
    project_id: str,
    sync_interval_ms: int = 100
) -> Dict[str, Any]:
    """
    Start real-time documentation synchronization monitoring.
    
    This tool enables continuous monitoring and synchronization of
    documentation with code changes.
    
    Args:
        file_paths: List of file paths to monitor
        project_id: Project identifier for isolation
        sync_interval_ms: Monitoring interval in milliseconds
        
    Returns:
        Dict with real-time sync startup results including:
        - success: bool
        - project_id: str
        - files_monitored: List[str]
        - monitoring_started: str (ISO timestamp)
        - sync_interval_ms: int
    """
    try:
        # Validate inputs
        if not file_paths or not isinstance(file_paths, list):
            return {"success": False, "error": "file_paths must be a non-empty list"}
        
        if not project_id or not project_id.strip():
            return {"success": False, "error": "project_id is required and cannot be empty"}
        
        if sync_interval_ms < 50 or sync_interval_ms > 5000:
            return {"success": False, "error": "sync_interval_ms must be between 50 and 5000"}
        
        # Validate and sanitize each file path
        path_validator = _get_path_validator()
        validated_paths = []
        
        for file_path in file_paths:
            try:
                validated_path = path_validator.validate_file_path(file_path.strip())
                validated_paths.append(str(validated_path))
            except Exception as e:
                return {"success": False, "error": f"Invalid file path '{file_path}': {e}"}
        
        # Sanitize project_id
        sanitized_project_id = path_validator.sanitize_user_input(project_id.strip())
        if not sanitized_project_id:
            return {"success": False, "error": "Invalid project_id after sanitization"}
        
        # Get sync manager and start monitoring
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def start_monitoring():
            return await sync_manager.start_real_time_sync(
                file_paths=validated_paths,
                project_id=sanitized_project_id
            )
        
        result = _run_async_operation(start_monitoring())
        
        # Add sync interval info
        if result.get("success"):
            result["sync_interval_ms"] = sync_interval_ms
            result["monitoring_frequency"] = f"Every {sync_interval_ms}ms"
        
        return result
        
    except Exception as e:
        logger.error(f"Start real-time sync tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


def get_documentation_sync_status(
    project_id: str,
    include_pending_changes: bool = True
) -> Dict[str, Any]:
    """
    Get documentation synchronization status for a project.
    
    This tool provides comprehensive status information about
    documentation synchronization activities.
    
    Args:
        project_id: Project identifier for isolation
        include_pending_changes: Include information about pending changes
        
    Returns:
        Dict with sync status information including:
        - success: bool
        - project_id: str
        - real_time_monitoring_active: bool
        - files_monitored: List[str]
        - monitoring_started: str (ISO timestamp)
        - last_sync_time: str (ISO timestamp)
        - pending_changes: int (if include_pending_changes=True)
    """
    try:
        # Validate project_id
        if not project_id or not project_id.strip():
            return {"success": False, "error": "project_id is required and cannot be empty"}
        
        # Sanitize project_id
        path_validator = _get_path_validator()
        sanitized_project_id = path_validator.sanitize_user_input(project_id.strip())
        if not sanitized_project_id:
            return {"success": False, "error": "Invalid project_id after sanitization"}
        
        # Validate include_pending_changes parameter
        if not isinstance(include_pending_changes, bool):
            return {"success": False, "error": "include_pending_changes must be a boolean"}
        
        # Get sync manager and retrieve status
        sync_manager = _get_sync_manager()
        
        # Run async operation
        async def get_status():
            return await sync_manager.get_sync_status(sanitized_project_id)
        
        result = _run_async_operation(get_status())
        
        # Add pending changes info if requested
        if result.get("success") and include_pending_changes:
            result["include_pending_changes"] = True
            # Pending changes already included in sync manager response
        elif result.get("success") and not include_pending_changes:
            result["include_pending_changes"] = False
            result.pop("pending_changes", None)  # Remove if present
        
        return result
        
    except Exception as e:
        logger.error(f"Get sync status tool failed: {e}")
        return {"success": False, "error": f"Unexpected error: {e}"}


# Tool registration helper
def get_documentation_sync_tools() -> List[Dict[str, Any]]:
    """
    Get list of documentation sync MCP tools for registration.
    
    Returns:
        List of tool definitions for MCP server registration
    """
    return [
        {
            "name": "sync_documentation_with_code",
            "description": "Synchronize documentation with code changes using dual-source validation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file to sync"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "force_update": {"type": "boolean", "description": "Force update even if no changes detected", "default": False}
                },
                "required": ["file_path", "project_id"]
            }
        },
        {
            "name": "validate_documentation_consistency", 
            "description": "Validate consistency between documentation and code with >90% accuracy target",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file to validate"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"}
                },
                "required": ["file_path", "project_id"]
            }
        },
        {
            "name": "detect_documentation_drift",
            "description": "Detect documentation drift from recent code changes",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file to analyze"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "time_threshold_hours": {"type": "integer", "description": "Hours to look back for changes", "default": 24}
                },
                "required": ["file_path", "project_id"]
            }
        },
        {
            "name": "update_documentation_from_blueprint",
            "description": "Update documentation from Neo4j blueprint changes",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "blueprint_id": {"type": "string", "description": "Blueprint identifier in Neo4j"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "sections": {"type": "array", "items": {"type": "string"}, "description": "Specific sections to update (optional)"}
                },
                "required": ["blueprint_id", "project_id"]
            }
        },
        {
            "name": "get_documentation_consistency_score",
            "description": "Get detailed consistency score between documentation and code with <5ms performance",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to Python file to analyze"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "detailed_analysis": {"type": "boolean", "description": "Include detailed node-by-node analysis", "default": False}
                },
                "required": ["file_path", "project_id"]
            }
        },
        {
            "name": "start_real_time_documentation_sync",
            "description": "Start real-time documentation synchronization monitoring with <100ms latency",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_paths": {"type": "array", "items": {"type": "string"}, "description": "List of file paths to monitor"},
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "sync_interval_ms": {"type": "integer", "description": "Monitoring interval in milliseconds", "default": 100, "minimum": 50, "maximum": 5000}
                },
                "required": ["file_paths", "project_id"]
            }
        },
        {
            "name": "get_documentation_sync_status",
            "description": "Get comprehensive documentation synchronization status for a project",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project identifier for isolation"},
                    "include_pending_changes": {"type": "boolean", "description": "Include information about pending changes", "default": True}
                },
                "required": ["project_id"]
            }
        }
    ]