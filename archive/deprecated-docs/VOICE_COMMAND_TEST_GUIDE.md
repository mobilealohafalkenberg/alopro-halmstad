# Voice Command Testing Guide

## System Status: ✅ READY

All services are running and tested:
- MuJoCo Server: Port 5000 ✅
- Simulation Bridge: Port 8082 ✅
- Test Command: Successful ✅

## How to Test Voice Commands

### 1. Open Browser Console
- Press **F12** to open Developer Tools
- Click on **Console** tab
- Keep this open while testing

### 2. Expected Console Logs

When you speak to Gemini, you should see:

```javascript
🎤 Voice command recognized: "Open the gripper"
🤖 Tool call received: {name: "control_gripper", args: {action: "open"}}
✅ control_gripper result: {success: true, state: "open", arm: "left"}
```

### 3. Test Commands to Try

Say these to test the system:

1. **"Open the gripper"**
   - Should see: `control_gripper` tool call
   - Response: `{success: true, state: "open"}`

2. **"Move the arm to ready position"**
   - Should see: `move_arm` tool call with `pose: "ready"`
   - Response: `{success: true, state: "moving"}`

3. **"Close the gripper"**
   - Should see: `control_gripper` with `action: "close"`
   - Response: `{success: true, state: "closed"}`

4. **"Move to home position"**
   - Should see: `move_arm` with `pose: "home"`
   - Response: `{success: true, state: "moving"}`

### 4. What to Check

**In Browser Console (F12):**
- Voice transcription logs (what Gemini heard)
- Tool call logs (what action Gemini decided to take)
- Response logs (confirmation from simulation)

**In Terminal (where bridge is running):**
```bash
[SimBridge] Tool call: control_gripper with args: {'action': 'open', 'arm': 'left'}
[SimBridge] Gripper action 'open' sent to left arm
```

### 5. Microphone Permission

**If browser doesn't ask for mic permission:**
- Check browser settings (usually chrome://settings/content/microphone)
- Make sure microphone is not blocked for localhost
- Try a different browser (Chrome, Edge work best)

**To manually test mic:**
- Click the microphone icon in the Gemini console
- You should see volume indicators moving when you speak
- Green bars = mic is working

## Troubleshooting

### No voice recognition?
1. Check browser console for errors
2. Verify microphone permissions granted
3. Check volume indicators are moving when you speak
4. Try refreshing the page

### Commands not executing?
1. Check endpoint is set to `http://localhost:8082` in .env
2. Verify simulation bridge is running (check terminal)
3. Check console logs show tool calls being sent

### Simulation not responding?
```bash
# Test manually:
curl -X POST http://localhost:8082/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "control_gripper", "args": {"action": "open"}}'

# Should return: {"success": true, "state": "open", ...}
```

## Quick Test Results

✅ **Backend Services:** All running and connected
✅ **API Endpoint:** http://localhost:8082 responding
✅ **Tool Call Pipeline:** Commands execute successfully
✅ **Response Format:** JSON responses validated

**Status:** Ready for voice control testing!

---

**Last Updated:** 2025-10-05
**Test Status:** All systems operational
