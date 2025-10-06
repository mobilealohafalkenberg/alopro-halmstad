#!/bin/bash

# Setup script to copy all .env.example files to .env
# Run this from the project root directory

echo "🔧 Setting up environment files..."
echo ""

# Function to copy and report
copy_env() {
    local dir=$1
    if [ -f "$dir/.env.example" ]; then
        if [ -f "$dir/.env" ]; then
            echo "⚠️  $dir/.env already exists - skipping"
        else
            cp "$dir/.env.example" "$dir/.env"
            echo "✓ Created $dir/.env"
        fi
    else
        echo "✗ Missing $dir/.env.example"
    fi
}

# Copy all .env files
copy_env "python_scripts"
copy_env "gemini-live/gemini-live-api-control"
copy_env "gemini-live/gemini-live-api-control/live-api-console"
copy_env "live-api-web-console"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Get your Gemini API key from: https://aistudio.google.com"
echo ""
echo "2. Edit each .env file and replace 'your-gemini-api-key-here' with your actual key:"
echo ""
echo "   nano python_scripts/.env"
echo "   nano gemini-live/gemini-live-api-control/.env"
echo "   nano gemini-live/gemini-live-api-control/live-api-console/.env"
echo "   nano live-api-web-console/.env"
echo ""
echo "3. For React apps, restart dev server after editing .env"
echo ""
echo "See ENV_SETUP_GUIDE.md for detailed instructions"
echo ""
