# Mobile ALOHA Gripper Integration with Gemini Live API

## 🎯 Overview
This integration allows you to control the real Mobile ALOHA robot gripper using voice commands through Gemini Live API.

## 🏗️ Architecture
```
Voice/Video → Browser → Gemini Live API
                ↓
         Function Calls
                ↓
      Python Bridge (8081)
                ↓
      Gripper Controller
                ↓
      Mobile ALOHA Robot
```

## 📋 Prerequisites
- Mobile ALOHA robot connected and powered on
- ROS2 Humble installed
- Node.js 18+ and npm
- Python 3.8+ with aiohttp
- Google Gemini API key

## 🚀 Quick Start

### 1. Setup Environment (First Time Only)
```bash
cd gemini-live-api-control

# Setup Python environment with uv
./setup_bridge.sh

# React app dependencies
cd live-api-console
npm install
cd ..
```

### 2. Configure API Key
```bash
cd gemini-live-api-control/live-api-console
echo "REACT_APP_GEMINI_API_KEY=your-api-key-here" > .env
```

### 3. Start the Services

**Terminal 1: Python Bridge (launches robot driver automatically)**
```bash
cd gemini-live-api-control
./run_bridge.sh
```

Or manually:
```bash
cd gemini-live-api-control
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
source .venv/bin/activate
python bridges/bridge_aloha_real.py
```

You should see:
```
ALOHA Robot Bridge for Gemini Live API
Starting bridge server on http://localhost:8081
[Bridge] Starting robot driver...
[Bridge] Initializing gripper controller...
[Bridge] ✓ Gripper controller initialized successfully
```

**Terminal 2: React App**
```bash
cd gemini-live-api-control/live-api-console
npm start
```

### 4. Use the System

1. Open http://localhost:3000
2. Select "ALOHA" mode
3. Click "Connect" to establish connection with Gemini
4. Allow camera/microphone access
5. Start controlling with voice or buttons!

## 🎤 Voice Commands

Try these commands:
- "Open the gripper"
- "Close the gripper"
- "What's the gripper status?"
- "Pick up the object in front of you"
- "Release what you're holding"

## 🎮 Manual Controls

The UI provides buttons for:
- 🤚 **Open Gripper** - Opens the gripper fully
- ✊ **Close Gripper** - Closes the gripper
- 📊 **Get Status** - Check current gripper state
- 🎯 **Pick Object** - Contextual pick command

## 📊 Visual Feedback

The UI shows:
- **Connection Status** - API and bridge connection
- **Gripper State** - OPEN/CLOSED/OPENING/CLOSING
- **Position Bar** - Visual 0-100% indicator
- **Real-time Updates** - State changes as gripper moves

## 🔧 Troubleshooting

### Bridge won't start
- Check robot is powered on
- Verify USB connection: `ls /dev/ttyDXL*`
- Ensure ROS environment is sourced

### "Load failed" errors
- This means Gemini is trying to execute Python code
- Check that bridge is running
- Verify fire-and-forget pattern is used

### Gripper not responding
- Check bridge console for errors
- Verify robot driver is running
- Try manual test: `python3 minimal_arm_control.py`

### Connection issues
- Check ports 3000 and 8081 are free
- Look for CORS errors in browser console
- Verify API key is set correctly

## 🏗️ File Structure
```
gemini-live/
├── gripper_controller.py        # Core gripper control class
├── minimal_launch.sh            # Robot driver launcher
├── minimal_arm_control.py       # Standalone test script
└── gemini-live-api-control/
    ├── bridges/
    │   └── bridge_aloha_real.py  # Python bridge server
    └── live-api-console/
        └── src/components/aloha-control/
            └── ALOHAControl.tsx   # React UI component
```

## 🔑 Key Implementation Details

### Fire-and-Forget Pattern
The bridge always responds immediately to Gemini with `{success: true}`, then processes the actual robot command asynchronously. This prevents "Load failed" errors.

### Tool Functions
- `control_gripper(action)` - Opens or closes gripper
- `get_gripper_status()` - Returns state and position

### Safety Features
- Current-based position control (300mA limit)
- Graceful shutdown moves arm to sleep position
- Error handling for disconnections

## 📝 Notes

- The bridge automatically launches `minimal_launch.sh` on startup
- Gripper position is tracked in real-time (10Hz)
- The system is designed for single gripper (left arm) control
- Future versions can add camera feed and arm movement

## 🚦 Status Endpoint

Check bridge status:
```bash
curl http://localhost:8081/status
```

Returns:
```json
{
  "bridge": "running",
  "controller_initialized": true,
  "gripper": {
    "state": "open",
    "position_percent": 100.0
  }
}
```

## 🛑 Shutdown

1. Stop React app: `Ctrl+C` in npm terminal
2. Stop Python bridge: `Ctrl+C` in bridge terminal
   - This automatically sleeps the arm and closes connections

## 🎉 Success!

You can now control your Mobile ALOHA robot gripper with voice commands through Gemini Live API!