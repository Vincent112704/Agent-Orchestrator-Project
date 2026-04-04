#!/bin/bash
set -e

# Default to production mode
DEBUG_MODE=${DEBUG_MODE:-false}
DEBUG_PORT=${DEBUG_PORT:-5678}

echo "=========================================="
echo "Real-Time Personalization Orchestrator"
echo "=========================================="
echo "Debug Mode: $DEBUG_MODE"
echo "Debug Port: $DEBUG_PORT"
echo ""

if [ "$DEBUG_MODE" = "true" ]; then
    echo "🔍 Starting in DEBUG mode..."
    echo "   Debugpy listening on 0.0.0.0:$DEBUG_PORT"
    echo "   Waiting for debugger client to attach..."
    echo ""
    exec python -m debugpy --listen 0.0.0.0:$DEBUG_PORT --wait-for-client src/main.py
else
    echo "🚀 Starting in PRODUCTION mode..."
    echo ""
    exec uvicorn src.main:app \
        --host 0.0.0.0 \
        --port 8000
fi