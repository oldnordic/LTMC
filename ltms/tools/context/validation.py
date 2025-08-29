"""
Request validation utilities for LTMC context tools.
Handles parameter validation, type conversion, and error handling.
"""

from typing import Dict, Any, Union, List, Optional
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_message_id(message_id: Union[str, int]) -> int:
    """
    Validate and convert message ID to integer.
    
    Args:
        message_id: Message ID as string or int
        
    Returns:
        int: Validated message ID
        
    Raises:
        ValidationError: If message ID is invalid
    """
    if isinstance(message_id, int):
        return message_id
        
    if isinstance(message_id, str):
        try:
            return int(message_id)
        except (ValueError, TypeError):
            raise ValidationError("message_id must be a valid integer")
    
    raise ValidationError("message_id must be a string or integer")


def validate_documents_list(documents: Any) -> List[Dict[str, Any]]:
    """
    Validate documents parameter is a proper list of dictionaries.
    
    Args:
        documents: Documents parameter to validate
        
    Returns:
        List[Dict[str, Any]]: Validated documents list
        
    Raises:
        ValidationError: If documents format is invalid
    """
    if not isinstance(documents, list):
        raise ValidationError("documents must be a list")
    
    validated_docs = []
    for i, doc in enumerate(documents):
        if not isinstance(doc, dict):
            raise ValidationError(f"Document at index {i} must be a dictionary")
        validated_docs.append(doc)
    
    return validated_docs


def validate_token_limit(max_tokens: Any, default: int = 4000, 
                        min_val: int = 100, max_val: int = 32000) -> int:
    """
    Validate token limit parameter.
    
    Args:
        max_tokens: Token limit to validate
        default: Default value if None
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        int: Validated token limit
        
    Raises:
        ValidationError: If token limit is invalid
    """
    if max_tokens is None:
        return default
    
    if isinstance(max_tokens, str):
        try:
            max_tokens = int(max_tokens)
        except (ValueError, TypeError):
            raise ValidationError("max_tokens must be a valid integer")
    
    if not isinstance(max_tokens, int):
        raise ValidationError("max_tokens must be an integer")
    
    if max_tokens < min_val:
        raise ValidationError(f"max_tokens must be at least {min_val}")
    
    if max_tokens > max_val:
        raise ValidationError(f"max_tokens must not exceed {max_val}")
    
    return max_tokens


def validate_top_k(top_k: Any, default: int = 5, min_val: int = 1, max_val: int = 100) -> int:
    """
    Validate top_k parameter.
    
    Args:
        top_k: Top k value to validate
        default: Default value if None
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        int: Validated top_k value
        
    Raises:
        ValidationError: If top_k is invalid
    """
    if top_k is None:
        return default
    
    if isinstance(top_k, str):
        try:
            top_k = int(top_k)
        except (ValueError, TypeError):
            raise ValidationError("top_k must be a valid integer")
    
    if not isinstance(top_k, int):
        raise ValidationError("top_k must be an integer")
    
    if top_k < min_val:
        raise ValidationError(f"top_k must be at least {min_val}")
    
    if top_k > max_val:
        raise ValidationError(f"top_k must not exceed {max_val}")
    
    return top_k


def validate_string_parameter(param: Any, param_name: str, required: bool = True) -> Optional[str]:
    """
    Validate string parameter.
    
    Args:
        param: Parameter value
        param_name: Parameter name for error messages
        required: Whether parameter is required
        
    Returns:
        str or None: Validated string parameter
        
    Raises:
        ValidationError: If parameter is invalid
    """
    if param is None:
        if required:
            raise ValidationError(f"{param_name} is required")
        return None
    
    if not isinstance(param, str):
        raise ValidationError(f"{param_name} must be a string")
    
    if required and not param.strip():
        raise ValidationError(f"{param_name} cannot be empty")
    
    return param.strip()


def validate_chunk_ids(chunk_ids: Any) -> List[int]:
    """
    Validate chunk IDs list.
    
    Args:
        chunk_ids: Chunk IDs to validate
        
    Returns:
        List[int]: Validated chunk IDs
        
    Raises:
        ValidationError: If chunk IDs are invalid
    """
    if not isinstance(chunk_ids, list):
        raise ValidationError("chunk_ids must be a list")
    
    if not chunk_ids:
        raise ValidationError("chunk_ids cannot be empty")
    
    validated_ids = []
    for i, chunk_id in enumerate(chunk_ids):
        try:
            if isinstance(chunk_id, str):
                chunk_id = int(chunk_id)
            elif not isinstance(chunk_id, int):
                raise ValueError("Not an integer")
            
            if chunk_id < 1:
                raise ValueError("Must be positive")
                
            validated_ids.append(chunk_id)
            
        except (ValueError, TypeError):
            raise ValidationError(f"chunk_id at index {i} must be a positive integer")
    
    return validated_ids


def create_error_response(error_message: str, error_code: str = "validation_error") -> Dict[str, Any]:
    """
    Create standardized error response.
    
    Args:
        error_message: Error message
        error_code: Error code for categorization
        
    Returns:
        Dict[str, Any]: Standardized error response
    """
    logger.error(f"Validation error: {error_code} - {error_message}")
    
    return {
        "success": False,
        "error": error_message,
        "error_code": error_code,
        "data": None
    }


def create_success_response(data: Any, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Create standardized success response.
    
    Args:
        data: Response data
        message: Optional success message
        
    Returns:
        Dict[str, Any]: Standardized success response
    """
    response = {
        "success": True,
        "error": None,
        "data": data
    }
    
    if message:
        response["message"] = message
    
    return response