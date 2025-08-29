"""
Database Operations for Subagent Intelligence Tracking
Unified interface for database operations with modular architecture.

File: ltms/subagent/database_operations.py
Lines: ~100 (under 300 limit)
Purpose: Main interface for database operations with modular components
"""

import logging
from typing import Dict, Any, List, Optional

from .database_core import CoreIntelligenceDBOperations
from .pattern_storage import PatternStorageManager

logger = logging.getLogger(__name__)


class IntelligenceDBOperations:
    """
    Unified database operations for subagent intelligence tracking.
    
    Provides a clean interface to modular database components:
    - Core database operations for sessions and tool invocations
    - Pattern storage and management with frequency tracking
    """
    
    def __init__(self):
        self.core_db = CoreIntelligenceDBOperations()
        self.pattern_storage = PatternStorageManager()
    
    # Core database operations delegation
    async def store_session_start(self, session_record: Dict[str, Any]) -> bool:
        """Store session start record with atomic transaction."""
        return await self.core_db.store_session_start(session_record)
    
    async def store_tool_invocation(self, invocation_record: Dict[str, Any]) -> bool:
        """Store tool invocation record with session statistics update."""
        return await self.core_db.store_tool_invocation(invocation_record)
    
    async def update_session_end(self, session_id: str, success_score: float) -> bool:
        """Update session with end time and success score."""
        return await self.core_db.update_session_end(session_id, success_score)
    
    async def get_session_intelligence(self, session_id: str) -> Dict[str, Any]:
        """Retrieve comprehensive intelligence data for a session."""
        core_intelligence = await self.core_db.get_session_intelligence(session_id)
        
        # Add pattern information if core retrieval was successful
        if 'error' not in core_intelligence:
            patterns = await self.pattern_storage.get_patterns_by_session(session_id)
            core_intelligence['patterns'] = patterns
        
        return core_intelligence
    
    # Pattern storage operations delegation
    async def store_intelligence_patterns(self, patterns: List[Dict[str, Any]], 
                                         session_id: str) -> bool:
        """Store detected intelligence patterns with frequency tracking."""
        return await self.pattern_storage.store_intelligence_patterns(patterns, session_id)
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics across all sessions."""
        return await self.pattern_storage.get_pattern_statistics()
    
    async def get_patterns_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all patterns associated with a specific session."""
        return await self.pattern_storage.get_patterns_by_session(session_id)
    
    async def get_patterns_by_type(self, pattern_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get patterns of a specific type."""
        return await self.pattern_storage.get_patterns_by_type(pattern_type, limit)
    
    async def update_pattern_effectiveness(self, pattern_signature: str, 
                                         effectiveness_score: float) -> bool:
        """Update the effectiveness score for a pattern."""
        return await self.pattern_storage.update_pattern_effectiveness(
            pattern_signature, effectiveness_score
        )
    
    async def cleanup_old_patterns(self, max_age_days: int = 30) -> int:
        """Clean up old patterns that haven't been seen recently."""
        return await self.pattern_storage.cleanup_old_patterns(max_age_days)
    
    async def export_patterns(self, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """Export patterns for external analysis."""
        return await self.pattern_storage.export_patterns(pattern_type)