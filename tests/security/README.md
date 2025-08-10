# Phase 1 TDD Security Test Framework

## Overview

This directory contains the **Test-Driven Development (TDD) security test framework** for Phase 1 of the LTMC Taskmaster integration. Following pure TDD methodology, these tests are written **FIRST** and will **FAIL initially** - this is expected and correct.

## TDD Philosophy

### Why Tests Fail Initially
- **Security components don't exist yet** - `ltms/security/project_isolation.py` and `ltms/security/path_security.py` are not implemented
- **MCP tools lack security parameters** - `store_memory`, `retrieve_memory`, etc. don't support `project_id` parameter
- **This is INTENTIONAL** - tests define the exact requirements before implementation

### TDD Process
1. ✅ **Write failing tests** (this step - DONE)
2. 🔄 **Run tests to confirm failures** (proves we're testing the right things)
3. 🔧 **Implement minimum code to make tests pass**
4. ♻️ **Refactor and improve while keeping tests passing**

## Test Structure

### Core Security Tests

#### `test_project_isolation.py`
- **Purpose**: Tests multi-project isolation and security
- **Key Components Tested** (not yet implemented):
  - `ProjectIsolationManager` class
  - `validate_project_access()` method
  - `get_scoped_database_path()` method
  - `get_scoped_redis_key()` method
- **Security Scenarios**:
  - Valid project access validation
  - Cross-project access blocking
  - Path traversal prevention
  - Unauthorized project rejection

#### `test_path_security.py`
- **Purpose**: Tests comprehensive path validation and injection prevention
- **Key Components Tested** (not yet implemented):
  - `SecurePathValidator` class
  - `validate_file_operation()` method
  - `sanitize_user_input()` method
- **Attack Vectors Tested**:
  - Path traversal (../../../etc/passwd)
  - Code injection (__import__, eval, system commands)
  - System file access (/etc/passwd, /root/.ssh/)
  - Unicode normalization attacks
  - Length-based attacks

### Performance Tests

#### `test_phase1_performance.py`
- **Purpose**: Ensures security doesn't degrade performance
- **Requirements**:
  - Project isolation: <5ms per operation
  - Path validation: <3ms per operation
  - Combined overhead: <10ms total
- **Test Types**:
  - Baseline performance measurement
  - Security overhead benchmarking
  - Concurrent load testing
  - Stress testing under attack

### Test Fixtures

#### `conftest.py`
- **Multi-project configurations** for realistic testing
- **Attack vector collections** (path traversal, code injection, etc.)
- **System sensitive paths** that must be blocked
- **Performance test data** for benchmarking
- **LTMC server integration** for real system testing

## Running the Tests

### Expected Results (Initial State)

```bash
# Run project isolation tests
python -m pytest tests/security/test_project_isolation.py -v
# EXPECTED: ALL TESTS FAIL (components don't exist)

# Run path security tests  
python -m pytest tests/security/test_path_security.py -v
# EXPECTED: ALL TESTS FAIL (components don't exist)

# Run performance tests
python -m pytest tests/performance/test_phase1_performance.py -v
# EXPECTED: Most tests FAIL, some baseline tests MAY PASS
```

### What Failures Mean

#### ✅ Good Failures (Expected)
```
ImportError: No module named 'ltms.security.project_isolation'
ImportError: No module named 'ltms.security.path_security'
TypeError: store_memory() got an unexpected keyword argument 'project_id'
```

#### ❌ Bad Failures (Investigate)
```
requests.exceptions.ConnectionError: Failed to connect to LTMC server
AssertionError: Server process has terminated
```

### After Implementation

Once security components are implemented, run tests again:
```bash
# Should start passing as components are implemented
python -m pytest tests/security/ -v --tb=short
```

## Security Requirements Defined by Tests

### Project Isolation Requirements
- ✅ **Project Registration**: Support for multiple isolated projects
- ✅ **Path Validation**: Prevent cross-project file access
- ✅ **Database Scoping**: Project-specific database paths
- ✅ **Redis Namespacing**: Project-isolated cache keys
- ✅ **Performance**: <5ms validation time

### Path Security Requirements  
- ✅ **Path Traversal Prevention**: Block ../../../ attacks
- ✅ **Code Injection Prevention**: Block __import__, eval, system commands
- ✅ **System File Protection**: Block access to /etc/, /root/, etc.
- ✅ **Input Sanitization**: Remove dangerous characters
- ✅ **Performance**: <3ms validation time

### Integration Requirements
- ✅ **MCP Tool Integration**: All 28 tools support project_id parameter
- ✅ **Backward Compatibility**: Existing functionality preserved
- ✅ **Error Handling**: Security violations return clear error messages
- ✅ **Performance**: <10ms total overhead per tool call

## Implementation Guidance

### Phase 1.1: Create Security Components

1. **Create directory structure**:
```bash
mkdir -p ltms/security
touch ltms/security/__init__.py
```

2. **Implement `ltms/security/project_isolation.py`**:
```python
class SecurityError(Exception):
    """Security violation exception"""
    pass

class ProjectConfigError(Exception):
    """Project configuration error"""
    pass

class ProjectIsolationManager:
    def __init__(self, project_root: Path):
        # Implementation based on failing tests
        pass
    
    def validate_project_access(self, project_id: str, operation: str, resource_path: str) -> bool:
        # Implementation based on test requirements
        pass
```

3. **Implement `ltms/security/path_security.py`**:
```python
class SecurePathValidator:
    def __init__(self, secure_root: Path):
        # Implementation based on failing tests
        pass
    
    def validate_file_operation(self, path: str, operation_type: str, project_id: str) -> bool:
        # Implementation based on test requirements
        pass
```

### Phase 1.2: Integrate with MCP Tools

1. **Modify `ltms/mcp_server.py`**:
```python
# Add project_id parameter to existing tools
@mcp.tool()
def store_memory(file_name: str, content: str, resource_type: str = "document", project_id: str = "default"):
    # Add security validation before existing logic
    isolation_manager.validate_project_access(project_id, "write", file_name)
    # ... existing implementation
```

### Phase 1.3: Run Tests and Iterate

1. **Run tests frequently** during implementation
2. **Fix one failing test at a time**
3. **Ensure performance requirements are met**
4. **Validate with integration tests**

## Test Categories by Priority

### P0 - Critical Security Tests
- Cross-project access blocking
- Path traversal prevention  
- System file access blocking
- Basic performance requirements

### P1 - Advanced Security Tests
- Code injection prevention
- Unicode attack prevention
- Concurrent security validation
- Attack load performance

### P2 - Edge Case Tests
- Case sensitivity bypasses
- Length-based attacks
- Memory usage under stress
- Complex encoding attacks

## Success Criteria

### Phase 1.1 Complete
- ✅ `ProjectIsolationManager` tests pass
- ✅ `SecurePathValidator` tests pass
- ✅ Basic integration tests pass
- ✅ Performance under <10ms total

### Phase 1.2 Complete  
- ✅ All MCP tools support project isolation
- ✅ Security validation integrated
- ✅ Backward compatibility maintained
- ✅ Integration tests pass

### Phase 1.3 Complete
- ✅ All security tests pass
- ✅ Performance requirements met
- ✅ Attack vector tests pass
- ✅ System ready for Phase 2

## Monitoring and Maintenance

### Test Execution Schedule
- **During development**: Run relevant tests after each change
- **Before commits**: Run full security test suite
- **CI/CD integration**: Automated testing on all changes

### Performance Monitoring
- Track response times for security operations
- Monitor memory usage during stress tests
- Validate concurrent performance regularly

### Security Updates
- Add new attack vectors to test suite as discovered
- Update test cases for new security requirements
- Maintain test coverage above 95% for security components

This TDD framework ensures Phase 1 security implementation is robust, performant, and thoroughly tested before deployment.