# Virtual Robot Arm - Quick Setup Guide

## What You Just Got

A complete 3D virtual robot arm simulator that you can control with your voice! It simulates the same ViperX 300s robot arm you have in the real system, but running entirely in your web browser.

## What's Inside

```
virtual-robot-arm/
├── src/
│   ├── components/
│   │   ├── RobotArm.tsx           # 3D robot arm model
│   │   ├── Scene.tsx              # Complete 3D scene
│   │   └── VirtualRobotControl.tsx # Voice control UI
│   ├── lib/
│   │   ├── kinematics.ts          # Robot math (FK/IK)
│   │   ├── robot-controller.ts    # Movement control
│   │   ├── genai-live-client.ts   # Gemini API client
│   │   └── audio-recorder.ts      # Voice recording
│   └── types/
│       └── robot.ts               # Robot specifications
├── README.md                       # Full documentation
├── start.sh                        # Quick start script
└── package.json                    # Dependencies
```

## Quick Start (3 Steps)

### 1. Get a Gemini API Key

1. Go to [https://aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click "Get API Key"
4. Copy your API key

### 2. Configure and Install

```bash
cd virtual-robot-arm

# Copy the environment template
cp .env.example .env

# Edit .env and paste your API key
nano .env  # or use your favorite editor

# Install dependencies
npm install
```

Your `.env` file should look like:
```
REACT_APP_GEMINI_API_KEY=AIzaSy...your-key-here
```

### 3. Run the Simulator

```bash
npm start
```

Or use the quick start script:
```bash
./start.sh
```

The app will open automatically at `http://localhost:3000`

## First Run Instructions

When the app opens:

1. **Click "Connect to Gemini"** (top right panel)
   - Wait for status to show "✅ Connected"

2. **Click "🎤 Start Voice Control"**
   - Your browser will ask for microphone permission - click "Allow"
   - Button will turn red when recording

3. **Say a command** (speak clearly):
   - "Move to home position"
   - "Pick up the green apple"
   - "Open the gripper"

4. **Watch the robot move!**
   - The 3D arm will animate smoothly
   - Status updates appear in the right panel

## Scene Controls

- **Rotate View**: Left-click + drag
- **Pan**: Right-click + drag
- **Zoom**: Mouse wheel

## Quick Command Buttons

Don't want to use voice? Click the buttons:

- 🏠 Home - Return to starting position
- ✅ Ready - Move to working position
- 🤚 Open Gripper
- ✊ Close Gripper
- 🍏 Pick Apple - Full pick-and-place sequence
- 🔵 Pick Cube - Full pick-and-place sequence

## Voice Command Examples

### Basic Movement
- "Move to home position"
- "Move to ready position"
- "Move to sleep position"

### Gripper Control
- "Open the gripper"
- "Close the gripper"
- "Open gripper halfway"

### Object Manipulation
- "Pick up the green apple"
- "Pick up the blue cube"
- "Grab the apple"

### Precise Control
- "Move to position x=0.3, y=0, z=0.2"
- "Set joint angles to 0, -55, 66, 0, -17, 0 degrees"
- "Move forward 10 centimeters"

## Troubleshooting

### "Module not found" errors
```bash
npm install
```

### Voice not working
1. Check browser microphone permissions (usually in URL bar)
2. Ensure you clicked "Start Voice Control"
3. Check browser console (F12) for errors

### Robot doesn't move
1. Verify "Connected" status shows ✅
2. Try a quick command button first
3. Check coordinates are within workspace (z must be > 0.1)

### API key errors
1. Verify key is correctly pasted in `.env`
2. No spaces or quotes around the key
3. Restart the dev server after changing `.env`

## Understanding the Scene

- **Table**: Brown wooden table (1.2m × 1.2m)
- **Green Apple**: Located at [0.25, 0.15, 0.04]
- **Blue Cube**: Located at [0.3, -0.1, 0.025]
- **Robot Base**: Centered at [0, 0, 0]
- **Grid Lines**: Show 10cm spacing

## Workspace Limits

The robot can reach:
- **X axis**: -0.5 to +0.5 meters (left/right)
- **Y axis**: -0.5 to +0.5 meters (forward/back)
- **Z axis**: 0.1 to 0.6 meters (up, minimum 0.1 for table safety)

## How It Works

1. **Your Voice** → Microphone captures audio
2. **Audio Processing** → Resampled to 16kHz PCM16 format
3. **Gemini API** → Converts speech to text and understands intent
4. **Tool Calls** → Gemini calls robot control functions
5. **Kinematics** → Calculates joint angles for target position
6. **Animation** → Smooth interpolated movement in 3D
7. **Visual Feedback** → See the arm move in real-time

## Next Steps

### For Development

Edit any file in `src/` and it will hot-reload automatically.

Key files to explore:
- `Scene.tsx` - Add more objects
- `robot-controller.ts` - Change movement behavior
- `VirtualRobotControl.tsx` - Add new voice commands

### Adding Physics (Future Enhancement)

Currently objects don't react to the gripper. To add physics:
1. Install `@react-three/cannon` or `@react-three/rapier`
2. Add physics bodies to objects
3. Implement collision detection in gripper

### Exporting to Real Robot

To use trajectories on the real robot:
1. Record waypoints during simulation
2. Export to JSON format
3. Load in `gemini-live/` bridge system

## Tips for Best Results

1. **Speak clearly** and wait for the robot to finish moving
2. **Use natural language** - Gemini understands context
3. **Start simple** - Try "home" before complex trajectories
4. **Watch the transcript** - See what Gemini understood
5. **Check workspace** - Keep z > 0.1m to avoid table collision

## Differences from Real Robot

This is a **simulation**, so:
- ✅ Instant response (no hardware latency)
- ✅ Perfect precision (no mechanical errors)
- ❌ No physics (objects don't move when touched)
- ❌ No collision detection yet
- ❌ Gripper doesn't actually grasp objects

## Support

If something doesn't work:
1. Check the console (F12 in browser)
2. Read error messages carefully
3. Try the quick command buttons
4. Restart the dev server
5. Check your API key is valid

## Building for Production

```bash
npm run build
```

Output will be in `build/` directory. Deploy to any static hosting:
- Netlify
- Vercel
- GitHub Pages
- AWS S3

Just remember to set the `REACT_APP_GEMINI_API_KEY` environment variable!

---

**Enjoy controlling your virtual robot! 🤖**
