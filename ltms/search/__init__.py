"""
LTMC Universal Semantic Search Module.
Provides unified search across all storage types with enhanced metadata support.
"""

from .universal_semantic_search import (
    UniversalSemanticSearch,
    SearchFacets,
    get_universal_search
)

__all__ = [
    "UniversalSemanticSearch",
    "SearchFacets", 
    "get_universal_search"
]