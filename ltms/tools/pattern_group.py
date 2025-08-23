"""Pattern group tools - canonical group:operation interface."""

from typing import Dict, Any, List

# Import existing implementations
from ltms.services.code_pattern_service import (
    log_code_attempt as _log_code_attempt,
    get_code_patterns as _get_code_patterns,
    analyze_code_patterns as _analyze_code_patterns
)
from ltms.services.code_analyzer import CodeAnalyzer


def pattern_log_attempt(input_prompt: str, generated_code: str, result: str, error_message: str = None, execution_time_ms: int = None, file_name: str = None, function_name: str = None, module_name: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """Log code attempt/experience."""
    return _log_code_attempt(
        input_prompt=input_prompt,
        generated_code=generated_code,
        result=result,
        error_message=error_message,
        execution_time_ms=execution_time_ms,
        file_name=file_name,
        function_name=function_name,
        module_name=module_name,
        tags=tags
    )


def pattern_get_patterns(query: str, result_filter: str = None, top_k: int = 5, file_name: str = None, function_name: str = None, module_name: str = None) -> Dict[str, Any]:
    """Retrieve code patterns/solutions."""
    return _get_code_patterns(
        query=query,
        result_filter=result_filter,
        top_k=top_k,
        file_name=file_name,
        function_name=function_name,
        module_name=module_name
    )


def pattern_analyze(patterns: List[str] = None, time_range_days: int = 30, file_name: str = None, function_name: str = None, module_name: str = None) -> Dict[str, Any]:
    """Analyze code pattern usage."""
    return _analyze_code_patterns(
        patterns=patterns,
        time_range_days=time_range_days,
        file_name=file_name,
        function_name=function_name,
        module_name=module_name
    )


def pattern_extract_functions(source_code: str, file_path: str = "", language: str = "auto", extract_docstrings: bool = True, include_private: bool = False, complexity_analysis: bool = True) -> Dict[str, Any]:
    """Extract function definitions (LangExtract)."""
    try:
        analyzer = CodeAnalyzer()
        result = analyzer.extract_functions(
            source_code=source_code,
            file_path=file_path,
            language=language,
            extract_docstrings=extract_docstrings,
            include_private=include_private,
            complexity_analysis=complexity_analysis
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "functions": [],
            "metadata": {
                "language": language,
                "processing_time": 0.0
            }
        }


def pattern_extract_classes(source_code: str, file_path: str = "", language: str = "auto", analyze_inheritance: bool = True, extract_relationships: bool = True, include_private: bool = False) -> Dict[str, Any]:
    """Extract class definitions (LangExtract)."""
    try:
        analyzer = CodeAnalyzer()
        result = analyzer.extract_classes(
            source_code=source_code,
            file_path=file_path,
            language=language,
            analyze_inheritance=analyze_inheritance,
            extract_relationships=extract_relationships,
            include_private=include_private
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "classes": [],
            "metadata": {
                "language": language,
                "processing_time": 0.0
            }
        }


def pattern_summarize(source_code: str, file_path: str = "", language: str = "auto", summary_length: str = "medium", include_complexity: bool = True, include_todos: bool = True) -> Dict[str, Any]:
    """Summarize code using AST/LLM (LangExtract)."""
    try:
        analyzer = CodeAnalyzer()
        result = analyzer.summarize_code(
            source_code=source_code,
            file_path=file_path,
            language=language,
            summary_length=summary_length,
            include_complexity=include_complexity,
            include_todos=include_todos
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "summary": "",
            "metadata": {
                "language": language,
                "processing_time": 0.0
            }
        }


def pattern_extract_comments(source_code: str, file_path: str = "", language: str = "auto", include_docstrings: bool = True, include_todos: bool = True, extract_metadata: bool = True) -> Dict[str, Any]:
    """Extract comments/docstrings (LangExtract)."""
    try:
        analyzer = CodeAnalyzer()
        result = analyzer.extract_comments(
            source_code=source_code,
            file_path=file_path,
            language=language,
            include_docstrings=include_docstrings,
            include_todos=include_todos,
            extract_metadata=extract_metadata
        )
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "comments": [],
            "metadata": {
                "language": language,
                "processing_time": 0.0
            }
        }


# Tool registry with group:operation names  
# PRODUCTION COMPLIANCE: Only include fully functional tools
PATTERN_GROUP_TOOLS = {
    # REMOVED: Database-dependent tools that fail
    # "pattern:log_attempt": FAILS - 'LTMCConfig' object has no attribute 'get_db_path'
    # REMOVED: Database-dependent pattern tools that fail
    # "pattern:get_patterns": FAILS - 'LTMCConfig' object has no attribute 'get_db_path'  
    # "pattern:analyze": FAILS - analyze_code_patterns() unexpected keyword argument
    
    "pattern:extract_functions": {
        "handler": pattern_extract_functions,
        "description": "Extract function definitions (LangExtract)",
        "schema": {
            "type": "object",
            "properties": {
                "source_code": {
                    "type": "string",
                    "description": "Source code content to analyze"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional file path for context and language detection",
                    "default": ""
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (auto-detect if not specified)",
                    "enum": ["auto", "python", "javascript"],
                    "default": "auto"
                },
                "extract_docstrings": {
                    "type": "boolean",
                    "description": "Whether to extract and parse docstrings",
                    "default": True
                },
                "include_private": {
                    "type": "boolean",
                    "description": "Whether to include private/internal functions",
                    "default": False
                },
                "complexity_analysis": {
                    "type": "boolean",
                    "description": "Whether to calculate complexity metrics",
                    "default": True
                }
            },
            "required": ["source_code"]
        }
    },
    
    "pattern:extract_classes": {
        "handler": pattern_extract_classes,
        "description": "Extract class definitions (LangExtract)",
        "schema": {
            "type": "object",
            "properties": {
                "source_code": {
                    "type": "string",
                    "description": "Source code content to analyze"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional file path for context and language detection",
                    "default": ""
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (auto-detect if not specified)",
                    "enum": ["auto", "python", "javascript"],
                    "default": "auto"
                },
                "analyze_inheritance": {
                    "type": "boolean",
                    "description": "Whether to analyze inheritance hierarchies",
                    "default": True
                },
                "extract_relationships": {
                    "type": "boolean",
                    "description": "Whether to analyze class relationships",
                    "default": True
                },
                "include_private": {
                    "type": "boolean",
                    "description": "Whether to include private/internal classes",
                    "default": False
                }
            },
            "required": ["source_code"]
        }
    },
    
    "pattern:summarize": {
        "handler": pattern_summarize,
        "description": "Summarize code using AST/LLM (LangExtract)",
        "schema": {
            "type": "object",
            "properties": {
                "source_code": {
                    "type": "string",
                    "description": "Source code content to summarize"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional file path for context and language detection",
                    "default": ""
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (auto-detect if not specified)",
                    "enum": ["auto", "python", "javascript"],
                    "default": "auto"
                },
                "summary_length": {
                    "type": "string",
                    "description": "Length of natural language summary",
                    "enum": ["brief", "medium", "detailed"],
                    "default": "medium"
                },
                "include_complexity": {
                    "type": "boolean",
                    "description": "Whether to include complexity analysis",
                    "default": True
                },
                "include_todos": {
                    "type": "boolean",
                    "description": "Whether to include TODO/FIXME analysis",
                    "default": True
                }
            },
            "required": ["source_code"]
        }
    },
    
    "pattern:extract_comments": {
        "handler": pattern_extract_comments,
        "description": "Extract comments/docstrings (LangExtract)",
        "schema": {
            "type": "object",
            "properties": {
                "source_code": {
                    "type": "string",
                    "description": "Source code content to analyze"
                },
                "file_path": {
                    "type": "string",
                    "description": "Optional file path for context and language detection",
                    "default": ""
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (auto-detect if not specified)",
                    "enum": ["auto", "python", "javascript"],
                    "default": "auto"
                },
                "include_docstrings": {
                    "type": "boolean",
                    "description": "Whether to extract and parse docstrings",
                    "default": True
                },
                "include_todos": {
                    "type": "boolean",
                    "description": "Whether to extract TODO/FIXME/NOTE comments",
                    "default": True
                },
                "extract_metadata": {
                    "type": "boolean",
                    "description": "Whether to include processing metadata",
                    "default": True
                }
            },
            "required": ["source_code"]
        }
    }
}