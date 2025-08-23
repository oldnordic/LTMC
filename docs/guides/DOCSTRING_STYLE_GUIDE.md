# LTMC Docstring Style Guide

## Overview

This guide establishes the official docstring standards for the LTMC project. All code documentation should follow Google Style docstrings for consistency, maintainability, and automated documentation generation.

## Standard: Google Style Docstrings

### **Why Google Style?**
- **Comprehensive**: Clear sections for Args, Returns, Raises, Examples
- **Python Standard**: Widely adopted in the Python ecosystem
- **Tool Compatible**: Works with Sphinx, pdoc, and other documentation generators  
- **MCP Aligned**: Matches structured approach of MCP tool definitions
- **Already Used**: High-quality LTMC modules already use this format

## Template Formats

### 1. Standard Function Template

```python
def function_name(param1: type, param2: type) -> return_type:
    """Brief description of what the function does.
    
    Longer description if needed, explaining the purpose, algorithm,
    or important implementation details.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        optional_param (type, optional): Description. Defaults to None.
        
    Returns:
        Description of return value and its structure
        
    Raises:
        ValueError: When invalid parameters are provided
        ConnectionError: When database connection fails
        
    Examples:
        >>> function_name("test", 42)
        {'success': True, 'result': 'processed'}
        
    Note:
        Any important implementation details or constraints.
    """
```

### 2. Action-Based Tool Function Template

```python
def tool_action(action: str, **params) -> Dict[str, Any]:
    """Tool operations with real internal implementation.
    
    Provides comprehensive functionality for [domain] operations
    including [key features and capabilities].
    
    Args:
        action: Operation to perform. Valid actions:
            - 'action1': Description of what action1 does
            - 'action2': Description of what action2 does  
            - 'action3': Description of what action3 does
        **params: Action-specific parameters:
            For 'action1': 
                - param_a (str): Required parameter description
                - param_b (int): Required parameter description
            For 'action2':
                - param_c (str): Required parameter description
                - param_d (bool, optional): Optional parameter. Defaults to False.
            For 'action3':
                - No additional parameters required
                
    Returns:
        Dict[str, Any]: Operation results containing:
            - success (bool): Operation success status
            - error (str): Error message if success is False
            - [action-specific fields]: Additional fields based on action
            
    Raises:
        ValueError: When action is invalid or required parameters missing
        ConnectionError: When database/external service connection fails
        
    Examples:
        >>> tool_action('action1', param_a='value', param_b=42)
        {'success': True, 'result': 'action1 completed', 'id': 123}
        
        >>> tool_action('action2', param_c='test', param_d=True)  
        {'success': True, 'items': [...], 'count': 5}
    """
```

### 3. Class Template

```python
class ClassName:
    """Brief description of the class purpose.
    
    Longer description explaining what the class does, its role in the system,
    and any important usage patterns or constraints.
    
    Attributes:
        attr1: Description of class attribute
        attr2: Description of class attribute
        
    Examples:
        >>> instance = ClassName(param='value')
        >>> result = instance.method()
    """
    
    def __init__(self, param: str):
        """Initialize the class instance.
        
        Args:
            param: Description of initialization parameter
        """
        
    def method(self) -> bool:
        """Brief description of what the method does.
        
        Returns:
            bool: Success status of the operation
        """
```

### 4. Simple Utility Function Template

```python
def simple_function(param: str) -> bool:
    """Brief description for simple utility functions."""
```

## Implementation Guidelines

### **Priority Levels**

#### **Level 1: Comprehensive Documentation Required**
- **Tool action functions** (`*_action` functions)
- **Service classes and methods** (`ltms/services/*.py`)
- **Public API functions**
- **Complex algorithms or business logic**

#### **Level 2: Standard Documentation Required** 
- **Helper functions within tool modules**
- **Database access functions**
- **Configuration and setup functions**

#### **Level 3: Basic Documentation Acceptable**
- **Simple utility functions**
- **Property getters/setters** 
- **Private methods** (still document, but can be brief)

### **Content Requirements**

#### **Args Section**
- **Required parameters**: Clear description of purpose and expected format
- **Optional parameters**: Include default values and "optional" designation
- **Type information**: Should match function signature type hints
- **Parameter validation**: Document expected ranges, formats, or constraints

#### **Returns Section**  
- **Return type**: Match function signature return type
- **Structure description**: For complex return types (dicts, objects), document structure
- **Success/failure patterns**: For functions returning status, document both cases

#### **Examples Section**
- **Typical usage**: Most common use case
- **Edge cases**: Important alternative usage patterns
- **Expected output**: Show actual return values, not just calls

### **LTMC-Specific Standards**

#### **Action Functions**
All `*_action` functions in LTMC tools must document:
- Complete list of available actions
- Required parameters for each action
- Return structure for each action
- Error conditions and messages

#### **Database Functions**
Functions interacting with databases must document:
- Database connection requirements
- Transaction behavior (if applicable)
- Error handling for connection issues
- Data validation and constraints

#### **MCP Integration**
MCP tool functions must document:
- MCP protocol compliance
- Parameter validation according to MCP standards
- Response format matching MCP expectations

## Examples from LTMC Codebase

### ✅ **Good Example** (Following Standard)

```python
def get_context_for_query(
    conn, 
    index_path: str, 
    conversation_id: str, 
    query: str, 
    top_k: int
) -> Dict[str, Any]:
    """Get relevant context for a query using vector similarity search.
    
    Implements the complete retrieval pipeline:
    1. Embed the query using sentence transformers
    2. Search for similar chunks in FAISS index
    3. Retrieve full text of matching chunks
    4. Log the query in chat history  
    5. Create context links for future reference
    
    Args:
        conn: SQLite database connection for chunk storage
        index_path: Path to the FAISS vector index file
        conversation_id: Unique identifier for the conversation
        query: User's search query text
        top_k: Maximum number of similar chunks to retrieve
        
    Returns:
        Dict[str, Any]: Context retrieval results containing:
            - success (bool): Whether retrieval succeeded
            - context (str): Combined text from retrieved chunks
            - chunks (List[Dict]): Individual chunk details with scores
            - query_id (int): Database ID of the logged query
            
    Raises:
        FileNotFoundError: When FAISS index file doesn't exist
        sqlite3.Error: When database operations fail
        
    Examples:
        >>> result = get_context_for_query(
        ...     conn, "faiss_index", "conv_123", "python functions", 5
        ... )
        >>> print(result['success'])
        True
        >>> print(len(result['chunks']))
        5
    """
```

### ❌ **Needs Improvement**

```python
def memory_action(action: str, **params) -> Dict[str, Any]:
    """Memory operations with real internal SQLite+FAISS implementation."""
    # Missing: Args documentation, Returns structure, Examples
```

### ✅ **After Improvement**

```python  
def memory_action(action: str, **params) -> Dict[str, Any]:
    """Memory operations with real internal SQLite+FAISS implementation.
    
    Provides persistent storage and retrieval capabilities using SQLite 
    for metadata and FAISS for vector similarity search. Supports storing
    documents, retrieving similar content, and building context chains.
    
    Args:
        action: Memory operation to perform. Valid actions:
            - 'store': Store new document or content
            - 'retrieve': Search for similar content
            - 'build_context': Build context from conversation
            - 'retrieve_by_type': Filter retrieval by content type
            - 'ask_with_context': Query with automatic context building
        **params: Action-specific parameters:
            For 'store':
                - file_name (str): Document identifier  
                - content (str): Text content to store
            For 'retrieve':
                - query (str): Search query text
                - top_k (int, optional): Max results. Defaults to 5.
                
    Returns:
        Dict[str, Any]: Operation results containing:
            - success (bool): Operation success status
            - error (str): Error message if success is False
            - [action-specific fields]: Depends on action performed
            
    Examples:
        >>> memory_action('store', file_name='doc1.txt', content='...')
        {'success': True, 'stored': True, 'chunk_id': 123}
        
        >>> memory_action('retrieve', query='python code', top_k=3)
        {'success': True, 'results': [...], 'count': 3}
    """
```

## Enforcement and Review

### **Code Review Checklist**
- [ ] All public functions have docstrings
- [ ] Docstrings follow Google Style format
- [ ] Args section documents all parameters with types
- [ ] Returns section describes structure and meaning
- [ ] Examples show realistic usage
- [ ] Raises section documents expected exceptions

### **Automated Checks**
- **Consistency Scoring**: Target 70%+ for all modules
- **Docstring Linting**: Use `pydocstyle` with Google convention
- **Documentation Coverage**: Track documentation completion percentage

### **Migration Strategy**
1. **Phase 1**: Update all tool action functions (`*_action`)
2. **Phase 2**: Update service classes and key business logic  
3. **Phase 3**: Complete coverage for all public functions
4. **Phase 4**: Add comprehensive examples and cross-references

---

**Approved**: August 22, 2025  
**Next Review**: September 2025  
**Compliance Target**: 90% by December 2025