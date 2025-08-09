#!/bin/bash
# Performance tracking script for LTMC tools

# Create performance log directory if it doesn't exist
mkdir -p /home/feanor/Projects/lmtc/performance_logs

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="/home/feanor/Projects/lmtc/performance_logs/performance_${TIMESTAMP}.log"

# Header for log file
echo "LTMC Performance Check: ${TIMESTAMP}" > "$LOG_FILE"
echo "-------------------------------------------" >> "$LOG_FILE"

# Run comprehensive tool validation and capture performance metrics
python /home/feanor/Projects/lmtc/test_all_28_tools.py 2>&1 | grep -E "Success Rate|Response Time|Throughput" >> "$LOG_FILE"

# Optional: Add system resource snapshot
echo "--- System Resources ---" >> "$LOG_FILE"
top -bn1 | head -n 5 >> "$LOG_FILE"

# Optional: Database connection metrics
sqlite3 /home/feanor/Projects/lmtc/ltmc.db "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM Resources;" >> "$LOG_FILE"

# Optional: Store results in LTMC memory system
curl -s http://localhost:5050/jsonrpc -X POST -H "Content-Type: application/json" \
-d "{
    \"jsonrpc\": \"2.0\",
    \"method\": \"tools/call\",
    \"params\": {
        \"name\": \"store_memory\", 
        \"arguments\": {
            \"file_name\": \"performance_log_${TIMESTAMP}.md\",
            \"content\": \"$(cat "$LOG_FILE")\",
            \"resource_type\": \"performance_log\"
        }
    },
    \"id\": 1
}" >> /dev/null

echo "Performance log generated: $LOG_FILE"