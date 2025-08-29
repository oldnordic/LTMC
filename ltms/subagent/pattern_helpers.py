"""
Pattern Analysis Helper Functions

Database helper functions for pattern analysis operations.
File: ltms/subagent/pattern_helpers.py
Lines: ~250 (under 300 limit)
Purpose: Database helpers and utility functions for pattern analysis
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import hashlib

from ..config.json_config_loader import get_config

logger = logging.getLogger(__name__)


class PatternDatabaseHelpers:
    """Database helper functions for pattern analysis."""
    
    def __init__(self):
        self.config = get_config()
    
    async def get_argument_pattern_frequency(self, pattern_signature: str) -> int:
        """Get frequency of a specific argument pattern across all sessions."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                result = conn.execute("""
                    SELECT frequency FROM subagent_intelligence_patterns 
                    WHERE pattern_type IN ('argument_pattern', 'target_pattern', 'argument_combination') 
                    AND pattern_signature = ?
                """, (pattern_signature,)).fetchone()
                
                return result[0] if result else 0
                
        except Exception:
            return 0
    
    async def get_recent_invocations_with_timing(self, session_id: str, 
                                                limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent tool invocations with timing information."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                invocations = conn.execute("""
                    SELECT tool_name, timestamp, execution_time_ms 
                    FROM subagent_tool_invocations 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (session_id, limit)).fetchall()
                
                return [dict(inv) for inv in reversed(invocations)]
                
        except Exception as e:
            logger.error(f"Failed to get invocations with timing: {e}")
            return []
    
    async def get_tool_success_statistics(self, tool_name: str) -> Dict[str, Any]:
        """Get success statistics for a specific tool across all sessions."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                # Get overall statistics
                stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total_uses,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_uses,
                        COUNT(DISTINCT session_id) as unique_sessions
                    FROM subagent_tool_invocations 
                    WHERE tool_name = ?
                """, (tool_name,)).fetchone()
                
                if not stats or stats[0] == 0:
                    return {"total_uses": 0, "success_rate": 0.0}
                
                # Get common error messages
                common_errors = conn.execute("""
                    SELECT error_message, COUNT(*) as error_count
                    FROM subagent_tool_invocations 
                    WHERE tool_name = ? AND success = 0 AND error_message IS NOT NULL
                    GROUP BY error_message 
                    ORDER BY error_count DESC 
                    LIMIT 3
                """, (tool_name,)).fetchall()
                
                success_rate = stats[1] / stats[0] if stats[0] > 0 else 0.0
                
                return {
                    "total_uses": stats[0],
                    "success_rate": success_rate,
                    "successful_uses": stats[1],
                    "unique_sessions": stats[2],
                    "common_errors": [{"message": err[0], "count": err[1]} for err in common_errors]
                }
                
        except Exception as e:
            logger.error(f"Failed to get tool success statistics: {e}")
            return {"total_uses": 0, "success_rate": 0.0}
    
    async def get_tool_correlations(self, current_tool: str) -> List[Dict[str, Any]]:
        """Get tools that are commonly used before/after the current tool."""
        try:
            correlations = []
            
            with sqlite3.connect(self.config.get_db_path()) as conn:
                # Tools that commonly precede this tool
                preceding_tools = conn.execute("""
                    WITH tool_sequences AS (
                        SELECT 
                            session_id,
                            tool_name,
                            timestamp,
                            LAG(tool_name) OVER (PARTITION BY session_id ORDER BY timestamp) as prev_tool
                        FROM subagent_tool_invocations
                    )
                    SELECT 
                        prev_tool as related_tool,
                        COUNT(*) as frequency,
                        COUNT(*) * 1.0 / (
                            SELECT COUNT(*) FROM subagent_tool_invocations WHERE tool_name = ?
                        ) as correlation_strength
                    FROM tool_sequences 
                    WHERE tool_name = ? AND prev_tool IS NOT NULL
                    GROUP BY prev_tool
                    HAVING COUNT(*) >= 2
                    ORDER BY correlation_strength DESC
                    LIMIT 5
                """, (current_tool, current_tool)).fetchall()
                
                for tool_data in preceding_tools:
                    correlations.append({
                        "related_tool": tool_data[0],
                        "frequency": tool_data[1],
                        "correlation_strength": min(tool_data[2], 1.0),
                        "type": "precedes"
                    })
                
                # Tools that commonly follow this tool
                following_tools = conn.execute("""
                    WITH tool_sequences AS (
                        SELECT 
                            session_id,
                            tool_name,
                            timestamp,
                            LEAD(tool_name) OVER (PARTITION BY session_id ORDER BY timestamp) as next_tool
                        FROM subagent_tool_invocations
                    )
                    SELECT 
                        next_tool as related_tool,
                        COUNT(*) as frequency,
                        COUNT(*) * 1.0 / (
                            SELECT COUNT(*) FROM subagent_tool_invocations WHERE tool_name = ?
                        ) as correlation_strength
                    FROM tool_sequences 
                    WHERE tool_name = ? AND next_tool IS NOT NULL
                    GROUP BY next_tool
                    HAVING COUNT(*) >= 2
                    ORDER BY correlation_strength DESC
                    LIMIT 5
                """, (current_tool, current_tool)).fetchall()
                
                for tool_data in following_tools:
                    correlations.append({
                        "related_tool": tool_data[0],
                        "frequency": tool_data[1],
                        "correlation_strength": min(tool_data[2], 1.0),
                        "type": "follows"
                    })
            
            return correlations
            
        except Exception as e:
            logger.error(f"Failed to get tool correlations: {e}")
            return []
    
    async def get_recent_tool_sequence(self, session_id: str, limit: int = 10) -> List[str]:
        """Get recent tool usage sequence for pattern analysis."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                tools = conn.execute("""
                    SELECT tool_name FROM subagent_tool_invocations 
                    WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?
                """, (session_id, limit)).fetchall()
                
                return [tool[0] for tool in reversed(tools)]
                
        except Exception as e:
            logger.error(f"Failed to get tool sequence: {e}")
            return []
    
    async def get_sequence_frequency(self, sequence_signature: str) -> int:
        """Get frequency of a specific tool sequence across all sessions."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                result = conn.execute("""
                    SELECT frequency FROM subagent_intelligence_patterns 
                    WHERE pattern_type = 'tool_sequence' AND pattern_signature = ?
                """, (sequence_signature,)).fetchone()
                
                return result[0] if result else 0
                
        except Exception:
            return 0


class PatternUtilities:
    """Utility functions for pattern analysis."""
    
    @staticmethod
    def extract_target_pattern(target: str) -> Optional[str]:
        """Extract pattern from target (file extensions, path patterns)."""
        try:
            if '.' in target:
                # File extension pattern
                extension = target.split('.')[-1].lower()
                if len(extension) <= 4:  # Valid extension
                    return f"*.{extension}"
            
            if '/' in target:
                # Path pattern
                parts = target.split('/')
                if len(parts) >= 2:
                    return f".../{parts[-2]}/{parts[-1]}" if len(parts) > 2 else target
            
        except Exception:
            pass
        
        return None
    
    @staticmethod
    def create_argument_signature(arguments: Dict[str, Any]) -> str:
        """Create a signature for argument combinations."""
        # Create a consistent signature for argument patterns
        sorted_keys = sorted(arguments.keys())
        key_signature = '+'.join(sorted_keys)
        
        # Add hash of values for uniqueness while maintaining privacy
        values_str = json.dumps({k: str(v)[:50] for k, v in arguments.items()}, sort_keys=True)
        values_hash = hashlib.md5(values_str.encode()).hexdigest()[:8]
        
        return f"args:{key_signature}:{values_hash}"
    
    @staticmethod
    def calculate_sequence_confidence(sequence: List[str], frequency: int) -> float:
        """Calculate confidence score for a sequence pattern."""
        base_confidence = min(frequency / 10.0, 1.0)
        length_bonus = min(len(sequence) / 5.0, 0.3)  # Longer sequences are more significant
        return min(base_confidence + length_bonus, 1.0)
    
    @staticmethod
    def calculate_pattern_strength(frequency: int, total_occurrences: int) -> float:
        """Calculate the strength of a pattern based on frequency."""
        if total_occurrences == 0:
            return 0.0
        
        raw_strength = frequency / total_occurrences
        # Apply logarithmic scaling to prevent domination by very frequent patterns
        import math
        return min(raw_strength + (math.log(frequency + 1) / 10.0), 1.0)
    
    @staticmethod
    def classify_pattern_confidence(confidence: float) -> str:
        """Classify pattern confidence into categories."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.2:
            return "low"
        else:
            return "very_low"