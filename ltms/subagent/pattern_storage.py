"""
Pattern Storage Operations
Handles storage and management of intelligence patterns with frequency tracking.
File: ltms/subagent/pattern_storage.py
Lines: ~295 (under 300 limit)
Purpose: Pattern storage, frequency tracking, and statistics
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from ..config import get_config

logger = logging.getLogger(__name__)

class PatternStorageManager:
    """Pattern storage and management for intelligence tracking."""
    
    def __init__(self):
        self.config = get_config()
        self._ensure_pattern_schema()
    
    def _ensure_pattern_schema(self):
        """Ensure pattern storage tables exist with proper schema."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS subagent_intelligence_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        pattern_signature TEXT NOT NULL,
                        pattern_data JSON,
                        frequency INTEGER DEFAULT 1,
                        effectiveness_score REAL DEFAULT 0.0,
                        last_seen TIMESTAMP NOT NULL,
                        sessions_observed JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(pattern_type, pattern_signature)
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_patterns_type_effectiveness 
                    ON subagent_intelligence_patterns(pattern_type, effectiveness_score DESC);
                """)
                logger.debug("Pattern storage schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pattern schema: {e}")
            raise
    
    async def store_intelligence_patterns(self, patterns: List[Dict[str, Any]], session_id: str) -> bool:
        """Store detected intelligence patterns with frequency tracking."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                for pattern in patterns:
                    pattern_type = pattern.get('type', 'unknown')
                    pattern_signature = pattern.get('signature', '')
                    
                    # Try to update existing pattern frequency
                    result = conn.execute("""
                        UPDATE subagent_intelligence_patterns 
                        SET frequency = frequency + 1,
                            last_seen = ?,
                            sessions_observed = json_insert(
                                COALESCE(sessions_observed, '[]'), 
                                '$[#]', ?
                            )
                        WHERE pattern_type = ? AND pattern_signature = ?
                    """, (
                        datetime.now(timezone.utc).isoformat(),
                        session_id,
                        pattern_type,
                        pattern_signature
                    ))
                    
                    # Insert new pattern if doesn't exist
                    if result.rowcount == 0:
                        conn.execute("""
                            INSERT INTO subagent_intelligence_patterns
                            (pattern_type, pattern_signature, pattern_data, 
                             frequency, last_seen, sessions_observed)
                            VALUES (?, ?, ?, 1, ?, ?)
                        """, (
                            pattern_type,
                            pattern_signature,
                            json.dumps(pattern),
                            datetime.now(timezone.utc).isoformat(),
                            json.dumps([session_id])
                        ))
                
                conn.commit()
            
            logger.debug(f"Stored {len(patterns)} intelligence patterns for session {session_id}")
            return True
                
        except Exception as e:
            logger.error(f"Failed to store intelligence patterns: {e}")
            return False
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern statistics across all sessions."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get pattern type distribution
                pattern_types = conn.execute("""
                    SELECT pattern_type, COUNT(*) as count, AVG(frequency) as avg_freq
                    FROM subagent_intelligence_patterns 
                    GROUP BY pattern_type ORDER BY count DESC
                """).fetchall()
                
                # Get most effective patterns
                top_patterns = conn.execute("""
                    SELECT pattern_type, pattern_signature, frequency, effectiveness_score
                    FROM subagent_intelligence_patterns 
                    ORDER BY effectiveness_score DESC, frequency DESC LIMIT 10
                """).fetchall()
                
                # Get recent pattern activity
                recent_patterns = conn.execute("""
                    SELECT pattern_type, COUNT(*) as recent_count
                    FROM subagent_intelligence_patterns 
                    WHERE last_seen > datetime('now', '-7 days')
                    GROUP BY pattern_type
                """).fetchall()
                
                return {
                    "pattern_types": [dict(row) for row in pattern_types],
                    "top_patterns": [dict(row) for row in top_patterns],
                    "recent_activity": [dict(row) for row in recent_patterns],
                    "total_patterns": len(pattern_types)
                }
                
        except Exception as e:
            logger.error(f"Failed to get pattern statistics: {e}")
            return {"error": str(e)}
    
    async def get_patterns_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get all patterns associated with a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of patterns associated with the session
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                patterns = conn.execute("""
                    SELECT * FROM subagent_intelligence_patterns 
                    WHERE sessions_observed LIKE ?
                    ORDER BY frequency DESC
                """, (f'%{session_id}%',)).fetchall()
                
                return [dict(pattern) for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Failed to get patterns for session {session_id}: {e}")
            return []
    
    async def get_patterns_by_type(self, pattern_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get patterns of a specific type.
        
        Args:
            pattern_type: Type of patterns to retrieve
            limit: Maximum number of patterns to return
            
        Returns:
            List of patterns of the specified type
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                patterns = conn.execute("""
                    SELECT * FROM subagent_intelligence_patterns 
                    WHERE pattern_type = ?
                    ORDER BY frequency DESC, last_seen DESC
                    LIMIT ?
                """, (pattern_type, limit)).fetchall()
                
                return [dict(pattern) for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Failed to get patterns by type {pattern_type}: {e}")
            return []
    
    async def update_pattern_effectiveness(self, pattern_signature: str, 
                                         effectiveness_score: float) -> bool:
        """
        Update the effectiveness score for a pattern.
        
        Args:
            pattern_signature: Pattern signature to update
            effectiveness_score: New effectiveness score (0.0-1.0)
            
        Returns:
            bool: Success status
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                result = conn.execute("""
                    UPDATE subagent_intelligence_patterns 
                    SET effectiveness_score = ?
                    WHERE pattern_signature = ?
                """, (effectiveness_score, pattern_signature))
                
                conn.commit()
                
                if result.rowcount > 0:
                    logger.debug(f"Updated effectiveness score for pattern {pattern_signature}")
                    return True
                else:
                    logger.warning(f"Pattern {pattern_signature} not found for effectiveness update")
                    return False
                
        except Exception as e:
            logger.error(f"Failed to update pattern effectiveness: {e}")
            return False
    
    async def cleanup_old_patterns(self, max_age_days: int = 30) -> int:
        """
        Clean up old patterns that haven't been seen recently.
        
        Args:
            max_age_days: Maximum age in days before pattern cleanup
            
        Returns:
            int: Number of patterns cleaned up
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                result = conn.execute("""
                    DELETE FROM subagent_intelligence_patterns 
                    WHERE last_seen < datetime('now', '-' || ? || ' days')
                    AND frequency < 3
                """, (max_age_days,))
                
                conn.commit()
                cleanup_count = result.rowcount
                
                if cleanup_count > 0:
                    logger.info(f"Cleaned up {cleanup_count} old patterns")
                
                return cleanup_count
                
        except Exception as e:
            logger.error(f"Failed to cleanup old patterns: {e}")
            return 0
    
    async def export_patterns(self, pattern_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Export patterns for external analysis.
        
        Args:
            pattern_type: Optional filter by pattern type
            
        Returns:
            Dict containing exported pattern data
        """
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                if pattern_type:
                    patterns = conn.execute("""
                        SELECT * FROM subagent_intelligence_patterns 
                        WHERE pattern_type = ?
                        ORDER BY frequency DESC
                    """, (pattern_type,)).fetchall()
                else:
                    patterns = conn.execute("""
                        SELECT * FROM subagent_intelligence_patterns 
                        ORDER BY pattern_type, frequency DESC
                    """).fetchall()
                
                return {
                    "export_timestamp": datetime.now(timezone.utc).isoformat(),
                    "pattern_type_filter": pattern_type,
                    "total_patterns": len(patterns),
                    "patterns": [dict(pattern) for pattern in patterns]
                }
                
        except Exception as e:
            logger.error(f"Failed to export patterns: {e}")
            return {"error": str(e)}