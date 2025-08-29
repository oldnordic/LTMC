"""
LTMC Semantic Query Data Models
Real data structures for parsing semantic queries - NO PLACEHOLDERS

These models define the structure of parsed semantic queries and their components.
Used by the semantic parser to represent queries like "memory%architecture%recent".
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


class QueryType(Enum):
    """Types of semantic queries supported by LTMC."""
    MEMORY = "memory"        # Queries for stored documents/embeddings
    CHAT = "chat"           # Queries for conversation history  
    DOCUMENT = "document"   # Queries for filesystem documents


class DatabaseTarget(Enum):
    """Target databases for query execution."""
    SQLITE = "sqlite"       # Structured data, metadata, chat history
    FAISS = "faiss"        # Vector embeddings for semantic search
    NEO4J = "neo4j"        # Graph relationships
    REDIS = "redis"        # Cache and session data
    FILESYSTEM = "filesystem"  # File system operations


class TemporalFilterType(Enum):
    """Types of temporal filters for queries."""
    RECENT = "recent"           # Last 24 hours
    YESTERDAY = "yesterday"     # 24-48 hours ago
    LAST_WEEK = "last_week"     # Last 7 days
    LAST_MONTH = "last_month"   # Last 30 days
    TODAY = "today"             # Current day
    CUSTOM = "custom"           # Custom date range


@dataclass
class TemporalFilter:
    """Temporal filter for time-based query constraints."""
    filter_type: TemporalFilterType
    start_time: datetime
    end_time: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert temporal filter to dictionary for tool integration."""
        return {
            "type": self.filter_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time
        }


@dataclass
class SemanticQuery:
    """Parsed semantic query with all components."""
    query_type: QueryType
    search_terms: List[str]
    temporal_filters: Optional[Dict[str, Any]] = None
    topic_filters: List[str] = field(default_factory=list)
    target_databases: List[DatabaseTarget] = field(default_factory=list)
    original_query: str = ""
    
    def to_memory_action_params(self) -> Dict[str, Any]:
        """Convert to parameters for memory_action tool."""
        params = {
            "action": "retrieve",
            "query": " ".join(self.search_terms),
            "conversation_id": f"semantic_query_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "limit": 10
        }
        return params
        
    def to_chat_action_params(self) -> Dict[str, Any]:
        """Convert to parameters for chat_action tool."""
        params = {
            "action": "get_by_tool",
            "source_tool": "memory_action",  # Default to memory-related chats
            "limit": 10
        }
        return params
        
    def to_unix_action_params(self) -> Dict[str, Any]:
        """Convert to parameters for unix_action tool."""
        # Extract file patterns from search terms
        file_patterns = [term for term in self.search_terms if "*" in term or term.endswith((".py", ".md", ".txt", ".json"))]
        pattern = file_patterns[0] if file_patterns else "*.py"
        
        params = {
            "action": "find",
            "pattern": pattern,
            "path": "./ltms",  # Default search path
            "limit": 20
        }
        return params
        
    def get_primary_database_target(self) -> DatabaseTarget:
        """Get the primary database target for this query."""
        if not self.target_databases:
            return DatabaseTarget.SQLITE  # Default fallback
            
        # Priority order based on query type
        if self.query_type == QueryType.MEMORY:
            return DatabaseTarget.FAISS if DatabaseTarget.FAISS in self.target_databases else DatabaseTarget.SQLITE
        elif self.query_type == QueryType.CHAT:
            return DatabaseTarget.SQLITE
        elif self.query_type == QueryType.DOCUMENT:
            return DatabaseTarget.FILESYSTEM
        else:
            return self.target_databases[0]


@dataclass  
class QueryParsingResult:
    """Result of query parsing operation."""
    success: bool
    parsed_query: Optional[SemanticQuery] = None
    error_message: str = ""
    parsing_time_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert parsing result to dictionary."""
        result = {
            "success": self.success,
            "parsing_time_ms": self.parsing_time_ms
        }
        
        if self.success and self.parsed_query:
            result["query"] = {
                "type": self.parsed_query.query_type.value,
                "search_terms": self.parsed_query.search_terms,
                "target_databases": [db.value for db in self.parsed_query.target_databases],
                "temporal_filters": self.parsed_query.temporal_filters,
                "topic_filters": self.parsed_query.topic_filters
            }
        else:
            result["error"] = self.error_message
            
        return result


# Query validation utilities

def validate_query_format(query: str) -> bool:
    """Validate that query follows expected format: type%terms%filters."""
    if not query or not query.strip():
        return False
        
    # Must contain at least one % separator
    if "%" not in query:
        return False
        
    parts = query.split("%")
    # Must have at least 2 parts: type and terms
    if len(parts) < 2:
        return False
        
    # First part must be valid query type
    valid_types = [qt.value for qt in QueryType]
    if parts[0].lower().strip() not in valid_types:
        return False
        
    return True


def extract_temporal_keywords() -> List[str]:
    """Get list of supported temporal keywords."""
    return [tf.value for tf in TemporalFilterType]


def extract_query_type_keywords() -> List[str]:
    """Get list of supported query type keywords."""
    return [qt.value for qt in QueryType]