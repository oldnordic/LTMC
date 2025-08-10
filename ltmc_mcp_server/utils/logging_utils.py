"""
Logging Utilities
================

Logging setup for LTMC MCP server.
Uses stderr to avoid interfering with stdio transport.
"""

import logging
import sys
from typing import Optional


def setup_logging(log_level: str = "INFO", log_format: Optional[str] = None) -> None:
    """
    Setup logging configuration for LTMC server.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_format: Optional custom log format
    """
    # Default format
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        stream=sys.stderr,  # Use stderr to avoid stdio transport interference
        force=True  # Override any existing configuration
    )
    
    # Set specific logger levels
    loggers_config = {
        'ltmc_mcp_server': log_level.upper(),
        'fastmcp': 'WARNING',  # Reduce FastMCP noise
        'aiosqlite': 'WARNING',
        'neo4j': 'WARNING',
        'redis': 'WARNING',
    }
    
    for logger_name, level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level))
    
    # Log startup message
    root_logger = logging.getLogger(__name__)
    root_logger.info(f"Logging initialized at level: {log_level}")


def get_performance_logger() -> logging.Logger:
    """Get logger specifically for performance metrics."""
    logger = logging.getLogger('ltmc_mcp_server.performance')
    return logger


def get_security_logger() -> logging.Logger:
    """Get logger specifically for security events."""  
    logger = logging.getLogger('ltmc_mcp_server.security')
    return logger


def get_tool_logger(tool_name: str) -> logging.Logger:
    """Get logger for specific tool."""
    logger = logging.getLogger(f'ltmc_mcp_server.tools.{tool_name}')
    return logger