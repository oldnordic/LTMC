# LTMC Database Schema Migration Plan

**Date**: 2025-08-09  
**Issue**: Critical CodePatterns table schema mismatch causing 3 out of 28 tools to fail  
**Priority**: P0 - Blocking core functionality

## Executive Summary

The LTMC system has a critical database schema inconsistency where the `CodePatterns` table in the actual database (created by `ltms/database/schema.py`) is missing 5 essential columns that the code pattern services expect. This causes all code pattern memory tools to fail with "no such column" errors.

## Root Cause Analysis

### Schema Definition Mismatch

**Current Database Schema** (from ltmc.db):
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

**Expected Schema** (from ltms/services/code_pattern_service.py):
```sql
CREATE TABLE CodePatterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT,              -- ❌ MISSING
    file_name TEXT,                  -- ❌ MISSING  
    module_name TEXT,                -- ❌ MISSING
    input_prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    result TEXT CHECK(result IN ('pass', 'fail', 'partial')),
    execution_time_ms INTEGER,       -- ❌ TYPE MISMATCH
    error_message TEXT,
    tags TEXT,                       -- ❌ MISSING
    created_at TEXT NOT NULL,
    vector_id INTEGER UNIQUE,        -- ❌ MISSING
    FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)
);
```

### Impact Assessment

**Failing Tools (3/28)**:
- `log_code_attempt` - Cannot store structured metadata
- `get_code_patterns` - Cannot filter by function/file names  
- `analyze_code_patterns` - Cannot perform advanced analytics

**Error Messages**:
- `"no such column: function_name"`
- `"table CodePatterns has no column named function_name"`

## Migration Strategy

### Phase 1: Immediate Schema Fix (Required)

#### Step 1: Add Missing Columns
```sql
-- Add missing columns to existing table
ALTER TABLE CodePatterns ADD COLUMN function_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN file_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN module_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN tags TEXT;
ALTER TABLE CodePatterns ADD COLUMN vector_id INTEGER UNIQUE;

-- Add column with different name for execution time
ALTER TABLE CodePatterns ADD COLUMN execution_time_ms INTEGER;
```

#### Step 2: Data Migration
```sql
-- Copy execution_time REAL to execution_time_ms INTEGER
UPDATE CodePatterns 
SET execution_time_ms = CAST(execution_time * 1000 AS INTEGER) 
WHERE execution_time IS NOT NULL;
```

#### Step 3: Update Schema Definition
Update `ltms/database/schema.py` lines 86-98 to match the service expectations.

### Phase 2: Schema Synchronization (Recommended)

#### Centralize Schema Definition
1. **Single Source of Truth**: Move schema definitions to dedicated migration files
2. **Service Layer Consistency**: Remove CREATE TABLE from services
3. **Version Control**: Add schema versioning system

#### Implementation Pattern
```python
# ltms/database/migrations/001_add_codepatterns_metadata.py
def up(conn: sqlite3.Connection):
    """Add missing columns to CodePatterns table."""
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(CodePatterns)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    if 'function_name' not in existing_columns:
        cursor.execute("ALTER TABLE CodePatterns ADD COLUMN function_name TEXT")
    
    # ... repeat for other columns
    conn.commit()

def down(conn: sqlite3.Connection):
    """Rollback changes (SQLite limitations apply)."""
    # SQLite doesn't support DROP COLUMN, would require table recreation
    pass
```

### Phase 3: Performance Optimization (Future)

#### Add Indexes for Common Queries
```sql
-- Index for result filtering (most common query pattern)
CREATE INDEX idx_codepatterns_result ON CodePatterns(result);

-- Index for time-based queries
CREATE INDEX idx_codepatterns_created_at ON CodePatterns(created_at);

-- Composite index for function-based filtering
CREATE INDEX idx_codepatterns_function_result ON CodePatterns(function_name, result);
```

## Implementation Timeline

### Immediate (Today)
- [ ] Create migration script for missing columns
- [ ] Update schema.py to match service expectations
- [ ] Test all 28 tools after migration
- [ ] Validate existing data integrity

### Short Term (This Week)
- [ ] Implement proper migration system
- [ ] Add schema versioning
- [ ] Create rollback procedures
- [ ] Performance testing with indexes

### Medium Term (Next Sprint)
- [ ] Centralize schema management
- [ ] Add schema validation tests
- [ ] Document schema evolution process
- [ ] Consider alternative database backends

## Risk Assessment

### Low Risk
- Adding columns with ALTER TABLE (SQLite supports this)
- Existing data remains intact
- Tools will work immediately after column addition

### Medium Risk  
- Type conversion from REAL to INTEGER for execution_time
- Need to test with existing patterns data
- May need data validation after migration

### Mitigation Strategies
1. **Backup Database**: Copy ltmc.db before migration
2. **Incremental Testing**: Test each tool after each schema change
3. **Rollback Plan**: Keep original database backup
4. **Validation**: Compare tool results before/after migration

## Success Criteria

### Functional Requirements
- [ ] All 28 LTMC tools pass validation tests
- [ ] Code pattern tools can store and retrieve with full metadata
- [ ] No "column not found" errors in logs
- [ ] Existing data remains accessible

### Performance Requirements  
- [ ] Tool response times remain under 500ms
- [ ] Database queries execute efficiently
- [ ] Vector ID constraints work properly
- [ ] No memory leaks in long-running processes

## SQL Migration Script

```sql
-- LTMC Database Schema Migration
-- Adds missing columns to CodePatterns table

BEGIN TRANSACTION;

-- Add missing columns
ALTER TABLE CodePatterns ADD COLUMN function_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN file_name TEXT;  
ALTER TABLE CodePatterns ADD COLUMN module_name TEXT;
ALTER TABLE CodePatterns ADD COLUMN tags TEXT;
ALTER TABLE CodePatterns ADD COLUMN vector_id INTEGER;
ALTER TABLE CodePatterns ADD COLUMN execution_time_ms INTEGER;

-- Migrate existing execution_time data
UPDATE CodePatterns 
SET execution_time_ms = CAST(execution_time * 1000 AS INTEGER) 
WHERE execution_time IS NOT NULL;

-- Add constraints (SQLite limitation: cannot add UNIQUE to existing column)
-- Will need to recreate table for UNIQUE constraint on vector_id

COMMIT;
```

## Next Steps

1. **Execute Migration**: Run schema changes on ltmc.db
2. **Update Schema.py**: Synchronize with actual table structure  
3. **Test Validation**: Run comprehensive tool testing
4. **Monitor Performance**: Check for any degradation
5. **Document Changes**: Update API documentation

This migration will restore full functionality to the LTMC system's code pattern memory capabilities, enabling all 28 tools to work as designed.