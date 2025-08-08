"""Import utilities for robust path resolution in different contexts."""

import sys
import os
from pathlib import Path
from typing import Optional, Any


def setup_import_paths() -> Path:
    """
    Setup import paths for all execution contexts.
    
    This function ensures that the project root is in sys.path and
    changes the working directory to the project root for consistent
    behavior across different execution contexts.
    
    Returns:
        Path: The project root directory
    """
    # Get the directory containing this file
    current_file = Path(__file__)
    
    # Navigate to project root (two levels up from core/)
    project_root = current_file.parent.parent
    
    # Ensure project root exists
    if not project_root.exists():
        raise RuntimeError(f"Project root not found: {project_root}")
    
    # Add to sys.path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    else:
        # If already there, move to front
        sys.path.remove(project_root_str)
        sys.path.insert(0, project_root_str)
    
    # Change to project root for consistent behavior
    os.chdir(project_root_str)
    
    return project_root


def safe_import(module_name: str, fallback_path: Optional[str] = None) -> Any:
    """
    Import module with fallback path handling.
    
    Args:
        module_name: Name of the module to import
        fallback_path: Optional fallback path to try if import fails
        
    Returns:
        The imported module
        
    Raises:
        ImportError: If module cannot be imported even with fallback
    """
    try:
        return __import__(module_name)
    except ImportError:
        if fallback_path:
            # Try with fallback path
            if fallback_path not in sys.path:
                sys.path.insert(0, fallback_path)
            return __import__(module_name)
        raise


def ensure_project_imports() -> None:
    """
    Ensure that project imports are available.
    
    This function sets up the import paths and verifies that
    key project modules can be imported.
    """
    # Setup import paths
    setup_import_paths()
    
    # Verify key imports work
    try:
        from core.config import settings
        assert settings is not None
    except ImportError as e:
        raise ImportError(f"Failed to import core.config: {e}")
    
    try:
        from tools.ask import ask_with_context
        assert ask_with_context is not None
    except ImportError as e:
        raise ImportError(f"Failed to import tools.ask: {e}")


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: The project root directory
    """
    current_file = Path(__file__)
    return current_file.parent.parent


def is_running_as_script() -> bool:
    """
    Check if the current execution is running as a script.
    
    Returns:
        bool: True if running as script, False if imported as module
    """
    return __name__ == "__main__"


def is_running_with_mcp_dev() -> bool:
    """
    Check if running in mcp dev context.
    
    Returns:
        bool: True if likely running with mcp dev
    """
    # Check for mcp dev indicators
    return (
        "mcp" in sys.argv[0] if sys.argv else False
        or any("mcp" in arg for arg in sys.argv)
    )


def setup_for_execution_context() -> Path:
    """
    Setup import paths based on execution context.
    
    This function detects the execution context and sets up
    imports appropriately for that context.
    
    Returns:
        Path: The project root directory
    """
    project_root = setup_import_paths()
    
    # Log context for debugging (commented out for now)
    # context_info = {
    #     "script": is_running_as_script(),
    #     "mcp_dev": is_running_with_mcp_dev(),
    #     "working_dir": os.getcwd(),
    #     "sys_path_length": len(sys.path)
    # }
    # print(f"Execution context: {context_info}")
    
    return project_root
