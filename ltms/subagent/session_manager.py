"""
Subagent Session Management System
Unified interface for comprehensive session management with modular architecture.

File: ltms/subagent/session_manager.py
Lines: ~100 (under 300 limit)
Purpose: Main interface for session management with modular components
"""

import logging
from typing import Dict, Any, List, Optional

from .session_core import CoreSessionManager
from .session_context import SessionContextManager
from .session_statistics import SessionStatisticsManager

logger = logging.getLogger(__name__)


class SubagentSessionManager:
    """
    Unified session management system for Claude Code subagents.
    
    Provides a clean interface to modular session management components:
    - Core session lifecycle management
    - Context management and inheritance
    - Statistics and performance analytics
    """
    
    def __init__(self):
        self.core_manager = CoreSessionManager()
        self.context_manager = SessionContextManager(self.core_manager)
        self.statistics_manager = SessionStatisticsManager(self.core_manager)
    
    # Core session operations
    async def create_session(self, session_type: str = "analysis",
                           parent_session: Optional[str] = None,
                           initial_context: Optional[Dict[str, Any]] = None) -> str:
        """Create new subagent session with intelligence tracking."""
        return await self.core_manager.create_session(session_type, parent_session, initial_context)
    
    async def end_session(self, session_id: str, 
                         success_score: float = 0.0,
                         final_context: Optional[Dict[str, Any]] = None) -> bool:
        """End subagent session with final intelligence capture."""
        return await self.core_manager.end_session(session_id, success_score, final_context)
    
    async def track_tool_usage(self, session_id: str, tool_name: str,
                              arguments: Dict[str, Any],
                              result: Any = None,
                              execution_time_ms: int = 0,
                              token_count: int = 0,
                              success: bool = True,
                              error_message: str = None) -> bool:
        """Track tool usage within a session."""
        return await self.core_manager.track_tool_usage(
            session_id, tool_name, arguments, result, 
            execution_time_ms, token_count, success, error_message
        )
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive session information."""
        return await self.core_manager.get_session_info(session_id)
    
    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active sessions."""
        return await self.core_manager.get_active_sessions()
    
    # Context management operations
    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context including inherited context from parent sessions."""
        return await self.context_manager.get_session_context(session_id)
    
    async def update_session_context(self, session_id: str, 
                                   context_updates: Dict[str, Any]) -> bool:
        """Update session context."""
        return await self.context_manager.update_session_context(session_id, context_updates)
    
    async def find_similar_sessions(self, session_id: str, 
                                  similarity_threshold: float = 0.7) -> List[str]:
        """Find sessions with similar characteristics and patterns."""
        return await self.context_manager.find_similar_sessions(session_id, similarity_threshold)
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old inactive sessions."""
        return await self.context_manager.cleanup_inactive_sessions(max_age_hours)
    
    # Statistics and analytics operations
    async def get_session_statistics(self) -> Dict[str, Any]:
        """Get comprehensive session statistics."""
        return await self.statistics_manager.get_session_statistics()
    
    async def get_session_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """Get detailed performance metrics for a specific session."""
        return await self.statistics_manager.get_session_performance_metrics(session_id)
    
    async def get_tool_usage_statistics(self) -> Dict[str, Any]:
        """Get comprehensive tool usage statistics across all sessions."""
        return await self.statistics_manager.get_tool_usage_statistics()
    
    async def get_session_type_analysis(self) -> Dict[str, Any]:
        """Analyze session types and their characteristics."""
        return await self.statistics_manager.get_session_type_analysis()
    
    async def generate_performance_insights(self) -> List[str]:
        """Generate actionable performance insights based on session data."""
        return await self.statistics_manager.generate_performance_insights()
    
    async def export_session_analytics(self) -> Dict[str, Any]:
        """Export comprehensive session analytics for external analysis."""
        return await self.statistics_manager.export_session_analytics()