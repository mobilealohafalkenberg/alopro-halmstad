#!/usr/bin/env python3
"""
Mobile ALOHA Robot Bridge for Gemini Live API.

Phase 1 Implementation: Read-Only Status
- Sets up an HTTP server.
- Implements `get_robot_status` to read and return arm/gripper positions.
- All other functions are placeholders and will be implemented in Phase 3.
"""

import asyncio
import json
import traceback
import time
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions

# Mock ALOHA imports for initial setup without hardware dependency.
# We will replace these with real imports from the `act_plus_plus` library.
class MockArm:
    def get_ee_pose(self):
        # Returns a mock 4x4 transformation matrix.
        return [[1, 0, 0, 0.3], [0, 1, 0, 0.1], [0, 0, 1, 0.25], [0, 0, 0, 1]]

    @property
    def core(self):
        return self

    @property
    def joint_states(self):
        # Mock joint positions.
        return type('obj', (object,), {'position': [0.1, -0.2, 0.3, 0.4, 0.5, 0.6, 0.0]})()

class MockGripper:
    @property
    def core(self):
        return self

    @property
    def joint_states(self):
        # Mock gripper joint position. > 0.02 is considered open.
        return type('obj', (object,), {'position': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.03]})()

class MockBot:
    def __init__(self):
        self.arm = MockArm()
        self.gripper = MockGripper()

class MockEnv:
    def __init__(self):
        self.puppet_bot_left = MockBot()
        self.puppet_bot_right = MockBot()

class ALOHABridge:
    def __init__(self):
        """Initialize Mobile ALOHA robot interface."""
        print("🤖 Initializing Mobile ALOHA Bridge...")
        
        # In a real scenario, this initializes ROS and connects to the hardware.
        # For now, we use a mock environment to allow development without a robot.
        self.env = MockEnv()
        
        # Safety limits (in meters from robot base)
        self.workspace_limits = {
            'x': (0.15, 0.55),   # Forward reach
            'y': (-0.35, 0.35),  # Left/right reach  
            'z': (0.05, 0.45)    # Up/down reach
        }
        
        print("✅ Bridge initialized successfully (using MOCK hardware).")

    async def get_robot_status(self, args):
        """Gets the current state of the robot's arms and grippers."""
        print("Executing: get_robot_status")
        status = {}
        
        for arm_name in ['left', 'right']:
            bot = self.env.puppet_bot_left if arm_name == 'left' else self.env.puppet_bot_right
            
            ee_pose = bot.arm.get_ee_pose()
            
            status[arm_name] = {
                'joint_positions': list(bot.arm.core.joint_states.position[:6]),
                'end_effector': {
                    'x': float(ee_pose[0][3]),
                    'y': float(ee_pose[1][3]),
                    'z': float(ee_pose[2][3])
                },
                'gripper_open': bot.gripper.core.joint_states.position[6] > 0.02
            }
            
        return {
            'arms': status,
            'timestamp': time.time(),
            'workspace_limits': self.workspace_limits
        }

    async def move_to_position(self, args):
        """Placeholder for moving an arm. To be implemented in Phase 3."""
        print(f"PHASE 3 - NOT IMPLEMENTED: move_to_position with args: {args}")
        # This is where the real robot movement code will go.
        await asyncio.sleep(1) # Simulate movement time
        return {'success': True, 'status': 'move_to_position not implemented'}

    async def control_gripper(self, args):
        """Placeholder for controlling a gripper. To be implemented in Phase 3."""
        print(f"PHASE 3 - NOT IMPLEMENTED: control_gripper with args: {args}")
        # This is where the real gripper control code will go.
        await asyncio.sleep(0.5) # Simulate gripper action time
        return {'success': True, 'status': 'control_gripper not implemented'}

    async def process_tool_call(self, data):
        """Processes incoming tool calls from the Gemini Live API frontend."""
        name = data.get('name')
        args = data.get('args', {})
        call_id = data.get('id')
        
        print(f"🔧 Processing tool call: {name} with args: {args}")
        
        try:
            if name == 'get_robot_status':
                result = await self.get_robot_status(args)
            elif name == 'move_to_position':
                result = await self.move_to_position(args)
            elif name == 'control_gripper':
                result = await self.control_gripper(args)
            else:
                raise ValueError(f"Unknown tool: {name}")
                
            return {
                'success': True,
                'result': result,
                'call_id': call_id
            }
            
        except Exception as e:
            error_msg = f"Error executing {name}: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            
            return {
                'success': False,
                'error': error_msg,
                'call_id': call_id
            }

# --- Server Setup ---
async def handle_aloha_tool_call(request):
    """Handle HTTP POST requests from the React console."""
    try:
        data = await request.json()
        # The bridge is a global variable initialized below.
        result = await bridge.process_tool_call(data)
        return web.json_response(result)
        
    except Exception as e:
        error_response = {
            'success': False, 
            'error': str(e),
            'call_id': data.get('id') if 'data' in locals() else None
        }
        return web.json_response(error_response, status=500)

def main():
    # Set up HTTP server with CORS enabled.
    app = web.Application()
    cors = setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*", 
            allow_methods="*"
        )
    })

    app.router.add_post('/aloha-tool-call', handle_aloha_tool_call)
    
    print("🌐 ALOHA Bridge server starting on http://0.0.0.0:8081")
    web.run_app(app, host='0.0.0.0', port=8081)

if __name__ == '__main__':
    # Initialize the bridge globally.
    bridge = ALOHABridge()
    main()