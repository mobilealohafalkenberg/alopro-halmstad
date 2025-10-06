#!/bin/bash
# Quick start script for Virtual Robot Arm Simulator

echo "🤖 Virtual Robot Arm Simulator - Starting..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from template..."
    cp .env.example .env
    echo "✏️  Please edit .env and add your REACT_APP_GEMINI_API_KEY"
    echo "   Get your API key at: https://aistudio.google.com"
    echo ""
    read -p "Press Enter after adding your API key to continue..."
fi

# Check if node_modules exists
if [ ! -d node_modules ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "🚀 Starting development server..."
echo "   The app will open at http://localhost:3000"
echo ""
echo "Controls:"
echo "  1. Click 'Connect to Gemini'"
echo "  2. Click 'Start Voice Control' to use your microphone"
echo "  3. Try saying: 'Move to home position' or 'Pick up the green apple'"
echo ""

npm start
