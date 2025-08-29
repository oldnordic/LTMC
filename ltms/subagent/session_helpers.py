"""
Session Analysis Helper Functions
Unified interface for session analysis with modular architecture.

File: ltms/subagent/session_helpers.py
Lines: ~50 (under 300 limit)
Purpose: Main interface for session analysis with modular components
"""

import logging
from typing import Dict, Any, List, Optional

from .session_database_helpers import SessionDatabaseHelpers
from .session_analysis_utilities import SessionAnalysisUtilities

logger = logging.getLogger(__name__)


class SessionHelpers:
    """
    Unified session analysis helper system.
    
    Provides a clean interface to modular session analysis components:
    - Database helpers for data retrieval and querying
    - Analysis utilities for calculations and pattern analysis
    """
    
    def __init__(self):
        self.db_helpers = SessionDatabaseHelpers()
        self.utilities = SessionAnalysisUtilities()
    
    # Database operations delegation
    async def get_all_sessions_summary(self, exclude_session: str = None) -> List[Dict[str, Any]]:
        """Get summary data for all sessions for similarity comparison."""
        return await self.db_helpers.get_all_sessions_summary(exclude_session)
    
    async def get_session_comprehensive_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive session data for similarity analysis."""
        return await self.db_helpers.get_session_comprehensive_data(session_id)
    
    async def get_session_tool_sequence(self, session_id: str) -> List[str]:
        """Get the complete tool sequence for a session."""
        return await self.db_helpers.get_session_tool_sequence(session_id)
    
    async def get_recent_session_tools(self, session_id: str, limit: int = 5) -> List[str]:
        """Get recent tools used in the session."""
        return await self.db_helpers.get_recent_session_tools(session_id, limit)
    
    async def get_pattern_evolution_data(self, pattern_signature: str) -> List[Dict[str, Any]]:
        """Get pattern evolution data for analysis."""
        return await self.db_helpers.get_pattern_evolution_data(pattern_signature)
    
    # Analysis utilities delegation
    def calculate_session_similarity(self, session1: Dict[str, Any], session2: Dict[str, Any], 
                                   similarity_thresholds: Dict[str, float],
                                   context: Dict[str, Any] = None) -> float:
        """Calculate comprehensive similarity score between two sessions."""
        return self.utilities.calculate_session_similarity(session1, session2, similarity_thresholds, context)
    
    def sequences_match(self, seq1: List[str], seq2: List[str], exact_match: bool = False) -> bool:
        """Check if two tool sequences match (exact or fuzzy)."""
        return self.utilities.sequences_match(seq1, seq2, exact_match)
    
    def calculate_frequency_trend(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate frequency trend for pattern evolution analysis."""
        return self.utilities.calculate_frequency_trend(pattern_history)
    
    def calculate_effectiveness_trend(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate effectiveness trend for pattern evolution analysis."""
        return self.utilities.calculate_effectiveness_trend(pattern_history)
    
    def analyze_session_type_distribution(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of pattern across session types."""
        return self.utilities.analyze_session_type_distribution(pattern_history)
    
    def analyze_temporal_distribution(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal distribution of pattern occurrences."""
        return self.utilities.analyze_temporal_distribution(pattern_history)
    
    def calculate_success_correlation(self, pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate correlation between pattern occurrence and session success."""
        return self.utilities.calculate_success_correlation(pattern_history)
    
    def calculate_tool_usage_patterns(self, tool_sequences: List[List[str]]) -> Dict[str, Any]:
        """Analyze tool usage patterns across multiple sessions."""
        return self.utilities.calculate_tool_usage_patterns(tool_sequences)


# Maintain backward compatibility by creating aliases
SessionDatabaseHelpers = SessionDatabaseHelpers
SessionAnalysisUtilities = SessionAnalysisUtilities