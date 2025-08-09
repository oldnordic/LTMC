#!/bin/bash
set -e

echo "🚀 Running Redis diagnostics..."

# Make the debug script executable
chmod +x debug_redis_connection.py

# Run the debug script
python debug_redis_connection.py