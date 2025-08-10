"""
Base Models for LTMC MCP Server
==============================

Pydantic models following FastMCP structured output support.

From research - FastMCP supports:
- Pydantic models
- TypedDicts  
- Dataclasses
- Primitive types
- Generic types

Using Pydantic for type safety and automatic schema generation.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response model for all tool outputs."""
    
    success: bool = Field(description="Whether the operation was successful")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    

class SuccessResponse(BaseResponse):
    """Success response with data."""
    
    success: bool = Field(default=True, description="Operation succeeded")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    message: Optional[str] = Field(default=None, description="Success message")


class ErrorResponse(BaseResponse):
    """Error response with details."""
    
    success: bool = Field(default=False, description="Operation failed")
    error: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")


class PaginatedResponse(SuccessResponse):
    """Paginated response for list operations."""
    
    items: List[Any] = Field(description="List of items")
    total_count: int = Field(description="Total number of items")
    page: int = Field(default=1, description="Current page number") 
    page_size: int = Field(default=10, description="Items per page")
    has_more: bool = Field(description="Whether there are more items")


class PerformanceMetrics(BaseModel):
    """Performance metrics for operations."""
    
    execution_time_ms: float = Field(description="Execution time in milliseconds")
    database_queries: int = Field(default=0, description="Number of database queries")
    cache_hits: int = Field(default=0, description="Number of cache hits")
    cache_misses: int = Field(default=0, description="Number of cache misses")
    memory_usage_mb: Optional[float] = Field(default=None, description="Memory usage in MB")


class ResourceMetadata(BaseModel):
    """Metadata for stored resources."""
    
    source: Optional[str] = Field(default=None, description="Source of the resource")
    tags: List[str] = Field(default_factory=list, description="Resource tags")
    content_type: Optional[str] = Field(default=None, description="MIME content type")
    language: Optional[str] = Field(default=None, description="Programming language if applicable")
    size_bytes: Optional[int] = Field(default=None, description="Size in bytes")
    checksum: Optional[str] = Field(default=None, description="Content checksum")


class SearchResult(BaseModel):
    """Search result item."""
    
    id: int = Field(description="Resource ID")
    content: str = Field(description="Content snippet")
    similarity_score: float = Field(description="Similarity score (0-1)")
    resource_type: str = Field(description="Type of resource")
    file_name: Optional[str] = Field(default=None, description="File name")
    created_at: datetime = Field(description="Creation timestamp")
    metadata: Optional[ResourceMetadata] = Field(default=None, description="Resource metadata")


class ValidationResult(BaseModel):
    """Validation result for inputs."""
    
    is_valid: bool = Field(description="Whether input is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")