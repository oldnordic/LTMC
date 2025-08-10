"""
Advanced Database Service - Todo and Code Pattern Operations
==========================================================

Advanced async SQLite operations for todos and code patterns.
Operations: todos management, code patterns, and complex queries.
"""

import aiosqlite
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from config.settings import LTMCSettings
from models.database_models import Todo, CodePattern
from models.base_models import PerformanceMetrics
from utils.performance_utils import measure_performance


class AdvancedDatabaseService:
    """
    Advanced async SQLite database service.
    
    Handles advanced SQLite operations:
    - Todo management
    - Code pattern learning
    - Complex queries and analytics
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self.db_path = settings.db_path
        
    async def initialize(self) -> None:
        """Initialize advanced database service."""
        self.logger.info(f"Initializing advanced database service with path: {self.db_path}")
        
    @measure_performance  
    async def add_todo(self, title: str, description: str, priority: str = "medium") -> int:
        """
        Add todo to todos table.
        
        Args:
            title: Todo title
            description: Todo description  
            priority: Priority (high, medium, low)
            
        Returns:
            int: Todo ID
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """INSERT INTO todos (title, description, priority, status, created_at)
                   VALUES (?, ?, ?, 'pending', ?)""",
                (title, description, priority, datetime.utcnow().isoformat())
            )
            todo_id = cursor.lastrowid
            await db.commit()
            
            self.logger.debug(f"Added todo {todo_id}: {title}")
            return todo_id
    
    @measure_performance
    async def list_todos(
        self, 
        status: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        List todos with filtering and pagination.
        
        Args:
            status: Optional status filter
            priority: Optional priority filter
            limit: Maximum todos to return
            offset: Number of todos to skip
            
        Returns:
            Tuple[List[Dict], int]: (todos, total_count)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if status:
                where_conditions.append("status = ?")
                params.append(status)
                
            if priority:
                where_conditions.append("priority = ?") 
                params.append(priority)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # Get total count
            count_cursor = await db.execute(f"SELECT COUNT(*) FROM todos {where_clause}", params)
            total_count = (await count_cursor.fetchone())[0]
            
            # Get todos with pagination
            params.extend([limit, offset])
            cursor = await db.execute(
                f"""SELECT * FROM todos {where_clause} 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?""",
                params
            )
            
            rows = await cursor.fetchall()
            todos = [dict(row) for row in rows]
            
            return todos, total_count
    
    @measure_performance
    async def complete_todo(self, todo_id: int) -> bool:
        """
        Mark todo as completed.
        
        Args:
            todo_id: Todo ID to complete
            
        Returns:
            bool: True if todo was found and completed
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """UPDATE todos 
                   SET status = 'completed', completed = 1, completed_at = ?
                   WHERE id = ?""",
                (datetime.utcnow().isoformat(), todo_id)
            )
            
            await db.commit()
            success = cursor.rowcount > 0
            
            if success:
                self.logger.debug(f"Completed todo {todo_id}")
            else:
                self.logger.warning(f"Todo {todo_id} not found for completion")
                
            return success
    
    @measure_performance
    async def log_code_pattern(
        self,
        input_prompt: str,
        generated_code: str,
        result: str,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Tuple[int, int]:
        """
        Log code pattern and return (pattern_id, vector_id).
        
        Args:
            input_prompt: Original prompt
            generated_code: Generated code
            result: Result status (pass, fail, partial)
            execution_time_ms: Optional execution time
            error_message: Optional error message
            tags: Optional tags list
            
        Returns:
            Tuple[int, int]: (pattern_id, vector_id)
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get next vector ID
            vector_id = await self._get_next_vector_id(db)
            
            # Convert tags to JSON
            tags_json = json.dumps(tags) if tags else None
            
            cursor = await db.execute(
                """INSERT INTO CodePatterns 
                   (input_prompt, generated_code, result, execution_time_ms, error_message, 
                    tags, created_at, vector_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    input_prompt,
                    generated_code,
                    result,
                    execution_time_ms,
                    error_message,
                    tags_json,
                    datetime.utcnow().isoformat(),
                    vector_id
                )
            )
            
            pattern_id = cursor.lastrowid
            await db.commit()
            
            self.logger.debug(f"Logged code pattern {pattern_id} with vector {vector_id}")
            return pattern_id, vector_id
    
    @measure_performance
    async def get_code_patterns(
        self,
        query_tags: Optional[List[str]] = None,
        result_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get code patterns with filtering.
        
        Args:
            query_tags: Optional tags to filter by
            result_filter: Optional result filter (pass, fail, partial)
            limit: Maximum patterns to return
            
        Returns:
            List of code pattern dictionaries
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Build WHERE clause
            where_conditions = []
            params = []
            
            if result_filter:
                where_conditions.append("result = ?")
                params.append(result_filter)
            
            # TODO: Add proper tags filtering with JSON operations
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            params.append(limit)
            
            cursor = await db.execute(
                f"""SELECT * FROM CodePatterns {where_clause} 
                    ORDER BY created_at DESC 
                    LIMIT ?""",
                params
            )
            
            rows = await cursor.fetchall()
            patterns = []
            
            for row in rows:
                pattern = dict(row)
                # Parse tags JSON if present
                if pattern.get('tags'):
                    try:
                        pattern['tags'] = json.loads(pattern['tags'])
                    except json.JSONDecodeError:
                        pattern['tags'] = []
                patterns.append(pattern)
            
            return patterns
    
    async def _get_next_vector_id(self, db: aiosqlite.Connection) -> int:
        """Get next available vector ID."""
        cursor = await db.execute("SELECT last_vector_id FROM VectorIdSequence WHERE id = 1")
        row = await cursor.fetchone()
        
        if row:
            next_id = row[0] + 1
        else:
            next_id = 1
        
        await db.execute(
            "UPDATE VectorIdSequence SET last_vector_id = ? WHERE id = 1",
            (next_id,)
        )
        
        return next_id