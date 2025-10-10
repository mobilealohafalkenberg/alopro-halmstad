# Virtual Robot Arm - 3D Simulator for Mobile ALOHA

**Browser-based voice-controlled robot simulator with Gemini 2.5 Flash integration**

## Quick Start

```bash
# 1. Install dependencies
npm install --legacy-peer-deps

# 2. Set up API key
cp .env.example .env
# Edit .env: REACT_APP_GEMINI_API_KEY=your-key-here

# 3. Start application on port 3002 (avoids conflict with real robot)
PORT=3002 npm start
# Or use: ./start.sh

# 4. Open browser
# http://localhost:3002
```

**Note:** Virtual robot runs on port **3002** to avoid conflicts with the real robot (port 3000).

## What's This?

A complete virtual replica of the Mobile ALOHA robot that runs in your browser:
- 🎤 **Voice Control** via Gemini 2.5 Flash
- 🤖 **3D Visualization** with realistic kinematics
- 📷 **Virtual Cameras** matching real robot setup
- 🔧 **No Hardware Needed** for development

## Features

- Natural language voice commands
- Smooth 3D robot animation (Three.js + MJCF)
- Inverse kinematics for XYZ position control
- Gripper with realistic finger mechanics
- Virtual cameras (gripper + overhead)
- Real-time position logging

## Example Commands

- "Move the arm to position 0.3, 0.2, 0.15"
- "Open the gripper"
- "Move to home position"
- "Close the gripper"

## Documentation

📄 **Complete documentation**: See [VIRTUAL_ROBOT_DOCUMENTATION.md](../VIRTUAL_ROBOT_DOCUMENTATION.md#-virtual-robot-arm---quick-start-guide)

The VIRTUAL_ROBOT_DOCUMENTATION.md file contains:
- Architecture overview
- Detailed setup instructions
- Tool function reference
- Development history (Phases 1-6)
- Known limitations and next steps

## Technology Stack

- **Frontend**: React + TypeScript
- **3D Rendering**: Three.js with MJCF parser
- **AI**: Gemini 2.5 Flash Live API
- **Kinematics**: Custom IK solver for ViperX 300s
- **Voice**: WebAudio API + AudioWorklet

## File Structure

```
src/
├── components/          # React components
│   ├── IntegratedRobotControl.tsx    # Main app
│   ├── VirtualRobotControl.tsx       # Voice control
│   ├── RobotArmMJCF.tsx              # 3D robot
│   └── VirtualCameraSystem.tsx       # Cameras
├── lib/                # Core libraries
│   ├── robot-controller.ts           # Kinematics
│   ├── mjcf-parser.ts                # MJCF parsing
│   └── genai-live-client.ts          # Gemini API
└── types.ts            # TypeScript types
```

## Development Status

✅ **Phase 6 Complete** (October 2025)
- MJCF parser with gripper mechanics
- Virtual camera system
- Gemini 2.5 Flash integration
- Voice control fully functional

## License

Part of the Mobile ALOHA robot control system.
