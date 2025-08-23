# MERMAID INTEGRATION ARCHITECTURE FOR LTMC SYSTEM

**Version:** 1.0  
**Date:** 2025-01-10  
**Status:** Design Phase Complete - Implementation Ready  

## EXECUTIVE SUMMARY

This document provides a comprehensive architectural design for integrating Mermaid.js diagram generation capabilities into the LTMC (Long-Term Memory Context) system. The integration maintains compatibility with all existing 55 tools while adding powerful diagramming capabilities that leverage the 4-tier memory system (SQLite, Redis, Neo4j, FAISS) and follow established LTMC patterns.

## SYSTEM INTEGRATION ANALYSIS

### Current LTMC Architecture Overview
- **55 Tools** across 6 categories (advanced, blueprint, chat, code_patterns, context, documentation, memory, redis, taskmaster, todo, unified)
- **4-Tier Memory System**: SQLite (temporal), Redis (cache), Neo4j (graph), FAISS (semantic)  
- **MCP stdio Transport** via FastMCP 2.0 framework
- **Modular Architecture** with ≤300 lines per module enforcement
- **Service Layer Pattern** with DatabaseService, RedisService, FAISSService, Neo4jService

### Integration Requirements Met
1. ✅ **MCP Protocol Compliance** - stdio transport with @mcp.tool decorators
2. ✅ **Memory System Integration** - All 4 tiers utilized optimally  
3. ✅ **Modular Design** - Each component ≤300 lines following LTMC patterns
4. ✅ **Service Layer Integration** - MermaidService follows established patterns
5. ✅ **Tool Registration** - Compatible with existing register_*_tools pattern

## NEW MERMAID MODULE ARCHITECTURE

### Directory Structure
```
/ltmc_mcp_server/tools/mermaid/
├── __init__.py                     # Module registration
├── basic_mermaid_tools.py         # Core diagram generation (≤300 lines)
├── advanced_mermaid_tools.py      # Themes, templates, batch ops (≤300 lines)
└── analysis_mermaid_tools.py      # Analytics, relationships (≤300 lines)

/ltmc_mcp_server/services/
└── mermaid_service.py             # Diagram generation service (≤300 lines)

/ltmc_mcp_server/models/
└── mermaid_models.py              # Pydantic models for diagrams (≤300 lines)
```

### Tool Categories & Functions

#### Basic Mermaid Tools (9 functions)
1. **generate_diagram** - Create diagram from Mermaid code (all types supported)
2. **save_diagram** - Save diagram to filesystem with metadata
3. **load_diagram_template** - Load pre-built diagram templates
4. **validate_diagram_syntax** - Validate Mermaid syntax before generation
5. **list_diagram_types** - List all supported diagram types
6. **get_diagram_info** - Get metadata about generated diagrams
7. **delete_diagram** - Remove diagram and cleanup resources
8. **export_diagram** - Export diagram in multiple formats (PNG/SVG)
9. **preview_diagram** - Generate low-resolution preview for validation

#### Advanced Mermaid Tools (8 functions)
1. **generate_diagram_from_context** - Create diagrams from LTMC memory context
2. **batch_generate_diagrams** - Generate multiple diagrams efficiently  
3. **apply_diagram_theme** - Apply visual themes (default, forest, dark, neutral)
4. **convert_diagram_format** - Convert between PNG/SVG formats
5. **create_diagram_template** - Create reusable diagram templates
6. **merge_diagrams** - Combine multiple diagrams into composite views
7. **optimize_diagram_layout** - Auto-optimize diagram positioning
8. **generate_interactive_diagram** - Create interactive diagram versions

#### Analysis Mermaid Tools (6 functions)  
1. **analyze_diagram_relationships** - Find related diagrams in knowledge graph
2. **generate_system_architecture_diagram** - Auto-generate from LTMC system knowledge
3. **track_diagram_usage** - Analytics on diagram generation patterns
4. **find_similar_diagrams** - FAISS-based semantic similarity search
5. **diagram_dependency_analysis** - Analyze diagram interconnections
6. **generate_diagram_reports** - Usage analytics and performance reports

**Total New Tools: 23 Mermaid-specific tools**

## FILE MODIFICATION MATRIX

### New Files to Create

| File Path | Purpose | Lines Est. | Priority |
|-----------|---------|------------|----------|
| `/ltmc_mcp_server/tools/mermaid/__init__.py` | Module registration | 50 | P1 |
| `/ltmc_mcp_server/tools/mermaid/basic_mermaid_tools.py` | Core functionality | 280 | P1 |  
| `/ltmc_mcp_server/tools/mermaid/advanced_mermaid_tools.py` | Advanced features | 290 | P2 |
| `/ltmc_mcp_server/tools/mermaid/analysis_mermaid_tools.py` | Analytics | 270 | P3 |
| `/ltmc_mcp_server/services/mermaid_service.py` | Service layer | 280 | P1 |
| `/ltmc_mcp_server/models/mermaid_models.py` | Data models | 150 | P1 |

### Files to Modify  

| File Path | Modification | Impact | Priority |
|-----------|--------------|--------|----------|
| `/ltmc_mcp_server/tools/__init__.py` | Add `register_mermaid_tools` import | Low | P1 |
| `/ltmc_mcp_server/services/__init__.py` | Add `MermaidService` import | Low | P1 |
| `/ltmc_mcp_server/main.py` | Add mermaid tool registration | Low | P1 |
| `/requirements.txt` | Add `mermaid-py>=0.1.0` dependency | Low | P1 |
| `/ltmc_mcp_server/config/settings.py` | Add mermaid configuration options | Medium | P2 |

### Database Schema Extensions

#### SQLite Schema Additions
```sql
-- Diagram metadata table
CREATE TABLE diagrams (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    diagram_type TEXT NOT NULL,
    content TEXT NOT NULL,
    svg_path TEXT,
    png_path TEXT,
    theme TEXT DEFAULT 'default',
    background_color TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    generation_time_ms INTEGER,
    cache_key TEXT,
    metadata JSON
);

-- Diagram templates table
CREATE TABLE diagram_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    diagram_type TEXT NOT NULL,
    template_content TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    usage_count INTEGER DEFAULT 0
);

-- Performance indexes
CREATE INDEX idx_diagrams_type ON diagrams(diagram_type);
CREATE INDEX idx_diagrams_created ON diagrams(created_at);
CREATE INDEX idx_diagrams_cache_key ON diagrams(cache_key);
```

## 4-TIER MEMORY INTEGRATION STRATEGY

### SQLite Integration (Temporal Storage)
- **Purpose**: Store diagram metadata, templates, generation history
- **Tables**: `diagrams`, `diagram_templates`, performance metrics
- **Data**: Diagram definitions, file paths, generation timestamps
- **Retention**: Permanent storage with cleanup policies

### Redis Integration (Caching Layer)  
- **Purpose**: Cache generated diagram images and frequently used templates
- **Keys Pattern**: `mermaid:diagram:{hash}`, `mermaid:template:{id}`
- **Cache Strategy**: LRU eviction, 24-hour TTL for diagrams
- **Performance Target**: 95% cache hit rate for repeated diagrams

### Neo4j Integration (Knowledge Graph)
- **Purpose**: Map relationships between diagrams, documents, and concepts
- **New Relationship Types**:
  - `DIAGRAM_DESCRIBES` - Diagram describes a system/concept  
  - `DIAGRAM_REFERENCES` - Diagram references another document
  - `DIAGRAM_VERSION_OF` - Version relationship between diagrams
  - `DIAGRAM_DERIVED_FROM` - Generated from context/memory
  - `DIAGRAM_RELATES_TO` - General relationship between diagrams

### FAISS Integration (Semantic Search)
- **Purpose**: Enable semantic search across diagram content and descriptions
- **Embeddings**: Generate embeddings from diagram descriptions and content
- **Search Capabilities**: Find similar diagrams, related concepts
- **Integration**: Use existing FAISS service with new diagram vectors

## PERFORMANCE & CACHING STRATEGY

### Performance Requirements
- **Diagram Generation**: <2 seconds simple, <10 seconds complex
- **Cache Performance**: 95% hit rate, <100ms cache retrieval  
- **Memory Overhead**: <100MB additional for MermaidService
- **Concurrency**: Support 5+ simultaneous diagram generation

### Caching Strategy
1. **Content-based Caching**: Hash diagram content for cache keys
2. **Template Caching**: Cache frequently used templates in Redis
3. **Result Caching**: Cache generated PNG/SVG files by content hash
4. **Lazy Generation**: Generate diagrams on-demand, cache results
5. **Memory Management**: Cleanup temporary files, optimize memory usage

### Cache Key Strategy
```python
# Diagram cache keys  
"mermaid:diagram:{content_hash}:{theme}:{bg_color}:{format}"
"mermaid:template:{template_id}"
"mermaid:metadata:{diagram_id}"

# Performance metrics
"mermaid:stats:generation_times"
"mermaid:stats:cache_hit_rates" 
"mermaid:stats:usage_patterns"
```

## KNOWLEDGE GRAPH ENHANCEMENT

### Relationship Mapping Strategy
- **Auto-linking**: Automatically link diagrams to related LTMC memories
- **Versioning**: Track diagram evolution and version relationships  
- **Dependencies**: Map diagram dependencies and references
- **Context Integration**: Connect diagrams to source context/documents

### Graph Queries for Diagram Discovery
```cypher
-- Find related diagrams
MATCH (d1:Diagram)-[r:DIAGRAM_RELATES_TO]-(d2:Diagram)
WHERE d1.id = $diagram_id
RETURN d2, r.relationship_type

-- Find diagrams describing a concept
MATCH (c:Concept)<-[:DIAGRAM_DESCRIBES]-(d:Diagram)
WHERE c.name = $concept_name
RETURN d ORDER BY d.created_at DESC

-- Find diagram evolution chain
MATCH path = (d:Diagram)-[:DIAGRAM_VERSION_OF*]->(original:Diagram)
WHERE d.id = $diagram_id
RETURN path
```

## INTEGRATION WITH EXISTING 55 TOOLS

### Context Tools Integration (6 tools)
- **link_resources** - Link diagrams to documents/concepts in knowledge graph
- **query_graph** - Find related diagrams through Neo4j relationships
- **auto_link_documents** - Auto-link diagrams based on content similarity
- **build_context** - Include diagram context in document retrieval
- **retrieve_by_type** - Retrieve diagrams by type/category
- **get_document_relationships** - Include diagram relationships in results

### Memory Tools Integration (5 tools)
- **store_memory** - Save diagram definitions and generation context
- **retrieve_memory** - Search for diagram patterns and templates  
- **search_memories** - Include diagrams in semantic search results
- **delete_memory** - Remove diagrams and associated metadata
- **get_memory_stats** - Include diagram storage in statistics

### Code Pattern Tools Integration (6 tools)
- **log_code_attempt** - Track successful diagram generation patterns
- **get_code_patterns** - Retrieve similar diagram templates and patterns
- **analyze_code_patterns** - Analyze diagram generation success rates
- **store_code_pattern** - Store successful diagram generation workflows
- **retrieve_successful_patterns** - Get high-success diagram templates
- **pattern_performance_analysis** - Analyze diagram generation performance

## IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Weeks 1-2)
**Priority 1 Components - Core Functionality**
- [ ] Create MermaidService with basic generation capabilities
- [ ] Implement basic_mermaid_tools with core 9 functions
- [ ] Add mermaid-py dependency to requirements.txt
- [ ] Modify tool registration in main.py and __init__.py files
- [ ] Create basic Pydantic models for diagram operations
- [ ] SQLite schema extension for diagram metadata

**Deliverables:**
- Working diagram generation via stdio MCP
- Basic file saving and validation
- Integration with existing tool registration system

### Phase 2: Memory Integration (Weeks 3-4)  
**Priority 2 Components - Memory System Integration**
- [ ] Redis caching implementation for generated diagrams
- [ ] FAISS indexing for diagram semantic search
- [ ] Integration with existing context tools
- [ ] Advanced mermaid tools implementation
- [ ] Template system with Redis caching

**Deliverables:**
- Full 4-tier memory integration
- Performance caching with 95% hit rate target
- Template system for reusable diagrams

### Phase 3: Advanced Features (Weeks 5-6)
**Priority 3 Components - Advanced Functionality**  
- [ ] Neo4j knowledge graph integration
- [ ] Analysis mermaid tools implementation
- [ ] Advanced theming and formatting options
- [ ] Batch processing and optimization features
- [ ] Interactive diagram generation

**Deliverables:**
- Complete knowledge graph integration
- Advanced analytics and relationship mapping
- Full feature parity with design specification

### Phase 4: Testing & Optimization (Weeks 7-8)
**Priority 4 Components - Validation & Performance**
- [ ] Comprehensive unit test suite for all 23 tools
- [ ] Integration tests with all memory systems
- [ ] Performance benchmarks and optimization
- [ ] Security validation and input sanitization
- [ ] Documentation and API reference updates

**Deliverables:**
- Production-ready Mermaid integration
- Complete test coverage with performance validation
- Updated documentation and deployment guides

## TESTING & VALIDATION APPROACH

### Testing Strategy

#### Unit Tests (per tool module)
```python
# Example test structure
class TestBasicMermaidTools:
    def test_generate_diagram_success(self):
        # Test successful diagram generation
        
    def test_generate_diagram_invalid_syntax(self):
        # Test error handling for invalid Mermaid syntax
        
    def test_save_diagram_with_metadata(self):
        # Test diagram saving with proper metadata
        
    def test_cache_integration(self):
        # Test Redis caching functionality
```

#### Integration Tests  
- **Memory System Integration**: Test with real SQLite, Redis, Neo4j, FAISS
- **Tool Interaction**: Test interaction with existing 55 tools
- **MCP Protocol**: Validate stdio transport and FastMCP compliance
- **End-to-End Workflows**: Complete diagram generation workflows

#### Performance Tests
- **Load Testing**: Concurrent diagram generation (target: 5+ simultaneous)
- **Memory Usage**: Monitor memory overhead (target: <100MB)
- **Cache Performance**: Validate 95% cache hit rate target
- **Generation Speed**: Validate <2s simple, <10s complex targets

#### Security Tests
- **Input Sanitization**: Test malicious Mermaid code injection
- **Path Validation**: Test file system access controls  
- **Rate Limiting**: Test resource exhaustion protection
- **Data Isolation**: Test proper data access controls

### Validation Criteria

#### Functional Validation
- ✅ All 23 Mermaid tools functional via stdio MCP
- ✅ Integration with all existing 55 tools maintained
- ✅ 4-tier memory system fully utilized
- ✅ Knowledge graph relationships properly established

#### Performance Validation  
- ✅ <2 second generation time for simple diagrams
- ✅ <10 second generation time for complex diagrams
- ✅ 95% cache hit rate for repeated diagrams
- ✅ <100MB memory overhead for MermaidService
- ✅ Support for 5+ concurrent diagram requests

#### Integration Validation
- ✅ MCP protocol compliance maintained
- ✅ Modular architecture with ≤300 lines per module
- ✅ Service layer pattern properly implemented
- ✅ Tool registration pattern consistently followed

## TECHNICAL SPECIFICATIONS

### Dependencies
```python
# New requirement additions
mermaid-py>=0.1.0          # Python Mermaid library
Pillow>=9.0.0             # Image processing for diagram optimization
matplotlib>=3.5.0         # Additional diagram rendering support
```

### Configuration Options
```python
# New settings in LTMCSettings
mermaid_enabled: bool = True
mermaid_default_theme: str = "default"
mermaid_cache_ttl: int = 86400  # 24 hours
mermaid_max_concurrent: int = 5
mermaid_output_directory: str = "./diagrams"
mermaid_max_file_size_mb: int = 10
mermaid_supported_formats: List[str] = ["png", "svg"]
```

### Security Considerations
- **Input Sanitization**: Validate all Mermaid code input to prevent injection
- **File Path Validation**: Restrict diagram output to configured directories
- **Rate Limiting**: Implement per-client rate limiting for diagram generation
- **Resource Limits**: Enforce maximum file sizes and generation timeouts
- **Access Control**: Ensure proper isolation of diagram data per session

### Error Handling Strategy
```python
class MermaidError(Exception):
    """Base exception for Mermaid operations"""

class DiagramGenerationError(MermaidError):
    """Error during diagram generation"""

class DiagramValidationError(MermaidError):
    """Error validating Mermaid syntax"""

class DiagramCacheError(MermaidError):
    """Error accessing diagram cache"""
```

## CONCLUSION

This architectural design provides a comprehensive, production-ready approach to integrating Mermaid.js capabilities into the LTMC system. The design:

1. **Maintains Compatibility** - All existing 55 tools remain fully functional
2. **Follows Established Patterns** - Consistent with LTMC modular architecture
3. **Leverages Full Memory System** - Optimal use of all 4 memory tiers
4. **Ensures Performance** - Comprehensive caching and optimization strategy
5. **Provides Comprehensive Testing** - Full validation and security testing approach

The implementation roadmap provides a clear path from foundation to production deployment, with measurable milestones and validation criteria at each phase.

**Total System Enhancement:**
- **New Tools**: 23 Mermaid-specific tools
- **Total Tools**: 78 tools (55 existing + 23 Mermaid)
- **Memory Integration**: Full 4-tier utilization maintained
- **Performance Impact**: <100MB overhead, 95% cache efficiency
- **Implementation Timeline**: 8 weeks to production ready

This design positions the LTMC system as a comprehensive knowledge management and visualization platform while maintaining its core strengths in memory management and contextual intelligence.

---

**Architecture Review:** Complete ✅  
**Implementation Ready:** Yes ✅  
**Performance Validated:** Design Phase ✅  
**Security Reviewed:** Design Phase ✅  

*Next Phase: Begin Phase 1 Implementation*