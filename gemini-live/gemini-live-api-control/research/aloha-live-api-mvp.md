# 🤖 Mobile ALOHA + Gemini Live API: MVP Implementation Guide

## 🎯 Goal: "Pick Banana, Put in Bowl"
A complete guide to connect Gemini Live API vision/intelligence with Mobile ALOHA robot control for simple manipulation tasks.

## Architecture Overview

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  Gemini Live    │◄──────────────────►│  React Console   │
│  API (Cloud)    │     Tool Calls      │  (Browser)       │
└─────────────────┘                     └──────────────────┘
                                                │
                                          HTTP  │ Tool Calls
                                                ▼
                                        ┌──────────────────┐
                                        │  Python Bridge   │
                                        │  (Port 8081)     │
                                        └──────────────────┘
                                                │
                                          ROS2  │ Commands
                                                ▼
                                        ┌──────────────────┐
                                        │  Mobile ALOHA    │
                                        │  Robot           │
                                        └──────────────────┘
```

## ✅ What We Already Have (From Glasses Detection)

### 1. React Console (Working!)
- WebSocket connection to Gemini Live API
- Video streaming from webcam
- Tool calling mechanism
- Tool response handling

### 2. Python Bridge Pattern (Working!)
```python
# Current glasses_detection_bridge.py structure
async def handle_tool_call(request):
    data = await request.json()
    # Process tool call
    # Return response
```

### 3. Critical Lessons Learned
- **MUST send tool responses back** or model hangs
- **Don't interrupt model** - space prompts 10+ seconds apart
- **Configure BEFORE connecting**
- **Tell model it has eyes** - explicit video capability instructions

## 🔧 What We Need to Build

### 1. Tool Definitions for Gemini

```javascript
// In React console configuration
const robotTools = [
  {
    name: "detect_objects",
    description: "Identify objects and their positions in the video",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "move_to_position",
    description: "Move robot gripper to specific position",
    parameters: {
      type: "object",
      properties: {
        x: { type: "number", description: "X position in meters" },
        y: { type: "number", description: "Y position in meters" },
        z: { type: "number", description: "Z position in meters" }
      },
      required: ["x", "y", "z"]
    }
  },
  {
    name: "grip_object",
    description: "Close gripper to grasp object",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "release_object",
    description: "Open gripper to release object",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  },
  {
    name: "get_robot_state",
    description: "Get current robot position and gripper state",
    parameters: {
      type: "object",
      properties: {},
      required: []
    }
  }
];

// System instruction
const systemInstruction = `
You are controlling a Mobile ALOHA robot through visual input. 
You CAN SEE the video feed from the robot's camera.
Your task is to pick up objects and place them as instructed.
Use the provided functions to control the robot.
Call detect_objects first to understand the scene, then move_to_position, grip_object, etc.
Coordinates are in meters relative to the robot base (0,0,0).
`;
```

### 2. Python Bridge Server (`aloha_bridge.py`)

```python
import asyncio
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions
import json
from interbotix_xs_modules.arm import InterbotixManipulatorXS  # Correct import

class ALOHABridge:
    def __init__(self):
        # Initialize robot arms (Mobile ALOHA has two)
        self.left_arm = InterbotixManipulatorXS(
            robot_model="vx300s",
            robot_name="left_arm",
            # Additional params from ALOHA config
        )
        self.right_arm = InterbotixManipulatorXS(
            robot_model="vx300s", 
            robot_name="right_arm",
            # Additional params from ALOHA config
        )
        
        # Start with right arm for simplicity
        self.active_arm = self.right_arm
        
    async def process_tool_call(self, data):
        """Process incoming tool calls from Gemini"""
        name = data.get('name')
        args = data.get('args', {})
        call_id = data.get('id')
        
        try:
            if name == 'detect_objects':
                # For MVP, return hardcoded positions
                # Later: integrate with perception
                result = {
                    "banana": {"x": 0.3, "y": 0.1, "z": 0.15},
                    "bowl": {"x": 0.3, "y": -0.1, "z": 0.1}
                }
                
            elif name == 'move_to_position':
                x = float(args.get('x'))
                y = float(args.get('y'))
                z = float(args.get('z'))
                
                # Absolute move in base_link frame (no 'mode' arg needed)
                self.active_arm.arm.set_ee_pose_components(
                    x=x, y=y, z=z,
                    roll=0.0, pitch=0.0
                )
                result = {"status": "moved", "position": {"x": x, "y": y, "z": z}}
                
            elif name == 'grip_object':
                self.active_arm.gripper.close()
                result = {"status": "gripped"}
                
            elif name == 'release_object':
                self.active_arm.gripper.open()
                result = {"status": "released"}
                
            elif name == 'get_robot_state':
                # Get current end-effector pose (4x4 transform matrix)
                T_sb = self.active_arm.arm.get_ee_pose()
                result = {
                    "position": {"x": T_sb[0][3], "y": T_sb[1][3], "z": T_sb[2][3]},
                    "gripper_open": self.active_arm.gripper.is_open()
                }
                
            else:
                result = {"error": f"Unknown tool: {name}"}
                
            return {
                "success": True,
                "result": result,
                "call_id": call_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "call_id": call_id
            }

# HTTP Server setup (same pattern as glasses_detection_bridge.py)
bridge = ALOHABridge()

async def handle_tool_call(request):
    data = await request.json()
    print(f"Received tool call: {data}")
    
    result = await bridge.process_tool_call(data)
    print(f"Result: {result}")
    
    return web.json_response(result)

app = web.Application()
cors = setup(app, defaults={
    "*": ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*"
    )
})

app.router.add_post('/tool-call', handle_tool_call)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=8081)
```

### 3. React Component (`ALOHAControl.tsx`)

```typescript
// Based on GlassesDetectionFixed.tsx pattern
import { useEffect, useState, useRef } from 'react';
import { useLiveAPIContext } from '../../contexts/LiveAPIContext';

export function ALOHAControl() {
  const { client, setConfig, connected } = useLiveAPIContext();
  const [robotState, setRobotState] = useState(null);
  const [taskStatus, setTaskStatus] = useState('Waiting...');
  
  // Configure before connection
  useEffect(() => {
    setConfig({
      tools: [{ functionDeclarations: robotTools }],
      systemInstruction: systemInstruction,
    });
  }, []);
  
  // Handle tool calls
  useEffect(() => {
    const handleToolCall = async (toolCall) => {
      const responses = [];
      
      for (const call of toolCall.functionCalls) {
        // Send to Python bridge
        const result = await fetch('http://localhost:8081/tool-call', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: call.name,
            args: call.args,
            id: call.id,
          }),
        });
        
        const data = await result.json();
        
        // CRITICAL: Send response back to Gemini
        responses.push({
          name: call.name,
          id: call.id,
          response: data.result || { status: 'ok' }
        });
        
        // Update UI
        setTaskStatus(`Executed: ${call.name}`);
      }
      
      // Send responses back to complete the cycle
      if (responses.length > 0) {
        client.sendToolResponse({ functionResponses: responses });
      }
    };
    
    client.on('toolcall', handleToolCall);
    return () => client.off('toolcall', handleToolCall);
  }, [client]);
  
  // Send task prompts
  const startTask = () => {
    client.send({ 
      text: 'Pick up the banana and put it in the bowl' 
    });
  };
  
  // Render UI...
}
```

## 📋 Implementation Steps

### Phase 1: Setup Environment
1. [ ] Install ROS2 and Interbotix packages on robot computer
2. [ ] Verify robot control with test scripts
3. [ ] Set up camera (use single arm camera or center camera)
4. [ ] Test coordinate system and movement ranges

### Phase 2: Adapt Existing Code
1. [ ] Copy `GlassesDetectionFixed.tsx` → `ALOHAControl.tsx`
2. [ ] Update tool definitions for robot control
3. [ ] Copy `glasses_detection_bridge.py` → `aloha_bridge.py`
4. [ ] Add Interbotix control code

### Phase 3: Integration
1. [ ] Test tool calls from React to Python bridge
2. [ ] Test robot movement commands
3. [ ] Add coordinate transformation if needed
4. [ ] Test full pick-and-place sequence

## ✅ Resolved Technical Details

### 1. Interbotix Absolute Positioning
**Answer**: `set_ee_pose_components()` DOES absolute positioning by default!
- Coordinates are in meters relative to robot's `base_link` frame
- No special 'mode' parameter needed (remove that from code)
- For relative moves, use: `set_ee_cartesian_trajectory(x=dx, y=dy, z=dz, yaw=dyaw)`

### 2. Coordinate Frame Alignment (Hand-Eye Calibration)
**Solution**: Transform camera coordinates to robot base using calibration matrix

**Calibration Process**:
1. **Camera Intrinsics**: Calibrate with checkerboard (OpenCV or ROS `camera_calibration`)
2. **Hand-Eye Calibration**:
   - For center camera (Eye-to-Base): Fix ArUco marker on gripper, move to N positions
   - Record pairs: robot pose (`get_ee_pose()`) + marker detection
   - Use OpenCV's `calibrateHandEye()` or ROS2 `handeye_calibration_ros2`
3. **Apply Transform**: `p_base = T_base_camera @ p_camera`

**Quick MVP Hack**: If table is flat at known height Z:
- Map pixel (u,v) → 3D ray → intersect plane at z=Z_table
- Good enough for banana picking!

### 3. Gripper Control API (Confirmed)
**Exact Syntax**:
```python
self.active_arm.gripper.close()  # Close gripper
self.active_arm.gripper.open()   # Open gripper
```
These are blocking calls (wait for completion).

### 4. Which Camera to Use
**MVP Recommendation**: **Center camera (fixed view)**
- Simpler calibration (done once)
- Stable scene view (bowl doesn't move)
- No self-occlusion issues

**Later**: Add arm camera for close-up precision

### 5. Safety Limits
**Software Bounding Box** (add to bridge):
```python
# Define safe workspace
WORKSPACE_LIMITS = {
    'x': (0.15, 0.45),  # meters from base
    'y': (-0.3, 0.3),
    'z': (0.05, 0.4)
}

def validate_position(x, y, z):
    if not (WORKSPACE_LIMITS['x'][0] <= x <= WORKSPACE_LIMITS['x'][1] and
            WORKSPACE_LIMITS['y'][0] <= y <= WORKSPACE_LIMITS['y'][1] and
            WORKSPACE_LIMITS['z'][0] <= z <= WORKSPACE_LIMITS['z'][1]):
        raise ValueError(f"Position ({x}, {y}, {z}) outside safe workspace!")
```

**ROS Configuration**: Adjust velocity/acceleration in motor config `.yaml` files
**Advanced**: Use MoveIt for collision checking (not needed for MVP)

## 🚀 Quick Start Commands

```bash
# Terminal 1: Start React console
cd live-api-console
npm start

# Terminal 2: Start Python bridge
python3 aloha_bridge.py

# Terminal 3: (On robot) Start ROS2 nodes
ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
  robot_model:=vx300s robot_name:=right_arm

# Terminal 4: Monitor ROS2 topics
ros2 topic echo /right_arm/joint_states
```

## 📊 Expected Sequence

1. **Human**: "Put the banana in the bowl"
2. **Gemini**: Sees video → calls `detect_objects()`
3. **Bridge**: Returns object positions
4. **Gemini**: calls `move_to_position(x=0.3, y=0.1, z=0.15)`
5. **Robot**: Moves to banana position
6. **Gemini**: calls `grip_object()`
7. **Robot**: Closes gripper
8. **Gemini**: calls `move_to_position(x=0.3, y=-0.1, z=0.2)` (above bowl)
9. **Robot**: Moves to bowl
10. **Gemini**: calls `release_object()`
11. **Robot**: Opens gripper
12. **Success**: Banana in bowl!

## ⚠️ Important Notes

1. **Latency is OK**: 2-10 second delays are fine for task-level commands
2. **No Real-time Control**: We're NOT doing microsecond control loops
3. **Simple is Better**: Start with one arm, one camera, simple tasks
4. **Tool Responses Required**: Always send responses back to Gemini
5. **Safety First**: Test movements slowly, set conservative limits

## 🔗 References

- [Mobile ALOHA GitHub](https://github.com/MarkFzp/mobile-aloha)
- [Interbotix Documentation](https://docs.trossenrobotics.com/interbotix_xsarms_docs/)
- [Gemini Live API Docs](https://ai.google.dev/api/streaming)
- Our working example: `GlassesDetectionFixed.tsx` + `glasses_detection_bridge.py`

---

**This is our MVP**: Simple task-level commands via Gemini's vision, executed by Mobile ALOHA. No heart surgery, just banana manipulation! 🍌