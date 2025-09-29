#!/usr/bin/env python3
"""
Mac Control Bridge - Control your Mac through Gemini Live API
Demonstrates tangible computer control through voice/text commands
"""

import asyncio
import subprocess
import time
import os
from datetime import datetime
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions
import json

class MacController:
    def __init__(self):
        self.volume_level = self.get_current_volume()
        self.notifications_sent = 0
        self.last_action = None
        
    def get_current_volume(self):
        """Get current system volume (0-100)"""
        try:
            result = subprocess.run(
                ["osascript", "-e", "output volume of (get volume settings)"],
                capture_output=True, text=True
            )
            return int(result.stdout.strip())
        except:
            return 50
    
    def play_sound(self, sound_name="Glass"):
        """Play a system sound"""
        sounds = {
            "glass": "Glass",
            "ping": "Ping", 
            "pop": "Pop",
            "basso": "Basso",
            "funk": "Funk",
            "hero": "Hero",
            "morse": "Morse",
            "sosumi": "Sosumi",
            "submarine": "Submarine"
        }
        
        sound = sounds.get(sound_name.lower(), "Glass")
        subprocess.run(["afplay", f"/System/Library/Sounds/{sound}.aiff"])
        return {"played": sound, "timestamp": time.time()}
    
    def show_notification(self, title="Robot Control", message="Command executed", sound=True):
        """Show a macOS notification"""
        self.notifications_sent += 1
        sound_flag = "with sound" if sound else ""
        
        script = f'''
        display notification "{message}" with title "{title}" {sound_flag}
        '''
        
        subprocess.run(["osascript", "-e", script])
        return {
            "notification_sent": True,
            "count": self.notifications_sent,
            "title": title,
            "message": message
        }
    
    def set_volume(self, level):
        """Set system volume (0-100)"""
        level = max(0, min(100, level))
        subprocess.run(["osascript", "-e", f"set volume output volume {level}"])
        old_volume = self.volume_level
        self.volume_level = level
        return {
            "previous_volume": old_volume,
            "new_volume": level,
            "changed": old_volume != level
        }
    
    def take_screenshot(self, filename=None):
        """Take a screenshot and save to Desktop"""
        if not filename:
            filename = f"gemini_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        desktop_path = os.path.expanduser("~/Desktop")
        filepath = os.path.join(desktop_path, filename)
        
        # Take screenshot with sound
        subprocess.run(["screencapture", filepath])
        
        return {
            "screenshot_taken": True,
            "filepath": filepath,
            "filename": filename,
            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        }
    
    def open_app(self, app_name):
        """Open an application"""
        try:
            subprocess.run(["open", "-a", app_name], check=True)
            return {"opened": app_name, "success": True}
        except subprocess.CalledProcessError:
            return {"opened": app_name, "success": False, "error": "App not found"}
    
    def say_text(self, text, voice="Samantha"):
        """Use text-to-speech to say something"""
        # Available voices: Alex, Samantha, Victoria, etc.
        subprocess.run(["say", "-v", voice, text])
        return {"spoken": text, "voice": voice}
    
    def system_beep(self, times=1):
        """Make the system beep"""
        for _ in range(times):
            subprocess.run(["osascript", "-e", "beep"])
            if times > 1:
                time.sleep(0.3)
        return {"beeped": times}

# Global controller instance
mac = MacController()

async def handle_tool_call(request: web.Request) -> web.Response:
    """Handle tool calls from the browser"""
    data = await request.json()
    name = data.get('name')
    args = data.get('args', {})
    
    print(f"\n🎯 Tool call: {name}")
    print(f"   Args: {args}")
    
    result = {"success": False, "error": "Unknown tool"}
    
    try:
        if name == 'play_sound':
            sound = args.get('sound', 'glass')
            result = mac.play_sound(sound)
            print(f"   🔊 Played sound: {sound}")
            
        elif name == 'show_notification':
            title = args.get('title', 'Gemini Control')
            message = args.get('message', 'Command executed')
            result = mac.show_notification(title, message)
            print(f"   📬 Notification shown: {title}")
            
        elif name == 'set_volume':
            level = int(args.get('level', 50))
            result = mac.set_volume(level)
            print(f"   🔊 Volume set to: {level}%")
            
        elif name == 'take_screenshot':
            result = mac.take_screenshot()
            print(f"   📸 Screenshot saved: {result.get('filename')}")
            
        elif name == 'open_app':
            app = args.get('app', 'Calculator')
            result = mac.open_app(app)
            print(f"   🚀 Opened app: {app}")
            
        elif name == 'say_text':
            text = args.get('text', 'Hello from Gemini')
            voice = args.get('voice', 'Samantha')
            result = mac.say_text(text, voice)
            print(f"   🗣️ Said: {text}")
            
        elif name == 'system_beep':
            times = int(args.get('times', 1))
            result = mac.system_beep(times)
            print(f"   🔔 Beeped {times} time(s)")
            
        elif name == 'get_system_status':
            result = {
                'volume': mac.volume_level,
                'notifications_sent': mac.notifications_sent,
                'last_action': mac.last_action,
                'timestamp': time.time()
            }
            print(f"   📊 Status: Volume={mac.volume_level}%, Notifications={mac.notifications_sent}")
        
        else:
            print(f"   ❌ Unknown tool: {name}")
            
        result['success'] = True
        mac.last_action = {'tool': name, 'args': args, 'time': time.time()}
        
    except Exception as e:
        result = {'success': False, 'error': str(e)}
        print(f"   ❌ Error: {e}")
    
    return web.json_response({'result': result, 'call_id': data.get('id')})

async def handle_status(request: web.Request) -> web.Response:
    """Get current system status"""
    return web.json_response({
        'volume': mac.volume_level,
        'notifications_sent': mac.notifications_sent,
        'last_action': mac.last_action,
        'system': 'macOS',
        'timestamp': time.time()
    })

def make_app() -> web.Application:
    app = web.Application()
    
    # Setup CORS
    cors = setup(app, defaults={
        '*': ResourceOptions(
            allow_credentials=True,
            expose_headers='*',
            allow_headers='*',
            allow_methods='*'
        )
    })
    
    # Add routes
    app.router.add_post('/mac-control', handle_tool_call)
    app.router.add_get('/status', handle_status)
    
    # CORS for routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    return app

if __name__ == '__main__':
    print("🖥️  Mac Control Bridge")
    print("=" * 50)
    print("🌐 Starting server on http://localhost:8082")
    print("🎮 Ready to control your Mac!")
    print("=" * 50)
    
    # Show initial notification
    mac.show_notification(
        "Mac Control Bridge",
        "Voice control is now active! Say commands to control your Mac.",
        sound=True
    )
    
    web.run_app(make_app(), host='0.0.0.0', port=8082)