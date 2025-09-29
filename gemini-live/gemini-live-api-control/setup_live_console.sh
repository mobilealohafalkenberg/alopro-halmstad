#!/bin/bash

# Setup script for Live API Console with pen detection

echo "🎥 Setting up Gemini Live API Console for pen detection..."

cd live-api-console

# Install dependencies
echo "Installing dependencies..."
npm install

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    echo "REACT_APP_GEMINI_API_KEY=${GEMINI_API_KEY}" > .env
fi

# Add pen detection function to the example
cat > src/pen-detection-config.js << 'EOF'
// Pen detection configuration for Live API Console

export const penDetectionTool = {
  functionDeclarations: [{
    name: "holding_pen",
    description: "Report whether a pen is visible in the video",
    parameters: {
      type: "object",
      properties: {
        is_holding: {
          type: "boolean",
          description: "True if pen is visible"
        }
      },
      required: ["is_holding"]
    }
  }]
};

export const penDetectionSystemInstruction = 
  "You see a live video stream. Every time you're asked, call holding_pen " +
  "with is_holding=true if you see a pen, is_holding=false otherwise. " +
  "Only call the function, no text responses.";

export const handlePenDetectionToolCall = (toolCall) => {
  console.log("Tool call received:", toolCall);
  
  const functionCalls = toolCall.functionCalls || [];
  for (const call of functionCalls) {
    if (call.name === "holding_pen") {
      const isHolding = call.args?.is_holding || false;
      const emoji = isHolding ? "✅" : "❌";
      const status = isHolding ? "PEN DETECTED" : "NO PEN";
      
      // Update UI or log
      console.log(`${emoji} ${status}`);
      
      // You could update a state variable here to show in the UI
      document.title = `${emoji} ${status}`;
    }
  }
};
EOF

echo "✅ Setup complete!"
echo ""
echo "To run the Live API Console with pen detection:"
echo "  1. cd live-api-console"
echo "  2. npm start"
echo "  3. Open http://localhost:3000"
echo "  4. The console will connect to Gemini Live API"
echo "  5. Enable webcam access when prompted"
echo "  6. Hold up a pen to test detection!"
echo ""
echo "Note: You'll need to modify App.tsx to import and use the pen detection config"