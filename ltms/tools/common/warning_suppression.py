"""
LTMC Warning Suppression System
Research-backed implementation for suppressing ML library warnings
"""

import os
import sys
import warnings
import logging
from io import StringIO
from typing import List


def setup_environment_suppressions():
    """System-level environment setup for warning suppression."""
    env_settings = {
        "PYTHONWARNINGS": "ignore::DeprecationWarning",
        "TF_CPP_MIN_LOG_LEVEL": "3",
        "PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION": "python",
        "SETUPTOOLS_USE_DISTUTILS": "stdlib", 
        "TRANSFORMERS_VERBOSITY": "error"
    }
    
    for key, value in env_settings.items():
        os.environ[key] = value


def setup_warning_filters():
    """Configure Python warnings system."""
    warnings.resetwarnings()
    warnings.simplefilter("ignore", DeprecationWarning)
    warnings.simplefilter("ignore", FutureWarning)
    
    # Specific message filters for exact warnings
    specific_filters = [
        ".*distutils Version classes are deprecated.*",
        ".*ml_dtypes.float8_e4m3b11 is deprecated.*",
        ".*Support for class-based.*config.*deprecated.*",
        ".*MessageFactory.*GetPrototype.*"
    ]
    
    for message_pattern in specific_filters:
        warnings.filterwarnings("ignore", message=message_pattern)


def setup_logging_suppression():
    """Configure logging system for reduced verbosity."""
    logging.basicConfig(level=logging.WARNING, force=True)
    logging.getLogger().setLevel(logging.WARNING)
    
    # Suppress specific loggers that generate noise
    critical_loggers = [
        "tensorflow", "absl", "sentence_transformers", "transformers",
        "ltms.security.project_isolation", "ltms.security.path_security", 
        "ltms.security.mcp_integration", "ltms.core.connection_pool"
    ]
    
    for logger_name in critical_loggers:
        logging.getLogger(logger_name).setLevel(logging.ERROR)


class AdvancedImportSuppressor:
    """Context manager for suppressing import-time warnings and errors.
    
    Uses multiple suppression layers: environment, warnings, logging, and stderr.
    Research-backed implementation for reliable ML library import suppression.
    """
    
    def __init__(self):
        self._original_stderr = None
        self._original_warnings = None
    
    def __enter__(self):
        # Store original states
        self._original_stderr = sys.stderr
        self._original_warnings = warnings.filters[:]
        
        # Temporary stderr suppression during critical imports
        sys.stderr = StringIO()
        
        # Additional warning suppression context
        warnings.filterwarnings("ignore")
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original states
        sys.stderr = self._original_stderr
        warnings.filters[:] = self._original_warnings
        
        # Don't suppress exceptions
        return False


def preemptive_import_trigger():
    """Import problematic libraries in controlled suppressed context."""
    try:
        with AdvancedImportSuppressor():
            # Trigger problematic imports in suppressed context
            import numpy
            import faiss
            from sentence_transformers import SentenceTransformer
            
            # Force transformers logging configuration
            try:
                from transformers.utils import logging as transformers_logging
                transformers_logging.set_verbosity_error()
            except ImportError:
                pass
                
    except Exception:
        # If imports fail, suppression systems remain active
        pass


def lazy_numpy():
    """Lazy import numpy only when needed to avoid binary distribution issues."""
    import numpy as np
    return np


def initialize_warning_suppression():
    """Initialize complete warning suppression system.
    
    Call this once at application startup to establish all suppression layers.
    """
    setup_environment_suppressions()
    setup_warning_filters() 
    setup_logging_suppression()
    preemptive_import_trigger()


# Auto-initialize when module is imported
initialize_warning_suppression()