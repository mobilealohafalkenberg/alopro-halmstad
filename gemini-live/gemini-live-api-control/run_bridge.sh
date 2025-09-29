#!/bin/bash

# Run script for ALOHA Gemini Bridge
# This handles all environment setup and launches the bridge

echo "=========================================="
echo "Starting ALOHA Gemini Bridge"
echo "=========================================="
echo ""

# Source ROS environment FIRST (before venv)
echo "Sourcing ROS environment..."
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Use system Python with ROS packages (don't use venv for ROS compatibility)
echo "Checking dependencies..."

# Install aiohttp in user space if not present
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "Installing aiohttp packages..."
    pip3 install --user aiohttp aiohttp-cors
fi

# Run the bridge with system Python (has access to ROS packages)
echo ""
echo "Starting bridge server..."
echo "=========================================="
python3 bridges/bridge_aloha_real.py