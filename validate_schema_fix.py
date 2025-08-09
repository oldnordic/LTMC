#!/usr/bin/env python3
"""Validate that schema fixes work correctly."""

import sqlite3
import json
from datetime import datetime

DB_PATH = '/home/feanor/Projects/lmtc/ltmc.db'

def test_code_pattern_operations():
    """Test all code pattern operations work after fix."""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Test INSERT with all new columns
        cursor = conn.cursor()
        
        test_data = {
            'function_name': 'test_function',
            'file_name': 'test.py',
            'module_name': 'test_module',
            'input_prompt': 'Create a test function',
            'generated_code': 'def test_function(): pass',
            'result': 'pass',
            'execution_time_ms': 100,
            'error_message': None,
            'tags': json.dumps(['test', 'function']),
            'created_at': datetime.now().isoformat(),
            'vector_id': 1
        }
        
        # Test INSERT
        cursor.execute("""
            INSERT INTO CodePatterns (
                function_name, file_name, module_name, input_prompt, generated_code,
                result, execution_time_ms, error_message, tags, created_at, vector_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(test_data.values()))
        
        pattern_id = cursor.lastrowid
        print(f"✅ INSERT test passed - Pattern ID: {pattern_id}")
        
        # Test SELECT with all columns
        cursor.execute("""
            SELECT id, function_name, file_name, module_name, input_prompt,
                   generated_code, result, execution_time_ms, error_message,
                   tags, created_at, vector_id
            FROM CodePatterns WHERE id = ?
        """, (pattern_id,))
        
        row = cursor.fetchone()
        if row:
            print("✅ SELECT test passed - All columns retrievable")
            print(f"   Retrieved: function_name={row[1]}, file_name={row[2]}")
        else:
            print("❌ SELECT test failed - No data retrieved")
            return False
        
        # Test UPDATE
        cursor.execute("""
            UPDATE CodePatterns SET function_name = ? WHERE id = ?
        """, ('updated_function', pattern_id))
        
        print("✅ UPDATE test passed")
        
        # Test filtering by new columns
        cursor.execute("""
            SELECT COUNT(*) FROM CodePatterns 
            WHERE function_name = ? AND result = ?
        """, ('updated_function', 'pass'))
        
        count = cursor.fetchone()[0]
        if count == 1:
            print("✅ FILTER test passed")
        else:
            print(f"❌ FILTER test failed - Expected 1, got {count}")
            return False
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
        
    finally:
        conn.close()

def test_mcp_tool_compatibility():
    """Test that the schema works with actual MCP tool parameters."""
    conn = sqlite3.connect(DB_PATH)
    
    try:
        cursor = conn.cursor()
        
        # Simulate data that would come from log_code_attempt MCP tool
        mcp_test_data = (
            'test_mcp_function',      # function_name
            'mcp_test.py',            # file_name  
            'mcp_module',             # module_name
            'Write a function that returns True',  # input_prompt
            'def test_mcp_function():\n    return True',  # generated_code
            'pass',                   # result
            250,                      # execution_time_ms
            None,                     # error_message
            json.dumps(['mcp', 'test', 'validation']),  # tags
            datetime.now().isoformat(),  # created_at
            2                         # vector_id
        )
        
        # Test the exact INSERT pattern used by MCP tools
        cursor.execute("""
            INSERT INTO CodePatterns (
                function_name, file_name, module_name, input_prompt, generated_code,
                result, execution_time_ms, error_message, tags, created_at, vector_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mcp_test_data)
        
        mcp_pattern_id = cursor.lastrowid
        print(f"✅ MCP tool INSERT compatibility test passed - Pattern ID: {mcp_pattern_id}")
        
        # Test retrieval with filters (used by get_code_patterns)
        cursor.execute("""
            SELECT id, function_name, file_name, module_name, input_prompt,
                   generated_code, result, execution_time_ms, error_message,
                   tags, created_at, vector_id
            FROM CodePatterns
            WHERE result = ? AND function_name = ?
            ORDER BY created_at DESC
        """, ('pass', 'test_mcp_function'))
        
        rows = cursor.fetchall()
        if len(rows) >= 1:
            print(f"✅ MCP tool filtering compatibility test passed - Found {len(rows)} patterns")
        else:
            print("❌ MCP tool filtering compatibility test failed")
            return False
        
        # Test analysis query (used by analyze_code_patterns)
        cursor.execute("""
            SELECT 
                COUNT(*) as total_patterns,
                SUM(CASE WHEN result = 'pass' THEN 1 ELSE 0 END) as pass_count,
                SUM(CASE WHEN result = 'fail' THEN 1 ELSE 0 END) as fail_count,
                SUM(CASE WHEN result = 'partial' THEN 1 ELSE 0 END) as partial_count,
                AVG(execution_time_ms) as avg_execution_time
            FROM CodePatterns
            WHERE created_at >= datetime('now', '-30 days')
        """)
        
        analysis_row = cursor.fetchone()
        if analysis_row and analysis_row[0] >= 2:  # We inserted 2 test records
            print(f"✅ MCP tool analysis compatibility test passed - {analysis_row[0]} total patterns")
        else:
            print("❌ MCP tool analysis compatibility test failed")
            return False
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ MCP compatibility test failed with error: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("Schema Fix Validation")
    print("=" * 30)
    
    basic_test_passed = test_code_pattern_operations()
    mcp_test_passed = test_mcp_tool_compatibility()
    
    if basic_test_passed and mcp_test_passed:
        print("\n🎉 ALL TESTS PASSED - Schema fix successful!")
        print("✅ CodePatterns table ready for MCP tools")
        print("✅ log_code_attempt tool will work")
        print("✅ get_code_patterns tool will work")
        print("✅ analyze_code_patterns tool will work")
    else:
        print("\n💥 TESTS FAILED - Schema fix incomplete!")
        if not basic_test_passed:
            print("❌ Basic database operations failed")
        if not mcp_test_passed:
            print("❌ MCP tool compatibility failed")