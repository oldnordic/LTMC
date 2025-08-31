# LTMC Sequential MCP Integration - Usage Guide

## Overview

This guide provides practical examples and patterns for using the Sequential MCP Integration with LTMC. The integration provides four main MCP tools for creating, analyzing, and searching sequential reasoning chains.

## Available MCP Tools

### 1. `thought_create`

Create a new thought in a sequential reasoning chain with atomic database storage.

**Schema**:
```json
{
  "session_id": "string (required)",
  "content": "string (required)", 
  "thought_type": "problem|intermediate|conclusion (default: intermediate)",
  "previous_thought_id": "string (optional ULID)",
  "step_number": "integer (optional, min: 1)",
  "metadata": "object (optional)"
}
```

**Example Usage**:
```json
{
  "session_id": "problem_solving_session_001",
  "content": "What is the most efficient algorithm for sorting large datasets?",
  "thought_type": "problem",
  "step_number": 1,
  "metadata": {
    "domain": "algorithms",
    "complexity": "high"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "ulid_id": "01HKPX8K2QG9W5T7N3M4R6V2B8",
    "session_id": "problem_solving_session_001",
    "content_hash": "a7b8c9d...",
    "created_at": "2024-01-01T10:00:00.000Z",
    "databases_affected": {
      "sqlite": true,
      "faiss": true, 
      "neo4j": true,
      "redis": true
    },
    "execution_time_ms": 47.2,
    "sla_compliant": true
  }
}
```

### 2. `thought_analyze_chain`

Analyze complete thought chain for a session using graph traversal.

**Schema**:
```json
{
  "session_id": "string (required)"
}
```

**Example Usage**:
```json
{
  "session_id": "problem_solving_session_001"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "problem_solving_session_001",
    "chain_length": 3,
    "thoughts": [
      {
        "ulid_id": "01HKPX8K2QG9W5T7N3M4R6V2B8",
        "content": "What is the most efficient algorithm for sorting large datasets?",
        "step_number": 1,
        "thought_type": "problem",
        "created_at": "2024-01-01T10:00:00Z"
      },
      {
        "ulid_id": "01HKPX8K2QG9W5T7N3M4R6V2B9", 
        "content": "Let me compare merge sort, quicksort, and radix sort for different data characteristics.",
        "step_number": 2,
        "thought_type": "intermediate",
        "created_at": "2024-01-01T10:05:00Z"
      },
      {
        "ulid_id": "01HKPX8K2QG9W5T7N3M4R6V2C0",
        "content": "For large datasets, a hybrid approach using quicksort with median-of-3 pivot and fallback to heapsort provides optimal performance.",
        "step_number": 3,
        "thought_type": "conclusion", 
        "created_at": "2024-01-01T10:10:00Z"
      }
    ],
    "analysis": {
      "total_thoughts": 3,
      "thought_types": {
        "problem": 1,
        "intermediate": 1,
        "conclusion": 1
      },
      "average_content_length": 127,
      "has_problem_definition": true,
      "has_conclusion": true,
      "coherence_score": 0.8,
      "summary": "Complete reasoning chain with 3 thoughts"
    }
  }
}
```

### 3. `thought_find_similar`

Find similar reasoning patterns using FAISS semantic search.

**Schema**:
```json
{
  "query": "string (required)",
  "k": "integer (optional, min: 1, max: 20, default: 5)",
  "include_chains": "boolean (optional, default: true)"
}
```

**Example Usage**:
```json
{
  "query": "efficient sorting algorithms for large datasets",
  "k": 3,
  "include_chains": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query": "efficient sorting algorithms for large datasets",
    "results_count": 2,
    "similar_thoughts": [
      {
        "doc_id": "01HKPX8K2QG9W5T7N3M4R6V2B8",
        "content": "What is the most efficient algorithm for sorting large datasets?",
        "similarity_score": 0.94,
        "metadata": {
          "session_id": "problem_solving_session_001",
          "domain": "algorithms"
        },
        "chain_length": 3,
        "session_preview": [
          {
            "content": "What is the most efficient algorithm for sorting large datasets?",
            "thought_type": "problem"
          }
        ],
        "full_chain": [
          // Complete chain when include_chains=true
        ]
      },
      {
        "doc_id": "01HKPX8K2QG9W5T7N3M4R6V2C1",
        "content": "Comparing quicksort vs mergesort performance characteristics",
        "similarity_score": 0.87,
        "metadata": {
          "session_id": "algorithm_comparison_session",
          "domain": "algorithms"  
        },
        "chain_length": 5,
        "session_preview": [
          {
            "content": "Comparing quicksort vs mergesort performance characteristics",
            "thought_type": "intermediate"
          }
        ]
      }
    ]
  }
}
```

### 4. `sequential_health_status`

Get comprehensive health status for Sequential MCP integration.

**Schema**:
```json
{}
```

**Example Usage**:
```json
{}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "sequential_coordinator_status": "healthy",
    "database_coordination": {
      "overall_status": "healthy",
      "databases": {
        "sqlite": true,
        "faiss": true,
        "neo4j": true, 
        "redis": true
      },
      "performance_metrics": {
        "avg_response_time_ms": 23.4
      }
    },
    "metrics": {
      "thoughts_created": 1247,
      "chains_analyzed": 89,
      "similarity_searches": 156,
      "avg_creation_time_ms": 42.7,
      "avg_retrieval_time_ms": 18.3
    },
    "sla_compliance": {
      "creation_sla_compliant": true,
      "creation_sla_target": 100,
      "retrieval_sla_compliant": true,
      "retrieval_sla_target": 50,
      "avg_creation_time_ms": 42.7,
      "avg_retrieval_time_ms": 18.3
    }
  }
}
```

## Usage Patterns

### 1. Basic Problem-Solving Chain

```python
# Step 1: Define the problem
problem_result = await mcp_client.call_tool("thought_create", {
    "session_id": "debug_session_001",
    "content": "The application is crashing when processing large JSON files. What could be causing this?",
    "thought_type": "problem",
    "step_number": 1,
    "metadata": {"severity": "high", "domain": "debugging"}
})

problem_ulid = problem_result["data"]["ulid_id"]

# Step 2: Analyze potential causes  
analysis_result = await mcp_client.call_tool("thought_create", {
    "session_id": "debug_session_001", 
    "content": "Potential causes: 1) Memory exhaustion from large files, 2) JSON parsing errors, 3) Thread safety issues. Let me examine each.",
    "thought_type": "intermediate",
    "previous_thought_id": problem_ulid,
    "step_number": 2
})

# Step 3: Reach conclusion
conclusion_result = await mcp_client.call_tool("thought_create", {
    "session_id": "debug_session_001",
    "content": "Memory profiling shows excessive heap usage. Solution: Implement streaming JSON parser with chunked processing.",
    "thought_type": "conclusion", 
    "previous_thought_id": analysis_result["data"]["ulid_id"],
    "step_number": 3
})

# Step 4: Analyze the complete chain
chain_analysis = await mcp_client.call_tool("thought_analyze_chain", {
    "session_id": "debug_session_001"
})
```

### 2. Leveraging Similar Reasoning

```python
# Find similar debugging approaches
similar_thoughts = await mcp_client.call_tool("thought_find_similar", {
    "query": "application crashing large files memory issues",
    "k": 5,
    "include_chains": True
})

# Use insights from similar cases
for thought in similar_thoughts["data"]["similar_thoughts"]:
    if thought["similarity_score"] > 0.8:
        # Analyze successful resolution patterns
        chain = thought["full_chain"]
        successful_solutions = [
            t for t in chain 
            if t["thought_type"] == "conclusion"
        ]
```

### 3. Iterative Problem Refinement

```python
# Start with broad problem statement
initial_thought = await mcp_client.call_tool("thought_create", {
    "session_id": "optimization_session",
    "content": "System performance is degrading under load",
    "thought_type": "problem"
})

# Add refinements based on analysis
refinement = await mcp_client.call_tool("thought_create", {
    "session_id": "optimization_session",
    "content": "Specifically: Response times increase from 100ms to 2000ms when concurrent users exceed 50",
    "thought_type": "intermediate", 
    "previous_thought_id": initial_thought["data"]["ulid_id"]
})

# Continue chain with specific analysis
database_analysis = await mcp_client.call_tool("thought_create", {
    "session_id": "optimization_session",
    "content": "Database connection pool exhaustion at 45 connections. Current pool size: 40 connections.",
    "thought_type": "intermediate",
    "previous_thought_id": refinement["data"]["ulid_id"]
})
```

### 4. Cross-Session Pattern Recognition

```python
# Search for patterns across multiple sessions
async def analyze_recurring_problems():
    # Find similar problem statements
    problem_patterns = await mcp_client.call_tool("thought_find_similar", {
        "query": "performance degradation under load",
        "k": 10,
        "include_chains": False
    })
    
    # Group by session and analyze successful resolutions
    sessions_with_solutions = []
    
    for thought in problem_patterns["data"]["similar_thoughts"]:
        session_id = thought["metadata"]["session_id"]
        
        # Get complete chain for this session
        chain = await mcp_client.call_tool("thought_analyze_chain", {
            "session_id": session_id
        })
        
        # Check if chain has successful conclusion
        if chain["data"]["analysis"]["has_conclusion"]:
            sessions_with_solutions.append({
                "session_id": session_id,
                "similarity_score": thought["similarity_score"],
                "chain": chain["data"]
            })
    
    return sessions_with_solutions
```

## Integration with LTMC Tools

### 1. Using with Memory Storage

```python
# Store reasoning chain results in LTMC memory
chain_result = await mcp_client.call_tool("thought_analyze_chain", {
    "session_id": "architecture_design_session"
})

# Store analysis in LTMC memory system
await ltmc_memory.store({
    "file_name": f"reasoning_chain_{chain_result['data']['session_id']}.json",
    "content": json.dumps(chain_result["data"], indent=2),
    "resource_type": "reasoning_analysis",
    "metadata": {
        "chain_length": chain_result["data"]["chain_length"],
        "has_conclusion": chain_result["data"]["analysis"]["has_conclusion"]
    }
})
```

### 2. Using with Graph Operations

```python
# Link reasoning chains to related concepts in knowledge graph
chain_analysis = await mcp_client.call_tool("thought_analyze_chain", {
    "session_id": "system_design_session"  
})

# Create graph relationships
for thought in chain_analysis["data"]["thoughts"]:
    if thought["thought_type"] == "conclusion":
        await ltmc_graph.link({
            "source_id": thought["ulid_id"],
            "target_id": "system_architecture_concept",
            "relation": "CONCLUDES_ABOUT",
            "properties": {
                "reasoning_session": "system_design_session",
                "conclusion_confidence": 0.9
            }
        })
```

## Performance Optimization Tips

### 1. Session Management

- **Keep sessions focused**: Limit chains to 10-15 thoughts for optimal performance
- **Use meaningful session IDs**: Include context in session identifiers for easier retrieval
- **Clean up old sessions**: Implement session lifecycle management

### 2. Content Optimization

- **Concise thoughts**: Keep individual thoughts focused and under 500 characters when possible
- **Rich metadata**: Use metadata for categorization and filtering rather than embedding in content
- **Thought types**: Use appropriate thought types (problem/intermediate/conclusion) for better analysis

### 3. Search Optimization

- **Specific queries**: More specific search queries yield better semantic matches
- **Appropriate k values**: Start with k=5, increase only when needed
- **Chain inclusion**: Set include_chains=false for faster searches when full context isn't needed

## Error Handling

### 1. Common Error Patterns

```python
async def create_thought_with_retry(session_id, content, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await mcp_client.call_tool("thought_create", {
                "session_id": session_id,
                "content": content
            })
            
            if result["success"]:
                return result
            else:
                logger.warning(f"Thought creation failed: {result['error']}")
                
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    raise Exception(f"Failed to create thought after {max_retries} attempts")
```

### 2. Health Monitoring

```python
async def monitor_sequential_health():
    while True:
        try:
            health = await mcp_client.call_tool("sequential_health_status", {})
            
            if not health["success"]:
                logger.error("Sequential health check failed")
                continue
                
            sla_compliance = health["data"]["sla_compliance"]
            
            if not sla_compliance["creation_sla_compliant"]:
                logger.warning(f"Creation SLA violation: {sla_compliance['avg_creation_time_ms']}ms")
                
            if not sla_compliance["retrieval_sla_compliant"]:
                logger.warning(f"Retrieval SLA violation: {sla_compliance['avg_retrieval_time_ms']}ms")
                
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
            
        await asyncio.sleep(60)  # Check every minute
```

## Best Practices

### 1. Reasoning Chain Design

- **Start with clear problems**: Begin each session with a well-defined problem statement
- **Use intermediate steps**: Break complex reasoning into logical intermediate steps  
- **End with conclusions**: Always provide clear conclusions or action items
- **Include context**: Use metadata to provide domain context and categorization

### 2. Performance Considerations

- **Monitor SLAs**: Regularly check health status to ensure performance targets are met
- **Batch operations**: When creating multiple thoughts, consider batching for efficiency
- **Use appropriate indexing**: Leverage FAISS semantic search for content-based queries
- **Session cleanup**: Implement policies for archiving or cleaning old reasoning sessions

### 3. Integration Patterns

- **Combine with memory**: Store important reasoning chains in LTMC memory for long-term reference
- **Link with graphs**: Create knowledge graph relationships between reasoning and concepts
- **Cross-reference sessions**: Use similarity search to find related reasoning across sessions
- **Pattern extraction**: Regularly analyze successful reasoning patterns for reuse

This usage guide provides the foundation for effectively leveraging Sequential MCP Integration within LTMC's ecosystem. The integration maintains full compatibility with LTMC's existing tools while providing powerful new reasoning capabilities.