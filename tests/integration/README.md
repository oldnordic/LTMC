# LTMC Integration Tests - REAL SYSTEM TESTING ONLY

## 🎯 CRITICAL TESTING PHILOSOPHY

**MANDATORY**: These integration tests use **REAL COMPONENTS ONLY** - NO MOCKS!

- ✅ **Real LTMC server processes** (HTTP and stdio transport)
- ✅ **Real database connections** (SQLite, Redis, Neo4j, Qdrant when available)
- ✅ **Real HTTP requests** to actual running servers
- ✅ **Real file operations** with actual filesystem access
- ✅ **Real security validation** with actual attack vectors
- ✅ **Real performance monitoring** with actual resource usage
- ✅ **Real multi-project isolation** with concurrent access testing

❌ **FORBIDDEN**: Mocks, stubs, fake responses, placeholder implementations

## 📋 Test Suite Overview

### 1. `test_full_system_integration.py` 
**Complete System Integration Testing**
- **Phase 0**: Mandatory system startup validation (`python server.py` must work)
- **System Integration**: End-to-end server functionality testing
- **28 MCP Tools**: Complete validation of all LTMC tools with project_id integration
- **Real Database**: Actual database operations with project isolation
- **Attack Vectors**: Real security attack testing with actual blocking validation
- **Multi-Project**: Concurrent project isolation validation

**Key Test Classes:**
- `TestPhase0SystemStartup` - Critical system operability validation
- `TestRealMCPToolsIntegration` - All 28 tools with real HTTP requests
- `TestRealDatabaseSecurityIntegration` - Multi-project data isolation
- `TestRealSecurityAttackVectors` - Real attack prevention testing

### 2. `test_mcp_security_integration.py`
**MCP Protocol Security Testing**
- **Transport Security**: HTTP JSON-RPC and stdio transport validation
- **Protocol Attacks**: Real JSON-RPC injection, parameter pollution, buffer overflow
- **Tool Validation**: Security parameter validation for all 28 MCP tools
- **Rate Limiting**: DoS protection and concurrent load testing
- **Authentication**: Real security header and request validation

**Key Test Classes:**
- `TestMCPTransportSecurity` - Transport-level security validation
- `TestMCPToolSecurityValidation` - Tool parameter security testing
- `TestRealTimeSecurityMonitoring` - Rate limiting and DoS protection

### 3. `test_database_security_integration.py`
**Database Security Integration Testing**
- **Multi-Database**: SQLite, Redis, Neo4j, Qdrant security testing
- **Injection Prevention**: Real SQL, NoSQL, Graph injection attack testing
- **Project Isolation**: Multi-tenant database isolation validation
- **Connection Security**: Real database connection authentication testing
- **Data Leakage**: Cross-project data access prevention testing

**Key Test Classes:**
- `TestDatabaseConnectionSecurity` - Real database connection validation
- `TestDatabaseInjectionPrevention` - Real injection attack testing
- `TestMultiProjectDatabaseIsolation` - Concurrent isolation validation

### 4. `test_performance_under_security.py`
**Performance Under Security Load Testing**
- **Security Overhead**: Performance impact measurement with security active
- **Load Testing**: Concurrent user performance with security validation
- **Resource Monitoring**: Real CPU/memory usage during security operations
- **Attack Performance**: System performance during active security attacks
- **Scalability**: Performance degradation analysis under security constraints

**Key Test Classes:**
- `TestPerformanceUnderSecurityLoad` - Security performance impact testing
- Resource monitoring with real `psutil` integration
- Attack scenario performance measurement

## 🚀 Running Integration Tests

### Prerequisites

1. **LTMC System Running**: Integration tests require actual LTMC system
2. **Databases Available**: Redis instance must be accessible
3. **Ports Available**: Tests use ports 5052-5055 for test servers
4. **Dependencies**: `pytest`, `requests`, optional: `psutil`, `redis`, `psycopg2`

### Basic Test Execution

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_full_system_integration.py -v

# Run with detailed output
pytest tests/integration/ -v --tb=short --durations=10

# Run specific test class
pytest tests/integration/test_full_system_integration.py::TestPhase0SystemStartup -v
```

### Advanced Test Options

```bash
# Run with coverage
pytest tests/integration/ --cov=ltms --cov-report=html -v

# Run in parallel (if pytest-xdist installed)
pytest tests/integration/ -n auto -v

# Run only fast tests (exclude performance tests)
pytest tests/integration/ -v -k "not performance"

# Run with detailed logging
pytest tests/integration/ -v -s --log-cli-level=INFO
```

## 📊 Expected Test Results

### Performance Expectations
- **Phase 0 Startup**: Server must start within 30 seconds
- **Response Times**: Average < 2s for light load, < 10s for heavy load
- **Throughput**: Minimum 10 req/s under security load
- **Error Rates**: < 5% for normal operations, < 20% during attacks
- **Resource Usage**: < 95% CPU peak, < 2GB memory peak

### Security Validation
- **Attack Blocking**: > 80% of attacks must be blocked
- **Data Isolation**: 0% cross-project data leakage allowed
- **Injection Prevention**: 100% of SQL/NoSQL injection attempts blocked
- **Path Traversal**: 100% of path traversal attempts blocked

## 🔧 Test Configuration

### Environment Variables
```bash
export LTMC_TEST_SERVER_PORT=5052  # Base port for test servers
export LTMC_TEST_TIMEOUT=30        # Test timeout in seconds
export LTMC_REDIS_HOST=localhost   # Redis host for testing
export LTMC_REDIS_PORT=6382        # Redis port for testing
```

### Optional Dependencies
```bash
# For database testing
pip install redis psycopg2-binary neo4j qdrant-client

# For performance monitoring
pip install psutil memory-profiler

# For performance visualization
pip install matplotlib
```

## 🛠️ Troubleshooting

### Common Issues

1. **Server Startup Failures**
   - Check port availability (5052-5055)
   - Verify LTMC system dependencies installed
   - Check Redis connection (localhost:6382)

2. **Database Connection Errors**
   - Verify Redis server running on port 6382
   - Check Redis authentication if required
   - Ensure database permissions

3. **Performance Test Timeouts**
   - Increase test timeouts for slower systems
   - Reduce concurrent user counts
   - Check system resource availability

4. **Import Errors**
   - Optional dependencies fail gracefully
   - Core functionality works without optional packages
   - Install missing packages if full features needed

### Debugging

```bash
# Enable debug logging
pytest tests/integration/ -v -s --log-cli-level=DEBUG

# Run single test with full output
pytest tests/integration/test_full_system_integration.py::TestPhase0SystemStartup::test_ltmc_server_starts_successfully -v -s

# Check server logs during test
tail -f logs/ltmc_server.log
```

## 📈 Test Reports

### Generating Reports
```bash
# HTML coverage report
pytest tests/integration/ --cov=ltms --cov-report=html

# Performance report (if matplotlib available)
pytest tests/integration/test_performance_under_security.py --performance-report

# Security test summary
pytest tests/integration/ -k "security" --tb=short
```

### Results Analysis
- Coverage reports: `htmlcov/index.html`
- Performance graphs: `test_reports/performance/`
- Security test logs: Check test output for attack blocking rates

## 🎯 Success Criteria

**✅ INTEGRATION TEST SUITE PASSES IF:**
1. **Phase 0**: System starts successfully and health endpoints respond
2. **All 28 MCP Tools**: Work with project_id parameter and security validation
3. **Security Attacks**: > 80% blocked with system remaining stable
4. **Multi-Project Isolation**: 0% data leakage between projects
5. **Performance**: Meets response time and throughput requirements
6. **Resource Usage**: Stays within CPU and memory limits

**❌ INTEGRATION TEST SUITE FAILS IF:**
- Any Phase 0 validation fails (system doesn't start)
- MCP tools don't work with security enabled
- Security attacks succeed or crash the system
- Cross-project data leakage detected
- Performance degrades beyond acceptable limits
- Resource usage exceeds system capacity

## 🚨 CI/CD Integration

### GitHub Actions Example
```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:6.2-alpine
        ports:
          - 6382:6379
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pip install pytest redis psutil
      - name: Run Integration Tests
        run: pytest tests/integration/ -v --tb=short
```

---

## 🏆 Real Integration Testing Achievement

**DELIVERED: Comprehensive Real System Integration Testing**

✅ **4 Complete Test Files** (3,000+ lines total)
✅ **Phase 0 System Validation** (mandatory startup testing)  
✅ **All 28 MCP Tools** (real HTTP/stdio testing)
✅ **Multi-Database Security** (SQLite, Redis, Neo4j, Qdrant)
✅ **Real Attack Vectors** (SQL injection, path traversal, DoS)
✅ **Performance Under Load** (concurrent users, resource monitoring)
✅ **Multi-Project Isolation** (complete tenant separation)

**NO MOCKS - REAL COMPONENTS ONLY!**

This integration test suite validates the complete LTMC system working end-to-end with actual security components, real databases, and authentic attack scenarios.