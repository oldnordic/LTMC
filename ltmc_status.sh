#!/bin/bash
# Claude Code status line script for LTMC tool usage statistics

# Read JSON input from Claude Code
input=$(cat)

# Extract basic info from Claude Code context
MODEL=$(echo "$input" | jq -r '.model.display_name // "Claude"' 2>/dev/null || echo "Claude")
# Shorten model name for status line
MODEL_SHORT=$(echo "$MODEL" | sed 's/claude-3-5-sonnet.*/Claude-3.5/' | sed 's/claude-3-haiku.*/Claude-3H/' | sed 's/claude-3-opus.*/Claude-3O/')
DIR=$(echo "$input" | jq -r '.workspace.current_dir // "/unknown"' 2>/dev/null || echo "/unknown")
PROJECT_NAME=$(basename "${DIR}")

# Function to get LTMC server stats
get_ltmc_stats() {
    # Make variables available in function
    local MODEL_SHORT="$1"
    local PROJECT_NAME="$2"
    
    # Check if LTMC server is running
    if ! curl -s http://localhost:5050/health >/dev/null 2>&1; then
        echo "❌ LTMC Down"
        return
    fi
    
    # Get tool count from HTTP endpoint
    TOOL_COUNT=$(curl -s http://localhost:5050/tools 2>/dev/null | jq -r '.count // 0' 2>/dev/null || echo "0")
    
    # Get Redis stats via JSON-RPC
    REDIS_STATS=$(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "redis_cache_stats", "arguments": {}}, "id": 1}' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$REDIS_STATS" ]; then
        CONNECTED=$(echo "$REDIS_STATS" | jq -r '.result.stats.connected // false' 2>/dev/null || echo "false")
        TOTAL_KEYS=$(echo "$REDIS_STATS" | jq -r '.result.stats.total_keys // 0' 2>/dev/null || echo "0")
        USED_MEMORY=$(echo "$REDIS_STATS" | jq -r '.result.stats.used_memory // "0"' 2>/dev/null || echo "0")
        
        if [ "$CONNECTED" = "true" ]; then
            REDIS_STATUS="🔥 Redis:${TOTAL_KEYS}keys"
        else
            REDIS_STATUS="❌ Redis"
        fi
    else
        REDIS_STATUS="❓ Redis"
    fi
    
    # Get context usage stats
    CONTEXT_STATS=$(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "get_context_usage_statistics", "arguments": {}}, "id": 1}' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$CONTEXT_STATS" ]; then
        CONTEXT_LINKS=$(echo "$CONTEXT_STATS" | jq -r '.result.statistics.total_context_links // 0' 2>/dev/null || echo "0")
        CONTEXT_STATUS="📈 Links:${CONTEXT_LINKS}"
    else
        CONTEXT_STATUS="📈 Links:?"
    fi
    
    # Format the status line
    echo "✅ LTMC:${TOOL_COUNT}/28 ${REDIS_STATUS} ${CONTEXT_STATUS} [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"
}

# Get stats with timeout to avoid hanging Claude Code
timeout 3s bash -c "$(declare -f get_ltmc_stats); get_ltmc_stats '$MODEL_SHORT' '$PROJECT_NAME'" 2>/dev/null || echo "⏱️ LTMC Timeout [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"