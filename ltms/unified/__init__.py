"""
Unified LTMC Operations Module

Single source of truth for storage, retrieval, and search operations.
Eliminates 75+ duplicate implementations from technical debt caused by context loss.

Migration: From monolithic to 3-file unified architecture
Goal: Prevent future reimplementation cycles through centralized APIs

Usage:
    from ltms.unified import store, retrieve, search
    
    # Unified storage (replaces memory_action calls)
    result = await store(resource_type='memory', content=content, file_name=filename)
    
    # Unified retrieval (replaces multiple retrieve implementations) 
    documents = await retrieve(resource_type='memory', query=query)
    
    # Unified search (replaces multiple search implementations)
    results = await search(resource_type='memory', query=query, filters=filters)
"""

# Import unified functions
from .store import unified_store as store
from .retrieve import unified_retrieve as retrieve
from .search import unified_search as search

# Backward compatibility imports
from .store import store as store_compat
from .retrieve import retrieve as retrieve_compat
from .search import search as search_compat

__all__ = [
    'store',
    'retrieve',
    'search',
    'store_compat',
    'retrieve_compat',
    'search_compat'
]

__version__ = '1.0.0'
__migration_source__ = 'monolithic_elimination'