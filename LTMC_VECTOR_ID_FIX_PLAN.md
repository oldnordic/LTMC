# LTMC Vector ID Constraint Fix Plan + Code Pattern Memory Enhancement

## 🚨 Issue Summary

**Problem**: `UNIQUE constraint failed: ResourceChunks.vector_id`
- **Impact**: Memory storage is blocked, preventing new resources from being added
- **Current State**: 37 resources, 106 chunks stored with non-sequential vector_ids
- **Root Cause**: Vector ID generation creates gaps and potential conflicts
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions) - **OPTIMAL CONFIGURATION**

## 🔍 Root Cause Analysis

### Current Vector ID Generation Logic
```python
# In resource_service.py line 47-48
vector_ids = list(range(len(chunks)))  # Sequential 0, 1, 2, 3...
```

### The Problem
1. **Non-Sequential Storage**: Vector IDs in database show gaps (0, 69, 15751, 21748, etc.)
2. **Hash-Based Generation**: The actual vector_id generation appears to use a hash function, not sequential IDs
3. **Constraint Violation**: When new chunks are added, hash collisions occur
4. **Database State**: 106 total chunks, 106 unique vector_ids (no duplicates currently, but collisions occur on insert)

### Evidence
- **Max vector_id**: 987651
- **Total chunks**: 106
- **Unique vector_ids**: 106
- **Sample vector_ids**: 0, 69, 15751, 21748, 30293, 31983, 35648, 39519, 80136, 82248

### Embedding Model Analysis
- **Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Performance**: ~37ms encoding time
- **Status**: ✅ **OPTIMAL** - No changes needed to embedding model
- **Compatibility**: Works perfectly with current vector storage system

## 🎯 Solution Design

### Option 1: Sequential Vector ID Generation (Recommended)
**Approach**: Use database auto-increment or sequential generation
**Pros**: Predictable, no conflicts, easy to debug, compatible with 384-dim embeddings
**Cons**: Requires migration of existing data

### Option 2: Hash-Based with Collision Resolution
**Approach**: Keep hash-based generation but add collision detection
**Pros**: Maintains current approach
**Cons**: Complex, potential performance issues

### Option 3: UUID-Based Vector IDs
**Approach**: Use UUIDs for vector_ids
**Pros**: No conflicts, globally unique
**Cons**: Larger storage, migration required

## 🛠 Implementation Plan

### Phase 1: Database Schema Update
1. **Add vector_id generation column**
   ```sql
   ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential';
   ```

2. **Create vector_id sequence table**
   ```sql
   CREATE TABLE VectorIdSequence (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       last_vector_id INTEGER DEFAULT 0
   );
   ```

### Phase 2: Vector ID Generation Service
1. **Create sequential vector_id generator**
   ```python
   def get_next_vector_id(conn: sqlite3.Connection) -> int:
       cursor = conn.cursor()
       cursor.execute("""
           INSERT INTO VectorIdSequence (last_vector_id) 
           VALUES (COALESCE((SELECT MAX(last_vector_id) FROM VectorIdSequence), 0) + 1)
       """)
       conn.commit()
       return cursor.lastrowid
   ```

2. **Update resource service** (compatible with 384-dim embeddings)
   ```python
   # Replace current vector_id generation
   vector_ids = [get_next_vector_id(conn) for _ in range(len(chunks))]
   
   # Embedding model remains unchanged
   model = create_embedding_model("all-MiniLM-L6-v2")  # 384 dimensions
   embeddings = encode_texts(model, chunks)  # Shape: (n_chunks, 384)
   ```

### Phase 3: Migration Strategy
1. **Backup existing data**
   ```bash
   cp ltmc.db ltmc.db.backup
   ```

2. **Create migration script**
   ```python
   def migrate_vector_ids():
       # Read existing chunks (106 chunks with 384-dim embeddings)
       # Generate new sequential IDs
       # Update database
       # Update FAISS index (maintain 384-dim compatibility)
   ```

3. **Test migration on copy**
   - Create test database
   - Run migration
   - Verify functionality with 384-dim embeddings

### Phase 4: FAISS Index Update
1. **Update vector index mapping** (384-dimension compatible)
   - Map old vector_ids to new sequential IDs
   - Rebuild FAISS index with new mappings
   - Ensure 384-dimension embeddings are preserved

2. **Verify index integrity**
   - Test vector search functionality
   - Ensure all chunks are retrievable
   - Validate 384-dimension embedding compatibility

### Phase 5: Code Pattern Memory Enhancement 🆕

#### 🧠 **Code Pattern Memory Overview**
**Concept**: "Experience Replay for Code" — LTMC module for learning from past success/failure across sessions

#### **Database Schema for Code Patterns**
```sql
-- Code Pattern Storage
CREATE TABLE CodePatterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    function_name TEXT,
    file_name TEXT,
    module_name TEXT,
    input_prompt TEXT NOT NULL,
    generated_code TEXT NOT NULL,
    result TEXT CHECK(result IN ('pass', 'fail', 'partial')),
    execution_time_ms INTEGER,
    error_message TEXT,
    tags TEXT,  -- JSON array of tags
    created_at TEXT NOT NULL,
    vector_id INTEGER UNIQUE,
    FOREIGN KEY (vector_id) REFERENCES ResourceChunks (id)
);

-- Code Pattern Context Links
CREATE TABLE CodePatternContext (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,
    context_type TEXT,  -- 'similar_function', 'same_file', 'same_module'
    context_id INTEGER,
    similarity_score REAL,
    FOREIGN KEY (pattern_id) REFERENCES CodePatterns (id)
);
```

#### **New MCP Tools for Code Pattern Memory**
```python
@mcp.tool()
def log_code_attempt(
    input_prompt: str,
    generated_code: str,
    result: str,  # 'pass', 'fail', 'partial'
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    execution_time_ms: int = None,
    error_message: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """Log a code generation attempt with result for pattern learning."""
    # Implementation: Store code pattern with embeddings
    pass

@mcp.tool()
def get_code_patterns(
    query: str,
    result_filter: str = None,  # 'pass', 'fail', 'partial', None for all
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Retrieve code patterns similar to query for learning."""
    # Implementation: Vector search on code patterns
    pass

@mcp.tool()
def analyze_code_patterns(
    function_name: str = None,
    file_name: str = None,
    module_name: str = None,
    time_range_days: int = 30
) -> Dict[str, Any]:
    """Analyze code pattern success rates and trends."""
    # Implementation: Statistical analysis of patterns
    pass
```

#### **Code Pattern Service Implementation**
```python
# ltms/services/code_pattern_service.py
from typing import Dict, Any, List, Optional
from ltms.services.embedding_service import create_embedding_model, encode_text
from ltms.database.dal import create_code_pattern, get_code_patterns_by_query

def store_code_pattern(
    conn,
    input_prompt: str,
    generated_code: str,
    result: str,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    execution_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Store a code generation attempt as a pattern."""
    
    # Create searchable text for embedding
    search_text = f"{input_prompt}\n{generated_code}"
    if function_name:
        search_text += f"\nFunction: {function_name}"
    if file_name:
        search_text += f"\nFile: {file_name}"
    
    # Generate embedding using existing 384-dim model
    model = create_embedding_model("all-MiniLM-L6-v2")
    embedding = encode_text(model, search_text)
    
    # Store in database with vector_id
    pattern_id = create_code_pattern(
        conn=conn,
        input_prompt=input_prompt,
        generated_code=generated_code,
        result=result,
        function_name=function_name,
        file_name=file_name,
        module_name=module_name,
        execution_time_ms=execution_time_ms,
        error_message=error_message,
        tags=tags,
        embedding=embedding
    )
    
    return {
        'success': True,
        'pattern_id': pattern_id,
        'message': f'Code pattern stored with result: {result}'
    }

def retrieve_code_patterns(
    conn,
    query: str,
    result_filter: Optional[str] = None,
    function_name: Optional[str] = None,
    file_name: Optional[str] = None,
    module_name: Optional[str] = None,
    top_k: int = 5
) -> Dict[str, Any]:
    """Retrieve similar code patterns for learning."""
    
    # Generate query embedding
    model = create_embedding_model("all-MiniLM-L6-v2")
    query_embedding = encode_text(model, query)
    
    # Search for similar patterns
    patterns = get_code_patterns_by_query(
        conn=conn,
        query_embedding=query_embedding,
        result_filter=result_filter,
        function_name=function_name,
        file_name=file_name,
        module_name=module_name,
        top_k=top_k
    )
    
    return {
        'success': True,
        'patterns': patterns,
        'count': len(patterns),
        'query': query
    }
```

#### **Integration with Existing LTMC Infrastructure**
- **Leverages existing 384-dim embedding model** (no model changes needed)
- **Uses existing FAISS vector storage** (extends current infrastructure)
- **Follows existing MCP tool patterns** (consistent API design)
- **Integrates with current database schema** (extends ResourceChunks)

#### **Benefits of Code Pattern Memory**
1. **✅ Learn from Success**: Models can see what worked in similar contexts
2. **❌ Avoid Known Failures**: Models can avoid previously failed approaches
3. **📈 Continuous Improvement**: Pattern success rates improve over time
4. **🔍 Debugging Aid**: Track common failure patterns and solutions
5. **🎯 Context-Aware**: Function/file/module-specific pattern learning

## 📋 Implementation Steps

### Step 1: Create Migration Script
```python
# migration_vector_ids.py
import sqlite3
import shutil
import numpy as np
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"ltmc.db.backup_{timestamp}"
    shutil.copy2("ltmc.db", backup_path)
    return backup_path

def create_vector_id_sequence_table(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS VectorIdSequence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_vector_id INTEGER DEFAULT 0
        )
    """)
    conn.commit()

def create_code_pattern_tables(conn):
    """Create tables for Code Pattern Memory feature."""
    conn.execute("""
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
    
    conn.execute("""
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

def migrate_vector_ids():
    # Implementation here
    # Ensure 384-dimension embeddings are preserved
    pass
```

### Step 2: Update Resource Service
```python
# In resource_service.py
def get_next_vector_id(conn: sqlite3.Connection) -> int:
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO VectorIdSequence (last_vector_id) 
        VALUES (COALESCE((SELECT MAX(last_vector_id) FROM VectorIdSequence), 0) + 1)
    """)
    conn.commit()
    return cursor.lastrowid

def add_resource(conn, index_path: str, file_name: str, resource_type: str, content: str):
    # ... existing code ...
    
    # Replace vector_id generation
    vector_ids = [get_next_vector_id(conn) for _ in range(len(chunks))]
    
    # Embedding model remains unchanged (384 dimensions)
    model = create_embedding_model("all-MiniLM-L6-v2")
    embeddings = encode_texts(model, chunks)  # Shape: (n_chunks, 384)
    
    # ... rest of function ...
```

### Step 3: Update Database Schema
```sql
-- Add generation method tracking
ALTER TABLE ResourceChunks ADD COLUMN generation_method TEXT DEFAULT 'sequential';

-- Create vector ID sequence table
CREATE TABLE VectorIdSequence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    last_vector_id INTEGER DEFAULT 0
);

-- Create Code Pattern Memory tables
CREATE TABLE CodePatterns (
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
);

CREATE TABLE CodePatternContext (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER,
    context_type TEXT,
    context_id INTEGER,
    similarity_score REAL,
    FOREIGN KEY (pattern_id) REFERENCES CodePatterns (id)
);
```

### Step 4: Test Implementation
1. **Unit Tests**
   ```python
   def test_vector_id_generation():
       # Test sequential generation
       # Test uniqueness
       # Test database constraints
       # Test 384-dimension embedding compatibility
   
   def test_code_pattern_memory():
       # Test code pattern storage
       # Test pattern retrieval
       # Test embedding generation for code
       # Test result filtering
   ```

2. **Integration Tests**
   ```python
   def test_memory_storage():
       # Test complete storage pipeline
       # Test retrieval functionality
       # Test 384-dimension embedding preservation
   
   def test_code_pattern_integration():
       # Test code pattern with existing memory system
       # Test vector search across code patterns
       # Test MCP tool integration
   ```

## 🧪 Testing Strategy

### Pre-Migration Tests
- [ ] Backup database integrity
- [ ] Current functionality baseline
- [ ] Vector search accuracy (384-dim embeddings)
- [ ] Embedding model performance (~37ms encoding)

### Migration Tests
- [ ] Data integrity during migration
- [ ] Vector ID uniqueness
- [ ] FAISS index mapping (384-dim compatible)
- [ ] Embedding dimension preservation
- [ ] Code pattern table creation

### Post-Migration Tests
- [ ] Memory storage functionality
- [ ] Memory retrieval accuracy
- [ ] Performance benchmarks
- [ ] All MCP tools working
- [ ] 384-dimension embedding compatibility
- [ ] Code pattern memory functionality
- [ ] Code pattern retrieval accuracy

## ⚠️ Risk Mitigation

### Backup Strategy
1. **Multiple backups**: Create timestamped backups
2. **Test migration**: Run on copy first
3. **Rollback plan**: Keep original database structure
4. **Embedding preservation**: Ensure 384-dim embeddings are not corrupted

### Validation Steps
1. **Data integrity**: Verify all chunks preserved
2. **Functionality**: Test all MCP tools
3. **Performance**: Ensure no degradation
4. **Embedding compatibility**: Verify 384-dimension embeddings work correctly
5. **Code pattern functionality**: Test new code pattern memory features

## 📊 Success Metrics

### Functional Requirements
- [ ] Memory storage works without constraint errors
- [ ] All 19 MCP tools functional
- [ ] Vector search accuracy maintained (384-dim)
- [ ] No data loss during migration
- [ ] Embedding model performance maintained (~37ms)
- [ ] Code pattern memory working (3 new MCP tools)
- [ ] Code pattern retrieval accuracy > 80%

### Performance Requirements
- [ ] Storage speed: < 2 seconds per resource
- [ ] Retrieval speed: < 1 second per query
- [ ] Memory usage: < 20% increase
- [ ] Embedding encoding: < 50ms per chunk
- [ ] Code pattern storage: < 100ms per pattern
- [ ] Code pattern retrieval: < 200ms per query

## 🎯 Timeline

### Day 1: Preparation
- [ ] Create backup strategy
- [ ] Implement migration script
- [ ] Test on copy database
- [ ] Verify 384-dimension embedding compatibility
- [ ] Implement code pattern service

### Day 2: Migration
- [ ] Execute migration on production
- [ ] Verify data integrity
- [ ] Test all functionality
- [ ] Validate embedding model performance
- [ ] Test code pattern memory features

### Day 3: Validation
- [ ] Performance testing
- [ ] User acceptance testing
- [ ] Documentation update
- [ ] Embedding model validation
- [ ] Code pattern memory validation

## 🔄 Rollback Plan

If issues occur:
1. **Stop LTMC server**
2. **Restore from backup**
3. **Revert code changes**
4. **Restart server**
5. **Verify 384-dimension embedding functionality**
6. **Verify code pattern memory functionality**

## 📝 Post-Fix Documentation

### Updated Architecture
- Vector ID generation method
- Database schema changes
- Migration procedures
- 384-dimension embedding model configuration
- Code Pattern Memory system design
- New MCP tools for code pattern learning

### Monitoring
- Vector ID collision detection
- Performance metrics
- Error logging
- Embedding model performance monitoring
- Code pattern success rate tracking
- Code pattern retrieval accuracy monitoring

---

**Status**: Ready for implementation
**Priority**: High (blocks memory storage + adds code pattern learning)
**Estimated Effort**: 3-4 days (includes code pattern memory)
**Risk Level**: Medium (requires data migration)
**Embedding Model**: all-MiniLM-L6-v2 (384 dimensions) - OPTIMAL CONFIGURATION
**New Features**: Code Pattern Memory with 3 new MCP tools
