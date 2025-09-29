#!/usr/bin/env python3
"""
Python bridge for pen detection with Gemini Live API Web Console.

This script:
1. Monitors the React app's console output for tool calls
2. Processes pen detection events
3. Can trigger Python functions based on the detections
"""

import asyncio
import json
import websocket
import threading
from datetime import datetime
from typing import Optional, Callable

class PenDetectionBridge:
    def __init__(self):
        self.last_pen_state: Optional[bool] = None
        self.detection_count = 0
        self.on_pen_detected: Optional[Callable] = None
        self.on_pen_removed: Optional[Callable] = None
        
    def register_callbacks(self, on_detected: Callable = None, on_removed: Callable = None):
        """Register Python functions to call when pen state changes"""
        self.on_pen_detected = on_detected
        self.on_pen_removed = on_removed
    
    def process_tool_call(self, tool_call_data: dict):
        """Process tool call from Gemini Live API"""
        if tool_call_data.get("name") == "holding_pen":
            is_holding = tool_call_data.get("args", {}).get("is_holding", False)
            
            # Check if state changed
            if is_holding != self.last_pen_state:
                self.detection_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if is_holding:
                    print(f"✅ [{timestamp}] Pen DETECTED (#{self.detection_count})")
                    if self.on_pen_detected:
                        self.on_pen_detected()
                else:
                    print(f"❌ [{timestamp}] Pen REMOVED (#{self.detection_count})")
                    if self.on_pen_removed:
                        self.on_pen_removed()
                
                self.last_pen_state = is_holding
                return True
        return False

# Example Python functions to trigger
def pen_detected_action():
    """Called when pen is detected"""
    print("  🎯 Python Action: Pen detected - triggering action!")
    # You could:
    # - Save a screenshot
    # - Start recording
    # - Send a notification
    # - Toggle a GPIO pin on Raspberry Pi
    # - Send data to another service
    # etc.

def pen_removed_action():
    """Called when pen is removed"""
    print("  🎯 Python Action: Pen removed - stopping action!")
    # You could:
    # - Stop recording
    # - Process collected data
    # - Reset state
    # etc.

# WebSocket approach - connect directly to the Gemini Live API
def connect_via_websocket():
    """
    Alternative: Connect directly to Gemini API via WebSocket
    This would bypass the React app entirely
    """
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Note: The exact WebSocket URL for Gemini Live API isn't publicly documented
    # This is a placeholder - you'd need the actual endpoint
    ws_url = f"wss://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:streamGenerateContent?key={api_key}"
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            print(f"Received: {data}")
        except json.JSONDecodeError:
            print(f"Raw message: {message}")
    
    def on_error(ws, error):
        print(f"Error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        print(f"Connection closed: {close_status_code} - {close_msg}")
    
    def on_open(ws):
        print("WebSocket connection opened")
        # Send initial configuration
        config = {
            "generationConfig": {
                "temperature": 0.2,
                "topK": 1,
                "topP": 1,
                "maxOutputTokens": 2048,
            },
            "tools": [{
                "functionDeclarations": [{
                    "name": "holding_pen",
                    "description": "Report if pen is visible",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "is_holding": {
                                "type": "boolean",
                                "description": "True if pen is visible"
                            }
                        },
                        "required": ["is_holding"]
                    }
                }]
            }]
        }
        ws.send(json.dumps(config))
    
    ws = websocket.WebSocketApp(ws_url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.run_forever()

# Monitor approach - parse React app logs
async def monitor_react_logs():
    """
    Monitor the React app's console output for tool calls
    This requires the React app to console.log the tool calls
    """
    bridge = PenDetectionBridge()
    bridge.register_callbacks(pen_detected_action, pen_removed_action)
    
    print("🎥 Python Pen Detection Bridge")
    print("="*50)
    print("Monitoring for pen detection events...")
    print("Make sure the React app is running and connected")
    print("="*50)
    
    # In a real implementation, you'd:
    # 1. Connect to the React app via WebSocket
    # 2. Or monitor shared log file
    # 3. Or use a message queue
    
    # For now, simulate with manual input
    while True:
        try:
            # Simulate receiving tool call data
            # In practice, this would come from the React app
            user_input = input("\nPress Enter to simulate pen detection, 'r' to remove, 'q' to quit: ")
            
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 'r':
                tool_call = {
                    "name": "holding_pen",
                    "args": {"is_holding": False}
                }
            else:
                tool_call = {
                    "name": "holding_pen", 
                    "args": {"is_holding": True}
                }
            
            bridge.process_tool_call(tool_call)
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break

# HTTP Server approach - React app posts to Python
async def run_http_server():
    """
    Run an HTTP server that the React app can POST tool calls to
    """
    from aiohttp import web
    
    bridge = PenDetectionBridge()
    bridge.register_callbacks(pen_detected_action, pen_removed_action)
    
    async def handle_tool_call(request):
        try:
            data = await request.json()
            result = bridge.process_tool_call(data)
            return web.json_response({"success": result})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)
    
    async def handle_status(request):
        return web.json_response({
            "status": "running",
            "last_state": bridge.last_pen_state,
            "detection_count": bridge.detection_count
        })
    
    app = web.Application()
    app.router.add_post('/tool-call', handle_tool_call)
    app.router.add_get('/status', handle_status)
    
    port = 8081
    print(f"🌐 Starting HTTP server on http://localhost:{port}")
    print(f"React app can POST tool calls to http://localhost:{port}/tool-call")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    # Keep server running
    await asyncio.Event().wait()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run HTTP server mode
        print("Starting in HTTP server mode...")
        asyncio.run(run_http_server())
    elif len(sys.argv) > 1 and sys.argv[1] == "--websocket":
        # Try direct WebSocket connection
        print("Starting in WebSocket mode...")
        connect_via_websocket()
    else:
        # Default: monitor mode
        print("Starting in monitor mode...")
        asyncio.run(monitor_react_logs())