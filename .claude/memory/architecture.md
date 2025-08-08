# KWE Architecture Memory

## 4-Agent MetaCognitive Framework

### Agent Types
- **MetaCognitiveCoderAgent**
  - Purpose: Advanced AI-powered coding
  - Location: `agents/meta_cognitive/coder_agent.py`
  - Responsibilities:
    - Generate high-quality, type-safe code
    - Implement complex algorithmic solutions
    - Use Ollama DeepSeek reasoning for intelligent code generation

- **MetaCognitiveResearchAgent**
  - Purpose: Intelligent research and investigation
  - Location: `agents/meta_cognitive/research_agent.py`
  - Responsibilities:
    - Conduct comprehensive knowledge gathering
    - Analyze complex technical problems
    - Support decision-making with contextual insights

- **DevelopmentAgent**
  - Purpose: Project management and task coordination
  - Location: `agents/development_agent.py`
  - Responsibilities:
    - Manage project workflow
    - Coordinate inter-agent communication
    - Track project progress and milestones

- **QualityAgent**
  - Purpose: Comprehensive testing and validation
  - Location: `agents/quality_agent.py`
  - Responsibilities:
    - Design and execute comprehensive test suites
    - Validate system integrity
    - Perform continuous quality assurance

## 4-Tier Memory System

### Memory Tier Architecture
1. **PostgreSQL (Temporal Memory)**
   - Host: `192.168.1.119:5432`
   - File: `postgresql_temporal_memory.py`
   - Purpose: Store time-series and historical data
   - Key Features:
     - Chronological data tracking
     - Temporal query capabilities
     - High-performance time-based indexing

2. **Redis (Cache Layer)**
   - Host: `localhost:6380`
   - File: `redis_cache_layer_async.py`
   - Purpose: High-speed, low-latency caching
   - Key Features:
     - Async cache operations
     - In-memory data storage
     - Quick retrieval and temporary state management

3. **Neo4j (Graph Memory)**
   - Host: `localhost:7474`
   - File: `neo4j_relational_memory.py`
   - Purpose: Complex relationship and graph-based data
   - Key Features:
     - Advanced relationship querying
     - Knowledge graph management
     - Semantic link analysis

4. **Qdrant (Semantic Memory)**
   - Host: `localhost:6333`
   - File: `qdrant_semantic_memory.py`
   - Purpose: Vector-based semantic storage
   - Key Features:
     - High-dimensional vector embeddings
     - Semantic similarity search
     - Machine learning model integration

## System Integration Principles
- Unified memory access through `memory/enhanced_state_manager.py`
- Async-first design for all memory interactions
- Comprehensive error handling and timeout management
- Strict type safety across memory interfaces

## Communication Protocols
- WebSocket for real-time updates
- gRPC for inter-agent communication
- JWT for secure authentication
- Ollama reasoning for intelligent routing