#!/bin/bash

# Run script for Trajectory Bridge with ROS/ALOHA support
# This handles all environment setup and launches the trajectory bridge

echo "=========================================="
echo "Starting Trajectory Bridge"
echo "=========================================="
echo ""

# Source venv FIRST for proper Python environment
echo "Activating Python virtual environment..."
source /home/aloha/gemini-live/gemini-live-api-control/.venv/bin/activate

# Source ROS environment (this provides the aloha module)
echo "Sourcing ROS environment..."
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# This adds the aloha module to Python path
export PYTHONPATH=$PYTHONPATH:/home/aloha/interbotix_ws/install/aloha/lib/python3.10/site-packages

# Check dependencies
echo "Checking dependencies..."
if ! python -c "import aiohttp" 2>/dev/null; then
    echo "Installing aiohttp packages..."
    pip install aiohttp aiohttp-cors
fi

# Set environment variables
export ROBOT_DRIVER=${ROBOT_DRIVER:-real}  # Use real driver by default
export DEFAULT_MOVING_TIME=2.0
export DEFAULT_ACCEL_TIME=0.3
export SAFETY_PROFILE=strict

# Run the trajectory bridge
echo ""
echo "Starting trajectory bridge server..."
echo "  Driver mode: $ROBOT_DRIVER"
echo "  Port: 8082"
echo "=========================================="

cd /home/aloha/gemini-live
python trajectory_bridge.py