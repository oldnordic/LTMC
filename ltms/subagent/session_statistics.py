"""
Session Statistics and Analytics
Provides comprehensive statistics and analytics for session management.

File: ltms/subagent/session_statistics.py
Lines: ~150 (under 300 limit)
Purpose: Session analytics, statistics, and performance monitoring
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class SessionStatisticsManager:
    """
    Session statistics and analytics manager.
    
    Provides comprehensive statistics, performance analytics,
    and insights for session management optimization.
    """
    
    def __init__(self, core_manager):
        self.core_manager = core_manager
        self.session_metrics: Dict[str, Any] = defaultdict(dict)
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive session statistics.
        
        Returns:
            Dict containing session statistics
        """
        stats = {
            "active_sessions": len(self.core_manager.active_sessions),
            "session_hierarchy_depth": max(
                len(children) for children in self.core_manager.session_hierarchy.values()
            ) if self.core_manager.session_hierarchy else 0,
            "sessions_by_type": {},
            "total_tool_calls": 0,
            "total_tokens": 0,
            "average_success_score": 0.0
        }
        
        # Calculate statistics from active sessions
        success_scores = []
        for session in self.core_manager.active_sessions.values():
            session_type = session.session_type
            stats["sessions_by_type"][session_type] = stats["sessions_by_type"].get(session_type, 0) + 1
            stats["total_tool_calls"] += session.total_tool_calls
            stats["total_tokens"] += session.total_tokens
            success_scores.append(session.success_score)
        
        if success_scores:
            stats["average_success_score"] = sum(success_scores) / len(success_scores)
        
        return stats
    
    async def get_session_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict containing performance metrics
        """
        if session_id not in self.core_manager.active_sessions:
            return {"error": "Session not found"}
        
        session = self.core_manager.active_sessions[session_id]
        
        # Calculate session duration
        from datetime import datetime, timezone
        start_time = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        duration_seconds = (current_time - start_time).total_seconds()
        
        # Calculate performance metrics
        metrics = {
            "session_id": session_id,
            "session_type": session.session_type,
            "duration_seconds": duration_seconds,
            "total_tool_calls": session.total_tool_calls,
            "unique_tools_used": len(session.tools_used),
            "total_tokens": session.total_tokens,
            "success_score": session.success_score,
            "tools_per_minute": (session.total_tool_calls / (duration_seconds / 60)) if duration_seconds > 0 else 0,
            "tokens_per_tool": session.total_tokens / session.total_tool_calls if session.total_tool_calls > 0 else 0,
            "intelligence_captured": session.intelligence_captured,
            "context_size": len(session.context),
            "has_parent": session.parent_session is not None,
            "child_count": len(self.core_manager.session_hierarchy.get(session_id, []))
        }
        
        return metrics
    
    async def get_tool_usage_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive tool usage statistics across all sessions.
        
        Returns:
            Dict containing tool usage statistics
        """
        tool_usage = defaultdict(int)
        tool_success = defaultdict(list)
        session_tool_combinations = []
        
        for session in self.core_manager.active_sessions.values():
            for tool in session.tools_used:
                tool_usage[tool] += 1
                tool_success[tool].append(session.success_score)
            
            # Track tool combinations
            if len(session.tools_used) > 1:
                tool_combo = sorted(list(session.tools_used))
                session_tool_combinations.append(tuple(tool_combo))
        
        # Calculate tool effectiveness
        tool_effectiveness = {}
        for tool, scores in tool_success.items():
            tool_effectiveness[tool] = {
                "usage_count": len(scores),
                "average_success_score": sum(scores) / len(scores) if scores else 0,
                "sessions_used": len(scores)
            }
        
        # Find common tool combinations
        from collections import Counter
        combo_counter = Counter(session_tool_combinations)
        common_combinations = combo_counter.most_common(10)
        
        return {
            "tool_usage_frequency": dict(tool_usage),
            "tool_effectiveness": tool_effectiveness,
            "most_used_tools": sorted(tool_usage.items(), key=lambda x: x[1], reverse=True)[:10],
            "common_tool_combinations": [
                {"tools": list(combo), "frequency": freq} 
                for combo, freq in common_combinations
            ],
            "total_unique_tools": len(tool_usage)
        }
    
    async def get_session_type_analysis(self) -> Dict[str, Any]:
        """
        Analyze session types and their characteristics.
        
        Returns:
            Dict containing session type analysis
        """
        type_stats = defaultdict(lambda: {
            "count": 0,
            "total_tools": 0,
            "total_tokens": 0,
            "success_scores": [],
            "durations": []
        })
        
        from datetime import datetime, timezone
        current_time = datetime.now(timezone.utc)
        
        for session in self.core_manager.active_sessions.values():
            stats = type_stats[session.session_type]
            stats["count"] += 1
            stats["total_tools"] += session.total_tool_calls
            stats["total_tokens"] += session.total_tokens
            stats["success_scores"].append(session.success_score)
            
            # Calculate duration
            start_time = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
            duration = (current_time - start_time).total_seconds()
            stats["durations"].append(duration)
        
        # Process statistics
        analysis = {}
        for session_type, stats in type_stats.items():
            analysis[session_type] = {
                "session_count": stats["count"],
                "average_tools_per_session": stats["total_tools"] / stats["count"] if stats["count"] > 0 else 0,
                "average_tokens_per_session": stats["total_tokens"] / stats["count"] if stats["count"] > 0 else 0,
                "average_success_score": sum(stats["success_scores"]) / len(stats["success_scores"]) if stats["success_scores"] else 0,
                "average_duration_seconds": sum(stats["durations"]) / len(stats["durations"]) if stats["durations"] else 0,
                "total_tools": stats["total_tools"],
                "total_tokens": stats["total_tokens"]
            }
        
        return analysis
    
    async def generate_performance_insights(self) -> List[str]:
        """
        Generate actionable performance insights based on session data.
        
        Returns:
            List of insight strings
        """
        insights = []
        
        # Get statistics for analysis
        session_stats = await self.get_session_statistics()
        tool_stats = await self.get_tool_usage_statistics()
        type_analysis = await self.get_session_type_analysis()
        
        # Analyze session patterns
        if session_stats["active_sessions"] > 10:
            insights.append(f"High session count ({session_stats['active_sessions']}) - consider session cleanup")
        
        # Analyze tool usage patterns
        if tool_stats["total_unique_tools"] < 5:
            insights.append("Low tool diversity - consider expanding tool usage for better coverage")
        
        # Analyze session types
        dominant_type = max(session_stats["sessions_by_type"], key=session_stats["sessions_by_type"].get) if session_stats["sessions_by_type"] else None
        if dominant_type and session_stats["sessions_by_type"][dominant_type] > session_stats["active_sessions"] * 0.7:
            insights.append(f"Session type '{dominant_type}' dominates ({session_stats['sessions_by_type'][dominant_type]} sessions) - consider diversification")
        
        # Analyze success scores
        if session_stats["average_success_score"] < 0.6:
            insights.append(f"Low average success score ({session_stats['average_success_score']:.2f}) - review session effectiveness")
        
        # Analyze token efficiency
        avg_tokens_per_call = session_stats["total_tokens"] / session_stats["total_tool_calls"] if session_stats["total_tool_calls"] > 0 else 0
        if avg_tokens_per_call > 100:
            insights.append(f"High token usage per tool call ({avg_tokens_per_call:.0f}) - consider optimization")
        
        return insights
    
    async def export_session_analytics(self) -> Dict[str, Any]:
        """
        Export comprehensive session analytics for external analysis.
        
        Returns:
            Dict containing complete analytics data
        """
        from datetime import datetime
        
        return {
            "export_timestamp": datetime.now().isoformat(),
            "session_statistics": await self.get_session_statistics(),
            "tool_usage_statistics": await self.get_tool_usage_statistics(),
            "session_type_analysis": await self.get_session_type_analysis(),
            "performance_insights": await self.generate_performance_insights(),
            "active_session_details": [
                await self.get_session_performance_metrics(session_id)
                for session_id in self.core_manager.active_sessions.keys()
            ]
        }