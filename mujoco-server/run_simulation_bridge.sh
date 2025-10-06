#!/bin/bash
#
# Launch script for Gemini-MuJoCo Simulation Bridge
#
# This bridge translates Gemini Live API tool calls to MuJoCo WebSocket commands.
# Runs on port 8082 (different from real robot bridge on 8081).
#
# Usage:
#   ./run_simulation_bridge.sh
#

echo "============================================================"
echo "Gemini-MuJoCo Simulation Bridge"
echo "============================================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please create it first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if MuJoCo server is running
echo "Checking MuJoCo server status..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "✓ MuJoCo server is running on port 5000"
else
    echo "✗ MuJoCo server not detected on port 5000"
    echo ""
    echo "Please start the simulation server first:"
    echo "  cd mujoco-server"
    echo "  source venv/bin/activate"
    echo "  python simulation_server.py --model models/aloha/aloha_simple.xml --port 5000 --headless"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if port 8082 is already in use
if lsof -Pi :8082 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✗ Port 8082 is already in use!"
    echo "Kill the existing process or use a different port"
    exit 1
fi

echo ""
echo "Starting simulation bridge on port 8082..."
echo "Press Ctrl+C to stop"
echo ""

# Run the bridge
python3 bridges/bridge_aloha_simulation.py
