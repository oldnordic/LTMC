# LTMC Database Schema Investigation - Complete Analysis

**Date**: 2025-08-09  
**Investigator**: Backend Architect (Claude Code)  
**Status**: INVESTIGATION COMPLETE - ROOT CAUSE IDENTIFIED

## Executive Summary

The LTMC system has a **critical database schema inconsistency** that causes 3 out of 28 tools to fail completely. The `CodePatterns` table is missing 5 essential columns that the code pattern services expect, causing all code pattern memory functionality to fail with SQLite column errors.

## Root Cause Analysis

### Primary Issue: Schema Definition Conflict

The LTMC system has **two different schema definitions** for the CodePatterns table:

1. **Database Creation Schema** (`ltms/database/schema.py:86-98`)
2. **Service Layer Schema** (`ltms/services/code_pattern_service.py:75-91`)

These schemas are **incompatible**, causing runtime failures when services query for columns that don't exist.

### Confirmed Database State

**Actual Database Schema** (verified via `sqlite3 ltmc.db ".schema CodePatterns"`):
```sql
CREATE TABLE CodePatterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    input_prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    result TEXT NOT NULL,
    language TEXT,
    execution_time REAL,
    error_message TEXT,
    created_at TEXT NOT NULL
);
```

**Expected Schema** (from code pattern service implementation):
```sql
CREATE TABLE CodePatterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT,              -- ❌ MISSING
    file_name TEXT,                  -- ❌ MISSING
    module_name TEXT,                -- ❌ MISSING
    input_prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    result TEXT CHECK(result IN ('pass', 'fail', 'partial')),
    execution_time_ms INTEGER,       -- ❌ TYPE MISMATCH (vs execution_time REAL)
    error_message TEXT,
    tags TEXT,                       -- ❌ MISSING
    created_at TEXT NOT NULL,
    vector_id INTEGER UNIQUE,        -- ❌ MISSING + CONSTRAINT
    FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)  -- ❌ MISSING FK
);
```

## Detailed Schema Discrepancies

### Missing Columns (5 Total)
1. **`function_name TEXT`** - Used for function-level filtering and analysis
2. **`file_name TEXT`** - File-based pattern organization
3. **`module_name TEXT`** - Module-level code pattern grouping
4. **`tags TEXT`** - JSON storage for pattern categorization
5. **`vector_id INTEGER UNIQUE`** - Links to FAISS vector embeddings

### Type Mismatches (1 Total)
- **`execution_time`**: Database has `REAL`, service expects `execution_time_ms INTEGER`

### Missing Constraints (2 Total)
- **UNIQUE constraint** on `vector_id` column
- **FOREIGN KEY** relationship to `ResourceChunks(id)`

## Impact Assessment

### Completely Broken Tools (3/28)

**Tool Failures Confirmed**:

1. **`log_code_attempt`** 
   - **Error**: `"table CodePatterns has no column named function_name"`
   - **Impact**: Cannot store code generation experiences
   - **Test Result**: ❌ FAIL

2. **`get_code_patterns`**
   - **Error**: `"no such column: function_name"`  
   - **Impact**: Cannot retrieve similar code patterns
   - **Test Result**: ❌ FAIL

3. **`analyze_code_patterns`**
   - **Error**: `"no such column: function_name"`
   - **Impact**: Cannot perform pattern analytics
   - **Test Result**: ❌ FAIL

### Functional Impact

**Experience Replay Learning**: **COMPLETELY DISABLED**
- No code pattern storage working
- No experience-based code generation
- No learning from previous successes/failures

**Code Intelligence**: **SEVERELY DEGRADED**  
- Cannot learn from coding patterns
- No function-level code analysis
- No module-based pattern recognition

## Architecture Analysis

### Schema Management Anti-Pattern

The current architecture has a **dangerous anti-pattern**:

1. **`ltms/database/schema.py`** - Creates basic tables on initialization
2. **Service layers** - Each service defines its own schema expectations
3. **No schema validation** - Services assume columns exist without verification
4. **No migration system** - Schema changes are not versioned or managed

This pattern **guarantees schema drift** over time as services evolve independently.

### Recommended Architecture Pattern

**Single Source of Truth**:
```
ltms/database/
├── migrations/
│   ├── 001_initial_schema.py
│   ├── 002_add_codepatterns_metadata.py
│   └── migration_runner.py
├── schema.py (generated from migrations)
└── version.py
```

## Technical Investigation Details

### Verification Commands Used

```bash
# Confirm database schema
sqlite3 ltmc.db ".schema CodePatterns"

# Test failing tool directly
curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d '{"jsonrpc": "2.0", "method": "tools/call", "params": {
  "name": "get_code_patterns", 
  "arguments": {"query": "test", "top_k": 1}
}, "id": 1}'

# Result: {"success":false,"error":"no such column: function_name"}
```

### File Analysis Performed

**Schema Definition Files**:
- ✅ `/home/feanor/Projects/lmtc/ltms/database/schema.py` - Basic schema  
- ✅ `/home/feanor/Projects/lmtc/ltms/services/code_pattern_service.py` - Extended schema
- ✅ Database verification via SQLite CLI

**Service Implementation Files**:
- ✅ `/home/feanor/Projects/lmtc/ltms/mcp_server.py` - Tool definitions
- ✅ `/home/feanor/Projects/lmtc/ltms/tools/code_pattern_tools.py` - Tool handlers

**Test Evidence**:
- ✅ Multiple validation reports showing consistent failures
- ✅ Direct database schema verification
- ✅ Live tool testing with confirmed error messages

## Solution Summary

### Immediate Fix Required (P0)

**Add Missing Columns**:
```sql
ALTER TABLE CodePatterns ADD COLUMN function_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN file_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN module_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN tags TEXT;
ALTER TABLE CodePatterns ADD COLUMN vector_id INTEGER;
ALTER TABLE CodePatterns ADD COLUMN execution_time_ms INTEGER;
```

**Update Schema Definition**:
- Synchronize `schema.py` with service expectations
- Add proper constraints and foreign keys
- Include migration path for existing data

### Long-term Architectural Fix (P1)

**Schema Management System**:
- Implement proper database migrations
- Add schema versioning and validation
- Create centralized schema management
- Add rollback and upgrade procedures

## Quality Assurance Requirements

### Pre-Migration Validation
- [ ] Backup existing database
- [ ] Test migration on copy
- [ ] Validate all existing data remains accessible

### Post-Migration Testing
- [ ] All 28 LTMC tools pass validation
- [ ] Code pattern tools store/retrieve correctly
- [ ] Performance remains acceptable
- [ ] Vector ID constraints work properly

### Monitoring Requirements
- [ ] Database integrity checks
- [ ] Tool response time monitoring  
- [ ] Error rate tracking for pattern tools
- [ ] Vector embedding storage validation

## Conclusion

This investigation has **conclusively identified** the root cause of LTMC code pattern tool failures:

**ROOT CAUSE**: Database schema created by `schema.py` is missing 5 essential columns that the code pattern services require.

**IMPACT**: 3 out of 28 tools completely non-functional, experience replay learning disabled.

**SOLUTION**: Database migration to add missing columns + architectural improvements for schema management.

**PRIORITY**: P0 - Critical functionality restoration required immediately.

The database schema inconsistency investigation is **COMPLETE** with clear remediation path identified.