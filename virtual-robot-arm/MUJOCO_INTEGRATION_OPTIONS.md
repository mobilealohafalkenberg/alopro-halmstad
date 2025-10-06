# MuJoCo Web Integration Options for ALOHA Robot

## Problem with Current Approach
- Manual STL positioning causes scale/proportion issues
- Hardcoded transformations don't match MuJoCo's kinematic tree
- Parts appear disconnected (no physics engine)
- Not using the working `aloha_sim` structure

## Solution Options

### Option 1: MuJoCo WASM (Community - zalo/mujoco_wasm) ⭐ EASIEST
**Status:** Mature, v2.3.1
**GitHub:** https://github.com/zalo/mujoco_wasm

**Pros:**
- ✅ Direct browser integration - load MJCF XML directly
- ✅ Automatic mesh loading, scaling, physics
- ✅ TypeScript definitions available
- ✅ Simple API, good documentation
- ✅ Works with React/Three.js

**Cons:**
- ❌ Older MuJoCo version (2.3.1 vs current 3.2.5)
- ❌ Some features may be missing

**Usage:**
```typescript
import load_mujoco from "./mujoco_wasm.js";

// Load MuJoCo
const mujoco = await load_mujoco();

// Mount filesystem and load XML
mujoco.FS.mkdir('/working');
mujoco.FS.writeFile("/working/aloha.xml", xmlContent);

// Create simulation
let model = new mujoco.Model("/working/aloha.xml");
let state = new mujoco.State(model);
let simulation = new mujoco.Simulation(model, state);

// Control joints
simulation.setJointAngles([0.0, -0.96, 1.16, 0.0, -0.3, 0.0]);
```

### Option 2: MuJoCo WASM (hashb/mujoco_web) ⭐ MOST RECENT
**Status:** Active development, MuJoCo 3.2.5
**GitHub:** https://github.com/hashb/mujoco_web

**Pros:**
- ✅ Latest MuJoCo version (3.2.5)
- ✅ Built specifically for React (Vite + TypeScript)
- ✅ pthread support for better performance
- ✅ Active maintenance

**Cons:**
- ❌ PNG textures not yet supported
- ❌ Less documentation than zalo's version
- ❌ May require building from source

**Setup:**
```bash
git clone https://github.com/hashb/mujoco_web.git
cd mujoco_web
pnpm install
# Follow docs/mujoco.md and docs/react.md
```

### Option 3: Python Backend + WebSocket Bridge ⭐ PRODUCTION-READY
**Best for:** Matching physical robot pipeline exactly

**Architecture:**
```
Python (MuJoCo) ←→ WebSocket ←→ React (Three.js visualization)
     ↓                             ↓
  Physics Sim                  3D Rendering
  Joint Control               User Interface
```

**Pros:**
- ✅ Use official MuJoCo Python bindings (same as physical robot)
- ✅ Can reuse existing `aloha_sim` code
- ✅ Real-time state streaming
- ✅ Easy to integrate with existing robot pipeline

**Cons:**
- ❌ Requires Python backend server
- ❌ More complex deployment
- ❌ Network latency

**Implementation:**
```python
# Backend: mujoco_server.py
import mujoco
import asyncio
import websockets

model = mujoco.MjModel.from_xml_path('aloha.xml')
data = mujoco.MjData(model)

async def stream_state(websocket):
    while True:
        mujoco.mj_step(model, data)
        state = {
            'joints': data.qpos.tolist(),
            'positions': data.xpos.tolist()
        }
        await websocket.send(json.dumps(state))
        await asyncio.sleep(0.016)  # 60 FPS
```

```typescript
// Frontend: React component
const ws = new WebSocket('ws://localhost:8080');
ws.onmessage = (event) => {
  const state = JSON.parse(event.data);
  updateRobotVisualization(state);
};
```

### Option 4: MJCF XML Parser (Custom Solution)
**Best for:** Fine control, learning purposes

**Pros:**
- ✅ Complete control over rendering
- ✅ Can optimize for specific use case
- ✅ No external dependencies

**Cons:**
- ❌ Most work to implement
- ❌ Must manually handle kinematics
- ❌ No physics simulation

## Recommended Approach

### For Your Use Case: **Option 1 (zalo/mujoco_wasm) + Migration Path to Option 2**

**Why:**
1. **Immediate solution:** Get working quickly with v2.3.1
2. **No backend needed:** Pure browser-based
3. **Loads aloha.xml directly:** Uses exact aloha_sim structure
4. **Integration with existing pipeline:** Can control via same API

**Migration strategy:**
1. Start with zalo/mujoco_wasm (quick win)
2. Once working, upgrade to hashb/mujoco_web (latest features)
3. If production deployment needed, add Python backend (Option 3)

## Implementation Plan

### Phase 1: Basic MuJoCo WASM Integration
```typescript
// New component: MuJoCoScene.tsx
import load_mujoco from './mujoco_wasm';

export function MuJoCoScene() {
  useEffect(() => {
    const init = async () => {
      const mujoco = await load_mujoco();

      // Load ALOHA XML
      const xmlResponse = await fetch('/models/aloha/aloha.xml');
      const xmlContent = await xmlResponse.text();

      mujoco.FS.mkdir('/working');
      mujoco.FS.writeFile('/working/aloha.xml', xmlContent);

      // Load all mesh files
      const meshes = [
        'vx300s_1_base.stl',
        'vx300s_2_shoulder.stl',
        // ... all other meshes
      ];

      for (const mesh of meshes) {
        const data = await fetch(`/models/aloha/assets/${mesh}`);
        const buffer = await data.arrayBuffer();
        mujoco.FS.writeFile(`/working/${mesh}`, new Uint8Array(buffer));
      }

      // Create simulation
      const model = new mujoco.Model('/working/aloha.xml');
      const state = new mujoco.State(model);
      const simulation = new mujoco.Simulation(model, state);

      // Render loop
      const render = () => {
        simulation.step();
        // Extract positions and render with Three.js
        requestAnimationFrame(render);
      };
      render();
    };

    init();
  }, []);

  return <canvas ref={canvasRef} />;
}
```

### Phase 2: Connect to Robot Controller
```typescript
// Bridge existing RobotController to MuJoCo
robotController.moveArm({ joints: [0, -0.96, 1.16, 0, -0.3, 0] });
// ↓
mujocoSimulation.setJointAngles([0, -0.96, 1.16, 0, -0.3, 0]);
```

### Phase 3: Replace Scene Component
```typescript
// App.tsx
{useMuJoCo ? (
  <MuJoCoScene robotState={robotState} />
) : (
  <Scene robotState={robotState} />
)}
```

## Next Steps

1. **Install zalo/mujoco_wasm:**
   ```bash
   npm install github:zalo/mujoco_wasm
   ```

2. **Create MuJoCoScene component** following examples

3. **Test with aloha.xml** to ensure all meshes load correctly

4. **Bridge to existing RobotController** for Gemini voice control

Would you like me to implement this approach?
