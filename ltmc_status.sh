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

# Function to get LTMC server stats with comprehensive tool usage data
get_ltmc_stats() {
    # Make variables available in function
    local MODEL_SHORT="$1"
    local PROJECT_NAME="$2"
    
    # Check if LTMC server is running
    if ! curl -s http://localhost:5050/health >/dev/null 2>&1; then
        echo "❌ LTMC Down [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"
        return
    fi
    
    # Get tool count from HTTP endpoint
    TOOL_COUNT=$(curl -s http://localhost:5050/tools 2>/dev/null | jq -r '.count // 0' 2>/dev/null || echo "0")
    
    # Look for recent test results to get detailed tool statistics
    LATEST_RESULTS=$(find . -name "ltmc_all_28_tools_test_results_*.json" -type f -exec ls -t {} + 2>/dev/null | head -1)
    
    if [ -n "$LATEST_RESULTS" ] && [ -f "$LATEST_RESULTS" ]; then
        # Parse detailed tool statistics from latest comprehensive test results
        TOTAL_TOOLS=$(jq -r '.summary.total_tools // 28' "$LATEST_RESULTS" 2>/dev/null || echo "28")
        PASSED_TOOLS=$(jq -r '.summary.http_passed // 0' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        SUCCESS_RATE=$(echo "scale=1; $PASSED_TOOLS * 100 / $TOTAL_TOOLS" | bc 2>/dev/null || echo "0")
        
        # Count passed tools by category from HTTP results
        MEMORY_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("store_memory|retrieve_memory")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        CHAT_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("log_chat|ask_with_context|route_query|get_chats_by_tool")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        TODO_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("add_todo|list_todos|complete_todo|search_todos")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        CONTEXT_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("build_context|retrieve_by_type|store_context_links|get_context_links|get_messages_for_chunk|get_context_usage")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        REDIS_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("redis_")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        CODE_PASSED=$(jq -r '.http | to_entries | map(select(.key | test("log_code_attempt|get_code_patterns|analyze_code_patterns")) | select(.value.success == true)) | length' "$LATEST_RESULTS" 2>/dev/null || echo "0")
        
        # Format success rate
        SUCCESS_PCT=$(echo "$SUCCESS_RATE" | cut -d'.' -f1)
        
        # Create tool status breakdown
        TOOL_BREAKDOWN="Mem:${MEMORY_PASSED} Chat:${CHAT_PASSED} Todo:${TODO_PASSED} Ctx:${CONTEXT_PASSED} Redis:${REDIS_PASSED} Code:${CODE_PASSED}"
        
        # Set status icon based on success rate
        if [ "$SUCCESS_PCT" -ge 95 ]; then
            STATUS_ICON="🔥"
        elif [ "$SUCCESS_PCT" -ge 85 ]; then
            STATUS_ICON="✅"
        elif [ "$SUCCESS_PCT" -ge 70 ]; then
            STATUS_ICON="⚠️"
        else
            STATUS_ICON="❌"
        fi
        
        TOOL_STATUS="${STATUS_ICON} ${PASSED_TOOLS}/${TOTAL_TOOLS}(${SUCCESS_PCT}%)"
    else
        # Fallback to basic tool count
        TOOL_STATUS="✅ ${TOOL_COUNT}/28"
        TOOL_BREAKDOWN=""
    fi
    
    # Get Redis stats via JSON-RPC
    REDIS_STATS=$(curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
        -d '{"jsonrpc": "2.0", "method": "tools/call", "params": {"name": "redis_cache_stats", "arguments": {}}, "id": 1}' 2>/dev/null)
    
    if [ $? -eq 0 ] && [ -n "$REDIS_STATS" ]; then
        CONNECTED=$(echo "$REDIS_STATS" | jq -r '.result.stats.connected // false' 2>/dev/null || echo "false")
        TOTAL_KEYS=$(echo "$REDIS_STATS" | jq -r '.result.stats.total_keys // 0' 2>/dev/null || echo "0")
        REDIS_VERSION=$(echo "$REDIS_STATS" | jq -r '.result.stats.redis_version // "?"' 2>/dev/null || echo "?")
        
        if [ "$CONNECTED" = "true" ]; then
            REDIS_STATUS="🚀 Redis:${TOTAL_KEYS}k"
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
        UNIQUE_MESSAGES=$(echo "$CONTEXT_STATS" | jq -r '.result.statistics.unique_messages // 0' 2>/dev/null || echo "0")
        
        # Format large numbers with k/M suffixes
        if [ "$CONTEXT_LINKS" -gt 1000 ]; then
            LINKS_DISPLAY=$(echo "$CONTEXT_LINKS" | awk '{printf "%.1fk", $1/1000}')
        else
            LINKS_DISPLAY="$CONTEXT_LINKS"
        fi
        
        CONTEXT_STATUS="📈 ${LINKS_DISPLAY}links"
    else
        CONTEXT_STATUS="📈 Links:?"
    fi
    
    # Format the enhanced status line
    if [ -n "$TOOL_BREAKDOWN" ] && [ ${#TOOL_BREAKDOWN} -lt 60 ]; then
        echo "${TOOL_STATUS} ${REDIS_STATUS} ${CONTEXT_STATUS} | ${TOOL_BREAKDOWN} [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"
    else
        echo "${TOOL_STATUS} ${REDIS_STATUS} ${CONTEXT_STATUS} [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"
    fi
}

# Get stats with timeout to avoid hanging Claude Code
timeout 3s bash -c "$(declare -f get_ltmc_stats); get_ltmc_stats '$MODEL_SHORT' '$PROJECT_NAME'" 2>/dev/null || echo "⏱️ LTMC Timeout [${MODEL_SHORT}] 📁 ${PROJECT_NAME}"