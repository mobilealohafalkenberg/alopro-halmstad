# Position Tracking Guide

## Overview

The updated bridge now includes **automatic position tracking** for every arm movement. You can get position coordinates in three ways:

1. **Automatic Tracking** - Every arm movement records initial and final positions
2. **Operation Status** - Query completed operations to see position changes
3. **Real-Time Position** - Poll current position at any time

---

## 📍 Position Data Format

Position data includes three representations:

```json
{
  "cartesian": {
    "x": 0.3,    // meters (forward/backward)
    "y": 0.0,    // meters (left/right)
    "z": 0.2     // meters (up/down)
  },
  "joints": [0.0, -0.96, 1.16, 0.0, -0.3, 0.0],  // radians
  "joints_degrees": [0.0, -55.0, 66.5, 0.0, -17.2, 0.0]  // degrees
}
```

**Joint Order:**
1. `waist` - Base rotation
2. `shoulder` - Shoulder pitch
3. `elbow` - Elbow pitch
4. `forearm_roll` - Forearm rotation
5. `wrist_angle` - Wrist pitch
6. `wrist_rotate` - Wrist rotation

---

## 🎯 Method 1: Automatic Position Tracking

Every arm movement automatically captures:
- **Initial position** - Where the arm started
- **Target** - Where you told it to go
- **Final position** - Where it actually ended up

### Example: Move Arm Command

```bash
# Send move command
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "move_arm",
    "args": {
      "position": [0.3, 0.1, 0.2]
    }
  }'

# Response (immediate):
{
  "success": true,
  "operation_id": "a3f7c2d1-8b9e-4f12-a456-789012345678",
  "status": "started",
  "message": "Arm position movement accepted"
}

# Check status after movement completes:
curl http://localhost:8081/operation/a3f7c2d1-8b9e-4f12-a456-789012345678/status

# Response (with positions):
{
  "success": true,
  "operation_id": "a3f7c2d1-8b9e-4f12-a456-789012345678",
  "type": "arm_move",
  "status": "completed",
  "started_at": 1698765432.123,
  "completed_at": 1698765434.567,
  "duration": 2.444,

  "initial_position": {
    "cartesian": {"x": 0.25, "y": 0.0, "z": 0.15},
    "joints": [0.0, -0.85, 1.0, 0.0, -0.25, 0.0],
    "joints_degrees": [0.0, -48.7, 57.3, 0.0, -14.3, 0.0]
  },

  "target": [0.3, 0.1, 0.2],

  "result": {
    "success": true,
    "final_position": {
      "cartesian": {"x": 0.3, "y": 0.1, "z": 0.2},
      "joints": [0.17, -0.92, 1.1, 0.0, -0.28, 0.0],
      "joints_degrees": [9.7, -52.7, 63.0, 0.0, -16.0, 0.0]
    }
  }
}
```

### Console Output

The bridge also logs position changes to the terminal:

```
[Bridge] 📍 Position: {'x': 0.25, 'y': 0.0, 'z': 0.15} → {'x': 0.3, 'y': 0.1, 'z': 0.2}
```

---

## 🔄 Method 2: Real-Time Position Query

Get the current arm position at any time:

```bash
curl http://localhost:8081/arm/position
```

**Response:**
```json
{
  "success": true,
  "timestamp": 1698765432.123,

  "cartesian": {
    "x": 0.3,
    "y": 0.1,
    "z": 0.2
  },

  "joints": [0.17, -0.92, 1.1, 0.0, -0.28, 0.0],
  "joints_degrees": [9.7, -52.7, 63.0, 0.0, -16.0, 0.0],

  "state": "idle",  // idle, moving, at_home, at_sleep, error
  "pose": null      // "home", "sleep", "ready", or null
}
```

### Polling Example (Python)

```python
import requests
import time

# Poll position every 100ms during movement
while True:
    response = requests.get('http://localhost:8081/arm/position')
    data = response.json()

    if data['success']:
        pos = data['cartesian']
        print(f"Position: x={pos['x']:.3f}, y={pos['y']:.3f}, z={pos['z']:.3f}")

        if data['state'] == 'idle':
            print("Movement complete!")
            break

    time.sleep(0.1)  # 10 Hz polling
```

---

## 📊 Method 3: Historical Position Tracking

View position history from all operations:

```bash
# List all completed operations
curl 'http://localhost:8081/operations?status=completed'
```

**Response:**
```json
{
  "success": true,
  "total": 3,
  "operations": [
    {
      "operation_id": "a3f7c2d1-...",
      "type": "arm_move",
      "status": "completed",
      "started_at": 1698765430.0,
      "completed_at": 1698765432.5,
      "duration": 2.5
    },
    {
      "operation_id": "b4e8d3f2-...",
      "type": "arm_move",
      "status": "completed",
      "started_at": 1698765435.0,
      "completed_at": 1698765437.2,
      "duration": 2.2
    }
  ]
}

# Then get detailed position info for each:
curl http://localhost:8081/operation/a3f7c2d1-.../status
```

---

## 🧪 Testing Position Tracking

### Test 1: Simple Movement

```bash
# Move to a known position
curl -X POST http://localhost:8081/aloha-tool-call \
  -d '{"name": "move_arm", "args": {"position": [0.3, 0, 0.2]}}'

# Get operation_id from response
OPERATION_ID="<paste-operation-id-here>"

# Wait 3 seconds for movement to complete
sleep 3

# Check position data
curl "http://localhost:8081/operation/${OPERATION_ID}/status" | jq '.result.final_position'
```

### Test 2: Real-Time Tracking

```bash
# Start a movement in background
curl -X POST http://localhost:8081/aloha-tool-call \
  -d '{"name": "move_arm", "args": {"pose": "home"}}' &

# Poll position during movement (run in another terminal)
for i in {1..20}; do
  curl -s http://localhost:8081/arm/position | jq '.cartesian'
  sleep 0.2
done
```

### Test 3: Multi-Step Sequence

```bash
# Execute multiple movements
curl -X POST http://localhost:8081/aloha-tool-call \
  -d '{"name": "move_arm", "args": {"position": [0.3, 0, 0.2]}}'

sleep 3

curl -X POST http://localhost:8081/aloha-tool-call \
  -d '{"name": "move_arm", "args": {"position": [0.3, 0.1, 0.2]}}'

sleep 3

curl -X POST http://localhost:8081/aloha-tool-call \
  -d '{"name": "move_arm", "args": {"position": [0.25, 0.1, 0.25]}}'

# View all operations
curl 'http://localhost:8081/operations?status=completed' | jq '.operations[] | {id: .operation_id, duration: .duration}'
```

---

## 📝 Debug Logging

All position data is automatically logged to the debug file:

```bash
tail -f /home/aloha/gemini-live/debug/tool_calls.log
```

**Log Format:**
```
[2025-11-07 14:32:15.123] ARM EXECUTION START: a3f7c2d1-...
  Data: {
    "operation_id": "a3f7c2d1-...",
    "move_type": "position",
    "target": [0.3, 0.1, 0.2],
    "initial_position": {
      "cartesian": {"x": 0.25, "y": 0.0, "z": 0.15},
      ...
    }
  }
--------------------------------------------------------------------------------

[2025-11-07 14:32:17.567] ARM EXECUTION COMPLETE: a3f7c2d1-...
  Data: {
    "operation_id": "a3f7c2d1-...",
    "success": true,
    "initial_position": {...},
    "final_position": {
      "cartesian": {"x": 0.3, "y": 0.1, "z": 0.2},
      ...
    }
  }
--------------------------------------------------------------------------------
```

---

## 🎓 Use Cases

### 1. Track Movement Accuracy

Compare target position vs actual final position:

```python
response = requests.get(f'http://localhost:8081/operation/{op_id}/status').json()

target = response['target']
actual = response['result']['final_position']['cartesian']

error_x = abs(target[0] - actual['x'])
error_y = abs(target[1] - actual['y'])
error_z = abs(target[2] - actual['z'])

print(f"Position error: x={error_x:.4f}, y={error_y:.4f}, z={error_z:.4f} meters")
```

### 2. Log Movement Path

```python
positions = []

# Start movement
response = requests.post('http://localhost:8081/aloha-tool-call', json={
    'name': 'move_arm',
    'args': {'position': [0.35, 0.05, 0.25]}
})

op_id = response.json()['operation_id']

# Record path every 100ms
for i in range(30):
    pos_resp = requests.get('http://localhost:8081/arm/position').json()
    if pos_resp['success']:
        positions.append(pos_resp['cartesian'])
    time.sleep(0.1)

# Analyze path
print(f"Total samples: {len(positions)}")
print(f"Start: {positions[0]}")
print(f"End: {positions[-1]}")
```

### 3. Verify "Pick and Place" Sequence

```python
# Execute pick and place
operations = []

# Move to object
resp = requests.post('http://localhost:8081/aloha-tool-call', json={
    'name': 'move_arm', 'args': {'position': [0.3, 0.1, 0.15]}
})
operations.append(resp.json()['operation_id'])

time.sleep(3)

# Close gripper
resp = requests.post('http://localhost:8081/aloha-tool-call', json={
    'name': 'control_gripper', 'args': {'action': 'close'}
})
operations.append(resp.json()['operation_id'])

time.sleep(2)

# Move to bowl
resp = requests.post('http://localhost:8081/aloha-tool-call', json={
    'name': 'move_arm', 'args': {'position': [0.25, -0.1, 0.2]}
})
operations.append(resp.json()['operation_id'])

time.sleep(3)

# Verify positions
for op_id in operations:
    status = requests.get(f'http://localhost:8081/operation/{op_id}/status').json()
    if status.get('initial_position'):
        print(f"Movement: {status['initial_position']['cartesian']} → {status['result']['final_position']['cartesian']}")
```

---

## 🔧 Configuration

### Enable/Disable Position Logging

Edit `updated_bridge_aloha.py`:

```python
# Line ~265: Toggle console logging
print(f"[Bridge] 📍 Position: {initial_position['cartesian']} → {final_position['cartesian']}")
# Comment out to disable

# Line ~287-292: Toggle debug file logging
log_debug(f"ARM EXECUTION COMPLETE: {operation_id}", {
    "operation_id": operation_id,
    "success": result.get('success'),
    "initial_position": initial_position,
    "final_position": result.get('final_position')
})
# Comment out to disable
```

### Polling Frequency

For real-time tracking, adjust sleep time:

```python
# High frequency (10 Hz)
time.sleep(0.1)

# Medium frequency (5 Hz)
time.sleep(0.2)

# Low frequency (1 Hz)
time.sleep(1.0)
```

**Note:** arm_controller.get_arm_state() is fast (~5-10ms), so high-frequency polling is fine.

---

## 📈 Position Coordinate System

```
              +Z (up)
               |
               |
               |
        +Y ----+---- -Y
      (left)   |   (right)
               |
               |
              -Z (down)

              +X (forward)
              -X (backward)
```

**Workspace Limits:**
- X: [-0.5, 0.5] meters
- Y: [-0.5, 0.5] meters
- Z: [0.1, 0.6] meters (min 0.1m for table safety)

**Origin (0, 0, 0):** Robot base center

---

## ✅ Quick Reference

| What You Want | Endpoint | When to Use |
|--------------|----------|-------------|
| Current position | `GET /arm/position` | Real-time monitoring |
| Movement history | `GET /operation/{id}/status` | After movement completes |
| All movements | `GET /operations?status=completed` | Review session |
| Live tracking | Poll `/arm/position` at 5-10 Hz | During movement |
| Debug logs | `tail -f /home/aloha/gemini-live/debug/tool_calls.log` | Troubleshooting |

---

## 🐛 Troubleshooting

**Problem:** "initial_position is null"
- Arm controller may not be initialized
- Check bridge startup logs for initialization errors

**Problem:** "final_position missing from result"
- Movement may have failed
- Check `result.success` and `result.error` fields

**Problem:** Position values seem wrong
- Verify coordinate system (see diagram above)
- Check if using radians vs degrees for joints
- Cartesian coordinates are in meters

**Problem:** Real-time position not updating
- Check if arm controller is initialized: `GET /status`
- Verify arm is actually moving (not in error state)

---

**Version:** 2.0 with Position Tracking
**Created:** 2025-11-07
**Compatibility:** updated_bridge_aloha.py
