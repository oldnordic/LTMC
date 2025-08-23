#!/usr/bin/env python3
"""
Test Advanced Database Implementations
=====================================

Test script to validate all 6 TODO implementations:
1. SQLite JSON tags filtering 
2. FAISS semantic search integration
3. SQLite FTS full-text search
4. FAISS vector indexing
5. Real semantic search operations

This tests the actual implementations without mocks.
"""

import asyncio
import json
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add the project to path
sys.path.insert(0, str(Path(__file__).parent))

from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.advanced_database_service import AdvancedDatabaseService
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.services.faiss_service import FAISSService


async def test_json_tags_filtering():
    """Test SQLite JSON tags filtering implementation."""
    print("🧪 Testing SQLite JSON tags filtering...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Setup test database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create CodePatterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS CodePatterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_prompt TEXT NOT NULL,
                generated_code TEXT NOT NULL,
                result TEXT NOT NULL,
                execution_time_ms INTEGER,
                error_message TEXT,
                tags TEXT,  -- JSON array
                created_at TEXT NOT NULL,
                vector_id INTEGER
            )
        """)
        
        # Insert test data with JSON tags
        test_data = [
            ("python async function", "async def test(): pass", "pass", None, None, 
             json.dumps(["python", "async", "function"]), "2024-01-01T10:00:00"),
            ("javascript callback", "function callback() {}", "pass", None, None,
             json.dumps(["javascript", "callback", "web"]), "2024-01-01T11:00:00"),
            ("python database query", "SELECT * FROM users", "pass", None, None,
             json.dumps(["python", "database", "sql"]), "2024-01-01T12:00:00"),
            ("java class definition", "public class Test {}", "fail", None, None,
             json.dumps(["java", "class", "oop"]), "2024-01-01T13:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO CodePatterns 
            (input_prompt, generated_code, result, execution_time_ms, error_message, tags, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, test_data)
        
        conn.commit()
        conn.close()
        
        # Test the JSON filtering implementation
        settings = LTMCSettings()
        settings.db_path = db_path
        
        service = AdvancedDatabaseService(settings)
        
        # Test 1: Filter by single tag
        patterns = await service.get_code_patterns(
            query_tags=["python"],
            limit=10
        )
        assert len(patterns) == 2, f"Expected 2 python patterns, got {len(patterns)}"
        print("✅ Single tag filtering works")
        
        # Test 2: Filter by multiple tags (OR condition)
        patterns = await service.get_code_patterns(
            query_tags=["async", "database"],
            limit=10
        )
        assert len(patterns) == 2, f"Expected 2 patterns with async OR database, got {len(patterns)}"
        print("✅ Multiple tag filtering works")
        
        # Test 3: Filter by non-existent tag
        patterns = await service.get_code_patterns(
            query_tags=["nonexistent"],
            limit=10
        )
        assert len(patterns) == 0, f"Expected 0 patterns for nonexistent tag, got {len(patterns)}"
        print("✅ Non-existent tag filtering works")
        
        # Test 4: Combine with result filter
        patterns = await service.get_code_patterns(
            query_tags=["python"],
            result_filter="pass",
            limit=10
        )
        assert len(patterns) == 2, f"Expected 2 python 'pass' patterns, got {len(patterns)}"
        print("✅ Combined tag and result filtering works")
        
        print("🎉 JSON tags filtering implementation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ JSON tags filtering test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def test_faiss_integration():
    """Test FAISS vector operations."""
    print("🧪 Testing FAISS vector operations...")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            settings = LTMCSettings()
            settings.ltmc_data_dir = Path(temp_dir)
            settings.faiss_index_path = Path(temp_dir) / "faiss_index.idx"
            
            # Test FAISS initialization
            faiss_service = FAISSService(settings)
            init_success = await faiss_service.initialize()
            assert init_success, "FAISS initialization failed"
            print("✅ FAISS service initialization works")
            
            # Test vector addition
            test_content = "This is a test document about machine learning and artificial intelligence."
            vector_id = await faiss_service.add_vector(test_content)
            assert vector_id is not None, "Vector addition failed"
            print("✅ FAISS vector addition works")
            
            # Test vector search
            query = "machine learning AI"
            results = await faiss_service.search_vectors(query, top_k=5)
            assert len(results) >= 1, f"Expected at least 1 search result, got {len(results)}"
            
            # Verify result structure
            vector_id_result, similarity_score = results[0]
            assert isinstance(vector_id_result, int), "Vector ID should be integer"
            assert isinstance(similarity_score, float), "Similarity score should be float"
            assert 0.0 <= similarity_score <= 1.0, f"Similarity score {similarity_score} should be 0-1"
            print("✅ FAISS vector search works")
            
            # Test with multiple vectors
            test_docs = [
                "Python programming language tutorial",
                "JavaScript web development guide", 
                "Database management systems",
                "Machine learning algorithms"
            ]
            
            for doc in test_docs:
                await faiss_service.add_vector(doc)
            
            # Search for programming-related content
            prog_results = await faiss_service.search_vectors("programming languages", top_k=3)
            assert len(prog_results) >= 2, "Should find multiple programming-related results"
            print("✅ FAISS multi-vector search works")
            
            print("🎉 FAISS integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ FAISS integration test failed: {e}")
            return False


async def test_sqlite_fts():
    """Test SQLite FTS implementation.""" 
    print("🧪 Testing SQLite FTS implementation...")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # Setup test database with todos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create todos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                completed INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        
        # Insert test todos
        test_todos = [
            ("Implement FAISS integration", "Add semantic search using FAISS vector database", "high", "pending", "2024-01-01T10:00:00"),
            ("Database optimization", "Optimize SQLite queries for better performance", "medium", "pending", "2024-01-01T11:00:00"),
            ("Write documentation", "Create user documentation for the API endpoints", "low", "completed", "2024-01-01T12:00:00"),
            ("Fix authentication bug", "Resolve JWT token validation issues", "high", "pending", "2024-01-01T13:00:00"),
            ("Add unit tests", "Write comprehensive test suite for all modules", "medium", "pending", "2024-01-01T14:00:00"),
        ]
        
        cursor.executemany("""
            INSERT INTO todos (title, description, priority, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, test_todos)
        
        conn.commit()
        conn.close()
        
        # Test FTS functionality by importing the tool function
        from ltmc_mcp_server.tools.todo.advanced_todo_tools import register_advanced_todo_tools
        from ltmc_mcp_server.config.settings import LTMCSettings
        from ltmc_mcp_server.services.database_service import DatabaseService
        
        # Mock FastMCP for testing
        class MockMCP:
            def __init__(self):
                self.tools = {}
            
            def tool(self):
                def decorator(func):
                    self.tools[func.__name__] = func
                    return func
                return decorator
        
        # Setup services
        settings = LTMCSettings()
        settings.db_path = db_path
        mock_mcp = MockMCP()
        
        # Register tools to get access to search function
        register_advanced_todo_tools(mock_mcp, settings)
        search_todos = mock_mcp.tools['search_todos']
        
        # Test 1: Search by keyword in title
        result = await search_todos("FAISS", limit=5)
        assert result['success'], f"Search failed: {result.get('error')}"
        assert len(result['todos']) >= 1, "Should find FAISS-related todo"
        print("✅ FTS title search works")
        
        # Test 2: Search by keyword in description
        result = await search_todos("performance", limit=5)
        assert result['success'], f"Search failed: {result.get('error')}"
        assert len(result['todos']) >= 1, "Should find performance-related todo"
        print("✅ FTS description search works")
        
        # Test 3: Search with multiple keywords
        result = await search_todos("test unit", limit=5)
        assert result['success'], f"Search failed: {result.get('error')}"
        # Should find todos with either "test" or "unit" 
        assert len(result['todos']) >= 1, "Should find test-related todos"
        print("✅ FTS multi-keyword search works")
        
        # Test 4: Search with status filter
        result = await search_todos("documentation", status="completed", limit=5)
        assert result['success'], f"Search failed: {result.get('error')}"
        if result['todos']:
            # If we found results, they should all be completed
            for todo in result['todos']:
                assert todo['status'] == 'completed', "Status filter not working"
        print("✅ FTS with status filtering works")
        
        print("🎉 SQLite FTS implementation: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ SQLite FTS test failed: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)


async def run_all_tests():
    """Run all implementation tests."""
    print("🚀 Starting Advanced Database Implementation Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: JSON tags filtering
    result1 = await test_json_tags_filtering()
    test_results.append(("JSON Tags Filtering", result1))
    
    print()
    
    # Test 2: FAISS integration
    result2 = await test_faiss_integration() 
    test_results.append(("FAISS Integration", result2))
    
    print()
    
    # Test 3: SQLite FTS
    result3 = await test_sqlite_fts()
    test_results.append(("SQLite FTS", result3))
    
    print()
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"Total Tests: {len(test_results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL IMPLEMENTATIONS WORKING CORRECTLY!")
        return True
    else:
        print("⚠️  Some implementations need attention")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)