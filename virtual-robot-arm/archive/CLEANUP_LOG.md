# Virtual Robot Arm Cleanup Log

**Date**: 2025-10-03
**Reason**: Migrated from client-side MuJoCo WASM to server-side MuJoCo architecture

---

## Summary

Removed deprecated MuJoCo WASM components after successfully implementing server-side MuJoCo architecture. The new architecture uses:
- Python Flask-SocketIO server (localhost:5000) running MuJoCo 3.2.5
- React client with WebSocket controls (localhost:3000)
- Same API pattern as real robot bridge

---

## Archived Files

All deprecated files moved to `archive/wasm-deprecated/`:

### Components
- **TestMuJoCoBasic.tsx** (19KB)
  - Extensive WASM testing component
  - Tested MuJoCo WASM loading, filesystem, model parsing
  - Identified WASM limitations (alignment bugs, missing `angle="radian"`, no `autolimits`)

- **MuJoCoRobotArm.tsx** (4KB)
  - WASM-based robot arm component

- **MuJoCoScene.tsx** (15KB)
  - WASM-based scene rendering component

### Libraries
- **mujoco-loader.ts** (2.6KB)
  - WASM module loader with browser compatibility patches
  - Patched Node.js-specific code for browser

- **mujoco-bridge.ts** (4KB)
  - WASM bridge for robot control

- **mujoco-wasm.d.ts** (1.2KB)
  - TypeScript type definitions for MuJoCo WASM

### Binaries
- **mujoco/** directory
  - MuJoCo WASM binaries (mujoco_wasm.js, mujoco_wasm.wasm)
  - ~30MB total

---

## What We Learned

### WASM Limitations (zalo/mujoco_wasm v2.3.1)
1. **Memory Alignment Bug**: "start offset of Float64Array should be a multiple of 8"
   - Affects qpos/qvel access in larger models
   - Minimal 3-link models work, but 6-DOF ALOHA crashes

2. **Missing Compiler Directives**:
   - `angle="radian"` not supported (requires C++ compiler changes)
   - `autolimits="true"` not supported
   - These are core C++ features, can't be added in JavaScript

3. **Include Directives**:
   - `<include file="..."/>` causes issues
   - Actuators and keyframes in separate files problematic

### Why Server-Side Won
1. **Same API as Real Robot**: Critical requirement for testing
2. **MuJoCo 3.2.5**: Latest version with proper physics validation
3. **No WASM Bugs**: Direct Python MuJoCo binding, no alignment issues
4. **Network Latency**: 30-65ms acceptable for testing
5. **Headless Mode**: Works in WSL/CI environments without X11

---

## Current Architecture

### Active Components
- **SimulationControls.tsx** - React UI for robot control
- **SimulationClient.ts** - WebSocket client library
- **App.tsx** - Main app (now only imports SimulationControls)

### Retained Libraries (for future use)
- **genai-live-client.ts** - Gemini integration (Phase 3)
- **audio-recorder.ts** - Voice control (Phase 3)
- **kinematics.ts** - Useful utility library
- **robot-controller.ts** - Useful utility library
- **types/robot.ts** - Type definitions

### Potentially Unused (not imported by active code)
- **RobotArm.tsx** - Three.js robot visualization
- **Scene.tsx** - Three.js scene
- **VirtualRobotControl.tsx** - Combined control component

These may be re-enabled later if we want to add Three.js visualization alongside server-side physics.

---

## Verification

✅ React app compiles successfully without WASM files
✅ No TypeScript errors
✅ App.tsx simplified to only use SimulationControls
✅ All WASM dependencies archived (not deleted)

---

## Future Considerations

If we ever need WASM again:
1. Consider hashb/mujoco_web (MuJoCo 3.2.5 WASM) - but still separate codebase
2. Files are archived, not deleted, so can be restored
3. Current server-side approach is working well and meets requirements

---

## Testing Status

- [x] WASM files archived
- [x] App.tsx updated
- [x] React app recompiled successfully
- [ ] Browser testing of cleaned interface
- [ ] End-to-end MuJoCo server integration testing
