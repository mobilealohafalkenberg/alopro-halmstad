#!/bin/bash

# Simple run script for ALOHA Gemini Bridge
# Uses system Python with ROS packages

echo "=========================================="
echo "Starting ALOHA Gemini Bridge (Simple)"
echo "=========================================="
echo ""

# Source ROS environment
echo "Sourcing ROS environment..."
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Check Python dependencies
echo "Checking Python packages..."
python3 -c "import aiohttp" 2>/dev/null && echo "✓ aiohttp installed" || echo "✗ aiohttp missing - run: pip3 install --user aiohttp"
python3 -c "import aiohttp_cors" 2>/dev/null && echo "✓ aiohttp-cors installed" || echo "✗ aiohttp-cors missing - run: pip3 install --user aiohttp-cors"
python3 -c "import numpy" 2>/dev/null && echo "✓ numpy installed" || echo "✗ numpy missing - run: pip3 install --user numpy"

# Run the bridge
echo ""
echo "Starting bridge server on http://localhost:8081"
echo "=========================================="
cd $(dirname "$0")
python3 bridges/bridge_aloha_real.py