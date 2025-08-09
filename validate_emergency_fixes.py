#!/usr/bin/env python3
"""Emergency fix validation script for LTMC production system.

This script validates that all critical production issues have been resolved:
1. Import dependencies are working
2. Database variable references are consistent  
3. Function parameters are aligned
4. Core system functionality is operational
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import_dependencies():
    """Test that all critical imports work without errors."""
    print("🔧 Testing import dependencies...")
    
    try:
        # Test previously broken import in context_service
        from ltms.services.context_service import get_context_for_query
        from ltms.database.context_linking import store_context_links
        print("  ✅ Context service imports working")
        
        # Test MCP server imports
        from ltms.mcp_server import list_todos, get_messages_for_chunk_tool
        print("  ✅ MCP server imports working")
        
        return True
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error: {e}")
        return False

def test_database_operations():
    """Test basic database operations work without variable reference errors."""
    print("🔧 Testing database operations...")
    
    try:
        # Create temporary database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.environ["DB_PATH"] = db_path
        
        from ltms.database.connection import get_db_connection, close_db_connection
        from ltms.database.schema import create_tables
        
        # Test database connection and schema creation
        conn = get_db_connection(db_path)
        create_tables(conn)
        print("  ✅ Database connection and schema creation working")
        
        # Test previously broken functions
        from ltms.mcp_server import (
            get_messages_for_chunk_tool, 
            get_context_usage_statistics_tool
        )
        
        # These should not throw NameError anymore
        result1 = get_messages_for_chunk_tool(chunk_id=999)
        result2 = get_context_usage_statistics_tool()
        
        print("  ✅ Database variable references working")
        
        # Cleanup
        close_db_connection(conn)
        os.close(db_fd)
        os.unlink(db_path)
        
        return True
    except Exception as e:
        print(f"  ❌ Database operation error: {e}")
        return False

def test_function_parameters():
    """Test that function parameter signatures are consistent."""
    print("🔧 Testing function parameter consistency...")
    
    try:
        # Setup temporary database for todo tests
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        os.environ["DB_PATH"] = db_path
        
        from ltms.database.connection import get_db_connection, close_db_connection
        from ltms.database.schema import create_tables
        from ltms.mcp_server import list_todos, add_todo
        
        conn = get_db_connection(db_path)
        create_tables(conn)
        close_db_connection(conn)
        
        # Test list_todos with various parameter combinations
        result1 = list_todos()  # No parameters
        result2 = list_todos(completed=None)  # Explicit None
        result3 = list_todos(completed=False)  # Boolean parameter
        
        print("  ✅ list_todos parameter variations working")
        
        # Test add_todo
        result4 = add_todo("Test todo", "Test description")
        print("  ✅ add_todo parameters working")
        
        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)
        
        return True
    except Exception as e:
        print(f"  ❌ Function parameter error: {e}")
        return False

def test_core_functionality():
    """Test that core LTMC functionality is operational."""
    print("🔧 Testing core system functionality...")
    
    try:
        # Setup environment
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        index_path = tempfile.mkdtemp()
        os.environ["DB_PATH"] = db_path
        os.environ["FAISS_INDEX_PATH"] = index_path
        
        from ltms.mcp_server import store_memory, log_chat
        
        # Test memory storage
        store_result = store_memory(
            file_name="validation_test.md",
            content="Emergency fix validation test content"
        )
        
        if store_result['success']:
            print("  ✅ Memory storage working")
        else:
            print(f"  ❌ Memory storage failed: {store_result.get('error')}")
            return False
        
        # Test chat logging  
        chat_result = log_chat(
            conversation_id="validation_test",
            role="system",
            content="Emergency fix validation complete",
            source_tool="claude-code"
        )
        
        if chat_result['success']:
            print("  ✅ Chat logging working")
        else:
            print(f"  ❌ Chat logging failed: {chat_result.get('error')}")
            return False
        
        # Cleanup
        os.close(db_fd)
        os.unlink(db_path)
        
        return True
    except Exception as e:
        print(f"  ❌ Core functionality error: {e}")
        return False

def main():
    """Run all emergency fix validations."""
    print("🚨 LTMC Emergency Fix Validation")
    print("=" * 50)
    
    tests = [
        ("Import Dependencies", test_import_dependencies),
        ("Database Operations", test_database_operations), 
        ("Function Parameters", test_function_parameters),
        ("Core Functionality", test_core_functionality)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test:")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("🎯 VALIDATION RESULTS:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🏆 ALL EMERGENCY FIXES VALIDATED - SYSTEM OPERATIONAL")
        print("🎉 Production environment restored to full functionality!")
        return 0
    else:
        print("🚨 SOME TESTS FAILED - ADDITIONAL FIXES REQUIRED")
        return 1

if __name__ == "__main__":
    sys.exit(main())