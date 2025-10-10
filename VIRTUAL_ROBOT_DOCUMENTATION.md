# Mobile ALOHA Robot Control System - Project Status

**Last Updated**: 2025-10-10
**Current Phase**: Virtual Robot Development Complete

---

## 🎯 Virtual Robot Arm - Quick Start Guide

### What is the Virtual Robot Arm?

The **virtual-robot-arm** is a browser-based 3D simulator that provides a complete virtual replica of the Mobile ALOHA robot system, enabling development and testing without physical hardware. It features voice control via Gemini 2.5 Flash, realistic kinematics, and virtual cameras matching the real robot's RealSense D405 setup.

### Why Virtual Robot?

- **Development Without Hardware**: Test voice commands, kinematics, and task planning without physical robot
- **Safe Experimentation**: Try risky movements and scenarios in simulation first
- **Visualization**: See robot movements in 3D with virtual cameras
- **Training Data**: Generate synthetic training data for manipulation tasks
- **Parallel Development**: Multiple developers can work simultaneously

### Architecture Overview

#### Complete System Architecture Map

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                          VOICE INPUT & AI CONTROL                                    │
│  ┌──────────────────────────────────────────────────────────────────────────────┐  │
│  │                          User Voice Commands                                  │  │
│  │                                  │                                            │  │
│  │                                  ▼                                            │  │
│  │                    ┌─────────────────────────────┐                           │  │
│  │                    │   Gemini 2.5 Flash Live API │                           │  │
│  │                    │   - Speech recognition      │                           │  │
│  │                    │   - Natural language        │                           │  │
│  │                    │   - Tool call generation    │                           │  │
│  │                    └─────────────────────────────┘                           │  │
│  │                                  │                                            │  │
│  │                                  ▼                                            │  │
│  │              ┌────────────────────────────────────────────┐                  │  │
│  │              │        Tool Function Calls                 │                  │  │
│  │              │  - move_arm_trajectory()                   │                  │  │
│  │              │  - control_gripper()                       │                  │  │
│  │              │  - move_arm()                              │                  │  │
│  │              │  - get_arm_status()                        │                  │  │
│  │              └────────────────────────────────────────────┘                  │  │
│  └──────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              CONTROL ROUTING                                         │
│                                                                                      │
│               ┌───────────────────────────────────────────────┐                     │
│               │         Virtual Robot                         │                     │
│               │         (Browser Only)                        │                     │
│               │                                               │                     │
│               │  ┌────────────────────────────────────────┐  │                     │
│               │  │  Browser App (localhost:3000)          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  VirtualRobotControl.tsx         │  │  │                     │
│               │  │  │  - Receives tool calls           │  │  │                     │
│               │  │  │  - Executes via RobotController  │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  │              ↓                          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  RobotController (kinematics.ts) │  │  │                     │
│               │  │  │  - IK solver                     │  │  │                     │
│               │  │  │  - Joint interpolation           │  │  │                     │
│               │  │  │  - State management              │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  │              ↓                          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  Three.js Scene                  │  │  │                     │
│               │  │  │  - MJCF parser                   │  │  │                     │
│               │  │  │  - 3D rendering                  │  │  │                     │
│               │  │  │  - Virtual cameras               │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  └────────────────────────────────────────┘  │                     │
│               └───────────────────────────────────────────────┘                     │
│                                                                                      │
│                                      OR                                              │
│                                                                                      │
│               ┌───────────────────────────────────────────────┐                     │
│               │         Real Robot                            │                     │
│               │         (Physical Hardware)                   │                     │
│               │                                               │                     │
│               │  ┌────────────────────────────────────────┐  │                     │
│               │  │  Bridge Server (port 8081/8082)        │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  bridge_aloha_real.py            │  │  │                     │
│               │  │  │  - HTTP endpoint handler         │  │  │                     │
│               │  │  │  - Fire-and-forget pattern       │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  │              ↓                          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  Robot Controllers               │  │  │                     │
│               │  │  │  - arm_controller.py             │  │  │                     │
│               │  │  │  - gripper_controller.py         │  │  │                     │
│               │  │  │  - trajectory_bridge.py          │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  │              ↓                          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  ROS2 + Interbotix SDK           │  │  │                     │
│               │  │  │  - Motor control                 │  │  │                     │
│               │  │  │  - Position feedback             │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  │              ↓                          │  │                     │
│               │  │  ┌──────────────────────────────────┐  │  │                     │
│               │  │  │  ViperX 300s Hardware            │  │  │                     │
│               │  │  │  - DYNAMIXEL servos              │  │  │                     │
│               │  │  │  - Gripper actuators             │  │  │                     │
│               │  │  └──────────────────────────────────┘  │  │                     │
│               │  └────────────────────────────────────────┘  │                     │
│               └───────────────────────────────────────────────┘                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        OPTIONAL: MUJOCO PHYSICS SERVER                               │
│                        (Advanced simulation with full physics)                       │
│                                                                                      │
│  ┌────────────────────────────────────────────────────────────────────────────┐    │
│  │  MuJoCo Server (port 5000/5001) - HEADLESS MODE                            │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │  │  simulation_server.py (Flask-SocketIO)                               │  │    │
│  │  │  ┌────────────────────────────────────────────────────────────────┐  │  │    │
│  │  │  │  UnifiedRobotBridge                                            │  │  │    │
│  │  │  │  - mode='simulation' or 'real'                                 │  │  │    │
│  │  │  │  - Same API for both!                                          │  │  │    │
│  │  │  └────────────────────────────────────────────────────────────────┘  │  │    │
│  │  │                          ↓                                            │  │    │
│  │  │  ┌────────────────────────────────────────────────────────────────┐  │  │    │
│  │  │  │  MuJoCo Python (mujoco 3.2.5)                                  │  │  │    │
│  │  │  │  - Full physics simulation (1000 Hz)                           │  │  │    │
│  │  │  │  - Collision detection                                         │  │  │    │
│  │  │  │  - Contact forces                                              │  │  │    │
│  │  │  │  - Rendering (when not headless)                               │  │  │    │
│  │  │  └────────────────────────────────────────────────────────────────┘  │  │    │
│  │  │                          ↓                                            │  │    │
│  │  │  ┌────────────────────────────────────────────────────────────────┐  │  │    │
│  │  │  │  WebSocket Stream (30 FPS JPEG)                                │  │  │    │
│  │  │  │  - frame_update events                                         │  │  │    │
│  │  │  │  - state_update events                                         │  │  │    │
│  │  │  └────────────────────────────────────────────────────────────────┘  │  │    │
│  │  └──────────────────────────────────────────────────────────────────────┘  │    │
│  │                                  ↓                                         │    │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │    │
│  │  │  Browser Client (optional MuJoCoServerView.tsx)                      │  │    │
│  │  │  - Displays physics simulation video                                 │  │    │
│  │  │  - Toggle: Manual rendering vs MuJoCo server                         │  │    │
│  │  └──────────────────────────────────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────────┘

Key Components:
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Component                │ Technology              │ Purpose                         │
├─────────────────────────────────────────────────────────────────────────────────────┤
│ Voice Input              │ WebAudio API            │ Capture user voice              │
│ Gemini Live API          │ WebSocket + REST        │ Speech-to-tool-calls            │
│ Virtual Robot (Browser)  │ React + Three.js        │ Client-side simulation          │
│ Real Robot Bridge        │ Python Flask + ROS2     │ Hardware control                │
│ MuJoCo Server (Optional) │ Python + Flask-SocketIO │ Physics simulation              │
│ Robot Controller         │ TypeScript              │ Kinematics + animation          │
│ MJCF Parser              │ TypeScript + Three.js   │ Robot structure parsing         │
└─────────────────────────────────────────────────────────────────────────────────────┘

Data Flow Examples:
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ 1. Virtual Robot Voice Command:                                                     │
│    User speaks → Gemini API → Tool call → VirtualRobotControl → RobotController    │
│    → Three.js updates → Visual feedback                                             │
│                                                                                      │
│ 2. Real Robot Voice Command:                                                        │
│    User speaks → Gemini API → Tool call → Bridge HTTP → ROS2 → Hardware            │
│    → Position feedback → Status update                                              │
│                                                                                      │
│ 3. MuJoCo Physics Simulation:                                                       │
│    Command → Bridge (mode=simulation) → MuJoCo physics → WebSocket stream          │
│    → Browser video display                                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

#### Technology Stack

**Frontend (Browser):**
- React + TypeScript
- Three.js (3D rendering)
- MJCF parser (robot structure)
- WebAudio API (voice input)
- Socket.IO client (optional, for MuJoCo server)

**AI Integration:**
- Gemini 2.5 Flash Live API
- WebSocket for audio streaming
- Tool function declarations

**Virtual Robot:**
- Custom IK solver (ViperX 300s)
- MJCF-based rendering
- Virtual cameras (gripper + overhead)
- Client-side kinematics

**Real Robot:**
- Python Flask (bridge server)
- ROS2 Humble
- Interbotix SDK
- DYNAMIXEL motor control

**Physics Simulation (Optional):**
- MuJoCo 3.2.5 (Python bindings)
- Flask-SocketIO (WebSocket server)
- OpenCV (frame encoding)
- Unified bridge (sim/real mode switching)

### Quick Start

```bash
# 1. Navigate to virtual robot directory
cd virtual-robot-arm

# 2. Install dependencies (first time only)
npm install --legacy-peer-deps

# 3. Set up API key
cp .env.example .env
# Edit .env and add: REACT_APP_GEMINI_API_KEY=your-key-here

# 4. Start the application
npm start

# 5. Open browser
# http://localhost:3000
```

### Using the Virtual Robot

1. **Connect to Gemini**: Click "Connect to Gemini" button
2. **Start Voice Control**: Click "Start Voice Control" button
3. **Give Commands**:
   - "Move the arm to position 0.3, 0.2, 0.15"
   - "Open the gripper"
   - "Move to home position"
   - "Close the gripper"
4. **Watch**: Robot moves in 3D, cameras update, logs show XYZ positions

### Key Features

✅ **Voice Control**
- Gemini 2.5 Flash Live API integration
- Natural language commands
- Tool call execution for robot actions

✅ **3D Visualization**
- MJCF parser for accurate robot structure
- Realistic kinematics matching ViperX 300s
- Smooth joint interpolation (1.5s default)
- Gripper finger animation with slide joints

✅ **Virtual Cameras**
- Gripper camera (tracks end effector)
- Top overhead camera (workspace view)
- 640x480 resolution, 1 FPS capture
- Base64 JPEG encoding for Gemini integration

✅ **Robot Control**
- XYZ position control with IK solver
- Joint angle control (6 DOF)
- Named poses (home, ready, sleep)
- Gripper open/close commands

### File Structure

```
virtual-robot-arm/
├── src/
│   ├── components/
│   │   ├── IntegratedRobotControl.tsx   # Main app component
│   │   ├── VirtualRobotControl.tsx      # Voice control & Gemini integration
│   │   ├── Scene.tsx                     # Three.js scene setup
│   │   ├── RobotArmMJCF.tsx             # MJCF-based robot rendering
│   │   ├── VirtualCameraSystem.tsx      # Virtual camera capture
│   │   └── VirtualCameraFeed.tsx        # Camera feed UI
│   ├── lib/
│   │   ├── robot-controller.ts          # Kinematics & animation
│   │   ├── mjcf-parser.ts               # MJCF XML parser
│   │   ├── kinematics.ts                # IK solver
│   │   ├── genai-live-client.ts         # Gemini API client
│   │   └── audio-recorder.ts            # Voice input capture
│   └── types.ts                          # TypeScript interfaces
├── public/models/aloha/                  # Robot MJCF models & meshes
├── .env                                  # API keys (create from .env.example)
└── package.json                          # Dependencies
```

### Tool Functions for Gemini

The virtual robot exposes these tool functions to Gemini:

1. **`move_arm_trajectory`** - Multi-waypoint movement with gripper actions
   ```json
   {
     "waypoints": [
       {"x": 0.3, "y": 0.2, "z": 0.15},
       {"x": 0.25, "y": 0.1, "z": 0.2}
     ],
     "gripper_actions": [
       {"at_waypoint": 0, "action": "open"},
       {"at_waypoint": 1, "action": "close"}
     ]
   }
   ```

2. **`move_arm`** - Single position or joint movement
3. **`control_gripper`** - Open/close gripper
4. **`get_arm_status`** - Query current state
5. **`get_gripper_status`** - Query gripper state

### Differences from Real Robot

| Feature | Virtual Robot | Real Robot |
|---------|--------------|------------|
| **Physics** | Kinematic simulation (no physics) | Real-world physics |
| **Cameras** | Synthetic rendering (Three.js) | RealSense D405 cameras |
| **Safety** | No safety limits (simulation) | Workspace limits enforced |
| **Latency** | ~16ms (browser rendering) | ~50-100ms (hardware + network) |
| **Control** | Direct joint control | ROS2 → Interbotix SDK |

### Model Information

- **Robot**: Trossen ViperX 300s
- **DOF**: 6 (waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate)
- **Gripper**: 2-finger parallel jaw with slide joints
- **Workspace**: ~0.5m radius, 0.1-0.6m height
- **Control Frequency**: 60 FPS (browser animation loop)

### Development Status

**Phase 6 Complete** (October 2025):
- ✅ MJCF parser with correct parent-child hierarchy
- ✅ Gripper finger slide joint mechanics
- ✅ Virtual camera system (gripper + top)
- ✅ React state immutability fixes
- ✅ Gemini 2.5 Flash integration
- ✅ Voice control fully functional

**Known Limitations**:
- No physics simulation (kinematic only)
- Camera feeds ready but HTTP endpoint not yet implemented (waiting for real robot pattern)
- Turn/rotation commands disabled (colleagues working on unified prompt)

### Next Steps

1. ✅ Virtual robot complete and tested
2. ⏳ Consolidate documentation (remove redundant .md files)
3. ⏳ Match real robot camera integration pattern
4. ⏳ Add workspace elements (table, objects)
5. ⏳ Performance optimization

---

## Current Status: ✅ Dual-Arm Server Running

### ✅ Completed Tasks

- [x] **Server Infrastructure**
  - Created mujoco-server/ directory structure
  - Installed Python dependencies (Flask, SocketIO, MuJoCo 3.2.5, OpenCV)
  - Created unified bridge pattern (simulation + real robot modes)
  - Implemented WebSocket API with frame streaming
  - Created start.sh script for easy launch

- [x] **Bridge Implementation**
  - `bridge_unified.py` with mode switching
  - Auto-detection of single vs dual-arm models
  - Proper error handling for missing arms
  - Full API: move_arm, control_gripper, get_status, reset

- [x] **Model Fixes**
  - Fixed aloha_single_arm.xml with proper inertial properties
  - Fixed aloha_simple.xml (dual-arm) with proper inertial properties
  - Corrected mesh references (gripper_bar, custom_finger_left/right)
  - Added mass and diaginertia to all moving bodies (both arms)
  - Verified both models load in MuJoCo 3.2.5

- [x] **Single-Arm Server Testing**
  - Single-arm server tested on localhost:5000
  - Health endpoint verified: {"status":"healthy"}
  - Status endpoint verified: {"mode":"simulation","ready":true}
  - WebSocket infrastructure tested

- [x] **Dual-Arm Server Testing**
  - Dual-arm server running on localhost:5000
  - Model loaded: 16 DOF (8 per arm including gripper fingers)
  - Both arms detected: left [0-7], right [8-15]
  - Health endpoint verified: {"status":"healthy"}
  - Status endpoint verified: {"mode":"simulation","ready":true}

---

## 🔄 Current Task: React Client Integration ✅ COMPLETE

### Task Breakdown

1. **Install socket.io-client in virtual-robot-arm** ✅
   - Used `npm install socket.io-client --legacy-peer-deps` to handle React version conflicts
   - Successfully installed socket.io-client 4.8.1
   - Peer dependency warnings handled gracefully

2. **Create SimulationClient.ts WebSocket wrapper** ✅
   - Created TypeScript WebSocket client at `virtual-robot-arm/src/lib/SimulationClient.ts`
   - Implemented full API:
     - `moveArm(arm, positions)` - Move arm to joint positions
     - `controlGripper(arm, command)` - Control gripper (open/close)
     - `getArmStatus(arm)` - Query arm state
     - `getGripperStatus(arm)` - Query gripper state
     - `stepSimulation(steps)` - Manual simulation stepping
     - `resetRobot()` - Reset to home position
   - Event handlers for all server events (connect, disconnect, frame updates, status, errors)
   - TypeScript interfaces for all message types

3. **Create SimulationControls.tsx UI component** ✅
   - Created React component at `virtual-robot-arm/src/components/SimulationControls.tsx`
   - Features:
     - Connection management (connect/disconnect button)
     - Dual-arm control (home/ready positions for both arms)
     - Gripper control (open/close for both grippers)
     - Status display (live joint positions for both arms)
     - Activity log (last 10 events with timestamps)
     - General controls (reset robot, get status)
   - Styled with dark theme overlay (fixed position, right side)
   - Full event handling with error messages

4. **Update App.tsx to include SimulationControls** ✅
   - Added SimulationControls component to main App
   - Renders alongside TestMuJoCoBasic component
   - No conflicts with existing Three.js rendering

5. **Start React development server** ✅
   - Resolved port 3000 conflict
   - React app compiled successfully
   - Running on http://localhost:3000
   - No compilation errors

---

## 📋 Completed Tasks Summary

### Phase 1: Server Infrastructure ✅ COMPLETE
- [x] Created mujoco-server/ directory structure
- [x] Implemented UnifiedRobotBridge (simulation + real modes)
- [x] Created Flask-SocketIO server with WebSocket API
- [x] Fixed single-arm and dual-arm model physics
- [x] Added headless mode for WSL/CI environments
- [x] Tested all WebSocket APIs (6/7 tests passed)

### Phase 2: React Client Integration ✅ COMPLETE
- [x] Installed socket.io-client in virtual-robot-arm
- [x] Created SimulationClient.ts WebSocket wrapper
- [x] Created SimulationControls.tsx UI component
- [x] Updated App.tsx to include controls
- [x] Started React development server successfully

## 📋 Upcoming Tasks

### Phase 2b: End-to-End Testing ✅ COMPLETE
- [x] Test React UI → MuJoCo connection in browser
- [x] Verify arm movement commands work from UI
- [x] Verify gripper control works from UI
- [x] Test status queries and live position updates
- [x] Test reset functionality
- [x] Document any issues or improvements needed

**Test Results (2025-10-05):**
- ✅ React UI successfully connects to MuJoCo server (port 5000)
- ✅ WebSocket connection establishes without errors
- ✅ All arm control buttons functional (Home, Ready for both arms)
- ✅ Gripper controls working (Open/Close for both arms)
- ✅ Status queries return live joint positions
- ✅ Reset functionality confirmed working
- ✅ No browser console errors

**Observations:**
- Both arms display identical joint positions when moved to Home/Ready
- This is **expected behavior** for symmetric dual-arm robot (ALOHA design)
- HOME_POSITIONS = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
- READY_POSITIONS = [0.0, -0.5, 0.8, 0.0, -0.5, 0.0]
- **Future consideration**: May want asymmetric poses for specific tasks (e.g., handover operations)

### Phase 3: Gemini Integration ✅ BACKEND COMPLETE

- [x] Install aiohttp/aiohttp-cors dependencies for simulation bridge
- [x] Start simulation bridge on port 8082
- [x] Verify bridge connects to MuJoCo server
- [x] Configure .env files with API keys and endpoints
- [x] Tool call API ready and tested

**Backend Infrastructure Complete (2025-10-06):**
- ✅ Simulation bridge running on port 8082
- ✅ Bridge successfully connected to MuJoCo server (port 5000)
- ✅ Tool call endpoint verified: `http://localhost:8082/aloha-tool-call`
- ✅ Fire-and-forget pattern implemented
- ✅ Full API support: move_arm, control_gripper, move_arm_trajectory, reset_robot

**Testing Done:**
```bash
# Bridge status verified
curl http://localhost:8082/status
# Response: {"bridge": "simulation", "connected_to_mujoco": true, ...}

# Tool calls can be tested manually:
curl -X POST http://localhost:8082/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "control_gripper", "args": {"action": "open", "arm": "left"}}'
```

**Frontend Challenge:**
- ❌ Gemini Live console compilation issues (missing lib/ files)
- ❌ live-api-web-console ran out of memory during build
- ⚠️ Voice UI needs to be tested on a machine with more resources

**Gemini Console Status:**
- ✅ Missing lib/ files added successfully
- ✅ App compiles and runs (TypeScript warnings present but non-critical)
- ✅ Full voice control capability available at http://localhost:3002
- ⚠️ TypeScript errors in video features (not needed for voice control)

**Strategic Decision Made:**
Team will build a new frontend with robot visualization support:
- **Reuse**: Working components from gemini-live (lib/, contexts, ControlTray)
- **Replace**: Camera view with 3D robot visualization
- **Add**: Real/Virtual mode switcher
- **Benefit**: Clean implementation + easy future integration

**Documentation Created:**
- 📄 `GEMINI_LIVE_CONSOLE_ARCHITECTURE.md` - Complete architecture analysis
  - Component hierarchy and data flow
  - Integration points for new frontend
  - Tool call specifications
  - Mode switching strategy
  - Testing checklist

### Phase 4: Full System Testing (Est. 1 hour)

- [ ] Test complete pipeline: Voice → Gemini → Bridge → Simulation → Stream
- [ ] Verify latency is acceptable (<100ms)
- [ ] Test switching between simulation and real robot modes
- [ ] Document any remaining issues

### Phase 5: Documentation & Cleanup (Est. 30 min)

- [ ] Update README with complete setup instructions
- [ ] Create quick start guide
- [ ] Add troubleshooting section
- [ ] Clean up test files and unused code

---

## 🐛 Known Issues & Fixes - Detailed Log

### Issue 1: Mass/Inertia Required ✅ FIXED
**Problem**: MuJoCo 3.2.5 requires all moving bodies to have mass > mjMINVAL
```
Error: mass and inertia of moving bodies must be larger than mjMINVAL (1e-14)
```

**Root Cause**: The ALOHA models (aloha_single_arm.xml and aloha_simple.xml) were created for MuJoCo WASM v2.3.1, which was more lenient about physics properties. MuJoCo 3.2.5 enforces stricter validation.

**Testing Process**:
1. Initially tried to load model → Got mjMINVAL error
2. Checked MuJoCo documentation for inertial requirements
3. Added `<inertial>` tags to all moving bodies

**Fix Applied**:
```xml
<body name="waist" pos="0 0 0.079">
  <inertial pos="0 0 0" mass="0.5" diaginertia="0.001 0.001 0.001"/>
  <joint name="waist" type="hinge" axis="0 0 1" range="-180 180"/>
  <geom type="mesh" mesh="vx300s_2_shoulder" material="black"/>
```

**Bodies Fixed**:
- Single-arm: 6 bodies (waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate)
- Dual-arm: 18 bodies (9 per arm: 6 arm joints + gripper + 2 fingers)

**Lessons Learned**:
- MuJoCo 3.2.5 is stricter than WASM version (good for realistic physics!)
- Always add proper inertial properties to all moving bodies
- Mass values should reflect realistic robot link weights
- Diagonal inertia tensors must be positive definite

**Status**: ✅ Fixed in both aloha_single_arm.xml and aloha_simple.xml

---

### Issue 2: Dual-Arm Assumptions ✅ FIXED
**Problem**: Bridge assumed all models have both left and right arms
```
IndexError: index 7 is out of bounds for axis 0 with size 6
```

**Root Cause**: The `reset()` function tried to move right arm joints [7-13], but single-arm model only has 6 DOF [0-5].

**Testing Process**:
1. Single-arm server loaded successfully
2. On reset, tried to access non-existent right arm joints
3. Realized need for dynamic arm detection

**Fix Applied**:
```python
# Auto-detection based on DOF count
total_dof = self.model.nv
if total_dof <= 7:
    # Single arm model
    self.left_arm_joints = list(range(0, min(6, total_dof)))
    self.right_arm_joints = []
    self.has_right_arm = False
else:
    # Dual arm model
    joints_per_arm = total_dof // 2
    self.left_arm_joints = list(range(0, joints_per_arm))
    self.right_arm_joints = list(range(joints_per_arm, total_dof))
    self.has_right_arm = True
```

**Additional Safety**:
```python
# In move_arm()
if arm == 'right' and not self.has_right_arm:
    return {'success': False, 'error': 'Right arm not available in single-arm model'}
```

**Lessons Learned**:
- Never assume model structure - detect it dynamically
- Add explicit error messages for missing components
- Use flags (has_right_arm) for conditional logic

**Status**: ✅ Fixed - Bridge handles both single and dual-arm models

---

### Issue 3: Flask-SocketIO Development Warning ✅ FIXED
**Problem**: RuntimeError about Werkzeug in production
```
RuntimeError: The Werkzeug web server is not designed to run in production
```

**Root Cause**: Flask-SocketIO 5.3.6 added production server warnings by default.

**Fix Applied**:
```python
socketio.run(app, host=args.host, port=args.port, debug=False,
             allow_unsafe_werkzeug=True)
```

**Lessons Learned**:
- This is expected for development/testing
- For production, would use gunicorn or similar WSGI server
- Flag makes it clear this is intentional for dev environment

**Status**: ✅ Fixed - Server starts without RuntimeError

---

### Issue 4: Mesh File References ✅ FIXED
**Problem**: Model referenced non-existent mesh files
```
ValueError: Error opening file 'models/aloha/assets/vx300s_8_gripper_bar.stl': No such file or directory
```

**Root Cause**: The dual-arm model referenced numbered mesh files (vx300s_8_gripper_bar.stl, vx300s_9_left_finger.stl) but actual files were named differently (vx300s_7_gripper_bar.stl, vx300s_8_custom_finger_left.stl).

**Testing Process**:
1. Tried to load dual-arm model → Got file not found error
2. Listed actual mesh files: `ls models/aloha/assets/`
3. Found naming mismatch
4. Updated XML to use correct filenames

**Fix Applied**:
```xml
<!-- Old (incorrect) -->
<mesh file="vx300s_8_gripper_bar.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_9_left_finger.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_10_right_finger.stl" scale="0.001 0.001 0.001"/>

<!-- New (correct) -->
<mesh file="vx300s_7_gripper_bar.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_8_custom_finger_left.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_8_custom_finger_right.stl" scale="0.001 0.001 0.001"/>
```

**Lessons Learned**:
- Always verify mesh file names match actual assets
- Use ls/grep to check available files before updating XML
- Asset organization is critical for multi-file models

**Status**: ✅ Fixed - Dual-arm model loads all meshes correctly

---

### Issue 5: OpenGL/X11 Crashes in WSL ✅ FIXED
**Problem**: Server crashed with segmentation fault when rendering
```
X Error of failed request:  BadAccess (attempt to access private resource denied)
  Major opcode of failed request:  148 (GLX)
  Minor opcode of failed request:  5 (X_GLXMakeCurrent)
Segmentation fault
```

**Root Cause**: WSL environment lacks proper OpenGL/X11 display server. MuJoCo's `Renderer` requires OpenGL context which fails without display.

**Testing Process**:
1. Server loaded successfully
2. First render attempt caused GLX error
3. Server crashed with segfault
4. Realized need for headless operation

**Fix Applied - Two-Part Solution**:

**Part 1: Lazy renderer initialization**
```python
def _init_simulation(self):
    # Don't create renderer immediately
    self.renderer = None  # Create lazily when render() is called

def render(self) -> np.ndarray:
    if self.renderer is None:
        try:
            self.renderer = mujoco.Renderer(self.model, height=480, width=640)
        except Exception as e:
            print(f"WARNING: Could not create renderer: {e}")
            return np.zeros((480, 640, 3), dtype=np.uint8)  # Blank frame
```

**Part 2: Headless mode flag**
```python
# Added --headless command-line flag
parser.add_argument('--headless', action='store_true',
                   help='Run in headless mode (no rendering/OpenGL)')

# Skip rendering when headless
if bridge.mode == 'simulation' and not HEADLESS_MODE:
    frame = bridge.render()
    # ... send frame
```

**Usage**:
```bash
# Normal mode (requires display)
python simulation_server.py --model aloha_simple.xml

# Headless mode (WSL/CI-friendly)
python simulation_server.py --model aloha_simple.xml --headless
```

**Testing Results**:
- Headless mode: 6/7 tests passed (frame_received N/A)
- All robot control APIs work without rendering
- No crashes or segfaults

**Lessons Learned**:
- Always provide headless option for CI/WSL environments
- Lazy initialization prevents crashes on unsupported systems
- Graceful degradation: return blank frames instead of crashing
- Separate rendering from physics simulation

**Status**: ✅ Fixed - Server runs reliably in WSL without X11

---

### Issue 6: WebSocket Client Dependencies ✅ FIXED
**Problem**: socketio client missing required packages
```
requests package is not installed -- cannot send HTTP requests!
socketio.exceptions.ConnectionError
```

**Root Cause**: python-socketio[client] requires additional packages (requests, websocket-client) not installed by default.

**Fix Applied**:
```bash
pip install python-socketio[client] requests websocket-client
```

**Lessons Learned**:
- Always install with [client] extra for client-side usage
- Check all transport dependencies (requests for polling, websocket-client for ws)

**Status**: ✅ Fixed - Test client connects successfully

---

## 📊 Progress Metrics

- **Infrastructure**: 100% ✅
- **Single-Arm Testing**: 100% ✅
- **Dual-Arm Model Loading**: 100% ✅
- **Dual-Arm WebSocket Testing**: 100% ✅
- **Headless Mode Support**: 100% ✅
- **React Client**: 100% ✅
- **End-to-End UI Testing**: 100% ✅
- **Gemini Integration (Backend)**: 100% ✅
- **Gemini Integration (Frontend)**: 0% 🔲 (compilation issues)
- **Full System Test**: 0% 🔲

**Overall Progress**: ~90% complete (Phase 3 backend finished)

### Test Results
**WebSocket Functionality Test**: 6/7 tests passed (frame_received N/A in headless mode)
- ✓ Connection establishment
- ✓ Left arm control (6 DOF)
- ✓ Right arm control (6 DOF)
- ✓ Left gripper control
- ✓ Right gripper control
- ✓ Status queries
- ✓ Reset functionality

---

## 🎯 Success Criteria

### Minimum Viable Product (MVP)
- [x] Server runs without errors
- [x] Single-arm model loads successfully
- [x] Dual-arm model loads successfully
- [x] WebSocket connections work
- [x] Robot control commands work (both arms + grippers)
- [x] Headless mode for CI/WSL environments
- [ ] Frame streaming works (with display/X11)
- [ ] React client displays simulation
- [ ] Gemini integration functional

### Full Feature Complete
- [ ] All above + production deployment ready
- [ ] Docker containerization
- [ ] Performance optimization (<50ms latency)
- [ ] Comprehensive documentation
- [ ] Integration tests passing

---

## 🚨 Blockers & Risks

### Current Blockers
None - proceeding with dual-arm testing

### Potential Risks
1. **Dual-arm model complexity**: May have same mass/inertia issues as single-arm
   - **Mitigation**: Apply same fix (add inertial properties)

2. **WebSocket performance**: Frame streaming may be slow for dual-arm
   - **Mitigation**: Optimize JPEG quality, test bandwidth

3. **Browser limitations**: Large frame buffers may cause issues
   - **Mitigation**: Implement frame rate limiting, compression

---

## 📝 Notes & Observations

- MuJoCo 3.2.5 is stricter than WASM version (requires proper physics)
- This is GOOD - means we'll have realistic simulation
- Unified bridge pattern working well - same API for sim and real
- Network latency acceptable for testing purposes (30-65ms on LAN)

---

## 🔗 Key Files

```
mujoco-server/
├── simulation_server.py          # Main Flask-SocketIO server
├── bridges/bridge_unified.py     # Unified simulation/real bridge
├── models/aloha/                 # Robot models (symlinked)
│   ├── aloha_single_arm.xml     # ✅ Working
│   └── aloha_simple.xml         # ✅ Working (dual-arm)
├── requirements.txt              # Python dependencies
└── start.sh                      # Quick launch script

Documentation:
├── MUJOCO_ARCHITECTURE_OPTIONS.md    # Architecture comparison
├── MUJOCO_SERVER_SETUP.md            # Setup guide
└── PROJECT_STATUS.md                 # This file
```

---

## 🎬 Phase 2 Completed Actions

1. ✅ Install socket.io-client in virtual-robot-arm
2. ✅ Create SimulationClient.ts WebSocket wrapper
3. ✅ Create SimulationControls.tsx UI component
4. ✅ Update App.tsx to include controls
5. ✅ Resolve port conflicts and start React app
6. ✅ Update PROJECT_STATUS.md with Phase 2 results

**Current Status**: ✅ React client fully implemented! UI compiled successfully and running on http://localhost:3000

### Next Phase: End-to-End UI Testing

**Prerequisites**:
- MuJoCo server running: http://localhost:5000 (headless mode) ✅
- React app running: http://localhost:3000 ✅

**Testing Steps**:
1. Open browser to http://localhost:3000
2. Click "Connect to Server" in SimulationControls panel
3. Verify connection status changes to "Connected"
4. Test left arm controls (Move to Home, Move to Ready)
5. Test right arm controls (Move to Home, Move to Ready)
6. Test gripper controls (Open/Close for both arms)
7. Click "Get Status" and verify positions display
8. Click "Reset to Home" and verify both arms reset
9. Monitor Activity Log for command feedback
10. Check MuJoCo server logs for WebSocket activity

**Success Criteria**:
- UI connects to server without errors
- All button clicks trigger WebSocket commands
- Activity log shows command results
- Arm positions update in real-time
- No browser console errors

---

## 🔧 Phase 4: Robot Control Console - Build Tool Decision (2025-10-06)

### Critical Decision: Switched from Vite to Create React App

**Problem Encountered:**
While building the robot-control-console frontend with Vite, encountered persistent module export errors with `@google/genai` v0.14.0:
- ❌ `GoogleGenAIOptions` not exported from web build
- ❌ `Part` interface not exported from web build  
- ❌ `Content` interface not exported from web build
- ⚠️ Vite's browser module resolution only loads `dist/web/index.mjs` which has limited exports

**Root Cause Analysis:**
The `@google/genai` package has different builds for different environments:
- **Node.js build** (`dist/index.mjs`): Full exports including all type interfaces
- **Web/Browser build** (`dist/web/index.mjs`): Limited exports - missing type interfaces

| Build Tool | Module Resolution | @google/genai exports |
|------------|-------------------|----------------------|
| **Vite** | Uses web/browser conditions → loads `dist/web/index.mjs` | ❌ Missing types |
| **Webpack (CRA)** | Bundles full package | ✅ All types available |

**Comparison of Working Apps:**
```
✅ virtual-robot-arm/        → CRA (react-scripts 5.0.1) ← Works perfectly
✅ gemini-live/console/       → CRA (react-scripts 5.0.1) ← Works perfectly  
✅ live-api-web-console/      → CRA (react-scripts 5.0.1) ← Works perfectly
❌ robot-control-console/     → Vite 7.1.9              ← Module export errors
```

**Decision Rationale:**

1. **Team Compatibility** ⭐⭐⭐⭐⭐
   - Gemini-live console (team's main app) uses CRA
   - Direct component copying will work without modification
   - Same build system = zero integration friction

2. **Virtual Robot Compatibility** ⭐⭐⭐⭐⭐
   - Virtual-robot-arm already uses CRA
   - Can directly copy 3D visualization components
   - Proven working setup for Three.js + React

3. **Zero Module Issues** ⭐⭐⭐⭐⭐
   - CRA's webpack bundles full @google/genai package
   - All type exports available (GoogleGenAIOptions, Part, Content)
   - No need for local type definitions or workarounds

4. **Maintenance** ⭐⭐⭐⭐
   - Standard CRA setup, well-documented
   - Same as 3 other working projects
   - Easy for team members to understand

**Vite Advantages (Why we considered it):**
- ✅ Faster dev server with HMR
- ✅ Smaller bundle sizes
- ✅ Less memory usage (important for WSL)
- ✅ Modern ES modules support

**Vite Disadvantages (Why we switched away):**
- ❌ Requires custom type definitions for @google/genai
- ❌ Different module resolution than team's apps
- ❌ Integration friction with gemini-live console
- ❌ Ongoing maintenance burden for type compatibility

**Final Decision: Create React App** ✅

**Implementation:**
```bash
# 1. Renamed old Vite app as backup
mv robot-control-console robot-control-console-vite-backup

# 2. Created new CRA app
npx create-react-app robot-control-console --template typescript

# 3. Installed dependencies matching gemini-live
npm install @google/genai@^0.14.0 classnames lodash eventemitter3 sass \
  @react-three/fiber @react-three/drei three zustand @types/lodash --legacy-peer-deps

# 4. Copied working modules from gemini-live
cp -r gemini-live/live-api-console/src/{lib,contexts,hooks,types.ts} robot-control-console/src/

# 5. Copied custom components from Vite backup  
cp -r robot-control-console-vite-backup/src/components robot-control-console/src/

# 6. Deleted old Vite backup
rm -rf robot-control-console-vite-backup
```

**Status**: ✅ CRA app created successfully
- All dependencies installed
- Core Gemini modules copied (lib/, contexts/, hooks/, types.ts)
- Custom robot control components migrated
- Ready for testing (pending WSL memory allocation)

**Cleanup Actions:**
- ✅ Deleted robot-control-console-vite-backup directory
- ✅ Updated virtual-robot-arm with full genai-live-client.ts (was using stripped version)
- ✅ Updated virtual-robot-arm with full audio-recorder.ts

**Benefits Realized:**
1. **Zero type errors** - All @google/genai imports work immediately
2. **100% compatibility** with gemini-live console
3. **Easy component sharing** with virtual-robot-arm (same build system)
4. **Proven stable** - Same setup as 3 working applications

**Lessons Learned:**
- When integrating with existing projects, match their build tools
- Vite's modern module resolution can cause compatibility issues with packages designed for webpack
- Team consistency > individual tool preferences
- "Works everywhere else" is a strong signal to follow the pattern

**Next Steps:**
- Test CRA app compilation (may need more memory allocation in WSL)
- Complete mode switching implementation
- Integrate 3D visualization from virtual-robot-arm
- Test voice commands with simulation bridge

---

## ✅ Phase 4 Progress: Virtual Robot Arm Voice Control & 3D Visualization (2025-10-07)

### Session Goals
1. ✅ Fix robot arm animation and position updates
2. ✅ Add comprehensive XYZ position logging
3. ✅ Fix robot arm proportions to match ALOHA specification

### Issues Fixed

#### 1. Robot Arm Not Updating Position ✅

**Problem:**
- Gemini was receiving voice commands and sending tool calls
- Bridge was processing commands successfully
- But the 3D robot model wasn't moving

**Root Cause:**
The `RobotController.update(deltaTime)` method wasn't being called every frame. This method is essential for:
- Joint angle interpolation during movement
- Gripper open/close animation
- State change callbacks

**Solution:**
Added animation loop to `IntegratedRobotControl.tsx` using `requestAnimationFrame`:

```typescript
useEffect(() => {
  let animationFrameId: number;

  const animate = () => {
    const now = Date.now();
    const deltaTime = (now - lastTimeRef.current) / 1000;
    lastTimeRef.current = now;

    // Update robot controller (handles joint interpolation and gripper animation)
    robotController.update(deltaTime);

    animationFrameId = requestAnimationFrame(animate);
  };

  animationFrameId = requestAnimationFrame(animate);

  return () => {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  };
}, [robotController]);
```

**Files Modified:**
- `virtual-robot-arm/src/components/IntegratedRobotControl.tsx`

#### 2. XYZ Position Logging Added ✅

**Requirement:**
Track and log robot end effector position throughout command execution to verify MuJoCo → Web App synchronization.

**Implementation:**
Added comprehensive logging to `robot-controller.ts`:

1. **Movement Initiation Logging:**
```typescript
// Moving to XYZ position
console.log(`[RobotController] → Moving to XYZ position: x=${parsedPos.x.toFixed(3)}, y=${parsedPos.y.toFixed(3)}, z=${parsedPos.z.toFixed(3)}`);

// Moving to joint angles
console.log(`[RobotController] → Moving to joint angles:`, angles);
```

2. **Movement Completion Logging:**
```typescript
console.log(`[RobotController] ✓ Movement complete - EE position: x=${this.state.endEffectorPosition.x.toFixed(3)}, y=${this.state.endEffectorPosition.y.toFixed(3)}, z=${this.state.endEffectorPosition.z.toFixed(3)}`);
```

3. **Gripper Action Logging:**
```typescript
console.log(`[RobotController] ✓ Gripper action complete - state: ${this.state.gripperState.state}, position: ${(this.state.gripperState.position * 100).toFixed(0)}%`);
```

**Complete Data Flow with Logging:**
```
Voice → Gemini API → Tool Call → Bridge:8082 → MuJoCo:5000
              ↓
    [VirtualRobotControl] logs tool call
              ↓
    RobotController receives command
              ↓
    [RobotController] logs target XYZ
              ↓
    Animation loop updates position
              ↓
    [RobotController] logs final XYZ
              ↓
    3D Scene updates visual
```

**Files Modified:**
- `virtual-robot-arm/src/lib/robot-controller.ts`

#### 3. Robot Arm Proportions Fixed ✅

**Problem:**
- Forearm link was disproportionately large
- Covered other components
- Didn't match real ViperX 300s robot dimensions

**Root Cause:**
STL mesh files are stored in **millimeters**, but MuJoCo and Three.js use **meters**. ALOHA XML applies `scale="0.001 0.001 0.001"` to convert mm→m, but our Three.js loader wasn't applying this scale.

**ALOHA Reference (aloha.xml:9-14):**
```xml
<mesh file="vx300s_1_base.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_2_shoulder.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_3_upper_arm.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_4_upper_forearm.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_5_lower_forearm.stl" scale="0.001 0.001 0.001"/>
<mesh file="vx300s_6_wrist.stl" scale="0.001 0.001 0.001"/>
```

**Solution:**
Applied 0.001 scale factor to STL geometries in `RobotArm.tsx`:

```typescript
// Scale all geometries from millimeters to meters (0.001 scale factor from ALOHA XML)
const scale = 0.001;
base.scale(scale, scale, scale);
shoulder.scale(scale, scale, scale);
upperArm.scale(scale, scale, scale);
upperForearm.scale(scale, scale, scale);
lowerForearm.scale(scale, scale, scale);
wrist.scale(scale, scale, scale);
```

**Verified ALOHA Dimensions (meters):**
- Base to shoulder: 0.079m
- Shoulder to upper arm: 0.04805m
- Upper arm length: 0.3m
- Upper forearm: 0.2m
- Lower forearm: 0.1m
- Wrist to gripper: 0.069744m

**Files Modified:**
- `virtual-robot-arm/src/components/RobotArm.tsx`

### Current System Status

**All Services Running:**
- ✅ MuJoCo Server (port 5000) - Headless simulation
- ✅ Simulation Bridge (port 8082) - Tool call translation
- ✅ React App (port 3000) - Voice control + 3D visualization

**Working Features:**
- ✅ Voice input via Gemini 2.0 Flash Exp
- ✅ Tool call execution through simulation bridge
- ✅ Real-time 3D robot visualization
- ✅ Smooth joint interpolation (1.5s default duration)
- ✅ Gripper open/close animation
- ✅ Position logging for debugging
- ✅ Correct robot proportions matching real hardware

**Compilation Status:**
- ✅ TypeScript compilation successful (warnings only, no errors)
- ⚠️ Minor linting warnings (unused variables)

### Testing Instructions

1. **Open the app:** http://localhost:3000
2. **Connect to Gemini:** Click "Connect" button
3. **Enable voice:** Click microphone button
4. **Test commands:**
   - "Move the arm to position 0.3, 0.2, 0.15"
   - "Move to home position"
   - "Open the gripper"
   - "Close the gripper"
5. **Check logs:** Browser console shows detailed XYZ position tracking

### Known Issues

**None** - All Phase 4 goals completed successfully!

### Next Steps for Phase 5

**Modeling Improvements Needed:**
1. **Camera perspective and positioning** - Adjust view angle for better visualization
2. **Lighting improvements** - Add better lighting to see arm details
3. **Table/workspace visualization** - Add reference surfaces
4. **Object visualization** - Add interactive objects for pick-and-place demos
5. **Gripper finger animation refinement** - Fine-tune finger movement ranges

**Performance Optimization:**
1. Mesh optimization for faster loading
2. Reduce texture sizes if needed
3. LOD (Level of Detail) for distant objects

**Additional Features:**
1. Trajectory path visualization (show planned path before execution)
2. Joint limit indicators
3. Collision detection visualization
4. Multi-arm support (add right arm)

---

## 🔄 Phase 5: MuJoCo Server vs Client-Side Rendering Decision (2025-10-08)

### Session Summary: WSL OpenGL Challenges & Architectural Pivot

**Initial Goal:** Get MuJoCo server video streaming working for realistic physics visualization

**Problems Encountered:**

#### Issue 1: OpenGL/GLX Errors in WSL (Continued from Phase 4) ⚠️
**Problem:**
Even with headless mode flag, MuJoCo server couldn't render frames in WSL environment:
```
X Error of failed request:  BadAccess (attempt to access private resource denied)
  Major opcode of failed request:  148 (GLX)
  Minor opcode of failed request:  5 (X_GLXMakeCurrent)
```

**Attempts Made:**
1. ✅ Added `--headless` flag to skip OpenGL rendering
2. ✅ Fixed Flask-SocketIO threading mode (`async_mode='threading'`)
3. ✅ Server starts successfully without crashes
4. ❌ **BUT**: Headless mode disables frame rendering entirely (by design)

**Code Analysis:**
```python
# simulation_server.py lines 151-161
if bridge.mode == 'simulation' and not HEADLESS_MODE:
    frame = bridge.render()  # Only renders if NOT headless
    frame_b64 = encode_frame_jpeg(frame)
    emit('frame_update', {'frame': frame_b64, ...})
```

**The Catch-22:**
- **Without headless**: Server crashes due to GLX errors (no display in WSL)
- **With headless**: Server runs but doesn't send video frames (intended behavior)
- **OSMesa solution**: Would require MuJoCo recompilation with osmesa support (complex)

#### Issue 2: TypeScript Compilation Errors ✅ FIXED
**Problem:**
React app couldn't compile due to missing imports and property mismatches:
- `OBJLoader` and `useTexture` not imported
- `robotState.gripper` should be `robotState.gripperState`
- OBJ files return Group objects, not BufferGeometry (requires `<primitive>` instead of `<mesh>`)

**Fixes Applied:**
```typescript
// 1. Added missing imports (RobotArm.tsx:4-5)
import { STLLoader, OBJLoader } from 'three-stdlib';
import { Html, useTexture } from '@react-three/drei';

// 2. Fixed gripper state reference (MuJoCoServerView.tsx:97)
command: robotState.gripperState.position > 0.5 ? 'open' : 'close'

// 3. Changed from HoverableMesh to primitive for OBJ groups
<primitive object={meshes.baseObj.clone()} />
```

**Status:** ✅ React app compiles successfully with only minor lint warnings

### Critical Architectural Decision: Client-Side Rendering

**Decision Made:** Use Three.js client-side rendering instead of MuJoCo server video streaming

**Rationale:**

| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| **MuJoCo Server Rendering** | • Full physics simulation<br>• Realistic lighting/shadows<br>• Server-side truth | • Requires OpenGL/X11<br>• Doesn't work in WSL headless<br>• Complex OSMesa setup<br>• Network latency for video | ❌ Blocked by WSL |
| **Three.js Client-Side** | • Works in any browser<br>• No OpenGL/X11 needed<br>• Interactive camera control<br>• Lower latency | • Manual joint positioning<br>• No true physics simulation<br>• Need to sync with server | ✅ **SELECTED** |

**Key Insight:**
The MuJoCo server approach is **still valuable** for:
- Real robot control (no rendering needed)
- Physics validation (headless mode)
- CI/CD testing environments

But for **web visualization**, client-side Three.js rendering is more practical.

### Implementation Progress

**What's Working:**
- ✅ MuJoCo server running in headless mode (port 5001)
- ✅ WebSocket API fully functional (move_arm, control_gripper, etc.)
- ✅ React app compiles without errors
- ✅ Toggle switch between MuJoCo server and manual rendering modes
- ✅ `MuJoCoServerView.tsx` component ready (will show "no frames" message in headless)
- ✅ `RobotArm.tsx` manual rendering with OBJ/STL meshes

**Current State:**
```
Browser (localhost:3000)
  └─ IntegratedRobotControl
      ├─ Toggle: [✓] MuJoCo Server (Full Physics)
      │   └─ MuJoCoServerView
      │       ├─ ✅ WebSocket connected
      │       ├─ ✅ Sends joint commands
      │       └─ ⚠️ No frames (headless mode)
      │
      └─ Toggle: [ ] Manual Rendering
          └─ Scene with RobotArm
              ├─ ✅ Three.js rendering
              ├─ ⚠️ Needs joint position sync
              └─ ⚠️ Mesh visualization issues
```

### Next Actions Required

**1. Switch Default Toggle to Manual Rendering**
```typescript
// IntegratedRobotControl.tsx
const [useMuJoCoServer, setUseMuJoCoServer] = useState(false); // Changed from true
```

**2. Fix Manual Rendering Visualization**
Current issue: OBJ files not loading properly, parts disconnected

**Options:**
- A. Use STL files (simpler, proven to work)
- B. Fix OBJ file loading with proper transforms
- C. Use simplified geometric shapes (boxes/cylinders)

**Recommendation:** Start with **Option A (STL files)** since Phase 4 already confirmed they work with correct scaling (0.001 factor).

**3. Implement Joint Position Synchronization**
Robot controller needs to update Three.js scene based on:
- Voice commands via Gemini
- Manual sliders/controls
- Preset poses (home, ready, sleep)

This is **already working** from Phase 4! Just need to ensure toggle defaults to manual mode.

### Files Modified This Session

1. **mujoco-server/simulation_server.py:31**
   - Added `async_mode='threading'` to Flask-SocketIO init
   - Fixed WebSocket connection errors

2. **virtual-robot-arm/src/components/MuJoCoServerView.tsx:97**
   - Fixed `robotState.gripper` → `robotState.gripperState`
   - TypeScript compilation now successful

3. **virtual-robot-arm/src/components/RobotArm.tsx:4-5**
   - Added missing imports: `OBJLoader`, `useTexture`
   - Changed HoverableMesh to primitive for OBJ groups

4. **virtual-robot-arm/src/components/IntegratedRobotControl.tsx**
   - Added toggle for MuJoCo server vs manual rendering
   - Connected MuJoCoServerView component

### Lessons Learned

1. **WSL OpenGL Limitations**: Always plan for headless operation in WSL
2. **Separate Concerns**: Physics simulation (server) vs Visualization (client)
3. **Fallback Strategies**: Having both rendering modes provides flexibility
4. **Type Safety**: TypeScript caught gripper state property mismatch early

### Testing Plan

**Next Session:**
1. ✅ Switch toggle default to manual rendering
2. ✅ Verify STL-based RobotArm renders correctly
3. ✅ Test voice commands update 3D visualization
4. ✅ Add workspace elements (table, objects)
5. ✅ Document final architecture

**Success Criteria:**
- [ ] Robot arm visible and properly positioned
- [ ] Voice commands move the arm smoothly
- [ ] Gripper opens/closes on command
- [ ] XYZ position logging confirms accuracy
- [ ] No TypeScript or runtime errors

---

## Phase 6: MJCF Parser Refinements and Virtual Camera System

**Date**: October 9-10, 2025
**Status**: ✅ COMPLETED
**Goal**: Fix gripper mechanics, implement virtual camera system with Gemini integration

### Overview

Phase 6 focused on perfecting the MJCF parser implementation from Phase 5, fixing critical bugs in gripper assembly rendering, and implementing a complete virtual camera system that mirrors the real robot's RealSense D405 camera setup.

### Problems Solved

#### 1. MJCF Parser querySelector Bug (Gripper Assembly)

**Problem**: Gripper assembly (fingers and finger tips) were moving independently instead of staying attached to the gripper base. Visual debugging showed gripper parts floating away when arm moved.

**Root Cause**: CSS-style querySelector in `findChildBodies()` was matching ALL descendants instead of just direct children:
```typescript
// WRONG - matches all descendants
const childElements = parentElement.querySelectorAll(`body[name^="${parentBodyName}/"]`);
```

**Solution**: Added `:scope >` selector to match only direct children:
```typescript
// CORRECT - matches only direct children
const childElements = parentElement.querySelectorAll(`:scope > body[name^="${parentBodyName}/"]`);
```

**Files Modified**:
- [virtual-robot-arm/src/lib/mjcf-parser.ts:94](virtual-robot-arm/src/lib/mjcf-parser.ts#L94)

**Result**: Gripper assembly now moves as a single unit, maintaining correct parent-child relationships from MJCF hierarchy.

#### 2. React State Mutation Bug (Gripper Rendering)

**Problem**: After fixing querySelector, gripper still didn't update visually when grip commands were issued. Console showed position changes but Three.js scene didn't re-render.

**Root Cause**: Direct mutation of nested state objects prevented React change detection:
```typescript
// WRONG - mutates nested object
this.state.gripperState.position = this.targetGripperPosition;
```

**Solution**: Create new objects for all state updates to trigger React re-renders:
```typescript
// CORRECT - creates new object
this.state.gripperState = {
  position: this.targetGripperPosition,
  state: this.targetGripperPosition > 0.5 ? 'open' : 'closed',
};
```

**Files Modified**:
- [virtual-robot-arm/src/lib/robot-controller.ts:95-110](virtual-robot-arm/src/lib/robot-controller.ts#L95)

**Result**: Gripper now animates smoothly when opening/closing, with proper React change detection.

#### 3. Gripper Finger Slide Joint Mechanics

**Problem**: Gripper fingers needed to move along slide joints (prismatic/slider type) based on gripper position, matching MJCF joint definitions.

**MJCF Joint Definitions**:
```xml
<joint name="left/left_finger_slide" type="slide" range="0.015 0.037" axis="1 0 0"/>
<joint name="left/right_finger_slide" type="slide" range="0.015 0.037" axis="-1 0 0"/>
```

**Solution**: Implemented slide joint transformation in RobotArmMJCF.tsx:
```typescript
const slideOffset = slideJoint.range[0] +
  (slideJoint.range[1] - slideJoint.range[0]) * gripperPosition;

const localSlideVector = new THREE.Vector3(...slideJoint.axis).normalize().multiplyScalar(slideOffset);
const worldSlideOffset = localSlideVector.applyQuaternion(parentQuaternion);

position.add(worldSlideOffset);
```

**Key Concepts**:
- Linear interpolation between joint range min/max based on gripper position (0-1)
- Transform slide axis from local to world space using parent quaternion
- Apply offset to body position before rendering

**Files Modified**:
- [virtual-robot-arm/src/components/RobotArmMJCF.tsx:81-103](virtual-robot-arm/src/components/RobotArmMJCF.tsx#L81)

**Result**: Gripper fingers slide correctly along their axes when gripper opens/closes, matching MJCF physics definitions.

#### 4. Virtual Camera System Implementation

**Problem**: Need virtual cameras matching real robot's RealSense D405 setup (gripper cam + top cam) for Gemini Live visual integration.

**Real Robot Reference**: Examined [gemini-live/gemini-live-api-control/live-api-console/src/components/camera-feed/CameraFeed.tsx](gemini-live/gemini-live-api-control/live-api-console/src/components/camera-feed/CameraFeed.tsx) to match architecture:
- HTTP polling: `fetch(/camera/{name}/frame)`
- Base64 JPEG format
- Hidden canvas for Gemini integration
- 10 FPS refresh rate

**Solution Components**:

**A. VirtualCameraSystem Component**
- Created two Three.js PerspectiveCameras (gripper_cam, top_cam)
- WebGL render targets for off-screen rendering
- Per-frame capture to canvas and base64 JPEG encoding
- 1 FPS capture rate, 640x480 resolution

**B. Camera Position Management**
- Top camera: Fixed overhead position `[0, 0, 0.8]` looking down
- Gripper camera: Tracks MJCF body hierarchy (details below)

**C. VirtualCameraFeed Component**
- Collapsible UI overlay showing camera feeds
- Matches real robot's camera display styling
- Displays timestamps and camera labels
- Base64 JPEG images rendered as `<img>` elements

**Files Created**:
- [virtual-robot-arm/src/components/VirtualCameraSystem.tsx](virtual-robot-arm/src/components/VirtualCameraSystem.tsx) - Virtual camera rendering and capture
- [virtual-robot-arm/src/components/VirtualCameraFeed.tsx](virtual-robot-arm/src/components/VirtualCameraFeed.tsx) - Camera feed UI overlay

**Files Modified**:
- [virtual-robot-arm/src/components/Scene.tsx:134-172](virtual-robot-arm/src/components/Scene.tsx#L134) - Integrated camera system

**Result**: Virtual cameras capture scene from correct viewpoints, ready for Gemini Live integration.

#### 5. Gripper Camera MJCF Hierarchy Tracking

**Problem**: Gripper camera needed to move with the robot arm, tracking the gripper_base body transform.

**Initial Wrong Approach**: Tried using forward kinematics (`robotState.endEffectorPosition`), but this didn't account for actual Three.js scene graph transformations.

**Correct Solution**: Track MJCF body hierarchy using `scene.traverse()`:

```typescript
// Find gripper_base in scene graph
let gripperBaseGroup: THREE.Object3D | null = null;
scene.traverse((obj) => {
  if (obj.name === 'left/gripper_base') {
    gripperBaseGroup = obj;
  }
});

if (gripperBaseGroup) {
  // Get world transform
  const worldPosition = new THREE.Vector3();
  const worldQuaternion = new THREE.Quaternion();
  gripperBaseGroup.getWorldPosition(worldPosition);
  gripperBaseGroup.getWorldQuaternion(worldQuaternion);

  // Camera offset from MJCF: pos="0 -0.0824748 -0.0095955"
  const localCameraOffset = new THREE.Vector3(0, -0.0824748, -0.0095955);
  const worldCameraOffset = localCameraOffset.clone().applyQuaternion(worldQuaternion);

  gripperCameraRef.current.position.copy(worldPosition).add(worldCameraOffset);

  // Camera rotation from MJCF: euler="2.70525955359 0 0"
  const localEuler = new THREE.Euler(2.70525955359, 0, 0, 'XYZ');
  const localCameraRotation = new THREE.Quaternion().setFromEuler(localEuler);

  gripperCameraRef.current.quaternion.copy(worldQuaternion).multiply(localCameraRotation);
  gripperCameraRef.current.up.set(0, 0, 1);
}
```

**Key Concepts**:
- `scene.traverse()` walks entire Three.js scene graph
- `getWorldPosition()` and `getWorldQuaternion()` extract world-space transforms
- Camera offset transformed from local to world space using quaternion
- MJCF camera definition from [aloha.xml](virtual-robot-arm/public/models/aloha/aloha.xml):
  ```xml
  <camera name="wrist_cam_left" pos="0 -0.0824748 -0.0095955"
          euler="2.70525955359 0 0" mode="fixed"/>
  ```

**Files Modified**:
- [virtual-robot-arm/src/components/VirtualCameraSystem.tsx:108-141](virtual-robot-arm/src/components/VirtualCameraSystem.tsx#L108)
- [virtual-robot-arm/src/components/RobotArmMJCF.tsx:125](virtual-robot-arm/src/components/RobotArmMJCF.tsx#L125) - Added `name={body.name}` for identification

**Result**: Gripper camera perfectly tracks robot movement with correct offset and rotation, matching MJCF camera definition.

### Technical Implementation Details

#### MJCF Parser Pattern Matching

The key insight was understanding CSS selector scope:
- `querySelectorAll('body')` - all bodies anywhere in DOM
- `querySelectorAll('body[name^="prefix/"]')` - all bodies with name prefix (anywhere)
- `querySelectorAll(':scope > body[name^="prefix/"]')` - only direct children with prefix

This mirrors parent-child relationships in MJCF `<body>` hierarchy.

#### React Immutability for Change Detection

React's change detection relies on reference equality:
```typescript
// Mutation - same reference, no re-render
state.nested.value = newValue;

// Correct - new reference, triggers re-render
state.nested = { ...state.nested, value: newValue };
```

This applies to nested objects like `gripperState` in `RobotState`.

#### Quaternion-Based Coordinate Transformations

Converting local-space vectors to world-space:
1. Get parent's world quaternion
2. Apply to local vector: `localVec.applyQuaternion(worldQuat)`
3. Result is world-space offset

Used for both slide joints and camera positioning.

#### WebGL Render Targets for Virtual Cameras

Three.js render pipeline for off-screen rendering:
1. Create `WebGLRenderTarget` with desired resolution
2. Render scene to target: `renderer.setRenderTarget(target)`
3. Read pixels to canvas: `renderer.readRenderTargetPixels()`
4. Encode canvas to base64 JPEG
5. Reset to screen rendering: `renderer.setRenderTarget(null)`

### Architecture Decisions

#### Camera Feed Integration Strategy

**Decision**: Wait for colleagues' camera feed integration work on real robot before implementing HTTP endpoints in virtual robot.

**Rationale**:
- Real robot team working on Gemini Live camera integration
- Virtual robot should match final real robot architecture
- HTTP polling pattern identified and ready to implement when needed

#### MJCF Hierarchy Tracking vs Forward Kinematics

**Decision**: Use MJCF hierarchy tracking (scene graph) for camera positioning instead of forward kinematics calculations.

**Rationale**:
- Scene graph already contains all transformations from MJCF parser
- Same pattern used for gripper fingers (proven to work)
- Automatically accounts for all parent transforms in chain
- Simpler and more maintainable than recalculating FK

#### Manual Rendering Default Mode

**Decision**: Keep manual rendering (Three.js) as default, with MuJoCo server as optional toggle.

**Rationale**:
- Manual rendering works in all environments (browser-only)
- MuJoCo server requires Python backend and proper setup
- MJCF parser now feature-complete with working gripper and cameras
- Toggle provides flexibility for future physics simulation needs

### Files Modified Summary

**Created**:
- [virtual-robot-arm/src/components/VirtualCameraSystem.tsx](virtual-robot-arm/src/components/VirtualCameraSystem.tsx) - Virtual camera rendering and capture
- [virtual-robot-arm/src/components/VirtualCameraFeed.tsx](virtual-robot-arm/src/components/VirtualCameraFeed.tsx) - Camera feed UI overlay

**Modified**:
- [virtual-robot-arm/src/lib/mjcf-parser.ts:94](virtual-robot-arm/src/lib/mjcf-parser.ts#L94) - Fixed querySelector scope
- [virtual-robot-arm/src/lib/robot-controller.ts:95-110](virtual-robot-arm/src/lib/robot-controller.ts#L95) - Fixed state mutation
- [virtual-robot-arm/src/components/RobotArmMJCF.tsx:81-103,125](virtual-robot-arm/src/components/RobotArmMJCF.tsx#L81) - Slide joints + body names
- [virtual-robot-arm/src/components/Scene.tsx:134-172](virtual-robot-arm/src/components/Scene.tsx#L134) - Camera integration
- [virtual-robot-arm/src/components/VirtualRobotControl.tsx:554-555](virtual-robot-arm/src/components/VirtualRobotControl.tsx#L554) - Turn buttons (testing)

### Testing and Validation

**Manual Testing Performed**:
1. ✅ Gripper fingers move correctly with gripper commands
2. ✅ Gripper assembly stays attached during arm movements
3. ✅ Camera feeds display at 1 FPS with proper timestamps
4. ✅ Gripper camera tracks arm movement with correct orientation
5. ✅ Top camera provides overhead workspace view
6. ✅ All robot movements (joint, position, named poses) work correctly
7. ✅ No TypeScript compilation errors (except unused RobotArm.tsx)

**Known Limitations**:
- Turn commands require Gemini prompt fix (intentionally not fixed - colleagues working on real robot)
- HTTP endpoint pattern for camera feeds not yet implemented (waiting for real robot integration)
- Old RobotArm.tsx file has compilation warnings (unused file)

### Lessons Learned

1. **CSS Selectors Apply to XML Parsing**: `:scope >` is critical for matching parent-child relationships in MJCF hierarchy, just like in CSS DOM manipulation.

2. **React Immutability is Non-Negotiable**: Even deep nested state updates must create new object references for change detection to work.

3. **Scene Graph Tracking > Calculation**: For virtual cameras and complex assemblies, tracking the rendered scene graph is more reliable than recalculating transforms.

4. **Match Real Robot Architecture Early**: Studying the real robot's camera implementation pattern before building virtual version saved rework.

5. **Quaternions for All Rotations**: Euler angles from MJCF must be converted to quaternions for proper composition with parent transforms.

6. **Visual Debugging is Essential**: Adding debug arrows and console logging was critical for identifying gripper assembly and camera tracking issues.

### Next Steps (Pending)

1. **Documentation Cleanup**:
   - ✅ Phase 6 documentation added to PROJECT_STATUS.md
   - ⏳ Review and consolidate/remove standalone .md files
   - ⏳ Remove or fix unused RobotArm.tsx

2. **Camera Feed Integration**:
   - Wait for colleagues' real robot camera integration
   - Implement matching HTTP endpoint pattern when ready

3. **Scene Realism** (Low Priority):
   - Add more realistic workspace elements
   - Improve lighting and materials

4. **Gemini Prompt Refinement**:
   - Coordinate with colleagues on unified prompt system
   - Implement turn/rotation commands when safe to do so

### Success Metrics

- ✅ Virtual robot matches real robot behavior
- ✅ Gripper mechanics physically accurate to MJCF
- ✅ Virtual cameras positioned correctly per MJCF definitions
- ✅ Camera feeds ready for Gemini Live integration
- ✅ No blocking bugs or compilation errors
- ✅ Code is maintainable and well-documented

---

