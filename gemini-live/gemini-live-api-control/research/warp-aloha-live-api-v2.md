# 🤖 Mobile ALOHA + Gemini Live API: Complete Integration Guide

**Goal**: Control your Trossen Robotics Mobile ALOHA robot using Gemini Live API's spatial understanding for real-time manipulation tasks like "Pick the banana and put it in the bowl."

## 🏗️ System Architecture

Based on your existing Live API Console demo and Trossen Robotics Mobile ALOHA setup:

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  Gemini Live    │◄──────────────────►│  Live API        │
│  API (Cloud)    │  Video + Tool Calls │  Console (React) │
└─────────────────┘                     └──────────────────┘
                                                │
                                          HTTP  │ Tool Calls
                                                ▼
                                        ┌──────────────────┐
                                        │  Python Bridge   │
                                        │  (Port 8081)     │  ← Based on glasses_detection_bridge.py
                                        └──────────────────┘
                                                │
                                      ROS2/ROS1 │ Commands
                                                ▼
                                        ┌──────────────────┐
                                        │  Mobile ALOHA    │
                                        │  (Interbotix +   │  ← Your Trossen setup
                                        │   SLATE base)    │
                                        └──────────────────┘
```

## 📋 What You Already Have

✅ **Live API Console**: Complete React app with WebSocket connection to Gemini  
✅ **Bridge Pattern**: `glasses_detection_bridge.py` shows HTTP → tool execution  
✅ **Mobile ALOHA Hardware**: Trossen Robotics starter kit  
✅ **ACT++ Framework**: `imitate_episodes.py` and robot control infrastructure  

## 🛠️ Implementation Plan

### Phase 1: Extend Live API Console

#### 1.1 Create ALOHA Control Component

Create `src/components/aloha-control/ALOHAControl.tsx`:

```typescript
import { useEffect, useState } from 'react';
import { useLiveAPIContext } from '../../contexts/LiveAPIContext';

// Robot control tool definitions
const ROBOT_TOOLS = [
  {
    name: "detect_objects",
    description: "Identify objects and their positions in the current video frame",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "move_to_position",
    description: "Move robot arm to specific 3D coordinates",
    parameters: {
      type: "object",
      properties: {
        arm: { 
          type: "string", 
          enum: ["left", "right"], 
          description: "Which arm to use" 
        },
        x: { type: "number", description: "X coordinate in meters from robot base" },
        y: { type: "number", description: "Y coordinate in meters from robot base" },
        z: { type: "number", description: "Z coordinate in meters from robot base" }
      },
      required: ["arm", "x", "y", "z"]
    }
  },
  {
    name: "control_gripper",
    description: "Open or close the robot gripper",
    parameters: {
      type: "object",
      properties: {
        arm: { type: "string", enum: ["left", "right"] },
        action: { type: "string", enum: ["open", "close"] }
      },
      required: ["arm", "action"]
    }
  },
  {
    name: "get_robot_status",
    description: "Get current robot arm positions and gripper states",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  }
];

const SYSTEM_INSTRUCTION = `
You are controlling a Mobile ALOHA robot with dual arms through live video.
You can see the robot's workspace and surrounding environment.
Use the provided functions to:
1. First detect_objects to understand the scene
2. Then move_to_position to move arms to target locations  
3. Use control_gripper to grasp/release objects
4. Always specify which arm ("left" or "right") to use

Coordinate system: X=forward, Y=left, Z=up from robot base (0,0,0).
Typical workspace: X: 0.2-0.5m, Y: -0.3 to +0.3m, Z: 0.1-0.4m
`;

export function ALOHAControl() {
  const { client, setConfig, connected } = useLiveAPIContext();
  const [taskStatus, setTaskStatus] = useState('Ready');
  const [robotState, setRobotState] = useState(null);

  // Configure before connection (like GlassesDetectionFixed)
  useEffect(() => {
    setConfig({
      tools: [{ functionDeclarations: ROBOT_TOOLS }],
      systemInstruction: SYSTEM_INSTRUCTION,
    });
  }, [setConfig]);

  // Handle tool calls from Gemini
  useEffect(() => {
    const handleToolCall = async (toolCall) => {
      const responses = [];
      
      for (const call of toolCall.functionCalls) {
        setTaskStatus(`Executing: ${call.name}`);
        
        try {
          // Send to Python bridge (same pattern as glasses detection)
          const result = await fetch('http://localhost:8081/aloha-tool-call', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: call.name,
              args: call.args,
              id: call.id,
            }),
          });
          
          const data = await result.json();
          
          // Update UI with result
          if (call.name === 'get_robot_status') {
            setRobotState(data.result);
          }
          
          // CRITICAL: Send response back to Gemini
          responses.push({
            name: call.name,
            id: call.id,
            response: data.result || { status: 'completed' }
          });
          
        } catch (error) {
          responses.push({
            name: call.name,
            id: call.id,
            response: { error: error.message }
          });
        }
      }
      
      // Send all responses back to complete the cycle
      if (responses.length > 0) {
        client.sendToolResponse({ functionResponses: responses });
        setTaskStatus('Ready');
      }
    };
    
    client.on('toolcall', handleToolCall);
    return () => client.off('toolcall', handleToolCall);
  }, [client]);

  // Quick action buttons
  const executeTask = (prompt: string) => {
    if (connected) {
      client.send({ text: prompt });
    }
  };

  return (
    <div className="aloha-control">
      <h2>🤖 ALOHA Robot Control</h2>
      
      <div className="status-panel">
        <p><strong>Status:</strong> {taskStatus}</p>
        <p><strong>Connected:</strong> {connected ? '✅' : '❌'}</p>
        {robotState && (
          <div>
            <strong>Robot State:</strong>
            <pre>{JSON.stringify(robotState, null, 2)}</pre>
          </div>
        )}
      </div>

      <div className="quick-actions">
        <button onClick={() => executeTask("What objects do you see on the table?")}>
          Detect Objects
        </button>
        <button onClick={() => executeTask("Pick up the red object with the right arm")}>
          Pick Red Object
        </button>
        <button onClick={() => executeTask("Move both arms to home position")}>
          Home Position
        </button>
        <button onClick={() => executeTask("Show me the current robot status")}>
          Get Status
        </button>
      </div>
      
      <div className="task-input">
        <input 
          type="text" 
          placeholder="Enter custom task..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              executeTask(e.target.value);
              e.target.value = '';
            }
          }}
        />
      </div>
    </div>
  );
}
```

#### 1.2 Add to Main App

Update `src/App.tsx` to include the ALOHA control:

```typescript
// Add import
import { ALOHAControl } from './components/aloha-control/ALOHAControl';

// Add to your main component tree
<div className="app-content">
  <ALOHAControl />
  {/* Your existing components */}
</div>
```

### Phase 2: Create ALOHA Bridge Server

#### 2.1 ALOHA Bridge (`aloha_bridge.py`)

Create this in your robot's workspace (based on your `glasses_detection_bridge.py`):

```python
#!/usr/bin/env python3
"""
Mobile ALOHA Robot Bridge for Gemini Live API
Handles tool calls from the React console and executes robot actions
"""

import asyncio
import json
import traceback
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions
import numpy as np

# ALOHA imports (adjust paths based on your setup)
try:
    # Try ACT++ structure first
    from aloha.real_env import RealEnv
    from aloha.constants import DT, START_ARM_POSE
except ImportError:
    # Fallback to direct imports
    import sys
    sys.path.append('/path/to/your/mobile-aloha')  # Adjust path
    from aloha_scripts.real_env import RealEnv
    from aloha_scripts.constants import DT, START_ARM_POSE

class ALOHABridge:
    def __init__(self):
        """Initialize Mobile ALOHA robot interface"""
        print("🤖 Initializing Mobile ALOHA...")
        
        # Initialize robot environment (from your imitate_episodes.py pattern)
        self.env = RealEnv(
            init_node=True,      # Initialize ROS node
            setup_robots=True,   # Setup both arms
            setup_base=False     # Skip mobile base for now
        )
        
        # Robot state tracking
        self.current_poses = {
            'left': None,
            'right': None
        }
        
        # Safety limits (in meters from robot base)
        self.workspace_limits = {
            'x': (0.15, 0.55),   # Forward reach
            'y': (-0.35, 0.35),  # Left/right reach  
            'z': (0.05, 0.45)    # Up/down reach
        }
        
        print("✅ ALOHA robot initialized successfully")

    def validate_position(self, x, y, z):
        """Check if position is within safe workspace"""
        limits = self.workspace_limits
        if not (limits['x'][0] <= x <= limits['x'][1] and
                limits['y'][0] <= y <= limits['y'][1] and
                limits['z'][0] <= z <= limits['z'][1]):
            raise ValueError(
                f"Position ({x:.3f}, {y:.3f}, {z:.3f}) outside safe workspace! "
                f"Limits: X{limits['x']}, Y{limits['y']}, Z{limits['z']}"
            )

    async def detect_objects(self, args):
        """Detect objects in current scene"""
        # Get current camera images
        obs = self.env._get_obs()
        images = obs.get('images', {})
        
        # For MVP: return hardcoded objects
        # Later: integrate with vision models or let Gemini's spatial understanding handle this
        detected_objects = {
            'red_cup': {
                'position': {'x': 0.35, 'y': 0.1, 'z': 0.12},
                'confidence': 0.85,
                'color': 'red'
            },
            'blue_bowl': {
                'position': {'x': 0.4, 'y': -0.15, 'z': 0.08},
                'confidence': 0.92,
                'color': 'blue'  
            },
            'banana': {
                'position': {'x': 0.3, 'y': 0.0, 'z': 0.15},
                'confidence': 0.78,
                'color': 'yellow'
            }
        }
        
        return {
            'objects': detected_objects,
            'camera_active': 'cam_high' in images,
            'timestamp': obs.get('timestamp', 'unknown')
        }

    async def move_to_position(self, args):
        """Move specified arm to target position"""
        arm = args.get('arm')
        x = float(args.get('x'))
        y = float(args.get('y')) 
        z = float(args.get('z'))
        
        # Safety check
        self.validate_position(x, y, z)
        
        # Get the appropriate robot arm
        if arm == 'left':
            bot = self.env.puppet_bot_left
        elif arm == 'right':
            bot = self.env.puppet_bot_right
        else:
            raise ValueError(f"Invalid arm: {arm}. Must be 'left' or 'right'")

        # Move to position (absolute coordinates)
        print(f"Moving {arm} arm to ({x:.3f}, {y:.3f}, {z:.3f})")
        
        # Use Interbotix API for Cartesian control
        success = bot.arm.set_ee_pose_components(
            x=x, y=y, z=z,
            roll=0.0, pitch=0.5, yaw=0.0,  # Keep gripper pointing down
            execute=True,
            moving_time=2.0,  # 2 second movement
            accel_time=0.5
        )
        
        # Update current pose tracking
        current_pose = bot.arm.get_ee_pose()
        self.current_poses[arm] = {
            'x': current_pose[0, 3],
            'y': current_pose[1, 3], 
            'z': current_pose[2, 3]
        }
        
        return {
            'success': success,
            'arm': arm,
            'target_position': {'x': x, 'y': y, 'z': z},
            'actual_position': self.current_poses[arm],
            'movement_time': 2.0
        }

    async def control_gripper(self, args):
        """Open or close gripper"""
        arm = args.get('arm')
        action = args.get('action')
        
        if arm == 'left':
            gripper = self.env.puppet_bot_left.gripper
        elif arm == 'right':
            gripper = self.env.puppet_bot_right.gripper
        else:
            raise ValueError(f"Invalid arm: {arm}")
            
        if action == 'open':
            gripper.open()
            print(f"Opening {arm} gripper")
        elif action == 'close':
            gripper.close() 
            print(f"Closing {arm} gripper")
        else:
            raise ValueError(f"Invalid action: {action}. Must be 'open' or 'close'")
            
        # Wait for movement completion
        await asyncio.sleep(1.0)
        
        return {
            'success': True,
            'arm': arm,
            'action': action,
            'gripper_state': 'open' if action == 'open' else 'closed'
        }

    async def get_robot_status(self, args):
        """Get current robot state"""
        status = {}
        
        for arm_name in ['left', 'right']:
            if arm_name == 'left':
                bot = self.env.puppet_bot_left
            else:
                bot = self.env.puppet_bot_right
                
            # Get current joint positions
            joint_positions = bot.arm.core.joint_states.position[:6]
            
            # Get end-effector pose
            ee_pose = bot.arm.get_ee_pose()
            
            status[arm_name] = {
                'joint_positions': joint_positions.tolist(),
                'end_effector': {
                    'x': float(ee_pose[0, 3]),
                    'y': float(ee_pose[1, 3]),
                    'z': float(ee_pose[2, 3])
                },
                'gripper_open': bot.gripper.core.joint_states.position[6] > 0.02
            }
            
        return {
            'arms': status,
            'timestamp': time.time(),
            'workspace_limits': self.workspace_limits
        }

    async def process_tool_call(self, data):
        """Process incoming tool calls from Gemini Live API"""
        name = data.get('name')
        args = data.get('args', {})
        call_id = data.get('id')
        
        print(f"🔧 Processing tool call: {name} with args: {args}")
        
        try:
            if name == 'detect_objects':
                result = await self.detect_objects(args)
            elif name == 'move_to_position':
                result = await self.move_to_position(args)
            elif name == 'control_gripper':
                result = await self.control_gripper(args)
            elif name == 'get_robot_status':
                result = await self.get_robot_status(args)
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

# Initialize bridge
print("🚀 Starting ALOHA Bridge Server...")
bridge = ALOHABridge()

async def handle_aloha_tool_call(request):
    """Handle HTTP requests from React console"""
    try:
        data = await request.json()
        print(f"📨 Received tool call: {data}")
        
        result = await bridge.process_tool_call(data)
        print(f"📤 Sending result: {result}")
        
        return web.json_response(result)
        
    except Exception as e:
        error_response = {
            'success': False, 
            'error': str(e),
            'call_id': data.get('id') if 'data' in locals() else None
        }
        print(f"❌ Request error: {error_response}")
        return web.json_response(error_response, status=500)

# Set up HTTP server (same pattern as glasses_detection_bridge)
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

if __name__ == '__main__':
    print("🌐 ALOHA Bridge server starting on http://0.0.0.0:8081")
    web.run_app(app, host='0.0.0.0', port=8081)
```

### Phase 3: Setup and Integration

#### 3.1 Environment Setup

On your robot computer, create the workspace:

```bash
# 1. Set up ROS environment (adjust for your ROS version)
source /opt/ros/humble/setup.bash  # or galactic/foxy
source ~/interbotix_ws/install/setup.bash

# 2. Install Python dependencies
pip install aiohttp aiohttp-cors numpy

# 3. Make sure your Mobile ALOHA packages are in Python path
export PYTHONPATH=$PYTHONPATH:~/your_aloha_workspace/src
```

#### 3.2 Launch Sequence

**Terminal 1 - Robot Hardware:**
```bash
# Start robot drivers (adjust launch file based on your setup)
ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
  robot_model:=vx300s \
  robot_name:=puppet_left \
  use_gripper:=true

ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
  robot_model:=vx300s \
  robot_name:=puppet_right \
  use_gripper:=true
```

**Terminal 2 - Camera Streams:**
```bash
# Start camera nodes (adjust based on your camera setup)
ros2 launch usb_cam usb_cam.launch.py camera_name:=cam_high
ros2 launch usb_cam usb_cam.launch.py camera_name:=cam_left_wrist  
ros2 launch usb_cam usb_cam.launch.py camera_name:=cam_right_wrist
```

**Terminal 3 - Python Bridge:**
```bash
cd ~/your_workspace
python aloha_bridge.py
```

**Terminal 4 - React Console (on your Mac):**
```bash
cd live-api-console
npm start
```

### Phase 4: Testing and Usage

#### 4.1 Basic Test Sequence

1. **Start all systems** as described above
2. **Open browser** to `http://localhost:3000`
3. **Connect to Gemini Live API** 
4. **Test basic commands**:
   - "What do you see on the table?"
   - "Show me the robot status"
   - "Move the right arm to position x=0.3, y=0.1, z=0.2"
   - "Open the left gripper"

#### 4.2 Complete Pick and Place Task

Voice command: **"Pick up the red cup with the right arm and place it in the blue bowl"**

Expected sequence:
1. Gemini calls `detect_objects()` → identifies objects and positions
2. Gemini calls `move_to_position(arm="right", x=0.35, y=0.1, z=0.25)` → moves above cup
3. Gemini calls `move_to_position(arm="right", x=0.35, y=0.1, z=0.12)` → lowers to cup
4. Gemini calls `control_gripper(arm="right", action="close")` → grasps cup  
5. Gemini calls `move_to_position(arm="right", x=0.35, y=0.1, z=0.25)` → lifts cup
6. Gemini calls `move_to_position(arm="right", x=0.4, y=-0.15, z=0.15)` → moves to bowl
7. Gemini calls `control_gripper(arm="right", action="open")` → releases cup

## 🔧 Troubleshooting

### Common Issues:

**1. ROS Connection Issues:**
```bash
# Check ROS topics
ros2 topic list | grep puppet
ros2 topic echo /puppet_left/joint_states
```

**2. Python Import Errors:**
```python
# Test ALOHA imports
python -c "from aloha.real_env import RealEnv; print('✅ Imports OK')"
```

**3. Bridge Connection:**
```bash
# Test bridge endpoint
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_robot_status", "args": {}, "id": "test"}'
```

**4. Camera Issues:**
```bash
# List cameras
v4l2-ctl --list-devices

# Test camera
ros2 run usb_cam usb_cam_node_exe --ros-args -p video_device:=/dev/video0
```

## 📈 Next Steps

1. **Improve Vision**: Replace hardcoded objects with real computer vision
2. **Add Safety**: Implement collision checking and emergency stops  
3. **Mobile Base**: Integrate the SLATE mobile base for navigation
4. **Task Planning**: Add multi-step task decomposition
5. **Learning**: Connect to ACT++ for demonstration learning

## 🎯 Key Advantages

- **Leverages existing infrastructure**: Uses your Live API console + Interbotix setup
- **Real-time interaction**: Voice commands execute immediately  
- **Spatial understanding**: Gemini 2.5's vision processes live video
- **Extensible**: Easy to add new tools and capabilities
- **Safe**: Built-in workspace limits and error handling

This setup gives you a powerful foundation for natural language robot control using Gemini's spatial reasoning capabilities!

<citations>
<document>
<document_type>WEB_PAGE</document_type>
<document_id>https://github.com/Interbotix/act_plus_plus/blob/main/act_plus_plus/imitate_episodes.py</document_id>
</document>
</citations>
