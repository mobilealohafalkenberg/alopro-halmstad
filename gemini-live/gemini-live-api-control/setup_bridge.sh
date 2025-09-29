#!/bin/bash

# Setup script for ALOHA Gemini Bridge
# This creates a uv environment and installs dependencies

echo "=========================================="
echo "Setting up ALOHA Gemini Bridge Environment"
echo "=========================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
fi

# Create virtual environment and install dependencies
echo "Creating virtual environment with uv..."
uv venv

echo ""
echo "Installing dependencies..."
uv pip install aiohttp aiohttp-cors

echo ""
echo "=========================================="
echo "Setup complete!"
echo "=========================================="
echo ""
echo "To run the bridge:"
echo "1. Source ROS environment:"
echo "   source /opt/ros/humble/setup.bash"
echo "   source ~/interbotix_ws/install/setup.bash"
echo ""
echo "2. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "3. Run the bridge:"
echo "   python bridges/bridge_aloha_real.py"
echo ""