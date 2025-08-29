"""
Subagent Intelligence Tracking System
Comprehensive intelligence capture and analysis for Claude Code subagent integration.

File: ltms/subagent/intelligence_tracker.py
Lines: ~290 (under 300 limit)
Purpose: Main interface for subagent intelligence tracking with modular architecture
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from .database_operations import IntelligenceDBOperations
from .pattern_analyzer import SubagentPatternAnalyzer
from .cross_session_linker import CrossSessionLinker

logger = logging.getLogger(__name__)


class SubagentIntelligenceTracker:
    """
    Comprehensive subagent intelligence capture system.
    
    Main interface for tracking subagent activities, patterns, and learning across sessions
    with real database operations across SQLite, Neo4j, FAISS, and Redis.
    Uses modular architecture for maintainability and extensibility.
    """
    
    def __init__(self):
        self.db_operations = IntelligenceDBOperations()
        self.pattern_analyzer = SubagentPatternAnalyzer()
        self.cross_session_linker = CrossSessionLinker()
        logger.info("Subagent Intelligence Tracker initialized with modular architecture")
    
    async def track_session_start(self, session_id: str, 
                                 session_metadata: Dict[str, Any]) -> bool:
        """
        Track subagent session initiation with comprehensive metadata.
        
        Args:
            session_id: Unique session identifier
            session_metadata: Session context and metadata
            
        Returns:
            bool: Success status
        """
        try:
            intelligence_record = {
                "session_id": session_id,
                "parent_session": session_metadata.get("parent_session"),
                "session_type": session_metadata.get("session_type", "analysis"),
                "start_time": datetime.now(timezone.utc).isoformat(),
                "metadata": json.dumps(session_metadata)
            }
            
            # Store session using modular database operations
            success = await self.db_operations.store_session_start(intelligence_record)
            
            if success:
                logger.info(f"Session {session_id} tracking initiated successfully")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to track session start {session_id}: {e}")
            return False
    
    async def track_tool_invocation(self, session_id: str, tool_name: str, 
                                   arguments: Dict[str, Any],
                                   execution_time_ms: int = 0,
                                   token_count: int = 0,
                                   success: bool = True,
                                   error_message: str = None) -> bool:
        """
        Track subagent tool usage with comprehensive analysis.
        
        Args:
            session_id: Session identifier
            tool_name: Name of tool invoked
            arguments: Tool arguments
            execution_time_ms: Execution time in milliseconds
            token_count: Estimated token count
            success: Success status
            error_message: Error message if failed
            
        Returns:
            bool: Success status
        """
        try:
            # Analyze patterns using modular pattern analyzer
            patterns_detected = await self.pattern_analyzer.analyze_tool_usage(
                tool_name, arguments, session_id
            )
            
            intelligence_record = {
                "session_id": session_id,
                "tool_name": tool_name,
                "arguments": json.dumps(arguments),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_time_ms": execution_time_ms,
                "token_count": token_count,
                "success": success,
                "error_message": error_message,
                "patterns_detected": json.dumps(patterns_detected)
            }
            
            # Store tool invocation using modular database operations
            db_success = await self.db_operations.store_tool_invocation(intelligence_record)
            
            # Update cross-session learning patterns
            await self.cross_session_linker.update_patterns(
                session_id, tool_name, arguments, patterns_detected
            )
            
            # Store detected patterns using modular database operations
            pattern_success = await self.db_operations.store_intelligence_patterns(
                patterns_detected, session_id
            )
            
            if db_success and pattern_success:
                logger.debug(f"Tool invocation tracked successfully: {tool_name} in session {session_id}")
                return True
            else:
                logger.warning(f"Partial failure tracking tool invocation: {tool_name}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to track tool invocation {tool_name}: {e}")
            return False
    
    async def track_session_end(self, session_id: str, 
                               success_score: float = 0.0) -> bool:
        """
        Track session completion with success metrics.
        
        Args:
            session_id: Session identifier
            success_score: Overall session success score (0.0-1.0)
            
        Returns:
            bool: Success status
        """
        try:
            success = await self.db_operations.update_session_end(session_id, success_score)
            
            if success:
                logger.info(f"Session {session_id} completed with score {success_score}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to track session end {session_id}: {e}")
            return False
    
    async def get_session_intelligence(self, session_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive intelligence for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict containing session intelligence data
        """
        try:
            return await self.db_operations.get_session_intelligence(session_id)
                
        except Exception as e:
            logger.error(f"Failed to get session intelligence {session_id}: {e}")
            return {"error": str(e)}
    
    async def find_similar_sessions(self, current_session: str, 
                                   context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Find sessions with similar patterns and context using modular cross-session linker.
        
        Args:
            current_session: Current session identifier
            context: Optional context for similarity matching
            
        Returns:
            List of similar sessions with detailed similarity data
        """
        try:
            similar_sessions = await self.cross_session_linker.find_similar_sessions(
                current_session, context
            )
            
            return [
                {
                    "session_id": session.session_id,
                    "similarity_score": session.similarity_score,
                    "common_tools": session.common_tools,
                    "common_patterns": session.common_patterns,
                    "temporal_distance_hours": session.temporal_distance
                }
                for session in similar_sessions
            ]
            
        except Exception as e:
            logger.error(f"Failed to find similar sessions: {e}")
            return []
    
    async def predict_next_tools(self, session_id: str, 
                                current_sequence: List[str]) -> List[Dict[str, Any]]:
        """
        Predict likely next tools based on patterns and similar sessions.
        
        Args:
            session_id: Current session identifier
            current_sequence: Current tool usage sequence
            
        Returns:
            List of predicted tools with confidence scores
        """
        try:
            predictions = await self.cross_session_linker.predict_next_tools(
                session_id, current_sequence
            )
            
            logger.info(f"Generated {len(predictions)} tool predictions for session {session_id}")
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to predict next tools: {e}")
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
            evolution_data = await self.cross_session_linker.get_pattern_evolution(
                pattern_signature
            )
            
            return evolution_data
            
        except Exception as e:
            logger.error(f"Failed to get pattern evolution: {e}")
            return {"error": str(e)}
    
    async def get_intelligence_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive intelligence statistics across all tracked sessions.
        
        Returns:
            Dict containing intelligence statistics
        """
        try:
            # Get pattern statistics from database operations
            pattern_stats = await self.db_operations.get_pattern_statistics()
            
            # Add cross-session insights
            pattern_stats["cross_session_insights"] = {
                "total_sessions_tracked": len(await self._get_all_session_ids()),
                "active_patterns": len([p for p in pattern_stats.get("pattern_types", []) 
                                      if p.get("recent_count", 0) > 0]),
                "prediction_capabilities": "enabled"
            }
            
            return pattern_stats
            
        except Exception as e:
            logger.error(f"Failed to get intelligence statistics: {e}")
            return {"error": str(e)}
    
    async def _get_all_session_ids(self) -> List[str]:
        """Helper method to get all tracked session IDs."""
        try:
            # This would use the database operations module
            intelligence_data = await self.db_operations.get_session_intelligence("")
            if "error" in intelligence_data:
                return []
            
            # Extract session IDs from the intelligence data
            return []  # Simplified for now
            
        except Exception:
            return []