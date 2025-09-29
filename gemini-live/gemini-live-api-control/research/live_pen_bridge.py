#!/usr/bin/env python3
"""
Bridge solution: Use Node.js/TypeScript to handle Live API connection,
then process tool calls in Python.

This script sets up a Node.js process that:
1. Connects to Gemini Live API using the official @google/genai SDK
2. Streams webcam frames
3. Receives tool calls
4. Forwards them to Python for processing
"""

import os
import json
import asyncio
import subprocess
import sys
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# First, let's create a simple Node.js script that handles the Live API
NODE_SCRIPT = """
const { GoogleGenAI } = require("@google/genai");
const cv = require("opencv4nodejs");
const readline = require("readline");

// Get API key
const API_KEY = process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;
if (!API_KEY) {
  console.error("ERROR: Set GEMINI_API_KEY environment variable");
  process.exit(1);
}

const client = new GoogleGenAI({ apiKey: API_KEY });

// Tool declaration for pen detection
const holdingPenTool = {
  name: "holding_pen",
  description: "Report whether a pen is visible",
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
};

async function startLiveSession() {
  console.error("Starting Live API session...");
  
  const session = await client.live.connect({
    model: "models/gemini-2.0-flash-exp",
    config: {
      tools: [{ functionDeclarations: [holdingPenTool] }],
      systemInstruction: "You see a video stream. Every second, call holding_pen with true if you see a pen, false otherwise. Only call the function, no text.",
      temperature: 0.2
    },
    callbacks: {
      onopen: () => {
        console.error("Connected to Live API");
      },
      onmessage: (message) => {
        // Handle tool calls
        if (message.toolCall) {
          const toolCall = message.toolCall;
          for (const call of toolCall.functionCalls || []) {
            // Output tool call to Python via stdout
            console.log(JSON.stringify({
              type: "tool_call",
              name: call.name,
              args: call.args,
              id: call.id
            }));
          }
        }
      },
      onerror: (error) => {
        console.error("Error:", error.message);
      },
      onclose: () => {
        console.error("Connection closed");
        process.exit(0);
      }
    }
  });

  // Start video capture
  const cap = new cv.VideoCapture(0);
  
  // Send frames periodically
  setInterval(() => {
    const frame = cap.read();
    if (!frame.empty) {
      // Resize frame
      const resized = frame.resize(640, 480);
      const jpeg = cv.imencode(".jpg", resized);
      
      // Send as base64
      session.sendRealtimeInput({
        media: {
          mimeType: "image/jpeg",
          data: jpeg.toString("base64")
        }
      });
    }
  }, 333); // ~3 FPS

  // Trigger turns periodically to get tool calls
  setInterval(() => {
    session.sendClientContent({
      turns: [{ text: "Check" }],
      turnComplete: true
    });
  }, 1000); // Every second

  // Handle tool responses from Python
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: false
  });

  rl.on("line", (line) => {
    try {
      const response = JSON.parse(line);
      if (response.type === "tool_response") {
        session.sendToolResponse({
          functionResponses: [{
            name: response.name,
            id: response.id,
            response: response.result
          }]
        });
      }
    } catch (e) {
      console.error("Error parsing response:", e);
    }
  });
}

startLiveSession().catch(console.error);
"""

async def install_dependencies():
    """Install Node.js dependencies if needed"""
    print("Checking Node.js dependencies...")
    
    # Check if package.json exists
    if not os.path.exists("package.json"):
        print("Initializing npm project...")
        subprocess.run(["npm", "init", "-y"], check=True)
    
    # Install required packages
    print("Installing dependencies...")
    subprocess.run([
        "npm", "install", 
        "@google/genai",
        "opencv4nodejs"  # For webcam capture
    ], check=True)

async def run_bridge():
    """Run the Node.js bridge and process tool calls in Python"""
    
    # Save the Node.js script
    with open("live_api_bridge.js", "w") as f:
        f.write(NODE_SCRIPT)
    
    print("🎥 Starting Gemini Live Pen Detection (Node.js Bridge)")
    print("="*50)
    print("This uses Node.js to handle the Live API connection")
    print("and Python to process tool calls.")
    print("="*50)
    
    # Start the Node.js process
    process = await asyncio.create_subprocess_exec(
        "node", "live_api_bridge.js",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
        env={**os.environ, "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")}
    )
    
    last_state: Optional[bool] = None
    
    async def read_stdout():
        nonlocal last_state
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            
            try:
                data = json.loads(line.decode())
                if data["type"] == "tool_call" and data["name"] == "holding_pen":
                    is_holding = data["args"].get("is_holding", False)
                    
                    # Only show state changes
                    if is_holding != last_state:
                        last_state = is_holding
                        emoji = "✅" if is_holding else "❌"
                        print(f"\n{emoji} Pen {'DETECTED' if is_holding else 'NOT DETECTED'}")
                    
                    # Send response back to Node.js
                    response = {
                        "type": "tool_response",
                        "name": data["name"],
                        "id": data["id"],
                        "result": {"result": "ok"}
                    }
                    process.stdin.write((json.dumps(response) + "\n").encode())
                    await process.stdin.drain()
                    
            except json.JSONDecodeError:
                pass
    
    async def read_stderr():
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            print(f"[Node.js] {line.decode().strip()}", file=sys.stderr)
    
    # Run both readers concurrently
    await asyncio.gather(
        read_stdout(),
        read_stderr()
    )

async def main():
    # First install dependencies
    await install_dependencies()
    
    # Then run the bridge
    try:
        await run_bridge()
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    asyncio.run(main())