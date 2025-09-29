#!/usr/bin/env python3
"""
Python bridge for glasses detection with Gemini Live API Web Console.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable
from aiohttp import web

class GlassesDetectionBridge:
    def __init__(self):
        self.last_glasses_state: Optional[bool] = None
        self.detection_count = 0
        self.on_glasses_detected: Optional[Callable] = None
        self.on_glasses_removed: Optional[Callable] = None
        
    def register_callbacks(self, on_detected: Callable = None, on_removed: Callable = None):
        """Register Python functions to call when glasses state changes"""
        self.on_glasses_detected = on_detected
        self.on_glasses_removed = on_removed
    
    def process_tool_call(self, tool_call_data: dict):
        """Process tool call from Gemini Live API"""
        if tool_call_data.get("name") == "person_wears_glasses":
            wearing_glasses = tool_call_data.get("args", {}).get("wearing_glasses", False)
            
            # Check if state changed
            if wearing_glasses != self.last_glasses_state:
                self.detection_count += 1
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if wearing_glasses:
                    print(f"👓 [{timestamp}] GLASSES DETECTED (#{self.detection_count})")
                    if self.on_glasses_detected:
                        self.on_glasses_detected()
                else:
                    print(f"👤 [{timestamp}] NO GLASSES (#{self.detection_count})")
                    if self.on_glasses_removed:
                        self.on_glasses_removed()
                
                self.last_glasses_state = wearing_glasses
                return True
        return False

# Example Python functions to trigger
def glasses_detected_action():
    """Called when glasses are detected"""
    print("  🎯 Python Action: Glasses detected!")
    print("     → Could trigger accessibility features")
    print("     → Could adjust display settings")
    print("     → Could enable vision assistance mode")
    # Add your custom actions here

def glasses_removed_action():
    """Called when glasses are removed"""
    print("  🎯 Python Action: No glasses detected!")
    print("     → Could revert to normal display")
    print("     → Could disable vision assistance")
    # Add your custom actions here

async def run_http_server():
    """
    Run an HTTP server that the React app can POST tool calls to
    """
    bridge = GlassesDetectionBridge()
    bridge.register_callbacks(glasses_detected_action, glasses_removed_action)
    
    async def handle_tool_call(request):
        try:
            data = await request.json()
            print(f"Received tool call: {data.get('name')}")
            result = bridge.process_tool_call(data)
            return web.json_response({"success": result})
        except Exception as e:
            print(f"Error: {e}")
            return web.json_response({"error": str(e)}, status=400)
    
    async def handle_status(request):
        return web.json_response({
            "status": "running",
            "last_state": bridge.last_glasses_state,
            "detection_count": bridge.detection_count,
            "mode": "glasses_detection"
        })
    
    # Enable CORS for browser requests
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware_handler
    
    app = web.Application(middlewares=[cors_middleware])
    app.router.add_post('/tool-call', handle_tool_call)
    app.router.add_get('/status', handle_status)
    app.router.add_options('/tool-call', lambda r: web.Response())
    app.router.add_options('/status', lambda r: web.Response())
    
    port = 8081
    print(f"👓 Glasses Detection Bridge Server")
    print(f"="*50)
    print(f"🌐 Running on http://localhost:{port}")
    print(f"📡 Waiting for detection events...")
    print(f"="*50)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', port)
    await site.start()
    
    # Keep server running
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(run_http_server())
    except KeyboardInterrupt:
        print("\n\nShutting down...")