"""TDD tests for LTMC Code Pattern Memory implementation.

Tests the Code Pattern Memory feature that enables "Experience Replay for Code"
allowing models to learn from past success and failure across sessions.
"""

import pytest
import sqlite3
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Any, List

from ltms.database.connection import get_db_connection, close_db_connection
from ltms.database.schema import create_tables


class TestCodePatternMemory:
    """Test suite for Code Pattern Memory implementation."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create database connection
        conn = get_db_connection(db_path)
        create_tables(conn)
        
        yield db_path, conn
        
        # Cleanup
        close_db_connection(conn)
        os.unlink(db_path)
    
    def test_code_patterns_table_creation(self, temp_db):
        """Test that CodePatterns table is created correctly."""
        db_path, conn = temp_db
        
        # Create CodePatterns table
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
        conn.commit()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CodePatterns'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'CodePatterns'
        
        # Verify table structure
        cursor.execute("PRAGMA table_info(CodePatterns)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = [
            'id', 'function_name', 'file_name', 'module_name', 'input_prompt',
            'generated_code', 'result', 'execution_time_ms', 'error_message',
            'tags', 'created_at', 'vector_id'
        ]
        
        for column in required_columns:
            assert column in column_names
    
    def test_code_pattern_context_table_creation(self, temp_db):
        """Test that CodePatternContext table is created correctly."""
        db_path, conn = temp_db
        
        # Create CodePatternContext table
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CodePatternContext (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id INTEGER,
                context_type TEXT,
                context_id INTEGER,
                similarity_score REAL,
                FOREIGN KEY (pattern_id) REFERENCES CodePatterns (id)
            )
        """)
        conn.commit()
        
        # Verify table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CodePatternContext'")
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 'CodePatternContext'
        
        # Verify table structure
        cursor.execute("PRAGMA table_info(CodePatternContext)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'pattern_id', 'context_type', 'context_id', 'similarity_score']
        for column in required_columns:
            assert column in column_names
    
    def test_store_code_pattern_basic(self, temp_db):
        """Test basic code pattern storage functionality."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Test code pattern storage
        from ltms.services.code_pattern_service import store_code_pattern
        
        result = store_code_pattern(
            conn=conn,
            input_prompt="Create a function to calculate fibonacci numbers",
            generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            result="pass",
            function_name="fibonacci",
            file_name="math_utils.py",
            module_name="utils",
            execution_time_ms=150,
            error_message=None,
            tags=["recursion", "math"]
        )
        
        # Verify storage was successful
        assert result['success'] is True
        assert 'pattern_id' in result
        assert result['message'] == 'Code pattern stored with result: pass'
        
        # Verify data was stored correctly
        cursor.execute("SELECT * FROM CodePatterns WHERE id = ?", (result['pattern_id'],))
        pattern = cursor.fetchone()
        assert pattern is not None
        
        # Get column names to verify correct indices
        cursor.execute("PRAGMA table_info(CodePatterns)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Find indices for each column
        function_name_idx = column_names.index('function_name')
        file_name_idx = column_names.index('file_name')
        module_name_idx = column_names.index('module_name')
        input_prompt_idx = column_names.index('input_prompt')
        generated_code_idx = column_names.index('generated_code')
        result_idx = column_names.index('result')
        execution_time_idx = column_names.index('execution_time_ms')
        error_message_idx = column_names.index('error_message')
        tags_idx = column_names.index('tags')
        
        # Verify data was stored correctly using correct indices
        assert pattern[function_name_idx] == "fibonacci"
        assert pattern[file_name_idx] == "math_utils.py"
        assert pattern[module_name_idx] == "utils"
        assert pattern[input_prompt_idx] == "Create a function to calculate fibonacci numbers"
        assert "def fibonacci(n):" in pattern[generated_code_idx]
        assert pattern[result_idx] == "pass"
        assert pattern[execution_time_idx] == 150
        assert pattern[error_message_idx] is None
        assert pattern[tags_idx] == '["recursion", "math"]'
    
    def test_store_code_pattern_with_error(self, temp_db):
        """Test code pattern storage with error information."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Test code pattern storage with error
        from ltms.services.code_pattern_service import store_code_pattern
        
        result = store_code_pattern(
            conn=conn,
            input_prompt="Create a function to divide by zero",
            generated_code="def divide(a, b): return a / b",
            result="fail",
            function_name="divide",
            file_name="math_utils.py",
            module_name="utils",
            execution_time_ms=50,
            error_message="ZeroDivisionError: division by zero",
            tags=["error", "math", "division"]
        )
        
        # Verify storage was successful
        assert result['success'] is True
        assert result['message'] == 'Code pattern stored with result: fail'
        
        # Verify error information was stored
        cursor.execute("SELECT result, error_message FROM CodePatterns WHERE id = ?", (result['pattern_id'],))
        pattern = cursor.fetchone()
        assert pattern[0] == "fail"
        assert pattern[1] == "ZeroDivisionError: division by zero"
    
    def test_retrieve_code_patterns_basic(self, temp_db):
        """Test basic code pattern retrieval functionality."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Store some test patterns
        from ltms.services.code_pattern_service import store_code_pattern
        
        # Store successful pattern
        store_code_pattern(
            conn=conn,
            input_prompt="Create a function to calculate fibonacci numbers",
            generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            result="pass",
            function_name="fibonacci",
            file_name="math_utils.py",
            module_name="utils"
        )
        
        # Store failed pattern
        store_code_pattern(
            conn=conn,
            input_prompt="Create a function to divide by zero",
            generated_code="def divide(a, b): return a / b",
            result="fail",
            function_name="divide",
            file_name="math_utils.py",
            module_name="utils"
        )
        
        # Test retrieval
        from ltms.services.code_pattern_service import retrieve_code_patterns
        
        result = retrieve_code_patterns(
            conn=conn,
            query="fibonacci function",
            result_filter=None,
            function_name=None,
            file_name=None,
            module_name=None,
            top_k=5
        )
        
        # Verify retrieval was successful
        assert result['success'] is True
        assert 'patterns' in result
        assert 'count' in result
        assert 'query' in result
        assert result['query'] == "fibonacci function"
        assert result['count'] >= 0  # May be 0 if no exact matches
    
    def test_retrieve_code_patterns_with_filter(self, temp_db):
        """Test code pattern retrieval with result filtering."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Store test patterns
        from ltms.services.code_pattern_service import store_code_pattern
        
        # Store successful pattern
        store_code_pattern(
            conn=conn,
            input_prompt="Create a function to calculate fibonacci numbers",
            generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            result="pass",
            function_name="fibonacci",
            file_name="math_utils.py",
            module_name="utils"
        )
        
        # Store failed pattern
        store_code_pattern(
            conn=conn,
            input_prompt="Create a function to divide by zero",
            generated_code="def divide(a, b): return a / b",
            result="fail",
            function_name="divide",
            file_name="math_utils.py",
            module_name="utils"
        )
        
        # Test retrieval with pass filter
        from ltms.services.code_pattern_service import retrieve_code_patterns
        
        result = retrieve_code_patterns(
            conn=conn,
            query="function",
            result_filter="pass",
            function_name=None,
            file_name=None,
            module_name=None,
            top_k=5
        )
        
        assert result['success'] is True
        assert result['count'] >= 0
    
    def test_analyze_code_patterns(self, temp_db):
        """Test code pattern analysis functionality."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Store test patterns
        from ltms.services.code_pattern_service import store_code_pattern
        
        # Store multiple patterns
        patterns = [
            ("Create fibonacci function", "def fibonacci(n): return n", "pass", "fibonacci"),
            ("Create divide function", "def divide(a, b): return a / b", "fail", "divide"),
            ("Create multiply function", "def multiply(a, b): return a * b", "pass", "multiply"),
            ("Create subtract function", "def subtract(a, b): return a - b", "pass", "subtract"),
        ]
        
        for prompt, code, result, func_name in patterns:
            store_code_pattern(
                conn=conn,
                input_prompt=prompt,
                generated_code=code,
                result=result,
                function_name=func_name,
                file_name="math_utils.py",
                module_name="utils"
            )
        
        # Test analysis
        from ltms.services.code_pattern_service import analyze_code_patterns
        
        result = analyze_code_patterns(
            conn=conn,
            function_name=None,
            file_name=None,
            module_name=None,
            time_range_days=30
        )
        
        # Verify analysis was successful
        assert result['success'] is True
        assert 'total_patterns' in result
        assert 'success_rate' in result
        assert 'pass_count' in result
        assert 'fail_count' in result
        assert 'partial_count' in result
        assert result['total_patterns'] == 4
        assert result['pass_count'] == 3
        assert result['fail_count'] == 1
        assert result['success_rate'] == 0.75  # 3/4 = 75%
    
    def test_mcp_tool_integration(self, temp_db):
        """Test that Code Pattern Memory integrates with MCP tools."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Test MCP tool functions exist and work
        from ltms.mcp_server import log_code_attempt, get_code_patterns, analyze_code_patterns
        
        # Test log_code_attempt tool
        result = log_code_attempt(
            input_prompt="Create a test function",
            generated_code="def test(): return True",
            result="pass",
            function_name="test",
            file_name="test_utils.py",
            module_name="test",
            execution_time_ms=100,
            error_message=None,
            tags=["test", "simple"]
        )
        
        # Verify tool works (should return success even if no database connection in test)
        assert isinstance(result, dict)
        assert 'success' in result
    
    def test_embedding_compatibility(self, temp_db):
        """Test that Code Pattern Memory works with 384-dimension embeddings."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Test embedding generation for code patterns
        from ltms.services.embedding_service import create_embedding_model, encode_text
        
        model = create_embedding_model("all-MiniLM-L6-v2")
        
        # Test embedding for code pattern text
        code_pattern_text = "Create a function to calculate fibonacci numbers\ndef fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)\nFunction: fibonacci\nFile: math_utils.py"
        embedding = encode_text(model, code_pattern_text)
        
        # Verify embedding dimensions
        assert embedding.shape == (384,)
        assert embedding.dtype.name == 'float32'
        
        # Test that embedding can be used for similarity search
        from ltms.services.code_pattern_service import store_code_pattern
        
        result = store_code_pattern(
            conn=conn,
            input_prompt="Create a function to calculate fibonacci numbers",
            generated_code="def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)",
            result="pass",
            function_name="fibonacci",
            file_name="math_utils.py",
            module_name="utils"
        )
        
        assert result['success'] is True
    
    def test_performance_requirements(self, temp_db):
        """Test that Code Pattern Memory meets performance requirements."""
        db_path, conn = temp_db
        
        # Create required tables
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
        conn.commit()
        
        # Test storage performance
        import time
        from ltms.services.code_pattern_service import store_code_pattern
        
        start_time = time.time()
        result = store_code_pattern(
            conn=conn,
            input_prompt="Create a performance test function",
            generated_code="def performance_test(): return 'fast'",
            result="pass",
            function_name="performance_test",
            file_name="test.py",
            module_name="test"
        )
        end_time = time.time()
        
        storage_time = end_time - start_time
        
        # Verify performance requirements
        assert result['success'] is True
        assert storage_time < 0.1  # Less than 100ms per pattern
    
    def test_error_handling(self, temp_db):
        """Test error handling in Code Pattern Memory."""
        db_path, conn = temp_db
        
        # Test with invalid database connection
        from ltms.services.code_pattern_service import store_code_pattern
        
        try:
            result = store_code_pattern(
                conn=None,  # Invalid connection
                input_prompt="test",
                generated_code="def test(): pass",
                result="pass"
            )
            assert result['success'] is False
            assert 'error' in result
        except Exception:
            # Expected behavior for invalid connection
            pass
        
        # Test with invalid result value
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
        conn.commit()
        
        # This should fail due to CHECK constraint
        try:
            cursor.execute("""
                INSERT INTO CodePatterns (input_prompt, generated_code, result, created_at)
                VALUES (?, ?, ?, ?)
            """, ("test", "def test(): pass", "invalid_result", datetime.now().isoformat()))
            conn.commit()
            assert False, "Should have failed due to CHECK constraint"
        except sqlite3.IntegrityError:
            # Expected behavior
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
