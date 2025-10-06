# Robot Control Console - Frontend Implementation Plan

**Goal**: Build a unified frontend with voice control + robot visualization that supports both real and virtual robots

**Timeline**: Phase 4 - Estimated 2-3 hours

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│          Robot Control Console (New App)                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────┐  ┌──────────────────────────────┐  │
│  │  Mode Selector │  │      ControlTray             │  │
│  │  [Real/Virtual]│  │  (Voice + Connection UI)     │  │
│  └────────────────┘  └──────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │            RobotControl Component                 │  │
│  │  (Tool call handler + endpoint switching)        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌─────────────────────┬────────────────────────────┐  │
│  │  3D Visualization   │   Camera Feed View         │  │
│  │  (Virtual Mode)     │   (Real Robot Mode)        │  │
│  │                     │                            │  │
│  │  - Three.js Scene   │   - Dual camera streams   │  │
│  │  - Robot arm model  │   - Gripper + overhead    │  │
│  │  - Joint angles     │   - Real-time updates     │  │
│  └─────────────────────┴────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
         ↓                              ↓
    Port 8082                      Port 8081
  (Simulation)                    (Real Robot)
```

---

## Phase 4: Implementation Steps

### Step 1: Create New React App (15 min)

**Commands:**
```bash
cd /home/celvin/wsl_repos/projects/alopro-halmstad
npx create-react-app robot-control-console --template typescript
cd robot-control-console
```

**Install Dependencies:**
```bash
npm install @google/genai@^1.21.0
npm install @react-three/fiber@^8.15.0
npm install @react-three/drei@^9.96.0
npm install three@^0.161.0
npm install zustand@^4.4.0
npm install eventemitter3@^5.0.1
npm install sass
```

---

### Step 2: Copy Working Components (20 min)

**From gemini-live console:**
```bash
# Copy audio/Gemini libraries
cp -r ../gemini-live/gemini-live-api-control/live-api-console/src/lib ./src/

# Copy contexts
cp -r ../gemini-live/gemini-live-api-control/live-api-console/src/contexts ./src/

# Copy hooks
cp -r ../gemini-live/gemini-live-api-control/live-api-console/src/hooks ./src/

# Copy types
cp ../gemini-live/gemini-live-api-control/live-api-console/src/types.ts ./src/

# Copy ControlTray (voice UI)
cp -r ../gemini-live/gemini-live-api-control/live-api-console/src/components/control-tray ./src/components/
```

**From virtual-robot-arm:**
```bash
# Copy 3D visualization components (we'll adapt these)
cp ../virtual-robot-arm/src/components/RobotArm.tsx ./src/components/visualization/
cp ../virtual-robot-arm/src/components/Scene.tsx ./src/components/visualization/

# Copy kinematics
cp ../virtual-robot-arm/src/lib/kinematics.ts ./src/lib/
cp ../virtual-robot-arm/src/lib/robot-controller.ts ./src/lib/

# Copy robot types
cp ../virtual-robot-arm/src/types/robot.ts ./src/types/
```

---

### Step 3: Create New Components (45 min)

#### 3.1 ModeSelector Component

**File:** `src/components/mode-selector/ModeSelector.tsx`

```typescript
import { useState } from 'react';
import './ModeSelector.scss';

export type RobotMode = 'simulation' | 'real';

interface ModeSelectorProps {
  mode: RobotMode;
  onModeChange: (mode: RobotMode) => void;
  disabled?: boolean;
}

export function ModeSelector({ mode, onModeChange, disabled }: ModeSelectorProps) {
  return (
    <div className="mode-selector">
      <label>Robot Mode:</label>
      <div className="mode-buttons">
        <button
          className={mode === 'simulation' ? 'active' : ''}
          onClick={() => onModeChange('simulation')}
          disabled={disabled}
        >
          🖥️ Virtual Robot
        </button>
        <button
          className={mode === 'real' ? 'active' : ''}
          onClick={() => onModeChange('real')}
          disabled={disabled}
        >
          🤖 Real Robot
        </button>
      </div>
      <div className="mode-info">
        {mode === 'simulation' ? (
          <span className="info">Connected to simulation (port 8082)</span>
        ) : (
          <span className="info">Connected to real robot (port 8081)</span>
        )}
      </div>
    </div>
  );
}
```

---

#### 3.2 RobotControl Component

**File:** `src/components/robot-control/RobotControl.tsx`

**Purpose**: Handles tool calls from Gemini and sends to appropriate bridge

```typescript
import { useEffect, useState } from 'react';
import { useLiveAPIContext } from '../../contexts/LiveAPIContext';
import { FunctionDeclaration } from '@google/genai';
import { RobotMode } from '../mode-selector/ModeSelector';

// Import tool declarations from gemini-live
import { ROBOT_TOOLS } from './tools';

interface RobotControlProps {
  mode: RobotMode;
  onJointUpdate?: (positions: number[]) => void;
  onGripperUpdate?: (state: 'open' | 'close') => void;
}

export function RobotControl({ mode, onJointUpdate, onGripperUpdate }: RobotControlProps) {
  const { client, connected } = useLiveAPIContext();
  const [taskStatus, setTaskStatus] = useState('Ready');

  // Get endpoint based on mode
  const ROBOT_ENDPOINT = mode === 'simulation'
    ? 'http://localhost:8082'
    : 'http://localhost:8081';

  // Configure Gemini with tools when connected
  useEffect(() => {
    if (!connected) return;

    const config = {
      model: 'models/gemini-2.0-flash-exp',
      systemInstruction: {
        parts: [{
          text: `You are controlling an ALOHA robot. Current mode: ${mode}.
Available commands: open/close gripper, move arm to positions, get status.
Respond naturally and confirm actions.`
        }]
      },
      tools: [{ functionDeclarations: ROBOT_TOOLS }],
      generationConfig: {
        responseModalities: 'audio',
        speechConfig: {
          voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' }}
        }
      }
    };

    client.connect(config);
  }, [connected, mode, client]);

  // Handle tool calls
  useEffect(() => {
    const handleToolCall = async (toolCall: any) => {
      const calls = toolCall.toolCall?.functionCalls || [];
      const responses: any[] = [];

      setTaskStatus('Executing...');

      for (const call of calls) {
        console.log(`[${mode}] Tool call:`, call.name, call.args);

        try {
          // Send to appropriate bridge
          const response = await fetch(`${ROBOT_ENDPOINT}/aloha-tool-call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: call.name, args: call.args })
          });

          const result = await response.json();
          console.log(`[${mode}] Result:`, result);

          // Update visualization if simulation mode
          if (mode === 'simulation') {
            if (result.joint_positions && onJointUpdate) {
              onJointUpdate(result.joint_positions);
            }
            if (result.state && onGripperUpdate) {
              onGripperUpdate(result.state);
            }
          }

          responses.push({
            functionResponses: [{
              response: { name: call.name, content: result },
              id: call.id
            }]
          });

        } catch (error) {
          console.error(`[${mode}] Tool call error:`, error);
          responses.push({
            functionResponses: [{
              response: {
                name: call.name,
                content: { success: false, error: String(error) }
              },
              id: call.id
            }]
          });
        }
      }

      // Send responses back to Gemini
      if (responses.length > 0) {
        client.sendToolResponse(responses);
      }
      setTaskStatus('Ready');
    };

    client.on('toolcall' as any, handleToolCall);
    return () => {
      client.off('toolcall' as any, handleToolCall);
    };
  }, [client, mode, ROBOT_ENDPOINT, onJointUpdate, onGripperUpdate]);

  return (
    <div className="robot-control">
      <div className="status-bar">
        <span className="mode-badge">{mode === 'simulation' ? '🖥️ Virtual' : '🤖 Real'}</span>
        <span className="task-status">{taskStatus}</span>
        <span className="endpoint">{ROBOT_ENDPOINT}</span>
      </div>
    </div>
  );
}
```

---

#### 3.3 RobotVisualization Component

**File:** `src/components/visualization/RobotVisualization.tsx`

**Purpose**: Switches between 3D view and camera feed based on mode

```typescript
import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { RobotMode } from '../mode-selector/ModeSelector';
import { CameraFeedView } from './CameraFeedView';
import './RobotVisualization.scss';

interface RobotVisualizationProps {
  mode: RobotMode;
  jointPositions?: number[];
  gripperState?: 'open' | 'close';
}

export function RobotVisualization({ mode, jointPositions, gripperState }: RobotVisualizationProps) {

  if (mode === 'real') {
    // Show camera feeds for real robot
    return <CameraFeedView endpoint="http://localhost:8081" />;
  }

  // Show 3D visualization for simulation
  return (
    <div className="robot-visualization">
      <Canvas camera={{ position: [2, 2, 2], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <OrbitControls />

        {/* 3D Robot Arm - will integrate from virtual-robot-arm */}
        <mesh>
          <boxGeometry args={[0.5, 0.1, 0.1]} />
          <meshStandardMaterial color="orange" />
        </mesh>

        <gridHelper args={[10, 10]} />
      </Canvas>

      <div className="visualization-overlay">
        <div className="joint-display">
          <h4>Joint Positions</h4>
          {jointPositions?.map((pos, i) => (
            <div key={i}>Joint {i}: {pos.toFixed(2)}°</div>
          ))}
        </div>
        <div className="gripper-display">
          Gripper: {gripperState || 'unknown'}
        </div>
      </div>
    </div>
  );
}
```

---

#### 3.4 CameraFeedView Component

**File:** `src/components/visualization/CameraFeedView.tsx`

**Purpose**: Display camera feeds from real robot

```typescript
import { useEffect, useState } from 'react';
import './CameraFeedView.scss';

interface CameraFeedViewProps {
  endpoint: string;
}

export function CameraFeedView({ endpoint }: CameraFeedViewProps) {
  const [cameraFrame, setCameraFrame] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${endpoint}/camera/merged`);
        const data = await response.json();
        if (data.frame) {
          setCameraFrame(`data:image/jpeg;base64,${data.frame}`);
        }
      } catch (error) {
        console.error('Camera feed error:', error);
      }
    }, 1000); // 1 FPS

    return () => clearInterval(interval);
  }, [endpoint]);

  return (
    <div className="camera-feed-view">
      <h3>Robot Camera Feeds</h3>
      {cameraFrame ? (
        <img src={cameraFrame} alt="Robot camera" className="camera-frame" />
      ) : (
        <div className="no-feed">No camera feed available</div>
      )}
    </div>
  );
}
```

---

#### 3.5 Main App Component

**File:** `src/App.tsx`

```typescript
import { useState, useRef } from 'react';
import { LiveAPIProvider } from './contexts/LiveAPIContext';
import { ModeSelector, RobotMode } from './components/mode-selector/ModeSelector';
import { RobotControl } from './components/robot-control/RobotControl';
import { RobotVisualization } from './components/visualization/RobotVisualization';
import ControlTray from './components/control-tray/ControlTray';
import './App.scss';

const API_KEY = process.env.REACT_APP_GEMINI_API_KEY as string;
if (!API_KEY) {
  throw new Error('Set REACT_APP_GEMINI_API_KEY in .env');
}

function App() {
  const [mode, setMode] = useState<RobotMode>('simulation');
  const [jointPositions, setJointPositions] = useState<number[]>([0, 0, 0, 0, 0, 0]);
  const [gripperState, setGripperState] = useState<'open' | 'close'>('unknown' as any);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);

  return (
    <div className="App">
      <LiveAPIProvider options={{ apiKey: API_KEY }}>
        <div className="app-header">
          <h1>🤖 ALOHA Robot Control Console</h1>
          <ModeSelector mode={mode} onModeChange={setMode} />
        </div>

        <RobotControl
          mode={mode}
          onJointUpdate={setJointPositions}
          onGripperUpdate={setGripperState}
        />

        <RobotVisualization
          mode={mode}
          jointPositions={jointPositions}
          gripperState={gripperState}
        />

        <ControlTray
          videoRef={videoRef}
          onVideoStreamChange={setVideoStream}
        />

        <video
          ref={videoRef}
          autoPlay
          playsInline
          style={{ display: videoStream ? 'block' : 'none' }}
        />
      </LiveAPIProvider>
    </div>
  );
}

export default App;
```

---

### Step 4: Create Environment Config (5 min)

**File:** `.env`
```env
REACT_APP_GEMINI_API_KEY=AIzaSy...your-key-here

# Endpoints are determined by mode selector in-app
# No need to configure them here
```

**File:** `.env.example`
```env
REACT_APP_GEMINI_API_KEY=your-gemini-api-key-here

# Get your API key at: https://aistudio.google.com
```

---

### Step 5: Styling (15 min)

**File:** `src/App.scss`

```scss
.App {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e2e 0%, #2d2d3a 100%);
  color: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  h1 {
    margin: 0;
    font-size: 24px;
  }
}

.mode-selector {
  display: flex;
  gap: 15px;
  align-items: center;

  .mode-buttons {
    display: flex;
    gap: 10px;

    button {
      padding: 10px 20px;
      border: 2px solid #4a9eff;
      background: transparent;
      color: #4a9eff;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.3s;

      &.active {
        background: #4a9eff;
        color: white;
      }

      &:hover:not(:disabled) {
        background: rgba(74, 158, 255, 0.2);
      }

      &:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
    }
  }

  .mode-info {
    font-size: 12px;
    color: #888;
  }
}

.robot-visualization {
  height: 600px;
  position: relative;
  margin: 20px;
  border-radius: 12px;
  overflow: hidden;
  background: #000;

  .visualization-overlay {
    position: absolute;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.7);
    padding: 15px;
    border-radius: 8px;
    font-size: 14px;

    h4 {
      margin: 0 0 10px 0;
    }
  }
}

.camera-feed-view {
  padding: 20px;
  text-align: center;

  .camera-frame {
    max-width: 100%;
    border-radius: 8px;
  }

  .no-feed {
    padding: 40px;
    color: #888;
  }
}
```

---

## Testing Checklist

### Phase 4a: Initial Setup
- [ ] Create React app
- [ ] Install dependencies
- [ ] Copy all components
- [ ] App compiles without errors

### Phase 4b: Voice Control
- [ ] ControlTray shows microphone button
- [ ] Can connect to Gemini
- [ ] Voice input captured
- [ ] Tool calls triggered

### Phase 4c: Simulation Mode
- [ ] Mode selector shows "Virtual Robot"
- [ ] Endpoint: http://localhost:8082
- [ ] 3D visualization displays
- [ ] Voice commands move robot
- [ ] Joint positions update in UI

### Phase 4d: Real Robot Mode
- [ ] Mode selector shows "Real Robot"
- [ ] Endpoint: http://localhost:8081
- [ ] Camera feed displays
- [ ] Voice commands control hardware
- [ ] Status updates in real-time

### Phase 4e: Mode Switching
- [ ] Can switch Real ↔ Virtual
- [ ] Endpoint changes correctly
- [ ] Visualization switches
- [ ] No errors on transition

---

## File Structure

```
robot-control-console/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── mode-selector/
│   │   │   ├── ModeSelector.tsx
│   │   │   └── ModeSelector.scss
│   │   ├── robot-control/
│   │   │   ├── RobotControl.tsx
│   │   │   └── tools.ts
│   │   ├── visualization/
│   │   │   ├── RobotVisualization.tsx
│   │   │   ├── RobotVisualization.scss
│   │   │   ├── CameraFeedView.tsx
│   │   │   └── CameraFeedView.scss
│   │   └── control-tray/          # Copied from gemini-live
│   │       └── ControlTray.tsx
│   ├── contexts/                  # Copied from gemini-live
│   │   └── LiveAPIContext.tsx
│   ├── hooks/                     # Copied from gemini-live
│   │   └── use-live-api.ts
│   ├── lib/                       # Copied from gemini-live
│   │   ├── genai-live-client.ts
│   │   ├── audio-recorder.ts
│   │   ├── audio-streamer.ts
│   │   └── utils.ts
│   ├── types/
│   │   ├── robot.ts
│   │   └── index.ts
│   ├── App.tsx
│   ├── App.scss
│   └── index.tsx
├── .env
├── .env.example
├── .gitignore
├── package.json
└── tsconfig.json
```

---

## Timeline Estimate

| Task | Time | Status |
|------|------|--------|
| Create React app | 15 min | ⏳ |
| Copy components | 20 min | ⏳ |
| Build ModeSelector | 15 min | ⏳ |
| Build RobotControl | 30 min | ⏳ |
| Build Visualization | 30 min | ⏳ |
| Build CameraFeed | 15 min | ⏳ |
| Create App layout | 15 min | ⏳ |
| Styling | 15 min | ⏳ |
| Testing | 30 min | ⏳ |
| **Total** | **~3 hours** | |

---

## Success Criteria

✅ App compiles and runs
✅ Voice control works
✅ Can switch between Real/Virtual modes
✅ 3D visualization updates when commands execute (simulation)
✅ Camera feed displays (real robot)
✅ Tool calls reach correct backend (8082 or 8081)
✅ No TypeScript errors
✅ Clean, maintainable codebase

---

## Next Steps After Completion

1. **Test with both backends**
2. **Add more 3D features** (workspace boundaries, trajectory preview)
3. **Enhance camera view** (split view, zoom controls)
4. **Add status dashboard** (battery, connection quality, etc.)
5. **Integrate with team's codebase** when ready

---

**Ready to start implementation!** 🚀
