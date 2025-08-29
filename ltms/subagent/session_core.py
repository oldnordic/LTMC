"""
Core Session Management
Core session lifecycle management for Claude Code subagents.

File: ltms/subagent/session_core.py
Lines: ~200 (under 300 limit)
Purpose: Core session creation, management, and tracking
"""

import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from ..config.json_config_loader import get_config
from .intelligence_tracker import SubagentIntelligenceTracker

logger = logging.getLogger(__name__)


@dataclass
class SubagentSession:
    """Represents a Claude Code subagent session."""
    session_id: str
    parent_session: Optional[str]
    session_type: str  # 'analysis', 'implementation', 'testing', 'debugging'
    start_time: str
    end_time: Optional[str]
    context: Dict[str, Any]
    tools_used: set
    total_tool_calls: int
    total_tokens: int
    success_score: float
    intelligence_captured: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        data = asdict(self)
        data['tools_used'] = list(self.tools_used)  # Convert set to list for JSON
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubagentSession':
        """Create session from dictionary."""
        data['tools_used'] = set(data.get('tools_used', []))  # Convert list to set
        return cls(**data)


class CoreSessionManager:
    """
    Core session lifecycle management for Claude Code subagents.
    
    Handles session creation, tracking, and basic operations with
    real database integration and intelligence tracking.
    """
    
    def __init__(self):
        self.config = get_config()
        self.intelligence_tracker = SubagentIntelligenceTracker()
        self.active_sessions: Dict[str, SubagentSession] = {}
        self.session_hierarchy: Dict[str, List[str]] = {}  # parent -> children
        self._session_lock = asyncio.Lock()
    
    async def create_session(self, session_type: str = "analysis",
                           parent_session: Optional[str] = None,
                           initial_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new subagent session with intelligence tracking.
        
        Args:
            session_type: Type of session ('analysis', 'implementation', 'testing', 'debugging')
            parent_session: Parent session ID if this is a child session
            initial_context: Initial session context
            
        Returns:
            str: New session ID
        """
        async with self._session_lock:
            session_id = str(uuid.uuid4())
            
            # Validate parent session if specified
            if parent_session and parent_session not in self.active_sessions:
                logger.warning(f"Parent session {parent_session} not found, creating independent session")
                parent_session = None
            
            # Create session object
            session = SubagentSession(
                session_id=session_id,
                parent_session=parent_session,
                session_type=session_type,
                start_time=datetime.now(timezone.utc).isoformat(),
                end_time=None,
                context=initial_context or {},
                tools_used=set(),
                total_tool_calls=0,
                total_tokens=0,
                success_score=0.0,
                intelligence_captured=True
            )
            
            # Store in active sessions
            self.active_sessions[session_id] = session
            
            # Update session hierarchy
            if parent_session:
                if parent_session not in self.session_hierarchy:
                    self.session_hierarchy[parent_session] = []
                self.session_hierarchy[parent_session].append(session_id)
            
            # Initialize intelligence tracking
            session_metadata = {
                "session_type": session_type,
                "parent_session": parent_session,
                "initial_context": initial_context or {},
                "created_by": "CoreSessionManager"
            }
            
            success = await self.intelligence_tracker.track_session_start(
                session_id, session_metadata
            )
            
            if not success:
                logger.error(f"Failed to initialize intelligence tracking for {session_id}")
                session.intelligence_captured = False
            
            logger.info(f"Created subagent session {session_id} (type: {session_type})")
            return session_id
    
    async def end_session(self, session_id: str, 
                         success_score: float = 0.0,
                         final_context: Optional[Dict[str, Any]] = None) -> bool:
        """
        End subagent session with final intelligence capture.
        
        Args:
            session_id: Session to end
            success_score: Overall session success score (0.0-1.0)
            final_context: Final session context
            
        Returns:
            bool: Success status
        """
        async with self._session_lock:
            if session_id not in self.active_sessions:
                logger.error(f"Cannot end session {session_id}: not found")
                return False
            
            session = self.active_sessions[session_id]
            session.end_time = datetime.now(timezone.utc).isoformat()
            session.success_score = success_score
            
            if final_context:
                session.context.update(final_context)
            
            # Track session completion in intelligence system
            if session.intelligence_captured:
                await self.intelligence_tracker.track_session_end(
                    session_id, success_score
                )
            
            # End all child sessions
            child_sessions = self.session_hierarchy.get(session_id, [])
            for child_id in child_sessions:
                if child_id in self.active_sessions:
                    await self.end_session(child_id, success_score * 0.8)  # Inherit partial score
            
            # Remove from active sessions but keep in hierarchy for reference
            del self.active_sessions[session_id]
            
            logger.info(f"Ended subagent session {session_id} with score {success_score}")
            return True
    
    async def track_tool_usage(self, session_id: str, tool_name: str,
                              arguments: Dict[str, Any],
                              result: Any = None,
                              execution_time_ms: int = 0,
                              token_count: int = 0,
                              success: bool = True,
                              error_message: str = None) -> bool:
        """
        Track tool usage within a session.
        
        Args:
            session_id: Session ID
            tool_name: Name of tool used
            arguments: Tool arguments
            result: Tool result
            execution_time_ms: Execution time in milliseconds
            token_count: Estimated token count
            success: Success status
            error_message: Error message if failed
            
        Returns:
            bool: Success status
        """
        if session_id not in self.active_sessions:
            logger.error(f"Cannot track tool usage for unknown session {session_id}")
            return False
        
        session = self.active_sessions[session_id]
        session.tools_used.add(tool_name)
        session.total_tool_calls += 1
        session.total_tokens += token_count
        
        # Track in intelligence system
        if session.intelligence_captured:
            success_tracked = await self.intelligence_tracker.track_tool_invocation(
                session_id=session_id,
                tool_name=tool_name,
                arguments=arguments,
                execution_time_ms=execution_time_ms,
                token_count=token_count,
                success=success,
                error_message=error_message
            )
            
            if not success_tracked:
                logger.warning(f"Intelligence tracking failed for tool {tool_name} in session {session_id}")
        
        logger.debug(f"Tracked tool usage: {tool_name} in session {session_id}")
        return True
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict containing session information or None if not found
        """
        # Check active sessions first
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session_info = session.to_dict()
            session_info['status'] = 'active'
            
            # Add child sessions
            child_sessions = self.session_hierarchy.get(session_id, [])
            session_info['child_sessions'] = child_sessions
            
            return session_info
        
        # Check intelligence tracker for historical sessions
        if hasattr(self.intelligence_tracker, 'get_session_intelligence'):
            historical_info = await self.intelligence_tracker.get_session_intelligence(session_id)
            if historical_info and 'error' not in historical_info:
                historical_info['status'] = 'completed'
                return historical_info
        
        return None
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active sessions.
        
        Returns:
            List of active session information
        """
        active_sessions_info = []
        
        for session_id, session in self.active_sessions.items():
            session_info = session.to_dict()
            session_info['status'] = 'active'
            
            # Add child sessions
            child_sessions = self.session_hierarchy.get(session_id, [])
            session_info['child_sessions'] = child_sessions
            
            active_sessions_info.append(session_info)
        
        return active_sessions_info