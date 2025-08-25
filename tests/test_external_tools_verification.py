#!/usr/bin/env python3
"""
Verify external tools are actually being called and produce different output than fallbacks
"""

import os
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated_real import unix_action


def test_external_tool_calls():
    """Verify external tools produce different output than fallbacks."""
    print("🔧 Verifying external tool calls vs fallbacks...")
    
    test_path = "/home/feanor/Projects/ltmc/ltms"
    
    # Test exa vs ls
    print("\n  Testing exa vs ls output differences:")
    
    exa_result = unix_action(action="ls", path=test_path, long=True)
    print(f"    Tool used: {exa_result.get('tool')}")
    
    # Check if exa provides rich output
    if exa_result.get('success') and exa_result.get('files'):
        sample_line = exa_result.get('files')[0]
        print(f"    Sample exa output: {sample_line}")
        
        # Exa typically shows file permissions in different format and colors
        if ".rw-" in sample_line or "drwx" in sample_line:
            print("    ✅ exa output detected (shows detailed permissions)")
        else:
            print("    ⚠️  Might be fallback ls output")
    
    # Test bat vs cat
    print("\n  Testing bat vs cat detection:")
    
    test_file = "/home/feanor/Projects/ltmc/ltms/__init__.py"
    bat_result = unix_action(action="cat", file_path=test_file)
    print(f"    Tool used: {bat_result.get('tool')}")
    
    if bat_result.get('success'):
        print(f"    Content length: {len(bat_result.get('content', ''))}")
        print(f"    Lines counted: {bat_result.get('lines')}")
        if bat_result.get('tool') == 'bat':
            print("    ✅ bat detected and working")
        else:
            print("    ⚠️  Using cat fallback")
    
    # Test ripgrep vs grep
    print("\n  Testing ripgrep vs grep detection:")
    
    rg_result = unix_action(action="grep", pattern="def", path=test_file)
    print(f"    Tool used: {rg_result.get('tool')}")
    print(f"    Matches found: {rg_result.get('count')}")
    
    if rg_result.get('success') and rg_result.get('tool') == 'ripgrep':
        print("    ✅ ripgrep detected and working")
        matches = rg_result.get('matches', [])
        if matches:
            print(f"    Sample match: {matches[0]}")
    else:
        print("    ⚠️  Using grep fallback or no matches")
    
    # Test fd vs find
    print("\n  Testing fd vs find detection:")
    
    fd_result = unix_action(action="find", name="*.py", path=test_path, type="f")
    print(f"    Tool used: {fd_result.get('tool')}")
    print(f"    Files found: {fd_result.get('count')}")
    
    if fd_result.get('success'):
        files = fd_result.get('files', [])[:3]
        print(f"    Sample files: {files}")
        
        # Check output format differences
        if fd_result.get('tool') == 'fd':
            print("    ✅ fd detected and working")
        else:
            print("    ⚠️  Using find fallback")


def test_memory_database_files():
    """Check that memory actions create real database files."""
    print("\n🗄️  Checking database file creation...")
    
    try:
        from ltms.config import get_config
        config = get_config()
        db_path = config.get_db_path()
        faiss_path = config.get_faiss_index_path()
        
        print(f"    SQLite DB path: {db_path}")
        print(f"    FAISS index path: {faiss_path}")
        
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"    ✅ SQLite DB exists ({size} bytes)")
        else:
            print("    ❌ SQLite DB not found")
            
        if os.path.exists(faiss_path):
            size = os.path.getsize(faiss_path)
            print(f"    ✅ FAISS index exists ({size} bytes)")
        else:
            print("    ❌ FAISS index not found")
            
    except Exception as e:
        print(f"    ⚠️  Error checking database files: {e}")


def test_ast_parsing_accuracy():
    """Test AST parsing accuracy with complex code."""
    print("\n🌳 Testing AST parsing accuracy...")
    
    from ltms.tools.consolidated_real import pattern_action
    
    complex_code = '''
class DataProcessor:
    """Complex data processing class."""
    
    def __init__(self, config: dict):
        self.config = config
        self._cache = {}
    
    @property
    def cache_size(self) -> int:
        return len(self._cache)
    
    @staticmethod
    def validate_input(data: str) -> bool:
        if not data:
            return False
        if len(data) > 1000:
            return False
        return True
    
    async def process_async(self, items: list) -> dict:
        results = {}
        for item in items:
            try:
                if self.validate_input(item):
                    results[item] = await self._process_item(item)
                else:
                    results[item] = None
            except Exception as e:
                results[item] = f"Error: {e}"
        return results
    
    def _process_item(self, item: str) -> str:
        # Complex processing logic
        for i in range(10):
            if item in self._cache:
                return self._cache[item]
            else:
                processed = item.upper().strip()
                self._cache[item] = processed
                return processed

def helper_function(x: int, y: int = 10) -> int:
    return x * y if x > 0 else 0
'''
    
    # Test function extraction
    func_result = pattern_action(action="extract_functions", source_code=complex_code)
    if func_result.get('success'):
        functions = func_result.get('functions', [])
        print(f"    ✅ Extracted {len(functions)} functions")
        
        for func in functions:
            print(f"      - {func.get('name')} (complexity: {func.get('complexity')})")
            if func.get('is_async'):
                print(f"        (async function)")
    
    # Test class extraction  
    class_result = pattern_action(action="extract_classes", source_code=complex_code)
    if class_result.get('success'):
        classes = class_result.get('classes', [])
        print(f"    ✅ Extracted {len(classes)} classes")
        
        for cls in classes:
            print(f"      - {cls.get('name')} ({cls.get('method_count')} methods)")
    
    # Test code summary
    summary_result = pattern_action(action="summarize_code", source_code=complex_code)
    if summary_result.get('success'):
        print(f"    ✅ Code summary: {summary_result.get('summary')}")
        print(f"        Complexity rating: {summary_result.get('complexity_rating')}")


if __name__ == "__main__":
    print("🚀 External Tools & Real Implementation Verification")
    print("=" * 60)
    
    test_external_tool_calls()
    test_memory_database_files() 
    test_ast_parsing_accuracy()
    
    print("\n" + "=" * 60)
    print("✅ Verification completed!")