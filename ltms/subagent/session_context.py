"""
Session Context Management
Handles session context operations, inheritance, and similarity analysis.

File: ltms/subagent/session_context.py
Lines: ~96 (under 300 limit)
Purpose: Session context management and cross-session analysis
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List

from .session_core import SubagentSession

logger = logging.getLogger(__name__)


class SessionContextManager:
    """
    Session context management and analysis.
    
    Handles context inheritance, updates, and cross-session similarity
    analysis for intelligent context sharing.
    """
    
    def __init__(self, core_manager):
        self.core_manager = core_manager
    
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """
        Get session context including inherited context from parent sessions.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict containing combined session context
        """
        if session_id not in self.core_manager.active_sessions:
            return {}
        
        session = self.core_manager.active_sessions[session_id]
        combined_context = session.context.copy()
        
        # Inherit context from parent session
        if session.parent_session and session.parent_session in self.core_manager.active_sessions:
            parent_context = await self.get_session_context(session.parent_session)
            # Parent context has lower priority than session-specific context
            for key, value in parent_context.items():
                if key not in combined_context:
                    combined_context[key] = value
        
        return combined_context
    
    async def update_session_context(self, session_id: str, 
                                   context_updates: Dict[str, Any]) -> bool:
        """
        Update session context.
        
        Args:
            session_id: Session ID
            context_updates: Context updates to apply
            
        Returns:
            bool: Success status
        """
        if session_id not in self.core_manager.active_sessions:
            logger.error(f"Cannot update context for unknown session {session_id}")
            return False
        
        session = self.core_manager.active_sessions[session_id]
        session.context.update(context_updates)
        
        logger.debug(f"Updated context for session {session_id}")
        return True
    
    async def find_similar_sessions(self, session_id: str, 
                                  similarity_threshold: float = 0.7) -> List[str]:
        """
        Find sessions with similar characteristics and patterns.
        
        Args:
            session_id: Current session ID
            similarity_threshold: Similarity threshold (0.0-1.0)
            
        Returns:
            List of similar session IDs
        """
        if session_id not in self.core_manager.active_sessions:
            return []
        
        current_session = self.core_manager.active_sessions[session_id]
        similar_sessions = []
        
        # Simple similarity based on session type and tools used
        for other_id, other_session in self.core_manager.active_sessions.items():
            if other_id == session_id:
                continue
            
            similarity_score = self._calculate_session_similarity(
                current_session, other_session
            )
            
            if similarity_score >= similarity_threshold:
                similar_sessions.append(other_id)
        
        return similar_sessions
    
    def _calculate_session_similarity(self, session1: SubagentSession, 
                                    session2: SubagentSession) -> float:
        """
        Calculate similarity score between two sessions.
        
        Args:
            session1: First session
            session2: Second session
            
        Returns:
            float: Similarity score (0.0-1.0)
        """
        score = 0.0
        
        # Session type similarity (40% weight)
        if session1.session_type == session2.session_type:
            score += 0.4
        
        # Tool usage similarity (60% weight)
        if session1.tools_used and session2.tools_used:
            intersection = session1.tools_used & session2.tools_used
            union = session1.tools_used | session2.tools_used
            jaccard_similarity = len(intersection) / len(union) if union else 0
            score += 0.6 * jaccard_similarity
        
        return score
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old inactive sessions.
        
        Args:
            max_age_hours: Maximum age in hours for keeping sessions
            
        Returns:
            int: Number of sessions cleaned up
        """
        current_time = datetime.now(timezone.utc)
        sessions_to_remove = []
        
        for session_id, session in self.core_manager.active_sessions.items():
            session_start = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
            age_hours = (current_time - session_start).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                sessions_to_remove.append(session_id)
        
        # Clean up old sessions
        cleanup_count = 0
        for session_id in sessions_to_remove:
            await self.core_manager.end_session(session_id, success_score=0.0)
            cleanup_count += 1
        
        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} inactive sessions")
        
        return cleanup_count