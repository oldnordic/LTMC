"""
Cross-Session Intelligence Linking
Links intelligence patterns across multiple subagent sessions for comprehensive learning.
File: ltms/subagent/cross_session_linker.py
Lines: ~295 (under 300 limit)
Purpose: Cross-session pattern linking and similarity analysis
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass

from .session_helpers import SessionDatabaseHelpers, SessionAnalysisUtilities

logger = logging.getLogger(__name__)

@dataclass
class SessionSimilarity:
    """Data class for session similarity analysis."""
    session_id: str
    similarity_score: float
    common_tools: List[str]
    common_patterns: List[str]
    temporal_distance: float

class CrossSessionLinker:
    """Advanced cross-session intelligence linking system."""
    
    def __init__(self):
        self.db_helpers = SessionDatabaseHelpers()
        self.utilities = SessionAnalysisUtilities()
        self.similarity_cache = {}
        self.cache_ttl = 3600  # 1 hour cache TTL
        self._similarity_thresholds = {
            'tool_overlap_weight': 0.4, 'pattern_overlap_weight': 0.3,
            'temporal_weight': 0.2, 'context_weight': 0.1, 'min_similarity_threshold': 0.3
        }
    
    async def update_patterns(self, session_id: str, tool_name: str, arguments: Dict[str, Any], patterns: List[Dict[str, Any]]):
        """Update cross-session pattern relationships and correlations."""
        try:
            # Update pattern relationships
            await self._update_pattern_relationships(session_id, patterns)
            
            # Update tool co-occurrence patterns
            await self._update_tool_cooccurrence(session_id, tool_name)
            
            # Update session similarity mappings
            await self._update_session_similarities(session_id)
            
            # Update temporal pattern evolution
            await self._update_temporal_patterns(session_id, tool_name, patterns)
            
            logger.debug(f"Cross-session patterns updated for session {session_id}")
            
        except Exception as e:
            logger.error(f"Cross-session pattern update error: {e}")
    
    async def find_similar_sessions(self, current_session: str, 
                                   context: Dict[str, Any] = None) -> List[SessionSimilarity]:
        """
        Find sessions with similar patterns, tools, and context.
        
        Args:
            current_session: Current session identifier
            context: Optional context for similarity matching
            
        Returns:
            List of similar sessions with similarity scores
        """
        try:
            # Check cache first
            cache_key = f"similar_{current_session}"
            if cache_key in self.similarity_cache:
                cached_time, cached_result = self.similarity_cache[cache_key]
                if (datetime.now().timestamp() - cached_time) < self.cache_ttl:
                    return cached_result
            
            similar_sessions = []
            
            # Get current session data using helper
            current_data = await self.db_helpers.get_session_comprehensive_data(current_session)
            if not current_data:
                return []
            
            # Get all other sessions for comparison using helper
            all_sessions = await self.db_helpers.get_all_sessions_summary(exclude_session=current_session)
            
            for session_data in all_sessions:
                similarity_score = self.utilities.calculate_session_similarity(
                    current_data, session_data, self._similarity_thresholds, context
                )
                
                similarity = SessionSimilarity(
                    session_id=session_data["session_id"],
                    similarity_score=similarity_score,
                    common_tools=list(set(current_data["tools"]) & set(session_data["tools"])),
                    common_patterns=list(set(current_data["patterns"]) & set(session_data["patterns"])),
                    temporal_distance=self._calculate_temporal_distance(
                        current_data["start_time"], session_data["start_time"]
                    )
                )
                
                if similarity.similarity_score >= self._similarity_thresholds['min_similarity_threshold']:
                    similar_sessions.append(similarity)
            
            # Sort by similarity score (descending)
            similar_sessions.sort(key=lambda x: x.similarity_score, reverse=True)
            
            # Cache the result
            self.similarity_cache[cache_key] = (datetime.now().timestamp(), similar_sessions[:10])
            
            return similar_sessions[:10]  # Return top 10 similar sessions
            
        except Exception as e:
            logger.error(f"Similar session search error: {e}")
            return []
    
    async def get_pattern_evolution(self, pattern_signature: str) -> Dict[str, Any]:
        """
        Analyze how a specific pattern has evolved across sessions.
        
        Args:
            pattern_signature: Pattern signature to analyze
            
        Returns:
            Pattern evolution analysis
        """
        try:
            # Get pattern evolution data using helper
            pattern_history = await self.db_helpers.get_pattern_evolution_data(pattern_signature)
            
            if not pattern_history:
                return {"error": f"Pattern {pattern_signature} not found"}
            
            # Analyze evolution trends using utility functions
            evolution_data = {
                "pattern_signature": pattern_signature,
                "total_occurrences": len(pattern_history),
                "frequency_trend": self.utilities.calculate_frequency_trend(pattern_history),
                "effectiveness_trend": self.utilities.calculate_effectiveness_trend(pattern_history),
                "session_type_distribution": self.utilities.analyze_session_type_distribution(pattern_history),
                "temporal_distribution": self.utilities.analyze_temporal_distribution(pattern_history),
                "success_correlation": self.utilities.calculate_success_correlation(pattern_history)
            }
            
            return evolution_data
                
        except Exception as e:
            logger.error(f"Pattern evolution analysis error: {e}")
            return {"error": str(e)}
    
    async def predict_next_tools(self, session_id: str, 
                                current_sequence: List[str]) -> List[Dict[str, Any]]:
        """
        Predict likely next tools based on current sequence and similar sessions.
        
        Args:
            session_id: Current session identifier
            current_sequence: Current tool usage sequence
            
        Returns:
            List of predicted tools with confidence scores
        """
        try:
            # Find similar sessions with matching sequences
            similar_sessions = await self.find_similar_sessions(session_id)
            
            # Analyze tool sequences from similar sessions
            next_tool_candidates = defaultdict(lambda: {"count": 0, "confidence": 0.0, "sessions": []})
            
            for similar_session in similar_sessions[:5]:  # Top 5 similar sessions
                session_tools = await self.db_helpers.get_session_tool_sequence(similar_session.session_id)
                
                # Find matching subsequences
                for i in range(len(session_tools) - len(current_sequence)):
                    subsequence = session_tools[i:i + len(current_sequence)]
                    
                    if self.utilities.sequences_match(subsequence, current_sequence):
                        # Get next tool(s) after this sequence
                        next_idx = i + len(current_sequence)
                        if next_idx < len(session_tools):
                            next_tool = session_tools[next_idx]
                            
                            next_tool_candidates[next_tool]["count"] += 1
                            next_tool_candidates[next_tool]["confidence"] += similar_session.similarity_score
                            next_tool_candidates[next_tool]["sessions"].append(similar_session.session_id)
            
            # Calculate final predictions
            predictions = []
            total_candidates = len(next_tool_candidates)
            
            for tool_name, data in next_tool_candidates.items():
                confidence = (data["confidence"] / len(data["sessions"])) * (data["count"] / total_candidates)
                
                predictions.append({
                    "tool_name": tool_name,
                    "confidence": min(confidence, 1.0),
                    "frequency": data["count"],
                    "supporting_sessions": len(data["sessions"]),
                    "evidence_sessions": data["sessions"][:3]  # Top 3 supporting sessions
                })
            
            # Sort by confidence
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            
            return predictions[:5]  # Return top 5 predictions
            
        except Exception as e:
            logger.error(f"Tool prediction error: {e}")
            return []
    
    # Private helper methods
    
    async def _update_pattern_relationships(self, session_id: str, 
                                          patterns: List[Dict[str, Any]]):
        """Update relationships between patterns within and across sessions."""
        try:
            # Create pattern co-occurrence matrix
            if len(patterns) > 1:
                for i, pattern1 in enumerate(patterns):
                    for pattern2 in patterns[i+1:]:
                        await self._record_pattern_cooccurrence(
                            pattern1.get('signature', ''),
                            pattern2.get('signature', ''),
                            session_id
                        )
        except Exception as e:
            logger.error(f"Pattern relationship update error: {e}")
    
    async def _update_tool_cooccurrence(self, session_id: str, current_tool: str):
        """Update tool co-occurrence patterns for predictive modeling."""
        try:
            recent_tools = await self.db_helpers.get_recent_session_tools(session_id, limit=5)
            
            for tool in recent_tools:
                if tool != current_tool:
                    await self._record_tool_cooccurrence(tool, current_tool, session_id)
                    
        except Exception as e:
            logger.error(f"Tool co-occurrence update error: {e}")
    
    async def _update_session_similarities(self, session_id: str):
        """Update session similarity mappings for faster retrieval."""
        # Invalidate cache for this session
        cache_keys_to_remove = [key for key in self.similarity_cache.keys() 
                               if session_id in key]
        for key in cache_keys_to_remove:
            del self.similarity_cache[key]
    
    async def _update_temporal_patterns(self, session_id: str, tool_name: str, 
                                       patterns: List[Dict[str, Any]]):
        """Update temporal evolution patterns."""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Record temporal pattern data
            for pattern in patterns:
                pattern_signature = pattern.get('signature', '')
                if pattern_signature:
                    await self._record_temporal_pattern(
                        pattern_signature, current_time, session_id
                    )
                    
        except Exception as e:
            logger.error(f"Temporal pattern update error: {e}")
    
    def _calculate_temporal_distance(self, time1_str: str, time2_str: str) -> float:
        """Calculate temporal distance between two session start times in hours."""
        try:
            time1 = datetime.fromisoformat(time1_str)
            time2 = datetime.fromisoformat(time2_str)
            return abs((time1 - time2).total_seconds() / 3600)
        except (ValueError, TypeError):
            return float('inf')
    
    async def _record_pattern_cooccurrence(self, pattern1_sig: str, pattern2_sig: str, session_id: str):
        """Record co-occurrence of patterns for relationship analysis."""
        # This would be implemented to track pattern relationships
        # For now, we log the co-occurrence
        logger.debug(f"Pattern co-occurrence: {pattern1_sig} <-> {pattern2_sig} in session {session_id}")
    
    async def _record_tool_cooccurrence(self, tool1: str, tool2: str, session_id: str):
        """Record co-occurrence of tools for predictive modeling."""
        # This would be implemented to track tool relationships
        # For now, we log the co-occurrence
        logger.debug(f"Tool co-occurrence: {tool1} -> {tool2} in session {session_id}")
    
    async def _record_temporal_pattern(self, pattern_signature: str, timestamp: datetime, session_id: str):
        """Record temporal occurrence of patterns."""
        # This would be implemented to track temporal patterns
        # For now, we log the temporal occurrence
        logger.debug(f"Temporal pattern: {pattern_signature} at {timestamp} in session {session_id}")