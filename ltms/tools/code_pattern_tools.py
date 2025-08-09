"""Code pattern learning and analysis tools for LTMC MCP server."""

from typing import Dict, Any

# Import implementation functions
from ltms.mcp_server import (
    log_code_attempt as _log_code_attempt,
    get_code_patterns as _get_code_patterns,
    analyze_code_patterns_tool as _analyze_code_patterns
)


def log_code_attempt_handler(input_prompt: str, generated_code: str, result: str,
                           function_name: str = None, file_name: str = None, module_name: str = None,
                           execution_time_ms: int = None, error_message: str = None,
                           tags = None) -> Dict[str, Any]:
    """Log a code generation attempt for learning patterns."""
    # Convert tags to list if provided - handle both string and list input
    if tags:
        if isinstance(tags, str):
            tag_list = [tag.strip() for tag in tags.split(',')]
        elif isinstance(tags, list):
            tag_list = tags
        else:
            tag_list = None
    else:
        tag_list = None
    
    return _log_code_attempt(input_prompt, generated_code, result,
                           function_name, file_name, module_name,
                           execution_time_ms, error_message, tag_list)


def get_code_patterns_handler(query: str, result_filter: str = None, function_name: str = None, file_name: str = None, module_name: str = None, top_k: int = 5) -> Dict[str, Any]:
    """Retrieve similar code patterns from previous successful attempts."""
    return _get_code_patterns(query, result_filter, function_name, file_name, module_name, top_k)


def analyze_code_patterns_handler(function_name: str = None, file_name: str = None, module_name: str = None, time_range_days: int = 30, patterns: list = None) -> Dict[str, Any]:
    """Analyze code patterns to identify success/failure trends."""
    return _analyze_code_patterns(function_name, file_name, module_name, time_range_days, patterns)


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
                    "description": "Result of the attempt (pass, fail, partial)",
                    "enum": ["pass", "fail", "partial"]
                },
                "function_name": {
                    "type": "string",
                    "description": "Name of the function being implemented (optional)"
                },
                "file_name": {
                    "type": "string",
                    "description": "Name of the file where code was generated (optional)"
                },
                "module_name": {
                    "type": "string",
                    "description": "Name of the module or package (optional)"
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
                    "oneOf": [
                        {
                            "type": "string",
                            "description": "Comma-separated tags for categorization (optional)"
                        },
                        {
                            "type": "array",
                            "description": "List of tags for categorization (optional)",
                            "items": {"type": "string"}
                        }
                    ]
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
                "result_filter": {
                    "type": "string",
                    "description": "Filter by result type (pass, fail, partial)",
                    "enum": ["pass", "fail", "partial"]
                },
                "function_name": {
                    "type": "string",
                    "description": "Filter by function name"
                },
                "file_name": {
                    "type": "string",
                    "description": "Filter by file name"
                },
                "module_name": {
                    "type": "string",
                    "description": "Filter by module name"
                },
                "top_k": {
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
                "function_name": {
                    "type": "string",
                    "description": "Filter analysis by function name (optional)"
                },
                "file_name": {
                    "type": "string",
                    "description": "Filter analysis by file name (optional)"
                },
                "module_name": {
                    "type": "string",
                    "description": "Filter analysis by module name (optional)"
                },
                "time_range_days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 365
                },
                "patterns": {
                    "type": "array",
                    "description": "Specific patterns to analyze (optional)",
                    "items": {"type": "string"}
                }
            }
        }
    }
}