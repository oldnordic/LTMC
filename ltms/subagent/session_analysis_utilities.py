"""
Session Analysis Utility Functions
Utility functions for session analysis and similarity calculations.

File: ltms/subagent/session_analysis_utilities.py
Lines: ~162 (under 300 limit)
Purpose: Analysis utilities and calculation functions for session data
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SessionAnalysisUtilities:
    """Utility functions for session analysis."""
    
    @staticmethod
    def calculate_session_similarity(session1: Dict[str, Any], session2: Dict[str, Any], 
                                   similarity_thresholds: Dict[str, float],
                                   context: Dict[str, Any] = None) -> float:
        """Calculate comprehensive similarity score between two sessions."""
        try:
            # Tool overlap similarity
            tools1 = set(session1["tools"])
            tools2 = set(session2["tools"])
            tool_overlap = len(tools1 & tools2) / max(len(tools1 | tools2), 1)
            
            # Pattern overlap similarity
            patterns1 = set(session1["patterns"])
            patterns2 = set(session2["patterns"])
            pattern_overlap = len(patterns1 & patterns2) / max(len(patterns1 | patterns2), 1)
            
            # Temporal similarity (sessions closer in time are more similar)
            time1 = datetime.fromisoformat(session1["start_time"])
            time2 = datetime.fromisoformat(session2["start_time"])
            time_diff_hours = abs((time1 - time2).total_seconds() / 3600)
            temporal_similarity = max(0, 1 - (time_diff_hours / (24 * 7)))  # Week normalization
            
            # Context similarity (if provided)
            context_similarity = 0.5  # Default neutral
            if context and session1.get("session_type") == session2.get("session_type"):
                context_similarity = 0.8
            
            # Calculate weighted similarity score
            similarity_score = (
                tool_overlap * similarity_thresholds['tool_overlap_weight'] +
                pattern_overlap * similarity_thresholds['pattern_overlap_weight'] +
                temporal_similarity * similarity_thresholds['temporal_weight'] +
                context_similarity * similarity_thresholds['context_weight']
            )
            
            return similarity_score
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    @staticmethod
    def sequences_match(seq1: List[str], seq2: List[str], exact_match: bool = False) -> bool:
        """Check if two tool sequences match (exact or fuzzy)."""
        if exact_match:
            return seq1 == seq2
        
        # Fuzzy matching - allow for small differences
        if len(seq1) != len(seq2):
            return False
        
        matches = sum(1 for a, b in zip(seq1, seq2) if a == b)
        return matches / len(seq1) >= 0.8  # 80% match threshold
    
    @staticmethod
    def calculate_frequency_trend(pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate frequency trend for pattern evolution analysis."""
        if len(pattern_history) < 2:
            return {"trend": "insufficient_data", "change_rate": 0.0}
        
        frequencies = [row["frequency"] for row in pattern_history]
        
        # Simple linear trend calculation
        n = len(frequencies)
        sum_x = sum(range(n))
        sum_y = sum(frequencies)
        sum_xy = sum(i * freq for i, freq in enumerate(frequencies))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if n * sum_x2 - sum_x * sum_x != 0 else 0
        
        return {
            "trend": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
            "change_rate": slope,
            "current_frequency": frequencies[-1],
            "initial_frequency": frequencies[0]
        }
    
    @staticmethod
    def calculate_effectiveness_trend(pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate effectiveness trend for pattern evolution analysis."""
        effectiveness_scores = [row["effectiveness_score"] for row in pattern_history if row["effectiveness_score"]]
        
        if not effectiveness_scores:
            return {"trend": "no_data", "average_effectiveness": 0.0}
        
        return {
            "trend": "improving" if len(effectiveness_scores) > 1 and effectiveness_scores[-1] > effectiveness_scores[0] else "stable",
            "average_effectiveness": sum(effectiveness_scores) / len(effectiveness_scores),
            "current_effectiveness": effectiveness_scores[-1] if effectiveness_scores else 0.0
        }
    
    @staticmethod
    def analyze_session_type_distribution(pattern_history: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of pattern across session types."""
        session_types = {}
        for row in pattern_history:
            session_type = row.get("session_type", "unknown")
            session_types[session_type] = session_types.get(session_type, 0) + 1
        
        return session_types
    
    @staticmethod
    def analyze_temporal_distribution(pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal distribution of pattern occurrences."""
        if not pattern_history:
            return {"analysis": "no_data"}
        
        timestamps = []
        for row in pattern_history:
            try:
                timestamps.append(datetime.fromisoformat(row["last_seen"]))
            except (ValueError, TypeError):
                continue
        
        if len(timestamps) < 2:
            return {"analysis": "insufficient_data"}
        
        # Calculate time intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        
        return {
            "analysis": "regular" if len(set(int(i/3600) for i in intervals)) <= 3 else "irregular",
            "average_interval_hours": avg_interval / 3600,
            "total_timespan_days": (timestamps[-1] - timestamps[0]).days,
            "pattern_frequency": "high" if avg_interval < 3600 else "medium" if avg_interval < 86400 else "low"
        }
    
    @staticmethod
    def calculate_success_correlation(pattern_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate correlation between pattern occurrence and session success."""
        success_scores = [row["success_score"] for row in pattern_history if row["success_score"] is not None]
        
        if not success_scores:
            return {"correlation": "no_data", "average_success": 0.0}
        
        avg_success = sum(success_scores) / len(success_scores)
        
        return {
            "correlation": "positive" if avg_success > 0.7 else "negative" if avg_success < 0.3 else "neutral",
            "average_success": avg_success,
            "sample_size": len(success_scores)
        }
    
    @staticmethod
    def calculate_tool_usage_patterns(tool_sequences: List[List[str]]) -> Dict[str, Any]:
        """Analyze tool usage patterns across multiple sessions."""
        if not tool_sequences:
            return {"analysis": "no_data"}
        
        # Calculate sequence similarities
        common_patterns = {}
        total_comparisons = 0
        similar_pairs = 0
        
        for i, seq1 in enumerate(tool_sequences):
            for j, seq2 in enumerate(tool_sequences[i+1:], i+1):
                total_comparisons += 1
                if SessionAnalysisUtilities.sequences_match(seq1, seq2):
                    similar_pairs += 1
                    
                    # Track common subsequences
                    min_len = min(len(seq1), len(seq2))
                    for k in range(2, min_len + 1):
                        subseq1 = tuple(seq1[:k])
                        subseq2 = tuple(seq2[:k])
                        if subseq1 == subseq2:
                            common_patterns[subseq1] = common_patterns.get(subseq1, 0) + 1
        
        similarity_rate = similar_pairs / total_comparisons if total_comparisons > 0 else 0
        
        # Find most common patterns
        top_patterns = sorted(common_patterns.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_sequences": len(tool_sequences),
            "similarity_rate": similarity_rate,
            "common_patterns": [{"pattern": list(pattern), "frequency": freq} for pattern, freq in top_patterns],
            "analysis": "high_similarity" if similarity_rate > 0.7 else "medium_similarity" if similarity_rate > 0.3 else "low_similarity"
        }