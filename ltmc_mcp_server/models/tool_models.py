"""
Tool Input/Output Models
=======================

Pydantic models for tool inputs and outputs following FastMCP patterns.

From research - FastMCP automatically generates schemas from type hints.
These models provide structured input/output for the 55+ tools.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .base_models import SuccessResponse, SearchResult, PerformanceMetrics


# MEMORY TOOLS MODELS

class StoreMemoryInput(BaseModel):
    """Input for store_memory tool."""
    
    content: str = Field(description="Content to store in memory")
    file_name: str = Field(description="File name for the stored content")
    resource_type: str = Field(default="document", description="Type of resource (document, code, note)")


class StoreMemoryOutput(SuccessResponse):
    """Output for store_memory tool."""
    
    resource_id: int = Field(description="ID of stored resource")
    vector_id: int = Field(description="FAISS vector ID for semantic search")
    chunks_created: int = Field(description="Number of text chunks created")
    performance: Optional[PerformanceMetrics] = Field(default=None)


class RetrieveMemoryInput(BaseModel):
    """Input for retrieve_memory tool."""
    
    query: str = Field(description="Search query for memory retrieval")
    conversation_id: Optional[str] = Field(default=None, description="Conversation context ID")
    top_k: int = Field(default=5, description="Number of results to return", ge=1, le=50)
    resource_type: Optional[str] = Field(default=None, description="Filter by resource type")


class RetrieveMemoryOutput(SuccessResponse):
    """Output for retrieve_memory tool."""
    
    results: List[SearchResult] = Field(description="Search results")
    query_processed: str = Field(description="Processed query string")
    total_matches: int = Field(description="Total number of matches found")
    performance: Optional[PerformanceMetrics] = Field(default=None)


# CHAT TOOLS MODELS

class LogChatInput(BaseModel):
    """Input for log_chat tool."""
    
    content: str = Field(description="Chat message content")
    conversation_id: str = Field(description="Conversation identifier")
    role: str = Field(description="Message role (user, assistant, system)")
    agent_name: Optional[str] = Field(default=None, description="Name of the agent")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class LogChatOutput(SuccessResponse):
    """Output for log_chat tool."""
    
    message_id: int = Field(description="ID of logged message")
    conversation_id: str = Field(description="Conversation identifier")
    performance: Optional[PerformanceMetrics] = Field(default=None)


class AskWithContextInput(BaseModel):
    """Input for ask_with_context tool."""
    
    query: str = Field(description="Query with automatic context retrieval")
    conversation_id: str = Field(description="Conversation identifier")
    context_limit: int = Field(default=5, description="Maximum context items to retrieve")
    include_history: bool = Field(default=True, description="Include chat history in context")


class AskWithContextOutput(SuccessResponse):
    """Output for ask_with_context tool."""
    
    response: str = Field(description="Generated response with context")
    context_used: List[SearchResult] = Field(description="Context items used")
    conversation_id: str = Field(description="Conversation identifier")
    performance: Optional[PerformanceMetrics] = Field(default=None)


# TODO TOOLS MODELS

class AddTodoInput(BaseModel):
    """Input for add_todo tool."""
    
    title: str = Field(description="Todo title")
    description: str = Field(description="Detailed todo description")
    priority: str = Field(default="medium", description="Priority (high, medium, low)")


class AddTodoOutput(SuccessResponse):
    """Output for add_todo tool."""
    
    todo_id: int = Field(description="ID of created todo")
    title: str = Field(description="Todo title")
    priority: str = Field(description="Todo priority")
    performance: Optional[PerformanceMetrics] = Field(default=None)


class ListTodosInput(BaseModel):
    """Input for list_todos tool."""
    
    status: Optional[str] = Field(default=None, description="Filter by status (pending, completed)")
    priority: Optional[str] = Field(default=None, description="Filter by priority")
    limit: int = Field(default=10, description="Maximum number of todos to return")
    offset: int = Field(default=0, description="Number of todos to skip")


class ListTodosOutput(SuccessResponse):
    """Output for list_todos tool."""
    
    todos: List[Dict[str, Any]] = Field(description="List of todos")
    total_count: int = Field(description="Total number of todos")
    filtered_count: int = Field(description="Number of todos after filtering")
    performance: Optional[PerformanceMetrics] = Field(default=None)


class CompleteTodoInput(BaseModel):
    """Input for complete_todo tool."""
    
    todo_id: int = Field(description="ID of todo to complete")


class CompleteTodoOutput(SuccessResponse):
    """Output for complete_todo tool."""
    
    todo_id: int = Field(description="ID of completed todo")
    completed_at: datetime = Field(description="Completion timestamp")
    performance: Optional[PerformanceMetrics] = Field(default=None)


# CODE PATTERN TOOLS MODELS

class LogCodeAttemptInput(BaseModel):
    """Input for log_code_attempt tool."""
    
    input_prompt: str = Field(description="Original prompt that generated the code")
    generated_code: str = Field(description="Generated code content")
    result: str = Field(description="Result status (pass, fail, partial)")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class LogCodeAttemptOutput(SuccessResponse):
    """Output for log_code_attempt tool."""
    
    pattern_id: int = Field(description="ID of logged code pattern")
    vector_id: int = Field(description="Vector ID for semantic search")
    performance: Optional[PerformanceMetrics] = Field(default=None)


class GetCodePatternsInput(BaseModel):
    """Input for get_code_patterns tool."""
    
    query: str = Field(description="Query to find similar code patterns")
    result_filter: Optional[str] = Field(default=None, description="Filter by result (pass, fail, partial)")
    top_k: int = Field(default=5, description="Number of patterns to return")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")


class GetCodePatternsOutput(SuccessResponse):
    """Output for get_code_patterns tool."""
    
    patterns: List[Dict[str, Any]] = Field(description="Matching code patterns")
    query_processed: str = Field(description="Processed query")
    total_matches: int = Field(description="Total number of matches")
    performance: Optional[PerformanceMetrics] = Field(default=None)