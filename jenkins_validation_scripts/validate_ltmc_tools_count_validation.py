#!/usr/bin/env python3
"""
LTMC Tools Count Validation Script for Jenkins
Validates that the actual tool count matches expected consolidated architecture
"""

import sys
import os
import re
from pathlib import Path

def main():
    """Validate LTMC consolidated tools count"""
    print("=== LTMC Tools Count Validation ===")
    
    # Set up paths
    ltmc_home = os.environ.get('LTMC_HOME', '/home/feanor/Projects/ltmc')
    consolidated_file = Path(ltmc_home) / 'ltms' / 'tools' / 'consolidated.py'
    
    # Check if consolidated file exists
    if not consolidated_file.exists():
        print(f"❌ FAIL: Consolidated tools file not found: {consolidated_file}")
        sys.exit(1)
    
    print(f"✅ Found consolidated tools file: {consolidated_file}")
    
    # Read and count @mcp.tool decorators
    try:
        with open(consolidated_file, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ FAIL: Could not read consolidated file: {e}")
        sys.exit(1)
    
    # Count LTMC consolidated tools (action-based pattern)
    tool_pattern = r'def\s+(\w+_action)\s*\([^)]*action:\s*str'
    tools = re.findall(tool_pattern, content)
    actual_count = len(tools)
    
    # Expected count based on consolidated architecture
    expected_count = 11
    
    print(f"Expected MCP tools: {expected_count}")
    print(f"Actual MCP tools found: {actual_count}")
    
    # Validate count
    if actual_count != expected_count:
        print(f"❌ FAIL: Tool count mismatch - Expected {expected_count}, found {actual_count}")
        
        # Show tool names for debugging
        print(f"Found tools: {tools}")
        
        sys.exit(1)
    
    # Extract tool names for verification
    print(f"✅ SUCCESS: Found {actual_count} LTMC consolidated tools as expected")
    print(f"Tools: {', '.join(tools)}")
    
    return 0

if __name__ == '__main__':
    main()