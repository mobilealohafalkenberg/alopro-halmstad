# Gemini Live Console - Architecture Analysis

**Purpose**: Documentation for integrating your new robot visualization frontend with the existing Gemini Live console architecture.

**Location**: `/gemini-live/gemini-live-api-control/live-api-console/`

---

## High-Level Architecture

```
User Voice Input
       ↓
ControlTray (Mic/Connection UI)
       ↓
LiveAPIContext (Gemini Client Wrapper)
       ↓
GenAILiveClient (lib/genai-live-client.ts)
       ↓
Tool Call Event → ALOHAControl Component
       ↓
HTTP POST to Bridge (port 8082 or 8081)
       ↓
Robot/Simulation
```

---

## Core Components

### 1. **App.tsx** - Main Entry Point
- **Path**: `src/App.tsx`
- **Purpose**: Application shell and layout
- **Key Elements**:
  - Wraps everything in `LiveAPIProvider`
  - Renders `ALOHAControl`, `ControlTray`, `DualCameraView`
  - Manages video stream state
  - Gets API key from env: `REACT_APP_GEMINI_API_KEY`

```tsx
<LiveAPIProvider options={apiOptions}>
  <ALOHAControl />              {/* Robot control logic */}
  <DualCameraView />            {/* Camera feeds */}
  <ControlTray />               {/* Voice/connection controls */}
</LiveAPIProvider>
```

---

### 2. **LiveAPIContext** - Gemini Client Provider
- **Path**: `src/contexts/LiveAPIContext.tsx`
- **Purpose**: React Context for Gemini Live API
- **Key Hook**: `useLiveAPIContext()` - Access Gemini client anywhere
- **Provides**:
  - `client`: GenAILiveClient instance
  - `connected`: Connection state
  - `setConfig`: Update Gemini configuration
  - Audio/video streaming utilities

**Integration Point**: Your new frontend MUST use this same context pattern

---

### 3. **ALOHAControl** - Robot Control Logic
- **Path**: `src/components/aloha-control/ALOHAControl.tsx`
- **Purpose**: Handles tool calls from Gemini and sends to robot bridge
- **Key Features**:
  - Listens for `toolCall` events from Gemini
  - Sends HTTP POST to `ROBOT_ENDPOINT` (env var)
  - Fire-and-forget pattern (immediate empty response)
  - Supports mode switching via env: `REACT_APP_ROBOT_ENDPOINT`

**Tool Declarations**:
```typescript
const tools = [
  toolControlGripper,     // Open/close gripper
  toolGetGripperStatus,   // Query gripper state
  toolMoveArm,            // Move to pose/position
  toolGetArmStatus,       // Query arm state
  toolMoveArmTrajectory,  // Multi-waypoint paths
  toolResetRobot,         // Reset to home
];
```

**Configuration on Connect**:
```typescript
const config = {
  model: 'models/gemini-2.0-flash-exp',
  systemInstruction: { parts: [{ text: SYSTEM_INSTRUCTION }] },
  tools: [{ functionDeclarations: tools }],
  generationConfig: {
    responseModalities: voice ? 'audio' : 'text',
    speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' }}}
  }
};
client.connect(config);
```

**Tool Call Handler**:
```typescript
const handleToolCall = async (toolCall: any) => {
  const calls = toolCall.toolCall?.functionCalls || [];

  for (const call of calls) {
    // Send to robot bridge
    const response = await fetch(`${ROBOT_ENDPOINT}/aloha-tool-call`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: call.name, args: call.args })
    });

    const result = await response.json();

    // Collect responses
    responses.push({
      functionResponses: [{
        response: { name: call.name, content: result },
        id: call.id
      }]
    });
  }

  // Send back to Gemini
  client.sendToolResponse(responses);
};
```

**Integration Point**: You'll copy this entire component but add robot visualization

---

### 4. **ControlTray** - Voice/Connection UI
- **Path**: `src/components/control-tray/ControlTray.tsx`
- **Purpose**: Microphone button, connection controls
- **Features**:
  - Connect/disconnect button
  - Microphone on/off
  - Audio visualization (volume meter)
  - Video stream toggle
  - Settings panel

**Integration Point**: Reuse this UI as-is, it's clean

---

### 5. **GenAILiveClient** - Gemini SDK Wrapper
- **Path**: `src/lib/genai-live-client.ts`
- **Purpose**: Wraps `@google/genai` LiveAPIClient
- **Key Methods**:
  - `connect(config)` - Establish connection
  - `disconnect()` - Close connection
  - `sendRealtimeInput(chunks)` - Send audio
  - `sendToolResponse(response)` - Respond to tool calls
  - `on(event, handler)` - Event listeners

**Events You Need**:
- `'connect'` - Connection established
- `'disconnect'` - Connection lost
- `'toolCall'` - Gemini wants to call a tool
- `'content'` - Gemini's response (audio/text)
- `'audiodata'` - Audio output from Gemini

**Integration Point**: Use this exact same client wrapper

---

### 6. **DualCameraView** - Robot Camera Feeds
- **Path**: `src/components/camera-feed/CameraFeed.tsx`
- **Purpose**: Display robot camera feeds
- **Features**:
  - Polls camera endpoint every 1 second
  - Displays two camera views (gripper + overhead)
  - Base64 JPEG decoding
  - Merge/split view toggle

**API Used**:
```typescript
GET http://localhost:8081/camera/merged  // Real robot
GET http://localhost:8082/camera/merged  // Simulation
```

**Integration Point**: You'll REPLACE this with your 3D visualization

---

## Key Files in lib/

### Audio Processing
- `audio-recorder.ts` - Microphone capture
- `audio-streamer.ts` - Stream audio to Gemini
- `audioworklet-registry.ts` - Web Audio API utilities
- `worklets/vol-meter.ts` - Volume visualization
- `worklets/audio-processing.ts` - Audio worklet processor

### Utilities
- `utils.ts` - Audio context helpers
- `store-logger.ts` - Logging with Zustand

**Integration Point**: Copy entire `lib/` directory unchanged

---

## Environment Variables

### Required
```env
REACT_APP_GEMINI_API_KEY=your-api-key-here
REACT_APP_ROBOT_ENDPOINT=http://localhost:8082  # Simulation
# REACT_APP_ROBOT_ENDPOINT=http://localhost:8081  # Real robot
```

**Mode Switching**: Just change `REACT_APP_ROBOT_ENDPOINT` and restart

---

## Tool Call Flow

1. User speaks: "Open the gripper"
2. `ControlTray` captures audio → `GenAILiveClient`
3. Gemini processes voice → generates tool call
4. `ALOHAControl` receives `toolCall` event
5. POST to `${ROBOT_ENDPOINT}/aloha-tool-call`
6. Bridge executes command on robot/simulation
7. Response sent back to Gemini
8. Gemini speaks confirmation

---

## Current Issues (To Avoid)

1. **TypeScript Errors**:
   - Type mismatches in tool responses
   - Missing video features (`sendMedia` not in SDK)
   - Mock logs import missing

2. **Compilation Warnings**:
   - Babel deprecation warnings (harmless)
   - Browser list outdated (harmless)

**Your Strategy**: Start fresh, copy only working components

---

## Integration Strategy for Your New Frontend

### Phase 1: Copy Foundation
1. ✅ Copy `lib/` directory (audio processing)
2. ✅ Copy `contexts/LiveAPIContext.tsx`
3. ✅ Copy `hooks/use-live-api.ts`
4. ✅ Copy `types.ts`

### Phase 2: Adapt Components
1. Copy `ControlTray` (voice UI) - NO CHANGES
2. Copy `ALOHAControl` tool declarations - ADD visualization hooks
3. **REPLACE** `DualCameraView` with your 3D robot visualization
4. Create mode switcher UI (Real/Virtual toggle)

### Phase 3: Add Visualization
1. Integrate `virtual-robot-arm` 3D components:
   - `RobotArm.tsx`
   - `Scene.tsx`
   - `lib/kinematics.ts`
2. Connect visualization to tool call results
3. Update robot pose when Gemini commands execute

### Phase 4: Enhanced Features
1. Add real-time joint position display
2. Add workspace visualization
3. Add trajectory preview
4. Add collision warnings

---

## Recommended New Frontend Structure

```
robot-control-console/
├── src/
│   ├── lib/                    # Copy from gemini-live (audio, client)
│   ├── contexts/
│   │   └── LiveAPIContext.tsx  # Copy unchanged
│   ├── hooks/
│   │   └── use-live-api.ts     # Copy unchanged
│   ├── components/
│   │   ├── control-tray/
│   │   │   └── ControlTray.tsx        # Copy unchanged
│   │   ├── robot-control/
│   │   │   └── RobotControl.tsx       # Modified ALOHAControl
│   │   ├── visualization/
│   │   │   ├── RobotVisualization.tsx # NEW - 3D view or camera
│   │   │   ├── RobotArm.tsx           # From virtual-robot-arm
│   │   │   └── Scene.tsx              # From virtual-robot-arm
│   │   └── mode-selector/
│   │       └── ModeSelector.tsx       # NEW - Real/Virtual toggle
│   ├── types.ts                # Copy from gemini-live
│   └── App.tsx                 # NEW - Your layout
├── .env                        # API keys + mode config
└── package.json                # Same deps as gemini-live
```

---

## Key Integration Points

### 1. Mode Switching
```typescript
// In your new App.tsx
const [mode, setMode] = useState<'simulation' | 'real'>('simulation');

const ENDPOINT = mode === 'simulation'
  ? 'http://localhost:8082'
  : 'http://localhost:8081';

// Pass to RobotControl component
<RobotControl endpoint={ENDPOINT} />
```

### 2. Visualization Update Hook
```typescript
// In RobotControl.tsx
const handleToolCall = async (toolCall: any) => {
  // Execute command
  const result = await executeCommand(call);

  // Update visualization
  if (mode === 'simulation') {
    updateVirtualRobot(result.joint_positions);
  } else {
    showCameraFeed();
  }
};
```

### 3. Shared Tool Declarations
```typescript
// Create tools.ts - shared between both apps
export const ROBOT_TOOLS = [
  toolControlGripper,
  toolMoveArm,
  toolMoveArmTrajectory,
  // ... etc
];

// Use in both your app AND gemini-live
```

---

## Dependencies You'll Need

```json
{
  "dependencies": {
    "@google/genai": "^1.21.0",      // Gemini Live API
    "@react-three/fiber": "^8.15.0", // 3D rendering
    "@react-three/drei": "^9.96.0",  // 3D helpers
    "three": "^0.161.0",             // Three.js
    "zustand": "^4.4.0",             // State management
    "eventemitter3": "^5.0.1"        // Events
  }
}
```

---

## Testing Checklist

### Voice Control
- [ ] Microphone connects
- [ ] Audio streams to Gemini
- [ ] Tool calls triggered by voice
- [ ] Gemini responds with audio

### Robot Control
- [ ] Commands reach bridge (8082/8081)
- [ ] Gripper opens/closes
- [ ] Arm moves to positions
- [ ] Status queries work

### Visualization
- [ ] 3D robot updates when commands execute
- [ ] Joint angles match real robot
- [ ] Smooth animations
- [ ] Workspace boundaries visible

### Mode Switching
- [ ] Toggle between simulation/real
- [ ] Endpoint changes correctly
- [ ] Visualization switches (3D ↔ Camera)
- [ ] No errors on switch

---

## Next Steps

1. **Create new React app**: `npx create-react-app robot-control-console --template typescript`
2. **Copy working components** from gemini-live (lib, contexts, ControlTray)
3. **Integrate 3D visualization** from virtual-robot-arm
4. **Add mode switcher** (simulation vs real)
5. **Test with both backends** (port 8082 and 8081)

---

## Contact Points with Colleagues

**What They're Working On** (in gemini-live/):
- Video streaming features
- Advanced tool responses
- Camera integration
- Type definitions

**What You're Building** (in new app):
- Robot visualization (3D + Camera)
- Mode switching (Real/Virtual)
- Enhanced UI for robot control
- Testing infrastructure

**Future Integration**:
When their codebase stabilizes, you can merge:
1. Your visualization components → their app
2. Your mode switcher → their settings
3. Your enhanced robot control → their ALOHAControl

---

## Summary

**Copy These (They Work)**:
- ✅ `lib/` - Audio processing
- ✅ `contexts/LiveAPIContext.tsx` - Gemini provider
- ✅ `hooks/use-live-api.ts` - Gemini hook
- ✅ `components/control-tray/` - Voice UI
- ✅ Tool declarations from ALOHAControl

**Replace These (Need Visualization)**:
- ❌ `DualCameraView` → Your 3D visualization
- ❌ App layout → Your custom layout with mode switcher

**Add These (New Features)**:
- ➕ Real/Virtual mode toggle
- ➕ 3D robot visualization
- ➕ Joint position display
- ➕ Trajectory preview

---

**Ready to build!** This architecture gives you a clean separation while maintaining full compatibility for future integration.
