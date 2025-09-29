#!/bin/bash

# Monitor tool calls debug log

LOG_FILE="/home/aloha/gemini-live/debug/tool_calls.log"

echo "============================================"
echo "Monitoring Tool Calls Debug Log"
echo "============================================"
echo ""
echo "Waiting for tool calls from Gemini..."
echo ""

# Create log file if it doesn't exist
touch "$LOG_FILE"

# Monitor the log file
tail -f "$LOG_FILE"