# Documentation for main.py

**Project:** audit_test_project
**Generated:** 2025-08-12T23:41:03.093506

## Overview

This document provides API documentation for `main.py`.

## Imports

| Module | Type | Line |
|--------|------|------|
| os | import | 15 |
| asyncio | import | 20 |
| logging | import | 21 |
| sys | import | 22 |
| pathlib | from_import | 23 |
| mcp.server.fastmcp | from_import | 30 |
| ltmc_mcp_server.config.settings | from_import | 33 |
| ltmc_mcp_server.config.database_config | from_import | 34 |
| ltmc_mcp_server.services.database_service | from_import | 35 |
| ltmc_mcp_server.utils.logging_utils | from_import | 36 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |
| ltmc_mcp_server.tools | from_import | 39 |

## Functions

### async create_server(skip_db_init)

**Line:** 57-141
**Complexity:** low (Score: 2)

**Description:**

Create and configure LTMC MCP server.

Following official FastMCP pattern:
mcp = FastMCP("Demo 🚀")

Args:
    skip_db_init: If True, skip database initialization (for testing)

Returns:
    FastMCP: Configured server instance

### main()

**Line:** 144-176
**Complexity:** low (Score: 4)

**Description:**

Main entry point with asyncio-compatible pattern.

Uses async methods to avoid event loop conflicts in nested environments.
Returns a task if running in an existing event loop, None otherwise.

### async init_and_run()

**Line:** 178-191
**Complexity:** low (Score: 1)

**Description:**

Initialize server and run with asyncio-compatible pattern.
