"""
Validation Utilities
==================

Input validation utilities following MCP security requirements.
From research: MCP requires explicit user consent and access controls.
"""

import re
from typing import Any, List, Dict, Optional
from pydantic import BaseModel, ValidationError

from models.base_models import ValidationResult


def validate_input(data: Any, model_class: BaseModel) -> ValidationResult:
    """
    Validate input data against Pydantic model.
    
    Args:
        data: Input data to validate
        model_class: Pydantic model class for validation
        
    Returns:
        ValidationResult: Validation result with errors/warnings
    """
    errors = []
    warnings = []
    
    try:
        # Attempt to create model instance
        model_class(**data) if isinstance(data, dict) else model_class(data)
        return ValidationResult(is_valid=True, errors=errors, warnings=warnings)
    
    except ValidationError as e:
        for error in e.errors():
            field = '.'.join(str(loc) for loc in error['loc'])
            message = f"{field}: {error['msg']}"
            errors.append(message)
        
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)


def validate_conversation_id(conversation_id: str) -> ValidationResult:
    """
    Validate conversation ID format.
    
    Security requirement: Prevent injection attacks through conversation IDs.
    """
    errors = []
    warnings = []
    
    # Check length
    if len(conversation_id) < 1:
        errors.append("Conversation ID cannot be empty")
    elif len(conversation_id) > 255:
        errors.append("Conversation ID too long (max 255 characters)")
    
    # Check format - alphanumeric, underscore, hyphen only
    if not re.match(r'^[a-zA-Z0-9_-]+$', conversation_id):
        errors.append("Conversation ID must contain only alphanumeric characters, underscores, and hyphens")
    
    # Security check - prevent SQL injection patterns
    sql_patterns = ['select', 'insert', 'update', 'delete', 'drop', 'union', '--', ';']
    conversation_lower = conversation_id.lower()
    for pattern in sql_patterns:
        if pattern in conversation_lower:
            errors.append(f"Conversation ID contains potentially unsafe pattern: {pattern}")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_file_name(file_name: str) -> ValidationResult:
    """
    Validate file name for security.
    
    Security requirement: Prevent path traversal attacks.
    """
    errors = []
    warnings = []
    
    # Check for path traversal patterns
    unsafe_patterns = ['../', '..\\', '/..', '\\..', './', '.\\']
    for pattern in unsafe_patterns:
        if pattern in file_name:
            errors.append(f"File name contains unsafe path pattern: {pattern}")
    
    # Check for absolute paths
    if file_name.startswith('/') or (len(file_name) > 1 and file_name[1] == ':'):
        errors.append("File name cannot be an absolute path")
    
    # Check length
    if len(file_name) > 255:
        errors.append("File name too long (max 255 characters)")
    
    # Check for null bytes
    if '\x00' in file_name:
        errors.append("File name contains null bytes")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_content_length(content: str, max_length: int = 1000000) -> ValidationResult:
    """
    Validate content length to prevent DoS attacks.
    
    Args:
        content: Content to validate
        max_length: Maximum allowed content length (default 1MB)
    """
    errors = []
    warnings = []
    
    content_length = len(content)
    
    if content_length == 0:
        errors.append("Content cannot be empty")
    elif content_length > max_length:
        errors.append(f"Content too large ({content_length} chars, max {max_length})")
    elif content_length > max_length * 0.8:  # 80% of max
        warnings.append(f"Content is large ({content_length} chars)")
    
    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def sanitize_user_input(user_input: str) -> str:
    """
    Sanitize user input for safe storage and processing.
    
    Args:
        user_input: Raw user input
        
    Returns:
        str: Sanitized input
    """
    # Remove null bytes
    sanitized = user_input.replace('\x00', '')
    
    # Remove control characters except newlines and tabs
    sanitized = ''.join(char for char in sanitized 
                       if ord(char) >= 32 or char in '\n\t\r')
    
    # Limit length
    if len(sanitized) > 1000000:  # 1MB limit
        sanitized = sanitized[:1000000]
    
    return sanitized


def validate_priority(priority: str) -> ValidationResult:
    """Validate todo priority value."""
    valid_priorities = ['high', 'medium', 'low']
    
    if priority.lower() not in valid_priorities:
        return ValidationResult(
            is_valid=False,
            errors=[f"Priority must be one of: {', '.join(valid_priorities)}"],
            warnings=[]
        )
    
    return ValidationResult(is_valid=True, errors=[], warnings=[])


def validate_resource_type(resource_type: str) -> ValidationResult:
    """Validate resource type value."""
    valid_types = ['document', 'code', 'note', 'image', 'audio', 'video', 'data']
    
    if resource_type.lower() not in valid_types:
        return ValidationResult(
            is_valid=False,
            errors=[f"Resource type must be one of: {', '.join(valid_types)}"],
            warnings=[]
        )
    
    return ValidationResult(is_valid=True, errors=[], warnings=[])