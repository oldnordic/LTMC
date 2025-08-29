"""
LTMC Pattern Logger - FIXED log_attempt Implementation
Contains the CRITICAL BUG FIX for MCP protocol parameter handling

This module specifically addresses the log_attempt concatenation bug
where MCP protocol sends tags as various types but code expected list
"""

import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any


def log_attempt_impl(**params) -> Dict[str, Any]:
    """Log pattern attempt with FIXED parameter handling for MCP protocol compatibility.
    
    CRITICAL BUG FIX: Handles tags parameter as string, list, JSON, or None
    Previously failed with: "can only concatenate list (not 'str') to list"
    """
    
    def _ensure_list(value):
        """Ensure value is a list for safe concatenation - BUG FIX for MCP protocol parameter handling"""
        if value is None:
            return []
        elif isinstance(value, list):
            return value
        elif isinstance(value, str):
            # Handle JSON string or comma-separated
            if value.startswith('[') and value.endswith(']'):
                try:
                    return json.loads(value)
                except:
                    return [value]
            else:
                return [value]
        else:
            return [str(value)]
    
    try:
        # Required parameters
        pattern_type = params.get('pattern_type')
        code_content = params.get('code_content') 
        result = params.get('result')
        
        if not pattern_type:
            return {'success': False, 'error': 'Missing required parameter: pattern_type'}
        if not code_content:
            return {'success': False, 'error': 'Missing required parameter: code_content'}
        if not result:
            return {'success': False, 'error': 'Missing required parameter: result'}
        
        # Optional parameters with FIXED bug handling
        metadata = params.get('metadata', {})
        tags = _ensure_list(params.get('tags', []))  # CRITICAL FIX: Safe parameter handling
        
        # Use LTMC memory to store pattern attempt
        log_entry = {
            "action_type": "pattern_attempt",
            "pattern_type": pattern_type,
            "code_content": code_content[:500] + "..." if len(code_content) > 500 else code_content,
            "result": result,
            "metadata": metadata,
            "tags": tags,
            "timestamp": datetime.now().isoformat()
        }
        
        content = f"Pattern attempt logged: {pattern_type} - {result}\n"
        content += f"Code sample: {code_content[:200]}...\n" 
        content += f"Metadata: {metadata}"
        
        # Store in memory (sync version for compatibility)
        from ltms.config.json_config_loader import get_config
        config = get_config()
        db_path = config.get_db_path()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create pattern_attempts table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pattern_attempts (
                id TEXT PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                result TEXT NOT NULL,
                code_content TEXT,
                metadata TEXT,
                tags TEXT,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        attempt_id = f"attempt_{int(time.time() * 1000)}"
        cursor.execute('''
            INSERT INTO pattern_attempts (id, pattern_type, result, code_content, metadata, tags, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            attempt_id,
            pattern_type,
            result, 
            content,
            json.dumps(metadata),
            json.dumps(tags),
            log_entry["timestamp"]
        ))
        
        conn.commit()
        conn.close()
        
        return {
            'success': True,
            'logged': True,
            'attempt_id': attempt_id,
            'pattern_type': pattern_type,
            'result': result,
            'tags': ["pattern_attempt", pattern_type] + tags  # FIXED: Safe concatenation with _ensure_list
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Failed to log pattern attempt: {str(e)}'}


# Export for import compatibility  
__all__ = ['log_attempt_impl']