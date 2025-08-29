"""
Base class for LTMC MCP tools with Mind Graph intelligence tracking.
Standardizes error handling, logging, database access, and Mind Graph integration.

File: ltms/tools/core/mcp_base.py
Lines: ~290 (under 300 limit)
Purpose: Base class for all modular MCP tools with Mind Graph tracking
"""

import logging
import time
import sqlite3
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from uuid import uuid4

from .database_manager import DatabaseManager
from ltms.config.json_config_loader import get_config

logger = logging.getLogger(__name__)


class MCPToolBase(ABC):
    """Base class for all LTMC MCP tools with Mind Graph intelligence tracking.
    
    Provides standardized:
    - Database access through DatabaseManager
    - Error handling and logging
    - Performance monitoring
    - Configuration management from ltmc_config.json
    - Mind Graph intelligence tracking
    - Reasoning chain creation and management
    """
    
    def __init__(self, tool_name: str = None, agent_id: str = None):
        """Initialize MCP tool base with Mind Graph tracking.
        
        Args:
            tool_name: Name of the tool for logging and monitoring
            agent_id: Optional agent identifier for Mind Graph tracking
        """
        self.tool_name = tool_name or self.__class__.__name__
        self.agent_id = agent_id or f"mcp_{self.tool_name}_{uuid4().hex[:8]}"
        self.db = DatabaseManager()
        self.config = get_config()
        self.logger = logging.getLogger(f"{__name__}.{self.tool_name}")
        
        # Mind Graph tracking state
        self.current_session_id = None
        self.current_conversation_id = None
        self.reasoning_chain_id = None
        self.context_tags = []
        
        # Initialize Mind Graph agent if not exists
        self._ensure_mind_graph_agent()
        
        self.logger.info(f"Initialized {self.tool_name} with Mind Graph tracking (agent_id: {self.agent_id})")
    
    def _validate_action(self, action: str, valid_actions: list) -> bool:
        """Validate that action is in the list of valid actions.
        
        Args:
            action: Action string to validate
            valid_actions: List of valid action strings
            
        Returns:
            True if action is valid, False otherwise
        """
        if action not in valid_actions:
            self.logger.error(f"Invalid action '{action}' for {self.tool_name}. Valid actions: {valid_actions}")
            return False
        return True
    
    def _log_action_start(self, action: str, params: Dict[str, Any]) -> float:
        """Log the start of an action and return start time.
        
        Args:
            action: Action being executed
            params: Action parameters (sensitive data will be filtered)
            
        Returns:
            Start timestamp for performance monitoring
        """
        # Filter sensitive parameters for logging
        safe_params = self._filter_sensitive_params(params)
        self.logger.info(f"{self.tool_name}.{action} started with params: {safe_params}")
        return time.time()
    
    def _log_action_complete(self, action: str, start_time: float, success: bool = True, error: str = None):
        """Log the completion of an action with timing.
        
        Args:
            action: Action that was executed
            start_time: Start timestamp from _log_action_start
            success: Whether the action succeeded
            error: Error message if action failed
        """
        duration_ms = (time.time() - start_time) * 1000
        status = "completed" if success else "failed"
        
        if success:
            self.logger.info(f"{self.tool_name}.{action} {status} in {duration_ms:.2f}ms")
        else:
            self.logger.error(f"{self.tool_name}.{action} {status} in {duration_ms:.2f}ms: {error}")
    
    def _filter_sensitive_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Filter sensitive parameters for safe logging.
        
        Args:
            params: Original parameters dictionary
            
        Returns:
            Filtered parameters with sensitive data masked
        """
        sensitive_keys = ['password', 'token', 'key', 'secret', 'auth', 'credential']
        safe_params = {}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_params[key] = "***FILTERED***"
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings for readability
                safe_params[key] = value[:100] + "..."
            else:
                safe_params[key] = value
        
        return safe_params
    
    def _safe_json_dumps(self, data: Any) -> str:
        """Safely serialize data to JSON with Unicode support.
        
        Args:
            data: Data to serialize
            
        Returns:
            JSON string with proper Unicode handling
        """
        try:
            return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            # Fallback for non-serializable objects
            self.logger.warning(f"JSON serialization warning: {e}, using safe fallback")
            try:
                return json.dumps(str(data), ensure_ascii=False)
            except:
                return '"JSON_SERIALIZATION_ERROR"'
    
    def _create_success_response(self, data: Any = None, message: str = None) -> Dict[str, Any]:
        """Create standardized success response.
        
        Args:
            data: Response data
            message: Success message
            
        Returns:
            Standardized success response dictionary
        """
        response = {"success": True}
        
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
            
        return response
    
    def _create_error_response(self, error: str, error_code: str = None, details: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized error response.
        
        Args:
            error: Error message
            error_code: Optional error code
            details: Additional error details
            
        Returns:
            Standardized error response dictionary
        """
        response = {
            "success": False,
            "error": error
        }
        
        if error_code:
            response["error_code"] = error_code
        if details:
            response["details"] = details
            
        return response
    
    def _check_database_availability(self, required_systems: list = None) -> Dict[str, Any]:
        """Check if required database systems are available.
        
        Args:
            required_systems: List of required database systems
                             (sqlite, redis, neo4j, faiss)
            
        Returns:
            Status dictionary or error response
        """
        if required_systems is None:
            required_systems = ['sqlite']  # Default to SQLite
        
        availability = self.db.is_available()
        
        missing_systems = []
        for system in required_systems:
            if not availability.get(system, False):
                missing_systems.append(system)
        
        if missing_systems:
            error_msg = f"Required database systems unavailable: {missing_systems}"
            self.logger.error(error_msg)
            return self._create_error_response(
                error_msg,
                error_code="DATABASE_UNAVAILABLE",
                details={"missing_systems": missing_systems, "availability": availability}
            )
        
        return self._create_success_response(availability)
    
    def _ensure_mind_graph_agent(self):
        """Ensure Mind Graph agent exists in database using config."""
        try:
            db_path = self.config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if agent exists
                cursor.execute("""
                    SELECT agent_id FROM MindGraph_Agents 
                    WHERE agent_id = ?
                """, (self.agent_id,))
                
                if not cursor.fetchone():
                    # Create new agent
                    cursor.execute("""
                        INSERT INTO MindGraph_Agents 
                        (agent_id, agent_name, agent_type, created_at, session_count, total_changes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        self.agent_id,
                        f"MCP Tool: {self.tool_name}",
                        "mcp_tool",
                        datetime.now(timezone.utc).isoformat(),
                        0,
                        0
                    ))
                    
                    self.logger.debug(f"Created Mind Graph agent: {self.agent_id}")
                    
        except Exception as e:
            self.logger.error(f"Failed to ensure Mind Graph agent: {e}")
    
    def set_context(self, session_id: str = None, conversation_id: str = None, 
                   context_tags: List[str] = None):
        """Set context for Mind Graph tracking.
        
        Args:
            session_id: Current session identifier
            conversation_id: Current conversation identifier  
            context_tags: List of context tags for this interaction
        """
        self.current_session_id = session_id
        self.current_conversation_id = conversation_id
        self.context_tags = context_tags or []
        
        # Start new reasoning chain for this context
        self.reasoning_chain_id = f"chain_{uuid4().hex[:12]}"
        
        self.logger.debug(f"Set Mind Graph context: session={session_id}, conv={conversation_id}, chain={self.reasoning_chain_id}")
    
    def _track_mind_graph_change(self, change_type: str, change_summary: str, 
                                change_details: str = None, file_path: str = None,
                                lines_changed: int = None) -> str:
        """Track a change in the Mind Graph.
        
        Args:
            change_type: Type of change (code_edit, decision, analysis, etc.)
            change_summary: Brief summary of the change
            change_details: Detailed change information (optional)
            file_path: File path if change affects a file
            lines_changed: Number of lines changed if applicable
            
        Returns:
            Change ID for further tracking
        """
        try:
            change_id = f"change_{uuid4().hex[:12]}"
            db_path = self.config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO MindGraph_Changes 
                    (change_id, agent_id, change_type, file_path, lines_changed,
                     change_summary, change_details, timestamp, session_id, 
                     conversation_id, impact_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    change_id,
                    self.agent_id,
                    change_type,
                    file_path,
                    lines_changed,
                    change_summary,
                    change_details,
                    datetime.now(timezone.utc).isoformat(),
                    self.current_session_id,
                    self.current_conversation_id,
                    0.5  # Default impact score
                ))
                
                # Update agent change count
                cursor.execute("""
                    UPDATE MindGraph_Agents 
                    SET total_changes = total_changes + 1,
                        last_active_at = ?
                    WHERE agent_id = ?
                """, (datetime.now(timezone.utc).isoformat(), self.agent_id))
                
                self.logger.debug(f"Tracked Mind Graph change: {change_id} ({change_type})")
                return change_id
                
        except Exception as e:
            self.logger.error(f"Failed to track Mind Graph change: {e}")
            return None
    
    def _track_reasoning(self, reason_type: str, description: str, 
                        priority_level: int = 1, confidence_score: float = 1.0) -> str:
        """Track reasoning in the Mind Graph.
        
        Args:
            reason_type: Type of reasoning (analysis, decision, inference, etc.)
            description: Detailed reasoning description
            priority_level: Priority level (1-5, 1=highest)
            confidence_score: Confidence in reasoning (0.0-1.0)
            
        Returns:
            Reason ID for linking to changes
        """
        try:
            reason_id = f"reason_{uuid4().hex[:12]}"
            db_path = self.config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO MindGraph_Reasons
                    (reason_id, reason_type, description, created_at, 
                     priority_level, confidence_score, context, reasoning_chain_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    reason_id,
                    reason_type,
                    description,
                    datetime.now(timezone.utc).isoformat(),
                    priority_level,
                    confidence_score,
                    self._safe_json_dumps({"context_tags": self.context_tags, "agent_id": self.agent_id}),
                    self.reasoning_chain_id
                ))
                
                self.logger.debug(f"Tracked reasoning: {reason_id} ({reason_type})")
                return reason_id
                
        except Exception as e:
            self.logger.error(f"Failed to track reasoning: {e}")
            return None
    
    def _link_change_to_reason(self, change_id: str, reason_id: str, 
                              relationship_type: str = "MOTIVATED_BY") -> bool:
        """Link a change to its reasoning in the Mind Graph.
        
        Args:
            change_id: Change identifier
            reason_id: Reason identifier
            relationship_type: Type of relationship
            
        Returns:
            True if linking successful, False otherwise
        """
        try:
            relationship_id = f"rel_{uuid4().hex[:12]}"
            db_path = self.config.get_db_path()
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO MindGraph_Relationships
                    (relationship_id, source_type, source_id, target_type, target_id,
                     relationship_type, strength, confidence, created_at, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    relationship_id,
                    "change",
                    change_id,
                    "reason", 
                    reason_id,
                    relationship_type,
                    1.0,  # Full strength
                    1.0,  # Full confidence
                    datetime.now(timezone.utc).isoformat(),
                    True
                ))
                
                self.logger.debug(f"Linked change {change_id} to reason {reason_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to link change to reason: {e}")
            return False
    
    @abstractmethod
    def get_valid_actions(self) -> list:
        """Get list of valid actions for this tool.
        
        Returns:
            List of valid action strings
        """
        pass
    
    @abstractmethod
    async def execute_action(self, action: str, **params) -> Dict[str, Any]:
        """Execute the specified action with parameters.
        
        Args:
            action: Action to execute
            **params: Action parameters
            
        Returns:
            Action result dictionary
        """
        pass
    
    async def __call__(self, action: str, **params) -> Dict[str, Any]:
        """Make the tool callable with action-based interface with Mind Graph tracking.
        
        Args:
            action: Action to execute
            **params: Action parameters
            
        Returns:
            Action result dictionary with Mind Graph intelligence
        """
        start_time = self._log_action_start(action, params)
        
        # Set context if provided in params
        if 'session_id' in params or 'conversation_id' in params:
            self.set_context(
                session_id=params.get('session_id'),
                conversation_id=params.get('conversation_id'),
                context_tags=params.get('context_tags', [])
            )
        
        # Track reasoning for this action
        reason_id = self._track_reasoning(
            reason_type="mcp_action",
            description=f"Executing {self.tool_name}.{action} with parameters: {self._filter_sensitive_params(params)}",
            priority_level=2,
            confidence_score=1.0
        )
        
        try:
            # Validate action
            if not self._validate_action(action, self.get_valid_actions()):
                # Track failed validation
                change_id = self._track_mind_graph_change(
                    change_type="validation_failure",
                    change_summary=f"Invalid action '{action}' attempted on {self.tool_name}",
                    change_details=f"Valid actions: {self.get_valid_actions()}"
                )
                
                if change_id and reason_id:
                    self._link_change_to_reason(change_id, reason_id, "CAUSED_BY")
                
                return self._create_error_response(
                    f"Invalid action '{action}'",
                    error_code="INVALID_ACTION",
                    details={"valid_actions": self.get_valid_actions()}
                )
            
            # Execute action
            result = await self.execute_action(action, **params)
            
            # Track successful execution
            change_id = self._track_mind_graph_change(
                change_type="mcp_execution",
                change_summary=f"Successfully executed {self.tool_name}.{action}",
                change_details=f"Result success: {result.get('success', False)}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "MOTIVATED_BY")
            
            # Add Mind Graph metadata to result
            if isinstance(result, dict):
                result['mind_graph'] = {
                    'agent_id': self.agent_id,
                    'reasoning_chain_id': self.reasoning_chain_id,
                    'change_id': change_id,
                    'reason_id': reason_id,
                    'context_tags': self.context_tags
                }
            
            self._log_action_complete(action, start_time, success=True)
            return result
            
        except Exception as e:
            # Track execution failure
            change_id = self._track_mind_graph_change(
                change_type="execution_failure",
                change_summary=f"Failed to execute {self.tool_name}.{action}",
                change_details=f"Error: {str(e)}"
            )
            
            if change_id and reason_id:
                self._link_change_to_reason(change_id, reason_id, "CAUSED_BY")
            
            self._log_action_complete(action, start_time, success=False, error=str(e))
            return self._create_error_response(
                f"Action execution failed: {str(e)}",
                error_code="EXECUTION_ERROR",
                details={
                    "action": action, 
                    "params": self._filter_sensitive_params(params),
                    "mind_graph": {
                        "agent_id": self.agent_id,
                        "reasoning_chain_id": self.reasoning_chain_id,
                        "change_id": change_id,
                        "reason_id": reason_id
                    }
                }
            )