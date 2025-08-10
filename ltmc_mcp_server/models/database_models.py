"""
Database Models
==============

Pydantic models representing database entities.
Matches existing SQLite schema from research findings.

Tables from existing schema:
- Resources, ResourceChunks
- ChatHistory, ContextLinks  
- Summaries, todos
- CodePatterns, CodePatternContext
- VectorIdSequence
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class Resource(BaseModel):
    """Resource model matching existing Resources table."""
    
    id: Optional[int] = Field(default=None, description="Resource ID")
    file_name: Optional[str] = Field(default=None, description="File name")
    type: str = Field(description="Resource type")
    created_at: str = Field(description="Creation timestamp ISO format")
    
    model_config = {"from_attributes": True}


class ResourceChunk(BaseModel):
    """Resource chunk model matching existing ResourceChunks table."""
    
    id: Optional[int] = Field(default=None, description="Chunk ID")
    resource_id: int = Field(description="Parent resource ID")
    chunk_text: str = Field(description="Text content of chunk")
    vector_id: int = Field(description="FAISS vector ID")
    
    model_config = {"from_attributes": True}


class ChatMessage(BaseModel):
    """Chat message model matching existing ChatHistory table."""
    
    id: Optional[int] = Field(default=None, description="Message ID")
    conversation_id: str = Field(description="Conversation identifier")
    role: str = Field(description="Message role (user, assistant, system)")
    content: str = Field(description="Message content")
    timestamp: str = Field(description="Message timestamp ISO format")
    agent_name: Optional[str] = Field(default=None, description="Agent name")
    metadata: Optional[str] = Field(default=None, description="JSON metadata")
    source_tool: Optional[str] = Field(default=None, description="Source tool name")
    
    model_config = {"from_attributes": True}


class ContextLink(BaseModel):
    """Context link model matching existing ContextLinks table."""
    
    id: Optional[int] = Field(default=None, description="Link ID")
    message_id: int = Field(description="Chat message ID")
    chunk_id: int = Field(description="Resource chunk ID")
    
    model_config = {"from_attributes": True}


class Summary(BaseModel):
    """Summary model matching existing Summaries table."""
    
    id: Optional[int] = Field(default=None, description="Summary ID")
    resource_id: int = Field(description="Resource ID")
    doc_id: Optional[str] = Field(default=None, description="Document ID")
    summary_text: str = Field(description="Summary content")
    model: Optional[str] = Field(default=None, description="Model used for summary")
    created_at: str = Field(description="Creation timestamp ISO format")
    
    model_config = {"from_attributes": True}


class Todo(BaseModel):
    """Todo model matching existing todos table."""
    
    id: Optional[int] = Field(default=None, description="Todo ID")
    title: str = Field(description="Todo title")
    description: str = Field(description="Todo description")
    priority: str = Field(default="medium", description="Priority (high, medium, low)")
    status: str = Field(default="pending", description="Status (pending, completed)")
    completed: bool = Field(default=False, description="Completion flag")
    created_at: str = Field(description="Creation timestamp ISO format")
    completed_at: Optional[str] = Field(default=None, description="Completion timestamp ISO format")
    
    model_config = {"from_attributes": True}


class CodePattern(BaseModel):
    """Code pattern model matching existing CodePatterns table."""
    
    id: Optional[int] = Field(default=None, description="Pattern ID")
    function_name: Optional[str] = Field(default=None, description="Function name")
    file_name: Optional[str] = Field(default=None, description="File name")
    module_name: Optional[str] = Field(default=None, description="Module name")
    input_prompt: str = Field(description="Input prompt")
    generated_code: str = Field(description="Generated code")
    result: str = Field(description="Result (pass, fail, partial)")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time")
    error_message: Optional[str] = Field(default=None, description="Error message")
    tags: Optional[str] = Field(default=None, description="JSON tags")
    created_at: str = Field(description="Creation timestamp ISO format")
    vector_id: Optional[int] = Field(default=None, description="Vector ID for search")
    
    model_config = {"from_attributes": True}


class CodePatternContext(BaseModel):
    """Code pattern context model matching existing CodePatternContext table."""
    
    id: Optional[int] = Field(default=None, description="Context ID")
    pattern_id: int = Field(description="Code pattern ID")
    context_type: str = Field(description="Context type")
    context_data: str = Field(description="Context data")
    
    model_config = {"from_attributes": True}


class VectorIdSequence(BaseModel):
    """Vector ID sequence model matching existing VectorIdSequence table."""
    
    id: Optional[int] = Field(default=None, description="Sequence ID")
    last_vector_id: int = Field(default=0, description="Last used vector ID")
    
    model_config = {"from_attributes": True}