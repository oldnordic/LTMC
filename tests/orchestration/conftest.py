"""
Pytest configuration for orchestration tests.

This module ensures proper Python path setup for all orchestration tests
so they can import ltms modules correctly.
"""

import os
import sys
from pathlib import Path

def setup_python_path():
    """Set up Python path to include project root."""
    # Get the project root (two levels up from this file)
    project_root = Path(__file__).parent.parent.parent.absolute()
    
    # Add project root to Python path if not already there
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
    
    return project_root_str

# Set up Python path when this module is imported
PROJECT_ROOT = setup_python_path()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with proper path setup."""
    # Ensure project root is in path during pytest execution
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)

def pytest_sessionstart(session):
    """Called after the Session object has been created."""
    # Print path info for debugging
    print(f"\n🔧 Python path setup for orchestration tests:")
    print(f"   Project root: {PROJECT_ROOT}")
    print(f"   Python path includes project root: {PROJECT_ROOT in sys.path}")
    print(f"   Working directory: {os.getcwd()}")