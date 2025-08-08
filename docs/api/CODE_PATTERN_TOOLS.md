# LTMC Code Pattern Tools Reference

## Overview

Code Pattern Tools provide machine learning-assisted code generation insights through "experience replay" functionality. These tools learn from successful and failed code attempts to improve future code generation and provide pattern-based recommendations.

## Learning and Analysis Tools

### log_code_attempt

Log a code generation attempt for pattern learning and experience replay.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Create an async function to fetch user data from API",
        "generated_code": "async def fetch_user_data(user_id: int):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(f\"/api/users/{user_id}\") as resp:\n            return await resp.json()",
        "result": "pass",
        "execution_time_ms": 150,
        "tags": "async,api,aiohttp"
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `input_prompt` (string, required): The prompt or description of what code was being generated
- `generated_code` (string, required): The code that was generated
- `result` (string, required): Result of the attempt - enum: ["pass", "fail", "error"]
- `execution_time_ms` (integer, optional): Execution time in milliseconds
- `error_message` (string, optional): Error message if the attempt failed
- `tags` (string, optional): Comma-separated tags for categorization

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "pattern_id": 789,
    "input_prompt": "Create an async function to fetch user data from API",
    "result": "pass",
    "tags": ["async", "api", "aiohttp"],
    "logged_at": "2025-08-08T10:30:00Z",
    "pattern_fingerprint": "async_api_fetch_pattern_v1"
  },
  "id": 1
}
```

### get_code_patterns

Retrieve similar successful code patterns for reference and learning.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_code_patterns",
      "arguments": {
        "query": "async API client implementation",
        "limit": 5
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, required): Query describing the type of code pattern needed
- `limit` (integer, optional): Maximum number of patterns to return (1-20, default: 5)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "query": "async API client implementation",
    "patterns": [
      {
        "pattern_id": 789,
        "input_prompt": "Create an async function to fetch user data from API",
        "generated_code": "async def fetch_user_data(user_id: int):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(f\"/api/users/{user_id}\") as resp:\n            return await resp.json()",
        "result": "pass",
        "execution_time_ms": 150,
        "tags": ["async", "api", "aiohttp"],
        "similarity_score": 0.94,
        "success_rate": 0.89,
        "created_at": "2025-08-08T10:30:00Z"
      },
      {
        "pattern_id": 456,
        "input_prompt": "Async HTTP client with error handling",
        "generated_code": "async def safe_api_call(url: str):\n    try:\n        async with aiohttp.ClientSession() as session:\n            async with session.get(url) as resp:\n                resp.raise_for_status()\n                return await resp.json()\n    except aiohttp.ClientError as e:\n        logger.error(f\"API call failed: {e}\")\n        return None",
        "result": "pass",
        "execution_time_ms": 200,
        "tags": ["async", "error-handling", "aiohttp"],
        "similarity_score": 0.87,
        "success_rate": 0.92,
        "created_at": "2025-08-07T15:20:00Z"
      }
    ],
    "total_patterns": 25,
    "average_success_rate": 0.85
  },
  "id": 1
}
```

### analyze_code_patterns

Analyze code generation patterns to identify trends and improvements.

**HTTP Request:**
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "analyze_code_patterns",
      "arguments": {
        "query": "async functions",
        "limit": 50
      }
    },
    "id": 1
  }'
```

**Parameters:**
- `query` (string, optional): Optional query to filter analysis to specific patterns
- `limit` (integer, optional): Maximum number of patterns to analyze (1-100, default: 10)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "analysis": {
      "total_patterns_analyzed": 50,
      "success_statistics": {
        "overall_success_rate": 0.78,
        "pass_count": 39,
        "fail_count": 8,
        "error_count": 3
      },
      "performance_metrics": {
        "average_execution_time_ms": 175,
        "fastest_execution_ms": 50,
        "slowest_execution_ms": 2500
      },
      "tag_analysis": {
        "most_common_tags": [
          {"tag": "async", "count": 45, "success_rate": 0.82},
          {"tag": "api", "count": 30, "success_rate": 0.85},
          {"tag": "error-handling", "count": 25, "success_rate": 0.92}
        ],
        "success_predictors": [
          {"tag": "error-handling", "success_boost": 0.15},
          {"tag": "type-hints", "success_boost": 0.12}
        ]
      },
      "failure_patterns": [
        {
          "common_error": "AttributeError: 'NoneType' object has no attribute",
          "frequency": 5,
          "suggested_fix": "Add null checks before attribute access"
        },
        {
          "common_error": "SyntaxError: invalid syntax",
          "frequency": 3,
          "suggested_fix": "Review Python syntax for async/await patterns"
        }
      ],
      "improvement_suggestions": [
        "Patterns with error handling have 15% higher success rates",
        "Type hints correlate with 12% improvement in success",
        "Async patterns average 23% faster execution than sync equivalents"
      ]
    },
    "query_filter": "async functions",
    "analysis_timestamp": "2025-08-08T10:30:00Z"
  },
  "id": 1
}
```

## Experience Replay Workflow

### 1. Learning Phase
```bash
# Log successful patterns
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Database connection with connection pooling",
        "generated_code": "import asyncpg\n\nclass DatabasePool:\n    def __init__(self, dsn: str):\n        self._pool = None\n        self.dsn = dsn\n    \n    async def connect(self):\n        self._pool = await asyncpg.create_pool(self.dsn)\n    \n    async def fetch_one(self, query: str, *args):\n        async with self._pool.acquire() as conn:\n            return await conn.fetchrow(query, *args)",
        "result": "pass",
        "execution_time_ms": 300,
        "tags": "database,asyncpg,connection-pool,async"
      }
    },
    "id": 1
  }'

# Log failed attempts for learning
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "log_code_attempt",
      "arguments": {
        "input_prompt": "Simple database query without connection pooling",
        "generated_code": "import asyncpg\n\nasync def get_user(user_id):\n    conn = await asyncpg.connect(\"postgresql://...\")\n    user = await conn.fetchrow(\"SELECT * FROM users WHERE id = $1\", user_id)\n    # Missing: await conn.close()\n    return user",
        "result": "fail",
        "error_message": "Connection not closed, resource leak detected",
        "tags": "database,asyncpg,resource-leak"
      }
    },
    "id": 2
  }'
```

### 2. Pattern Retrieval Phase
```bash
# Get similar successful patterns
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "get_code_patterns",
      "arguments": {
        "query": "database connection async",
        "limit": 3
      }
    },
    "id": 3
  }'
```

### 3. Analysis Phase
```bash
# Analyze patterns for insights
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "analyze_code_patterns",
      "arguments": {
        "query": "database",
        "limit": 20
      }
    },
    "id": 4
  }'
```

## Pattern Quality Indicators

### High-Quality Patterns
- **Success Rate > 0.85**: Patterns with high reliability
- **Error Handling**: Patterns that include proper exception handling
- **Type Hints**: Code with comprehensive type annotations
- **Documentation**: Patterns with docstrings and comments
- **Performance**: Fast execution times relative to complexity

### Pattern Improvement Factors
- **Tag Diversity**: Multiple relevant tags increase pattern discoverability
- **Context Richness**: Detailed input prompts improve matching accuracy
- **Performance Metrics**: Execution time data helps with optimization decisions
- **Failure Learning**: Failed attempts provide valuable negative examples

## Best Practices

### Logging Code Attempts
1. **Be Specific**: Use detailed input prompts that capture the exact requirements
2. **Tag Consistently**: Use standardized tags across similar patterns
3. **Include Context**: Add execution time and error details when available
4. **Log Both Success and Failure**: Failed attempts are valuable for learning

### Retrieving Patterns
1. **Use Descriptive Queries**: Include key technical terms and concepts
2. **Review Multiple Patterns**: Don't rely on just the top result
3. **Consider Success Rates**: Prefer patterns with higher success rates
4. **Adapt to Context**: Modify retrieved patterns for your specific use case

### Pattern Analysis
1. **Regular Analysis**: Perform pattern analysis periodically to identify trends
2. **Focus on Failures**: Analyze failure patterns to avoid common mistakes
3. **Track Performance**: Monitor execution time trends for optimization opportunities
4. **Update Based on Insights**: Use analysis results to improve coding practices

## Integration with Development Workflow

### IDE Integration
```python
# Example: Using patterns in development workflow
async def get_successful_pattern(prompt: str):
    """Get a successful code pattern for reference."""
    response = await ltmc_client.call_tool(
        "get_code_patterns",
        {"query": prompt, "limit": 1}
    )
    return response["patterns"][0] if response["patterns"] else None

# Usage in development
pattern = await get_successful_pattern("async database query with error handling")
if pattern:
    print(f"Reference code:\n{pattern['generated_code']}")
    print(f"Success rate: {pattern['success_rate']}")
```

### Continuous Learning
```python
# Example: Automatic pattern logging
async def log_attempt_with_execution(prompt: str, code: str, test_result: bool):
    """Log code attempt with test results."""
    result = "pass" if test_result else "fail"
    await ltmc_client.call_tool("log_code_attempt", {
        "input_prompt": prompt,
        "generated_code": code,
        "result": result,
        "tags": extract_tags_from_code(code)
    })

# Automatic logging after code execution
await log_attempt_with_execution(
    "Create user authentication endpoint",
    generated_code,
    test_results.all_passed
)
```

## Next Steps

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [Context Tools Reference](CONTEXT_TOOLS.md) - Advanced context management tools
- [System Architecture](../architecture/SYSTEM_ARCHITECTURE.md) - Technical architecture overview
- [ML Integration Guide](../guides/ML_INTEGRATION.md) - Advanced ML features documentation