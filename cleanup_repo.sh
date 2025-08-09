#!/bin/bash

# LTMC Repository Cleanup Script
# Organizes the repository structure and removes clutter

set -e

echo "🧹 Starting LTMC Repository Cleanup..."

# Create necessary directories if they don't exist
echo "📁 Creating directory structure..."
mkdir -p tests/manual
mkdir -p tests/integration  
mkdir -p tests/benchmarks
mkdir -p config
mkdir -p archive/results
mkdir -p docs/testing
mkdir -p tools/scripts

# Move test files from root to appropriate test directories
echo "🔄 Moving test files to tests/ directory..."

# Manual/debug test files to tests/manual/
test_files=(
    "test_all_28_ltmc_tools_comprehensive.py"
    "test_all_28_tools.py" 
    "test_comprehensive_mcp_servers.py"
    "test_comprehensive_validation.py"
    "test_final_mcp_config.py"
    "test_fixed_stdio.py"
    "test_ltmc_mcp_protocol.py"
    "test_ltmc_simple.py"
    "test_ltmc_stdio_direct.py"
    "test_ltmc_stdio_fixed.py"
    "test_ltmc_stdio.py"
    "test_mcp_config.py"
    "test_mcp_debug.py"
    "test_quick_validation.py"
    "test_simple_debug.py"
    "test_simple_mcp_validation.py"
    "test_stdio_simple.py"
    "test_p1_client_library.py"
    "test_p1_comprehensive_validation.py"
    "test_p1_transport_consistency.py"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  Moving $file to tests/manual/"
        mv "$file" tests/manual/
    fi
done

# Move integration test files
integration_files=(
    "test_orchestration_integration.py"
    "run_comprehensive_mcp_tests.py"
    "ltmc_tools_stats_tester.py"
)

for file in "${integration_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  Moving $file to tests/integration/"
        mv "$file" tests/integration/
    fi
done

# Move JSON result files to archive
echo "📦 Archiving JSON result files..."
json_files=(
    "comprehensive_mcp_server_results_mcp_servers_test_*.json"
    "ltmc_all_28_tools_test_results_*.json" 
    "ltmc_tools_stats_results_*.json"
    "mcp_test_results_*.json"
)

for pattern in "${json_files[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "  Archiving $file"
            mv "$file" archive/results/
        fi
    done
done

# Move configuration files to config/
echo "⚙️  Organizing configuration files..."
config_files=(
    "ltmc_config.env"
    "ltmc_config.env.example"
    ".env"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  Moving $file to config/"
        cp "$file" config/
    fi
done

# Move utility scripts to tools/scripts/
echo "🔧 Organizing utility scripts..."
script_files=(
    "debug_stdio.py"
    "ltmc_http_wrapper.py"
    "ltmc_mcp_server_unwrapped.py"
    "ltmc_stdio_proxy.py"
    "client_utils.py"
    "simple_orchestration_demo.py"
    "start_dual_transport.py"
    "update_agents_ltmc.py"
    "track_performance.sh"
)

for file in "${script_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  Moving $file to tools/scripts/"
        mv "$file" tools/scripts/
    fi
done

# Move documentation files to docs/testing/
echo "📚 Organizing documentation files..."
doc_files=(
    "STDIO_MCP_ANALYSIS.md"
    "TESTING_IMPLEMENTATION_GUIDE.md" 
    "TESTING_RESULTS_*.md"
    "mcp_server_improvement_plan.md"
)

for pattern in "${doc_files[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            echo "  Moving $file to docs/testing/"
            mv "$file" docs/testing/
        fi
    done
done

# Clean up temporary files and directories
echo "🗑️  Removing temporary files..."
temp_items=(
    "__pycache__"
    ".pytest_cache" 
    ".mypy_cache"
    ".coverage"
    "*.pid"
    "test_stdio_faiss_index"
    "node_modules"
    "package.json"
    "package-lock.json"
)

for item in "${temp_items[@]}"; do
    if [[ "$item" == "*"* ]]; then
        # Handle glob patterns
        for file in $item; do
            if [ -f "$file" ]; then
                echo "  Removing $file"
                rm -f "$file"
            fi
        done
    else
        if [ -d "$item" ] || [ -f "$item" ]; then
            echo "  Removing $item"
            rm -rf "$item"
        fi
    fi
done

echo "✅ Repository cleanup completed!"
echo ""
echo "📁 New directory structure:"
echo "  tests/manual/       - Manual and debug test files"
echo "  tests/integration/  - Integration test files" 
echo "  config/            - Configuration files"
echo "  tools/scripts/     - Utility scripts and helpers"
echo "  archive/results/   - Historical test results"
echo "  docs/testing/      - Testing documentation"
echo ""
echo "🎯 Next steps:"
echo "  1. Update README.md to reflect new structure"
echo "  2. Update .gitignore for better artifact management" 
echo "  3. Test that main functionality still works"