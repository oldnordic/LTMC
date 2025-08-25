#!/usr/bin/env python3
"""
PyInstaller Hook for LTMC MCP Server
====================================

This hook ensures that PyInstaller properly detects and includes
all necessary modules and dependencies for the LTMC MCP server.
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Collect all submodules from the main package
hiddenimports = collect_submodules('ltmc_mcp_server')

# Add specific modules that might be missed
hiddenimports.extend([
    'ltmc_mcp_server.config.settings',
    'ltmc_mcp_server.config.database_config',
    'ltmc_mcp_server.services.database_service',
    'ltmc_mcp_server.services.advanced_database_service',
    'ltmc_mcp_server.services.redis_service',
    'ltmc_mcp_server.services.neo4j_service',
    'ltmc_mcp_server.services.faiss_service',
    'ltmc_mcp_server.services.mermaid_service',
    'ltmc_mcp_server.services.blueprint_service',
    'ltmc_mcp_server.services.analytics_service',
    'ltmc_mcp_server.services.monitoring_service',
    'ltmc_mcp_server.services.routing_service',
    'ltmc_mcp_server.utils.logging_utils',
    'ltmc_mcp_server.utils.performance_utils',
    'ltmc_mcp_server.utils.validation_utils',
])

# Collect data files
datas = collect_data_files('ltmc_mcp_server')

# Add specific data files
datas.extend([
    ('ltmc_config.env', '.'),
    ('ltmc_config.json', '.'),
    ('docs', 'docs'),
])

# Exclude modules that are not needed in the binary
excludes = [
    'pytest',
    'pytest_asyncio',
    'mock',
    'coverage',
    'black',
    'flake8',
    'mypy',
    'isort',
    'jupyter',
    'ipython',
    'notebook',
    'matplotlib',
    'seaborn',
    'plotly',
    'bokeh',
    'dash',
    'streamlit',
    'gradio',
]