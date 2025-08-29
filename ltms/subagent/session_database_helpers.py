"""
Session Database Helper Functions
Database helper functions for cross-session analysis operations.

File: ltms/subagent/session_database_helpers.py
Lines: ~165 (under 300 limit)
Purpose: Database helpers for session analysis and data retrieval
"""

import json
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from ..config.json_config_loader import get_config

logger = logging.getLogger(__name__)


class SessionDatabaseHelpers:
    """Database helper functions for session analysis."""
    
    def __init__(self):
        self.config = get_config()
    
    async def get_all_sessions_summary(self, exclude_session: str = None) -> List[Dict[str, Any]]:
        """Get summary data for all sessions for similarity comparison."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                where_clause = "WHERE session_id != ?" if exclude_session else ""
                params = (exclude_session,) if exclude_session else ()
                
                sessions = conn.execute(f"""
                    SELECT 
                        session_id,
                        session_type,
                        start_time,
                        success_score
                    FROM subagent_sessions 
                    {where_clause}
                    ORDER BY start_time DESC 
                    LIMIT 50
                """, params).fetchall()
                
                session_summaries = []
                for session in sessions:
                    session_id = session["session_id"]
                    
                    # Get tools for this session
                    tools = conn.execute("""
                        SELECT DISTINCT tool_name FROM subagent_tool_invocations 
                        WHERE session_id = ?
                    """, (session_id,)).fetchall()
                    
                    # Get patterns for this session
                    patterns = conn.execute("""
                        SELECT pattern_signature FROM subagent_intelligence_patterns
                        WHERE sessions_observed LIKE ?
                    """, (f'%{session_id}%',)).fetchall()
                    
                    session_summaries.append({
                        "session_id": session_id,
                        "session_type": session["session_type"],
                        "tools": [tool["tool_name"] for tool in tools],
                        "patterns": [pattern["pattern_signature"] for pattern in patterns],
                        "success_score": session["success_score"],
                        "start_time": session["start_time"]
                    })
                
                return session_summaries
                
        except Exception as e:
            logger.error(f"Failed to get sessions summary: {e}")
            return []
    
    async def get_session_comprehensive_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive session data for similarity analysis."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get session info
                session = conn.execute("""
                    SELECT * FROM subagent_sessions WHERE session_id = ?
                """, (session_id,)).fetchone()
                
                if not session:
                    return None
                
                # Get tools used
                tools = conn.execute("""
                    SELECT DISTINCT tool_name FROM subagent_tool_invocations 
                    WHERE session_id = ?
                """, (session_id,)).fetchall()
                
                # Get patterns
                patterns = conn.execute("""
                    SELECT pattern_signature FROM subagent_intelligence_patterns
                    WHERE sessions_observed LIKE ?
                """, (f'%{session_id}%',)).fetchall()
                
                return {
                    "session_id": session_id,
                    "session_type": session["session_type"],
                    "tools": [tool["tool_name"] for tool in tools],
                    "patterns": [pattern["pattern_signature"] for pattern in patterns],
                    "success_score": session["success_score"],
                    "start_time": session["start_time"]
                }
                
        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None
    
    async def get_session_tool_sequence(self, session_id: str) -> List[str]:
        """Get the complete tool sequence for a session."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                tools = conn.execute("""
                    SELECT tool_name FROM subagent_tool_invocations 
                    WHERE session_id = ? 
                    ORDER BY timestamp
                """, (session_id,)).fetchall()
                
                return [tool[0] for tool in tools]
                
        except Exception as e:
            logger.error(f"Failed to get session tool sequence: {e}")
            return []
    
    async def get_recent_session_tools(self, session_id: str, limit: int = 5) -> List[str]:
        """Get recent tools used in the session."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                tools = conn.execute("""
                    SELECT tool_name FROM subagent_tool_invocations 
                    WHERE session_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (session_id, limit)).fetchall()
                
                return [tool[0] for tool in tools]
                
        except Exception:
            return []
    
    async def get_pattern_evolution_data(self, pattern_signature: str) -> List[Dict[str, Any]]:
        """Get pattern evolution data for analysis."""
        try:
            with sqlite3.connect(self.config.get_db_path()) as conn:
                conn.row_factory = sqlite3.Row
                
                # Get pattern occurrences over time
                pattern_history = conn.execute("""
                    SELECT 
                        p.last_seen,
                        p.frequency,
                        p.effectiveness_score,
                        p.sessions_observed,
                        s.session_type,
                        s.success_score
                    FROM subagent_intelligence_patterns p
                    JOIN subagent_sessions s ON JSON_EXTRACT(p.sessions_observed, '$[0]') = s.session_id
                    WHERE p.pattern_signature = ?
                    ORDER BY p.last_seen
                """, (pattern_signature,)).fetchall()
                
                return [dict(row) for row in pattern_history]
                
        except Exception as e:
            logger.error(f"Failed to get pattern evolution data: {e}")
            return []