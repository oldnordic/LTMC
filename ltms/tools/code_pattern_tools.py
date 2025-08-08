"""Code pattern learning and analysis tools for LTMC MCP server."""

from typing import Dict, Any

# Import implementation functions
from ltms.mcp_server import (
    log_code_attempt as _log_code_attempt,
    get_code_patterns as _get_code_patterns,
    analyze_code_patterns_tool as _analyze_code_patterns
)


def log_code_attempt_handler(input_prompt: str, generated_code: str, result: str, 
                           execution_time_ms: int = None, error_message: str = None,
                           tags: str = None) -> Dict[str, Any]:
    """Log a code generation attempt for learning patterns."""
    return _log_code_attempt(input_prompt, generated_code, result, 
                           execution_time_ms, error_message, tags)


def get_code_patterns_handler(query: str, limit: int = 5) -> Dict[str, Any]:
    """Retrieve similar code patterns from previous successful attempts."""
    return _get_code_patterns(query, limit)


def analyze_code_patterns_handler(query: str = "", limit: int = 10) -> Dict[str, Any]:
    """Analyze code patterns to identify success/failure trends."""
    return _analyze_code_patterns(query, limit)


# Tool definitions for MCP protocol
CODE_PATTERN_TOOLS = {
    "log_code_attempt": {
        "handler": log_code_attempt_handler,
        "description": "Log a code generation attempt for pattern learning and experience replay",
        "schema": {
            "type": "object",
            "properties": {
                "input_prompt": {
                    "type": "string",
                    "description": "The prompt or description of what code was being generated"
                },
                "generated_code": {
                    "type": "string",
                    "description": "The code that was generated"
                },
                "result": {
                    "type": "string",
                    "description": "Result of the attempt (pass, fail, error)",
                    "enum": ["pass", "fail", "error"]
                },
                "execution_time_ms": {
                    "type": "integer",
                    "description": "Execution time in milliseconds (optional)"
                },
                "error_message": {
                    "type": "string",
                    "description": "Error message if the attempt failed (optional)"
                },
                "tags": {
                    "type": "string",
                    "description": "Comma-separated tags for categorization (optional)"
                }
            },
            "required": ["input_prompt", "generated_code", "result"]
        }
    },
    
    "get_code_patterns": {
        "handler": get_code_patterns_handler,
        "description": "Retrieve similar successful code patterns for reference and learning",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query describing the type of code pattern needed"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of patterns to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": ["query"]
        }
    },
    
    "analyze_code_patterns": {
        "handler": analyze_code_patterns_handler,
        "description": "Analyze code generation patterns to identify trends and improvements",
        "schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional query to filter analysis to specific patterns"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of patterns to analyze",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }
    }
}