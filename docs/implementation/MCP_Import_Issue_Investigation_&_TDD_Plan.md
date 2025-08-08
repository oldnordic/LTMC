# MCP Import Issue Investigation & TDD Plan

## 🔍 **Root Cause Analysis**

### **Issue Description**
- **Error**: `ModuleNotFoundError: No module named 'core.config'`
- **Context**: Server works with `mcp dev` but fails when run directly
- **Location**: `tools/ask.py` line 7 and 13
- **Impact**: Prevents server from starting in direct execution mode

### **Why Tests Didn't Catch This**
1. **Different Execution Contexts**: Tests run in pytest context vs direct Python execution
2. **Import Path Differences**: `mcp dev` vs `python script.py` have different `sys.path` behavior
3. **Missing Test Coverage**: No tests for direct script execution scenarios
4. **Test Environment**: Tests may have been run from different working directories

## 📚 **Research Findings**

### **Python Import Path Resolution**
From Python documentation research:

1. **Execution Context Differences**:
   - `python script.py`: Prepends script's directory to `sys.path`
   - `python -m module`: Prepends current working directory to `sys.path`
   - `mcp dev`: Uses module import context with different path resolution

2. **sys.path Initialization**:
   ```python
   # From Python docs:
   # - python script.py: prepend script's directory
   # - python -m module: prepend current working directory  
   # - python -c code: prepend empty string (current working directory)
   ```

3. **Best Practices for MCP Servers**:
   - Use absolute imports with proper path setup
   - Handle multiple execution contexts
   - Use `importlib.util` for dynamic imports
   - Set up `sys.path` before any imports

### **MCP Server Configuration Best Practices**
From MCP server research:

1. **Import Structure**: MCP servers should be importable from any context
2. **Path Resolution**: Must work in both stdio and HTTP transport modes
3. **Error Handling**: Graceful fallbacks for import failures
4. **Configuration**: Environment-based path resolution

## 🎯 **Systematic Solution Design**

### **Phase 1: Proper Import Path Resolution**
```python
# Robust import path setup
import sys
import os
from pathlib import Path

def setup_import_paths():
    """Setup import paths for all execution contexts."""
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Add to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Change to project root for consistent behavior
    os.chdir(str(project_root))
    
    return project_root
```

### **Phase 2: Import Error Handling**
```python
# Robust import with fallbacks
def safe_import(module_name, fallback_path=None):
    """Import module with fallback path handling."""
    try:
        return __import__(module_name)
    except ImportError:
        if fallback_path:
            sys.path.insert(0, fallback_path)
            return __import__(module_name)
        raise
```

### **Phase 3: MCP Server Structure**
```python
# Proper MCP server structure
from fastmcp import FastMCP

# Setup paths before any imports
setup_import_paths()

# Now safe to import
from core.config import settings
from tools.ask import ask_with_context
# ... other imports

# Create server
server = FastMCP("LTMC Server")
```

## 🧪 **TDD Implementation Plan**

### **Test 1: Import Path Resolution**
```python
def test_import_path_resolution():
    """Test that imports work in all execution contexts."""
    # Test direct execution
    # Test module execution  
    # Test mcp dev context
    pass
```

### **Test 2: Execution Context Compatibility**
```python
def test_execution_context_compatibility():
    """Test server works in all execution contexts."""
    # Test python script.py
    # Test python -m module
    # Test mcp dev
    pass
```

### **Test 3: Import Error Handling**
```python
def test_import_error_handling():
    """Test graceful handling of import errors."""
    # Test missing modules
    # Test fallback paths
    # Test error reporting
    pass
```

### **Test 4: MCP Server Integration**
```python
def test_mcp_server_integration():
    """Test full MCP server functionality."""
    # Test server creation
    # Test tool registration
    # Test client communication
    pass
```

## 📋 **Implementation Steps**

### **Step 1: Create Import Utilities**
1. Create `core/import_utils.py` with robust path resolution
2. Add fallback import mechanisms
3. Test in all execution contexts

### **Step 2: Update Server Structure**
1. Update `ltms/production_fastmcp_server.py` to use import utilities
2. Add proper error handling
3. Test with `mcp dev`

### **Step 3: Update Tool Imports**
1. Update all tool files to use robust imports
2. Add fallback mechanisms
3. Test individual tools

### **Step 4: Comprehensive Testing**
1. Test all execution contexts
2. Test import error scenarios
3. Test MCP server functionality
4. Test client communication

## 🎯 **Success Criteria**

- [ ] Server starts successfully with `python ltms/production_fastmcp_server.py`
- [ ] Server works with `mcp dev ltms/production_fastmcp_server.py`
- [ ] All imports work in all execution contexts
- [ ] Graceful error handling for missing modules
- [ ] Tests pass in all environments
- [ ] No import errors in logs

## 📝 **Documentation Updates**

- [ ] Update `LTMC_Project_Status_Tracking.md` with findings
- [ ] Document import best practices
- [ ] Update troubleshooting guide
- [ ] Add execution context documentation

## 🔄 **Next Actions**

1. **Implement import utilities** with TDD approach
2. **Update server structure** with proper imports
3. **Test all execution contexts** systematically
4. **Document findings** and best practices
5. **Update tests** to catch similar issues

---

**Status**: Investigation Complete - Ready for Implementation
**Priority**: High - Blocking server functionality
**Approach**: Systematic TDD with research-based solutions
