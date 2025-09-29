# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a voice-controlled Mobile ALOHA robot system using Google's Gemini 2.5 Live API with advanced spatial reasoning. The system enables trajectory-based manipulation through natural language, leveraging Gemini's spatial understanding for complex pick-and-place operations. Features multi-waypoint trajectories with gripper coordination, visual object detection, and scene analysis.

## Critical Commands

### Starting the System

1. **Start Robot Bridge** (Terminal 1):
```bash
cd /home/aloha/gemini-live/gemini-live-api-control
./run_bridge.sh
```

2. **Start Web Interface** (Terminal 2):
```bash
cd /home/aloha/gemini-live/gemini-live-api-control/live-api-console
npm start
```

### Development Commands

**React App (in live-api-console/):**
```bash
npm install          # Install dependencies
npm start           # Start dev server on port 3000
npm run build       # Build for production
npm test            # Run tests
```

**Python Bridge:**
```bash
# Dependencies (installed via run_bridge.sh)
pip3 install --user aiohttp aiohttp-cors numpy

# Test gripper controller directly
python3 example_gemini_integration.py

# Launch robot driver only (without bridge)
./minimal_launch.sh
```

### Testing Robot Control
```bash
# Test gripper without Gemini
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
python3 minimal_arm_control.py
```

## Architecture Overview

### System Flow
```
Voice Input → Gemini Live API → Tool Calls → Python Bridge → Robot Controller → ALOHA Hardware
     ↑                                              ↓
     └──────── Visual Feedback ← State Updates ────┘
```

### Key Components

**Frontend (React/TypeScript):**
- `src/lib/genai-live-client.ts` - Wrapper around Google's Live API, handles WebSocket connection to Gemini
- `src/lib/audio-recorder.ts` - Captures microphone audio, converts to PCM16 at 16kHz, handles resampling
- `src/components/aloha-control/ALOHAControl.tsx` - Main robot control UI with trajectory and spatial tools
- `src/components/control-tray/ControlTray.tsx` - Connection management, camera mode selector, frame merging

**Bridge Layer (Python):**
- `bridges/bridge_aloha_real.py` - HTTP server on port 8081, translates Gemini tool calls to robot commands
- Uses fire-and-forget pattern - returns immediately to avoid Gemini "Load failed" errors
- Launches robot driver subprocess automatically

**Robot Control (Python/ROS2):**
- `gripper_controller.py` - Thread-safe gripper control with 10Hz state monitoring
- `arm_controller.py` - Flexible arm control with auto-detection of radians/degrees, Cartesian control, safety constraints
- `camera_controller.py` - RealSense camera capture with correct serial number mapping
- `minimal_arm_control.py` - Direct arm control with proper sleep positions
- `minimal_launch.sh` - Launches only follower_left arm (not full ALOHA system)
- Uses current-based position control (300mA limit) for safe gripper operation
- Controllers share robot interface to avoid conflicts

### Critical Implementation Details

**Camera System:**
- Two Intel RealSense D405 cameras feed visual data to Gemini
- Camera Serial Mapping:
  - `130322273632` → `gripper_cam` (LEFT arm gripper camera)
  - `130322273629` → `top_cam` (overhead workspace view)
  - `130322270224` → `unused_cam` (right arm, not used)
- Camera modes available in UI:
  - **Merged View (Recommended)**: Single 1280x480 frame with both cameras side-by-side, labeled "LEFT GRIPPER" and "TOP VIEW"
  - **Both Cameras**: Sends separate frames from each camera
  - **Gripper Only**: Only gripper camera feed
  - **Top Only**: Only overhead camera feed
  - **No Camera**: Disables robot camera streaming
- Frame rate: 1 FPS (reduced from 2 FPS for bandwidth optimization)
- Frame merging done client-side using HTML canvas before sending to Gemini

**Audio Processing Pipeline:**
1. Browser captures audio at default sample rate (usually 48kHz)
2. AudioRecorder resamples to 16kHz for Gemini compatibility
3. Converts Float32Array to PCM16 format
4. Base64 encodes and streams via WebSocket

**Tool Functions (Priority Order):**
```typescript
// Trajectory and spatial tools (primary)
- move_arm_trajectory: Multi-waypoint paths with gripper coordination
- detect_and_target_object: Visual object detection and approach
- analyze_workspace: Scene analysis for spatial understanding

// Standard control tools
- move_arm: Single-point movements
- control_gripper: Open/close gripper
- get_arm_status / get_gripper_status: State queries
```

**Trajectory Format:**
```typescript
{
  "trajectory": [
    {"point": [x,y,z], "label": "approach", "gripper_action": "open"},
    {"point": [x,y,z], "label": "grasp", "gripper_action": "close"},
    {"point": [x,y,z], "label": "lift", "gripper_action": "maintain"}
  ],
  "speed": "medium"  // slow/medium/fast
}

// Fire-and-forget response pattern
client.on('toolCall', async (toolCall) => {
  // Call bridge but don't wait for result
  fetch('http://localhost:8081/aloha-tool-call', {
    method: 'POST',
    body: JSON.stringify(toolCall)
  });
  
  // Return empty response immediately
  client.sendToolResponse([{
    functionResponses: [{
      response: {},
      id: toolCall.id
    }]
  }]);
});
```

**State Structures:**
```python
# Gripper State
{
    "state": "open",  # open/closed/opening/closing/unknown
    "position_normalized": 0.8,  # 0.0 (closed) to 1.0 (open)
    "success": True
}

# Arm State
{
    "state": "idle",  # idle/moving/at_home/at_sleep/at_target/error
    "joints": [0.0, -0.96, 1.16, 0.0, -0.3, 0.0],  # radians
    "joints_degrees": [0.0, -55.0, 66.5, 0.0, -17.2, 0.0],
    "ee_position": {"x": 0.3, "y": 0.0, "z": 0.25},  # meters
    "pose": "ready",  # home/sleep/ready/null
    "success": True
}
```

## Environment Configuration

**Required Environment Variables:**
- `REACT_APP_GEMINI_API_KEY` - Set in `live-api-console/.env`

**ROS2 Environment:**
- Must source `/opt/ros/humble/setup.bash` before any robot operations
- Must source `~/interbotix_ws/install/setup.bash` for Interbotix packages

**Port Usage:**
- 3000: React development server
- 8081: Python bridge HTTP server

## Common Issues and Solutions

**"AudioContext.createMediaStreamSource: different sample-rate"**
- Fixed by using default AudioContext sample rate and resampling in software

**"Load failed" errors from Gemini**
- Use fire-and-forget pattern for tool responses
- Return empty response immediately, don't wait for robot action

**Gripper not moving**
- Check robot power and USB connection
- Verify ROS environment is sourced correctly
- Check bridge server is running on port 8081

**Arm not moving or "IK solution not found"**
- Ensure target position is within workspace limits
- Minimum z must be ≥ 0.1m (table level)
- Check joint limits aren't exceeded
- Verify arm controller initialized successfully

**No voice pickup**
- Check browser microphone permissions
- Look for volume indicator movement in UI
- Ensure not muted (check mic icon state)

## Robot Specifications

- Model: ViperX 300s (vx300s)
- Control Group: follower_left
- Arm: 6 DOF (waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate)
- Gripper Mode: current_based_position
- Current Limit: 300mA
- Sleep Position (wrist_angle): -1.57 radians (pointing up)
- Workspace Limits:
  - x, y: [-0.5, 0.5] meters
  - z: [0.1, 0.6] meters (minimum 0.1m for safety)
- Cameras:
  - 2x Intel RealSense D405 (gripper and overhead)
  - Resolution: 640x480 RGB @ 30fps capture, 1 FPS to Gemini
  - Merged view creates 1280x480 labeled frame

## Testing Checklist

When making changes:
1. Test gripper controller standalone: `python3 example_gemini_integration.py`
2. Test arm controller: `python3 test_arm_controller.py`
3. Verify bridge connectivity: `curl http://localhost:8081/status`
4. Check voice capture: Watch volume indicators in UI
5. Test tool calls: Monitor browser console for tool call events
6. Verify robot response: Check bridge terminal for action logs
7. Test trajectories:
   ```bash
   curl -X POST http://localhost:8081/aloha-tool-call \
     -H "Content-Type: application/json" \
     -d '{
       "name": "move_arm_trajectory",
       "args": {
         "trajectory": [
           {"point": [0.25, 0, 0.2], "label": "start", "gripper_action": "open"},
           {"point": [0.25, 0.1, 0.2], "label": "shift", "gripper_action": "close"},
           {"point": [0.25, 0, 0.25], "label": "lift", "gripper_action": "maintain"}
         ],
         "speed": "medium"
       }
     }'
   ```

## Arm Control Features

### Automatic Format Detection
- Joint angles > 2π (6.28) are auto-detected as degrees
- Joint angles ≤ 2π are treated as radians
- Normalized coordinates (0-1000) are converted to meters
- [y, x] format is converted to [x, y, z] automatically

### Named Poses
- `home`: All joints at 0 (straight up)
- `ready`: Standard working position
- `sleep`: Safe resting position

### Safety Features
- Workspace limits enforced
- Joint limits checked before movement  
- Minimum z=0.1m prevents table collision
- Smooth trajectory planning with configurable speed
- Wrist rotation limited when gripper is close to base (prevents self-collision)
- Special constraints when operating near table level (z < 0.15m)
- Trajectory execution aborts on first failure for safety

### Spatial Control Features

**Trajectory Execution:**
- Multi-waypoint paths with descriptive labels
- Gripper coordination at each waypoint
- Speed control (slow: 2.5s, medium: 1.5s, fast: 0.8s per move)
- Automatic [y,x] to [x,y,z] format conversion
- Sequential execution with safety checks

**Visual Understanding (Placeholders for future CV):**
- Object detection and targeting
- Workspace scene analysis
- Spatial relationship understanding
- Approach trajectory generation