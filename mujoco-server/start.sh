#!/bin/bash
# Quick start script for MuJoCo simulation server

set -e

echo "======================================================================"
echo "MuJoCo Simulation Server"
echo "======================================================================"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate venv
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import mujoco" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install --quiet -r requirements.txt
    echo "✓ Dependencies installed"
fi

# Parse arguments or use defaults
MODE="${1:-simulation}"
MODEL="${2:-models/aloha/aloha_single_arm.xml}"
PORT="${3:-5000}"

echo ""
echo "Starting server with:"
echo "  Mode:  $MODE"
echo "  Model: $MODEL"
echo "  Port:  $PORT"
echo ""

# Start server
python simulation_server.py --mode "$MODE" --model "$MODEL" --port "$PORT"
