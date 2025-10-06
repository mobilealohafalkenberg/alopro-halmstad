# Voice Control Setup Guide

**Enable Gemini Live API voice control for MuJoCo simulation**

---

## Quick Start

### Option 1: Use Existing Gemini Live Console (Recommended)

The Gemini Live console in `gemini-live/gemini-live-api-control/live-api-console/` can control both real robot and simulation.

**Switch to Simulation Mode:**

1. Edit `.env` file:
```bash
cd gemini-live/gemini-live-api-control/live-api-console
nano .env
```

2. Change the robot endpoint:
```env
# FOR SIMULATION:
REACT_APP_ROBOT_ENDPOINT=http://localhost:8082

# FOR REAL ROBOT:
# REACT_APP_ROBOT_ENDPOINT=http://localhost:8081
```

3. Add your Gemini API key if not already set:
```env
REACT_APP_GEMINI_API_KEY=your-actual-api-key-here
```

4. Restart the console:
```bash
npm start
```

The console will now send voice commands to the simulation bridge (port 8082) instead of the real robot bridge (port 8081)!

---

## System Architecture

### Real Robot Mode (Port 8081)
```
Voice → Gemini Live → ALOHAControl → Bridge (8081) → ROS2 → Hardware
```

### Simulation Mode (Port 8082)
```
Voice → Gemini Live → ALOHAControl → Sim Bridge (8082) → WebSocket → MuJoCo (5000)
```

**Key Difference**: Just the port number! Everything else is identical.

---

## Full System Startup

### Terminal 1: MuJoCo Server
```bash
cd mujoco-server
source venv/bin/activate
python simulation_server.py --model models/aloha/aloha_simple.xml --port 5000 --headless
```

### Terminal 2: Simulation Bridge
```bash
cd mujoco-server
source venv/bin/activate
python bridges/bridge_aloha_simulation.py
# Or use: ./run_simulation_bridge.sh
```

### Terminal 3: Gemini Live Console
```bash
cd gemini-live/gemini-live-api-control/live-api-console

# Make sure .env has:
# REACT_APP_ROBOT_ENDPOINT=http://localhost:8082
# REACT_APP_GEMINI_API_KEY=your-key

npm start
```

---

## Testing Voice Commands

Once the Gemini Live console is open:

1. **Connect to Gemini**
   - Click microphone button
   - Allow microphone access
   - Wait for "Connected" status

2. **Try These Commands**
   ```
   "Open the gripper"
   "Move the arm to ready position"
   "Close the left gripper"
   "Move the arm to home"
   "Reset the robot"
   ```

3. **Monitor Activity**
   - Console shows tool calls in browser
   - Simulation bridge logs commands
   - MuJoCo server executes movements
   - SimulationControls panel updates (if running on port 3000)

---

## Supported Voice Commands

| Voice Command | Tool Call | Result |
|--------------|-----------|--------|
| "Open the gripper" | control_gripper(action: "open") | Left gripper opens |
| "Close the gripper" | control_gripper(action: "close") | Left gripper closes |
| "Move to ready position" | move_arm(pose: "ready") | Arm moves to ready pose |
| "Move to home" | move_arm(pose: "home") | Arm returns to home |
| "Move to sleep position" | move_arm(pose: "sleep") | Arm moves to sleep pose |
| "Reset the robot" | reset_robot() | Both arms reset to home |

---

## Port Reference

| Service | Port | Purpose |
|---------|------|---------|
| MuJoCo Server | 5000 | Physics simulation |
| Real Robot Bridge | 8081 | ROS2 hardware control |
| Simulation Bridge | 8082 | MuJoCo simulation control |
| React Apps | 3000 | UI and controls |

---

## Switching Between Real and Simulation

**To Control Real Robot:**
```env
REACT_APP_ROBOT_ENDPOINT=http://localhost:8081
```

**To Control Simulation:**
```env
REACT_APP_ROBOT_ENDPOINT=http://localhost:8082
```

**Important**: Restart `npm start` after changing .env!

---

## Troubleshooting

### Voice Commands Not Working

1. **Check Gemini Connection**
   - Microphone button should show "Connected"
   - Look for green status indicator
   - Check browser console for errors

2. **Check Bridge Connection**
   ```bash
   curl http://localhost:8082/status
   # Should return: {"bridge": "simulation", "connected_to_mujoco": true}
   ```

3. **Check MuJoCo Server**
   ```bash
   curl http://localhost:5000/health
   # Should return: {"status": "healthy"}
   ```

4. **Check Environment Variable**
   - Verify `.env` has correct port (8082)
   - Restart React app after changes
   - Check browser network tab for endpoint URL

### Gripper Not Moving

- The simulation currently doesn't have visual gripper feedback in headless mode
- Check bridge logs for command confirmation
- Use SimulationControls panel to verify commands are received

### "Command Failed" Errors

- Check simulation bridge terminal for error messages
- Verify WebSocket connection is active
- Try restarting MuJoCo server and bridge

---

## Alternative: Direct Simulation Control

If you don't want to use Gemini Live, you can control the simulation directly:

**Via curl:**
```bash
curl -X POST http://localhost:8082/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "control_gripper", "args": {"action": "open"}}'
```

**Via React UI:**
- Open http://localhost:3000
- Use SimulationControls panel
- Click buttons to control robot

---

## Next Steps

### Current Status
✅ MuJoCo simulation server
✅ Simulation bridge (Gemini → MuJoCo)
✅ Tool call API compatibility
⏳ Gemini Live console configuration (manual step)

### To Complete Voice Control
1. Update .env with simulation endpoint (8082)
2. Add Gemini API key
3. Start Gemini Live console
4. Test voice commands
5. Enjoy voice-controlled simulation!

---

**Pro Tip**: You can run both bridges simultaneously!
- Real robot on 8081
- Simulation on 8082
- Switch between them by changing .env port
