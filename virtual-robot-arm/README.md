# Virtual Robot Arm Simulator

A 3D virtual robot arm simulator with voice control powered by Google Gemini 2.5 Live API. This application simulates a ViperX 300s robotic arm with realistic kinematics, allowing you to control it using natural language voice commands.

## Features

- **3D Visualization**: Interactive Three.js scene with a realistic 6-DOF robot arm
- **Voice Control**: Natural language commands via Gemini 2.5 Live API
- **Realistic Kinematics**: Forward and inverse kinematics matching ViperX 300s specifications
- **Interactive Scene**: Green apple and blue cube objects on a table
- **Trajectory Planning**: Multi-waypoint path execution with gripper coordination
- **Real-time Animation**: Smooth interpolated movements with configurable speeds

## Prerequisites

- Node.js 18+ and npm
- Google Gemini API key (get one at [aistudio.google.com](https://aistudio.google.com))

## Setup

1. **Install dependencies:**
   ```bash
   cd virtual-robot-arm
   npm install
   ```

2. **Configure API key:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Gemini API key
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The app will open at `http://localhost:3000`

## Usage

### Getting Started

1. Click **"Connect to Gemini"** to establish the API connection
2. Click **"Start Voice Control"** to enable microphone input
3. Speak commands to control the robot arm
4. Use the quick command buttons for common actions

### Voice Commands

Try these example commands:

- **"Move to home position"** - Return to starting position
- **"Move to ready position"** - Move to working pose
- **"Open the gripper"** - Open the gripper fingers
- **"Close the gripper"** - Close the gripper fingers
- **"Pick up the green apple"** - Execute pick-and-place trajectory
- **"Pick up the blue cube"** - Execute pick-and-place trajectory
- **"Move to position x=0.3, y=0, z=0.2"** - Move to specific coordinates
- **"Set joint angles to 0, -55, 66, 0, -17, 0 degrees"** - Direct joint control

### Scene Controls

- **Rotate**: Left mouse button + drag
- **Pan**: Right mouse button + drag (or Middle mouse button)
- **Zoom**: Scroll wheel

## Architecture

### Components

- **Scene.tsx**: Three.js scene with robot arm, table, and objects
- **RobotArm.tsx**: 3D robot arm model with animated joints
- **VirtualRobotControl.tsx**: Voice control UI and Gemini integration

### Libraries

- **kinematics.ts**: Forward/inverse kinematics and joint interpolation
- **robot-controller.ts**: State management and trajectory execution
- **genai-live-client.ts**: Gemini Live API WebSocket client
- **audio-recorder.ts**: Microphone capture and audio resampling

### Robot Specifications

- **Model**: ViperX 300s (vx300s) simulator
- **DOF**: 6 joints (waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate)
- **Workspace**: x,y ∈ [-0.5, 0.5]m, z ∈ [0.1, 0.6]m
- **Gripper**: Smooth open/close animation (0-100%)

## Tool Functions

The robot exposes these functions to Gemini:

- **move_arm()**: Single-point movements (pose, joints, or position)
- **control_gripper()**: Open or close gripper
- **get_arm_status()**: Query current joint angles and end effector position
- **get_gripper_status()**: Query gripper state and position
- **move_arm_trajectory()**: Execute multi-waypoint paths with gripper coordination

## Development

### Project Structure

```
virtual-robot-arm/
├── public/              # Static files
├── src/
│   ├── components/      # React components
│   │   ├── Scene.tsx
│   │   ├── RobotArm.tsx
│   │   └── VirtualRobotControl.tsx
│   ├── lib/             # Core libraries
│   │   ├── kinematics.ts
│   │   ├── robot-controller.ts
│   │   ├── genai-live-client.ts
│   │   └── audio-recorder.ts
│   ├── types/           # TypeScript types
│   │   └── robot.ts
│   ├── App.tsx          # Main app component
│   └── index.tsx        # Entry point
├── package.json
└── README.md
```

### Building for Production

```bash
npm run build
```

The optimized build will be in the `build/` directory.

## Troubleshooting

### No voice input detected
- Check browser microphone permissions
- Ensure you clicked "Start Voice Control"
- Check browser console for errors

### Robot doesn't move
- Verify Gemini connection (status should show "Connected")
- Check that commands are valid (within workspace limits)
- Open browser console to see tool call logs

### Connection fails
- Verify API key is correct in `.env`
- Check internet connection
- Ensure API key has necessary permissions

## Differences from Real Robot

This is a **simulation** with these key differences:

1. **No physics engine**: Objects don't respond to gripper interactions yet
2. **Simplified IK**: Uses geometric approach instead of full inverse kinematics solver
3. **No collision detection**: Arm can pass through objects and table
4. **Instant responses**: No hardware latency or communication delays
5. **Perfect execution**: No mechanical errors or drift

These limitations may be addressed in future versions.

## Future Enhancements

- [ ] Physics simulation for object manipulation
- [ ] Collision detection and avoidance
- [ ] Multiple camera views
- [ ] Record and replay trajectories
- [ ] More interactive objects
- [ ] Export trajectories to real robot format
- [ ] Multi-arm coordination

## License

This project is part of the alopro-halmstad Mobile ALOHA robot control system.

## Related Projects

- **gemini-live/**: Real robot control with Gemini Live API
- **live-api-web-console/**: React starter for Gemini Live API
- **python_scripts/**: Python utilities for robot control
