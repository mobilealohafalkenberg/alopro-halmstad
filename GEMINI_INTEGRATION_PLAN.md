# Phase 3: Gemini Integration Plan

**Goal**: Enable voice control of MuJoCo simulation through Gemini Live API, using the same interface as the real robot.

---

## Architecture Overview

### Current Systems

**Real Robot System:**
```
Gemini Live API → bridge_aloha_real.py (8081) → Robot Controllers → ROS2 → Hardware
```

**MuJoCo Simulation System:**
```
React UI → SimulationClient → WebSocket → simulation_server.py (5000) → UnifiedBridge → MuJoCo
```

### Target Integration

**Option A: Simulation Bridge (RECOMMENDED)**
```
Gemini Live API → bridge_aloha_simulation.py (8082) → WebSocket Client → simulation_server.py (5000)
```

**Benefits:**
- No modification to working real robot code
- Clean separation of concerns
- Can run simultaneously with real robot bridge
- Easy to test and debug
- Same tool call API as real robot

---

## Implementation Steps

### Step 1: Create Simulation Bridge (Est. 30 min)

**File**: `mujoco-server/bridges/bridge_aloha_simulation.py`

**Features:**
- HTTP server on port 8082 (different from real robot's 8081)
- Same API endpoints as bridge_aloha_real.py
- Uses socketio.Client to connect to localhost:5000
- Translates Gemini tool calls to WebSocket messages
- Fire-and-forget pattern (return immediately)

**Tool Call Mapping:**
```python
Gemini Tool Call              →  MuJoCo WebSocket Event
─────────────────────────────────────────────────────────
control_gripper(action)       →  control_gripper(arm, command)
move_arm(joints/position)     →  move_arm(arm, positions)
get_gripper_status()          →  get_gripper_status(arm)
get_arm_status()              →  get_arm_status(arm)
move_arm_trajectory(...)      →  Multiple move_arm + control_gripper calls
```

### Step 2: Add Dual-Arm Support (Est. 15 min)

**Challenge**: Gemini tools currently assume single arm, but MuJoCo has dual arms.

**Solutions:**
- Add optional `arm` parameter to tool definitions (default: 'left')
- Or: Create separate tools for each arm (move_left_arm, move_right_arm)
- Or: Let Gemini specify "left" or "right" in natural language, parse from command

**Recommended**: Add `arm` parameter with default 'left' for backward compatibility.

### Step 3: Update Gemini Tool Definitions (Est. 15 min)

**File**: `virtual-robot-arm/src/lib/genai-live-client.ts` or create simulation-specific version

**Changes:**
- Update tool call endpoint from `http://localhost:8081` to `http://localhost:8082`
- Add mode switcher UI (simulation vs real robot)
- Optional: Add arm selector for dual-arm control

### Step 4: Test Integration (Est. 30 min)

**Test Cases:**
1. Voice command: "Open the gripper" → Left gripper opens
2. Voice command: "Move the left arm to ready position" → Left arm moves
3. Voice command: "Move the right arm to home" → Right arm moves
4. Voice command: "Close both grippers" → Both grippers close
5. Check status queries work correctly

### Step 5: Add Trajectory Support (Est. 20 min)

Gemini already has `move_arm_trajectory` tool. Bridge needs to:
1. Parse trajectory waypoints
2. Execute each waypoint sequentially via WebSocket
3. Handle gripper actions at each waypoint
4. Return status updates

---

## File Structure

```
mujoco-server/
├── bridges/
│   └── bridge_aloha_simulation.py    # NEW: Gemini → MuJoCo bridge
├── simulation_server.py               # Existing MuJoCo server
├── requirements.txt                   # Add aiohttp, aiohttp-cors
└── run_simulation_bridge.sh           # NEW: Launch script

virtual-robot-arm/
├── src/
│   └── lib/
│       └── genai-live-client.ts       # Update endpoint URL
└── .env                               # REACT_APP_GEMINI_API_KEY

gemini-live/gemini-live-api-control/
├── bridges/
│   └── bridge_aloha_real.py           # Existing real robot bridge
└── live-api-console/                  # Can reuse for simulation!
```

---

## API Compatibility Matrix

| Tool Function | Real Robot Bridge | Simulation Bridge | Status |
|---------------|-------------------|-------------------|--------|
| control_gripper | ✅ Supported | ✅ To implement | Maps to left/right |
| move_arm | ✅ Supported | ✅ To implement | Maps to left/right |
| get_gripper_status | ✅ Supported | ✅ To implement | Returns left status |
| get_arm_status | ✅ Supported | ✅ To implement | Returns left status |
| move_arm_trajectory | ✅ Supported | ✅ To implement | Sequential execution |
| detect_and_target_object | 🚧 Placeholder | ❌ Not needed | Visual CV feature |
| analyze_workspace | 🚧 Placeholder | ❌ Not needed | Visual CV feature |

---

## Testing Strategy

### Terminal Testing (No GUI)
```bash
# 1. Start MuJoCo server
cd mujoco-server
source venv/bin/activate
python simulation_server.py --model models/aloha/aloha_simple.xml --port 5000 --headless

# 2. Start simulation bridge
python bridges/bridge_aloha_simulation.py --port 8082

# 3. Test with curl
curl -X POST http://localhost:8082/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "control_gripper", "args": {"action": "open"}}'
```

### Browser Testing (With GUI)
1. Open Gemini Live console (port 3000)
2. Connect to Gemini API
3. Speak commands
4. Observe simulation controls panel update
5. Check Activity Log for feedback

### Integration Testing
```python
# Test script: test_gemini_simulation.py
import requests
import time

def test_tool_call(name, args):
    response = requests.post('http://localhost:8082/aloha-tool-call',
                            json={'name': name, 'args': args})
    print(f"{name}: {response.json()}")

# Run tests
test_tool_call('control_gripper', {'action': 'open'})
time.sleep(2)
test_tool_call('move_arm', {'pose': 'ready'})
time.sleep(2)
test_tool_call('get_arm_status', {})
```

---

## Success Criteria

✅ Phase 3 Complete When:
1. bridge_aloha_simulation.py runs on port 8082
2. Connects to MuJoCo server (port 5000) via WebSocket
3. All 5 core tool functions work (control_gripper, move_arm, status queries, trajectory)
4. Voice commands control simulation robot
5. Same natural language interface as real robot
6. No errors in browser console or server logs
7. Documentation updated with usage instructions

---

## Future Enhancements

### Phase 4: Advanced Features
- [ ] Add camera feed support (simulate camera views)
- [ ] Object detection integration with MuJoCo scene
- [ ] Visual feedback to Gemini (render frames)
- [ ] Trajectory visualization in 3D
- [ ] Multi-step task execution
- [ ] Record and replay voice-commanded sequences

### Phase 5: Deployment
- [ ] Docker containerization
- [ ] Production WSGI server (gunicorn)
- [ ] HTTPS support
- [ ] Rate limiting
- [ ] Authentication

---

## Next Immediate Actions

1. ✅ Test current WebSocket integration (DONE)
2. 🔄 Create bridge_aloha_simulation.py
3. 🔲 Test bridge with curl
4. 🔲 Update React app endpoint
5. 🔲 Test voice commands
6. 🔲 Document usage
