# ALOHA Robot Control via Gemini Live API

🎤 **Voice-controlled Mobile ALOHA robot arm and gripper using Google's Gemini Live API**

## ✨ Features

- 🗣️ **Natural Language Control** - Control arm and gripper with voice commands
- 🦾 **6-DOF Arm Control** - Full arm movement with multiple input formats
- 🤖 **Real-time Robot Control** - Direct control of Mobile ALOHA robot
- 📊 **Visual Feedback** - Live arm pose and gripper state display
- 🎯 **Smart Format Detection** - Auto-detects degrees vs radians
- 🎚️ **Audio Level Indicators** - See your voice being captured in real-time
- 🔌 **Hot-swappable** - No need to launch full ALOHA system
- ⚡ **Minimal Latency** - Fire-and-forget pattern for instant response

## 🚀 Quick Start

### Prerequisites
- Mobile ALOHA robot with ViperX 300s arms
- ROS2 Humble installed
- Node.js 16+ and npm
- Python 3.8+
- Google Gemini API key

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd gemini-live
```

2. **Set up your Gemini API key:**
```bash
cd gemini-live-api-control/live-api-console
echo "REACT_APP_GEMINI_API_KEY=your-actual-api-key" > .env
```

3. **Install Node.js dependencies:**
```bash
npm install
```

### Running the System

**Terminal 1 - Start Robot Bridge:**
```bash
cd gemini-live-api-control
./run_bridge.sh
```
Wait for: `✓ Gripper controller initialized successfully`

**Terminal 2 - Start Web Interface:**
```bash
cd gemini-live-api-control/live-api-console
npm start
```
Opens automatically at http://localhost:3000

### Using Voice Control

1. Click **"🔌 Connect"** button in the web interface
2. Allow microphone and camera access when prompted
3. Watch the "In" volume meter - it should respond to your voice
4. Speak commands clearly:
   - **Gripper:** "Open/close the gripper"
   - **Arm Movement:** "Move to home position", "Go to ready position"
   - **Cartesian:** "Move forward 20 centimeters"
   - **Joint Control:** "Set joint angles to 0, -55, 66, 0, -17, 0 degrees"
   - **Status:** "What's the arm status?"

## 📁 Project Structure

```
gemini-live/
├── CLAUDE.md                    # AI assistant instructions
├── README.md                    # This file
├── gripper_controller.py        # Thread-safe gripper control API
├── arm_controller.py           # Flexible arm control with auto-detection
├── test_arm_controller.py      # Arm controller test suite
├── minimal_arm_control.py       # Direct arm control testing
├── minimal_launch.sh           # Robot driver launcher
├── example_gemini_integration.py # Test script
└── gemini-live-api-control/
    ├── run_bridge.sh           # Bridge startup script
    ├── bridges/
    │   └── bridge_aloha_real.py # Python bridge server (port 8081)
    └── live-api-console/       # React web interface
        ├── src/
        │   ├── components/     # UI components
        │   │   ├── aloha-control/    # Robot control UI
        │   │   └── control-tray/     # Connection controls
        │   └── lib/           # Core libraries
        │       ├── genai-live-client.ts  # Gemini API wrapper
        │       └── audio-recorder.ts     # Voice capture
        ├── package.json
        └── .env              # API key configuration
```

## 🏗️ Architecture

```
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Voice Input  │────▶│ Gemini Live │────▶│ Tool Calls   │────▶│   Python    │
│  (Browser)   │     │     API     │     │   (JSON)     │     │   Bridge    │
└──────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
                                                                       │
                                                                       ▼
┌──────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Visual     │◀────│    State    │◀────│   Gripper    │◀────│    ROS2     │
│   Feedback   │     │   Updates   │     │  Controller  │     │   Driver    │
└──────────────┘     └─────────────┘     └──────────────┘     └─────────────┘
```

## 🎯 Key Features Explained

### Voice Processing
- Captures audio at browser's default rate (usually 48kHz)
- Resamples to 16kHz for Gemini compatibility
- Converts to PCM16 format
- Base64 encodes and streams via WebSocket

### Robot Control
- Uses current-based position control (300mA limit)
- Thread-safe with 10Hz state monitoring
- Fire-and-forget pattern prevents timeout errors
- Automatic robot driver management

### Tool Functions
The system declares these tools for Gemini:
- `control_gripper` - Open/close the gripper
- `get_gripper_status` - Query gripper state
- `move_arm` - Move arm to position/pose/joints
- `get_arm_status` - Query arm state and position

### Arm Control Features
- **Auto-detection:** Values > 2π detected as degrees
- **Named poses:** home, ready, sleep
- **Cartesian control:** x, y, z in meters
- **Joint control:** 6 DOF in radians or degrees
- **Workspace limits:** z ≥ 0.1m for safety

## 🔧 Development

### Testing Gripper Without Voice
```bash
# Terminal 1: Launch robot
./minimal_launch.sh

# Terminal 2: Test control
python3 example_gemini_integration.py
```

### Running Individual Components
```bash
# Test arm control directly
python3 minimal_arm_control.py

# Check bridge status
curl http://localhost:8081/status

# View React app logs
npm start --verbose
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **No voice pickup** | Check mic permissions, look for volume meter movement |
| **Gripper not moving** | Verify robot power, check bridge is running (port 8081) |
| **"Load failed" errors** | Bridge uses fire-and-forget pattern - this is normal |
| **Connection refused** | Ensure both bridge and React app are running |
| **Audio context error** | Browser security - must interact with page first |

## 📊 System Status Indicators

- **Bridge:** 🟢 Connected / 🔴 Disconnected
- **Video:** 📹 Active / ❌ Inactive  
- **Audio:** 🎤 Recording / 🔇 Muted
- **Gripper:** Visual progress bar (0-100% open)

## 🤖 Robot Specifications

- **Model:** ViperX 300s (vx300s)
- **Control Group:** follower_left
- **Arm:** 6 DOF (waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate)
- **Gripper Mode:** current_based_position
- **Current Limit:** 300mA
- **Update Rate:** 10Hz
- **Workspace:** x,y: ±0.5m, z: 0.1-0.6m
- **Sleep Position:** Wrist points straight up (-1.57 rad)

## 📝 API Endpoints

**Bridge Server (Port 8081):**
- `POST /aloha-tool-call` - Execute Gemini tool calls
- `GET /status` - System health check

**Response Formats:**
```json
// Gripper State
{
  "state": "open",
  "position_normalized": 0.8,
  "success": true
}

// Arm State
{
  "state": "idle",
  "joints_degrees": [0, -55, 66, 0, -17, 0],
  "ee_position": {"x": 0.3, "y": 0, "z": 0.25},
  "pose": "ready",
  "success": true
}
```

## 🚦 Prerequisites Check

Before running, ensure:
- [ ] ROS2 Humble is installed
- [ ] Interbotix workspace is built (`~/interbotix_ws/`)
- [ ] Robot is powered on and USB connected
- [ ] Gemini API key is configured in `.env`
- [ ] Ports 3000 and 8081 are available

## 📚 Additional Resources

- [Mobile ALOHA Project](https://mobile-aloha.github.io/)
- [Gemini Live API Docs](https://ai.google.dev/api/multimodal-live)
- [Interbotix Documentation](https://docs.trossenrobotics.com/)

## 🤝 Contributing

Feel free to open issues or submit pull requests. Make sure to test with actual hardware before submitting changes.

## 📄 License

MIT License - See LICENSE file for details

---

🤖 **Built with [Claude Code](https://claude.ai/code)** | Co-Authored-By: Claude <noreply@anthropic.com>