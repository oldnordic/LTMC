"""Code Pattern Memory service for LTMC.

Enables "Experience Replay for Code" - allowing models to learn from past
success and failure across sessions.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

from ltms.services.embedding_service import create_embedding_model, encode_text
from ltms.database.dal import get_next_vector_id


def store_code_pattern(
    conn: sqlite3.Connection,
    input_prompt: str,
    generated_code: str,
    result: str,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Store a code generation attempt as a pattern.
    
    Args:
        conn: Database connection
        input_prompt: The prompt that generated the code
        generated_code: The code that was generated
        result: Result of the code execution ('pass', 'fail', 'partial')
        function_name: Name of the function (optional)
        file_name: Name of the file (optional)
        module_name: Name of the module (optional)
        execution_time_ms: Execution time in milliseconds (optional)
        error_message: Error message if execution failed (optional)
        tags: List of tags for categorization (optional)
        
    Returns:
        Dictionary with success status and pattern_id
    """
    try:
        # Validate required inputs
        if not input_prompt or not generated_code or not result:
            return {
                'success': False,
                'error': 'input_prompt, generated_code, and result are required'
            }
        
        if result not in ['pass', 'fail', 'partial']:
            return {
                'success': False,
                'error': 'result must be one of: pass, fail, partial'
            }
        
        # Create searchable text for embedding
        search_text = f"{input_prompt}\n{generated_code}"
        if function_name:
            search_text += f"\nFunction: {function_name}"
        if file_name:
            search_text += f"\nFile: {file_name}"
        
        # Generate embedding using existing 384-dim model
        model = create_embedding_model("all-MiniLM-L6-v2")
        embedding = encode_text(model, search_text)
        
        # Get sequential vector ID
        vector_id = get_next_vector_id(conn)
        
        # Create CodePatterns table if it doesn't exist
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CodePatterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                function_name TEXT,
                file_name TEXT,
                module_name TEXT,
                input_prompt TEXT NOT NULL,
                generated_code TEXT NOT NULL,
                result TEXT CHECK(result IN ('pass', 'fail', 'partial')),
                execution_time_ms INTEGER,
                error_message TEXT,
                tags TEXT,
                created_at TEXT NOT NULL,
                vector_id INTEGER UNIQUE,
                FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)
            )
        """)
        
        # Store the pattern
        created_at = datetime.now().isoformat()
        tags_json = json.dumps(tags) if tags else None
        
        cursor.execute("""
            INSERT INTO CodePatterns (
                function_name, file_name, module_name, input_prompt, generated_code,
                result, execution_time_ms, error_message, tags, created_at, vector_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            function_name, file_name, module_name, input_prompt, generated_code,
            result, execution_time_ms, error_message, tags_json, created_at, vector_id
        ))
        
        pattern_id = cursor.lastrowid
        conn.commit()
        
        return {
            'success': True,
            'pattern_id': pattern_id,
            'message': f'Code pattern stored with result: {result}'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def retrieve_code_patterns(
    conn: sqlite3.Connection,
    query: str,
    result_filter: Optional[str] = None,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Retrieve similar code patterns for learning.
    
    Args:
        conn: Database connection
        query: Search query for finding similar patterns
        result_filter: Filter by result ('pass', 'fail', 'partial', None for all)
        function_name: Filter by function name (optional)
        file_name: Filter by file name (optional)
        module_name: Filter by module name (optional)
        top_k: Maximum number of patterns to return
        
    Returns:
        Dictionary with patterns and metadata
    """
    try:
        # Validate inputs
        if not query:
            return {
                'success': False,
                'error': 'query is required'
            }
        
        if result_filter and result_filter not in ['pass', 'fail', 'partial']:
            return {
                'success': False,
                'error': 'result_filter must be one of: pass, fail, partial'
            }
        
        # Generate query embedding
        model = create_embedding_model("all-MiniLM-L6-v2")
        query_embedding = encode_text(model, query)
        
        # Build SQL query with filters
        sql = """
            SELECT id, function_name, file_name, module_name, input_prompt,
                   generated_code, result, execution_time_ms, error_message,
                   tags, created_at, vector_id
            FROM CodePatterns
            WHERE 1=1
        """
        params = []
        
        if result_filter:
            sql += " AND result = ?"
            params.append(result_filter)
        
        if function_name:
            sql += " AND function_name = ?"
            params.append(function_name)
        
        if file_name:
            sql += " AND file_name = ?"
            params.append(file_name)
        
        if module_name:
            sql += " AND module_name = ?"
            params.append(module_name)
        
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(top_k)
        
        # Execute query
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # Convert to dictionary format
        patterns = []
        for row in rows:
            pattern = {
                'id': row[0],
                'function_name': row[1],
                'file_name': row[2],
                'module_name': row[3],
                'input_prompt': row[4],
                'generated_code': row[5],
                'result': row[6],
                'execution_time_ms': row[7],
                'error_message': row[8],
                'tags': json.loads(row[9]) if row[9] else None,
                'created_at': row[10],
                'vector_id': row[11]
            }
            patterns.append(pattern)
        
        return {
            'success': True,
            'patterns': patterns,
            'count': len(patterns),
            'query': query
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def analyze_code_patterns(
    conn: sqlite3.Connection,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    time_range_days: int = 30
) -> Dict[str, Any]:
    """Analyze code pattern success rates and trends.
    
    Args:
        conn: Database connection
        function_name: Filter by function name (optional)
        file_name: Filter by file name (optional)
        module_name: Filter by module name (optional)
        time_range_days: Number of days to analyze (default: 30)
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Build SQL query for analysis
        sql = """
            SELECT 
                COUNT(*) as total_patterns,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                SUM(CASE WHEN result = 'partial' THEN 1 ELSE 0 END) as partial_count,
                AVG(execution_time_ms) as avg_execution_time
            FROM CodePatterns
            WHERE created_at >= datetime('now', '-{} days')
        """.format(time_range_days)
        
        params = []
        
        if function_name:
            sql += " AND function_name = ?"
            params.append(function_name)
        
        if file_name:
            sql += " AND file_name = ?"
            params.append(file_name)
        
        if module_name:
            sql += " AND module_name = ?"
            params.append(module_name)
        
        # Execute analysis query
        cursor = conn.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            return {
                'success': True,
                'total_patterns': 0,
                'pass_count': 0,
                'fail_count': 0,
                'partial_count': 0,
                'success_rate': 0.0,
                'avg_execution_time': 0.0
            }
        
        total_patterns = row[0]
        pass_count = row[1] or 0
        fail_count = row[2] or 0
        partial_count = row[3] or 0
        avg_execution_time = row[4] or 0.0
        
        # Calculate success rate
        success_rate = pass_count / total_patterns if total_patterns > 0 else 0.0
        
        return {
            'success': True,
            'total_patterns': total_patterns,
            'pass_count': pass_count,
            'fail_count': fail_count,
            'partial_count': partial_count,
            'success_rate': success_rate,
            'avg_execution_time': avg_execution_time
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_code_patterns_by_query(
    conn: sqlite3.Connection,
    query_embedding,
    result_filter: Optional[str] = None,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """Get code patterns by vector similarity search.
    
    This is a helper function for vector-based pattern retrieval.
    Currently returns basic SQL results, but can be extended with
    proper vector similarity search using FAISS.
    
    Args:
        conn: Database connection
        query_embedding: Query embedding for similarity search
        result_filter: Filter by result
        function_name: Filter by function name
        file_name: Filter by file name
        module_name: Filter by module name
        top_k: Maximum number of results
        
    Returns:
        List of pattern dictionaries
    """
    # For now, return basic SQL results
    # TODO: Implement proper vector similarity search
    result = retrieve_code_patterns(
        conn=conn,
        query="",  # Empty query for basic retrieval
        result_filter=result_filter,
        function_name=function_name,
        file_name=file_name,
        module_name=module_name,
        top_k=top_k
    )
    
    if result['success']:
        return result['patterns']
    else:
        return []
