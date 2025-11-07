# Trajectory Bridge Test

Tests the hybrid approach for trajectory execution through the bridge:
- Simple `move_arm` calls use `blocking=False` (fire-and-forget)
- Trajectory calls use `blocking=False` with status tracking

## Prerequisites

1. **Bridge must be running:**
   ```bash
   cd gemini-live/gemini-live-api-control
   ./run_bridge.sh
   ```

2. **Robot must be powered on and connected**

## Running Tests

```bash
cd gemini-live/test/test_trajectory_bridge
python3 test_trajectory_tracking.py
```

## What Gets Tested

### Test 1: Trajectory Status Polling
- Starts a multi-waypoint trajectory
- Polls status endpoint every 500ms
- Verifies progress updates
- Confirms successful completion

### Test 2: Trajectory Cancellation
- Starts a long trajectory
- Cancels it mid-execution
- Verifies cancellation status

### Test 3: List Trajectories
- Retrieves list of all tracked trajectories
- Shows status, progress, and waypoint counts

## Expected Output

```
====================================================
Trajectory Tracking Test Suite
====================================================

=== Checking Bridge Connectivity ===
✅ Bridge is running and arm controller initialized

====================================================
=== Test 1: Trajectory Status Polling ===

1. Starting trajectory...
✅ Trajectory started with ID: a1b2c3d4-...
   Total waypoints: 5

2. Polling trajectory status...
   Poll 1: status=running, waypoint=0/5, progress=0.0%
   Poll 5: status=running, waypoint=1/5, progress=20.0%
   ...
✅ Trajectory finished with status: completed

====================================================
=== Test 2: Trajectory Cancellation ===
...
✅ Trajectory successfully canceled

====================================================
=== Test 3: List Trajectories ===
...
✅ List trajectories successful

====================================================
Test Summary
====================================================
✅ PASS: Trajectory Status Polling
✅ PASS: Trajectory Cancellation
✅ PASS: List Trajectories

Passed: 3/3

✅ All tests passed!
```

## API Endpoints Tested

1. **POST /aloha-tool-call** (move_arm_trajectory)
   - Returns: `{success, trajectory_id, status, total_waypoints}`

2. **GET /trajectory/{trajectory_id}/status**
   - Returns: `{found, status, progress, current_waypoint, total_waypoints, ...}`

3. **POST /trajectory/{trajectory_id}/cancel**
   - Returns: `{success, message, trajectory_id}`

4. **GET /trajectories**
   - Returns: `{success, trajectories: [...], count}`

## Manual Testing via cURL

### Start trajectory
```bash
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "move_arm_trajectory",
    "args": {
      "trajectory": [
        {"point": [0.25, 0, 0.2], "label": "start", "gripper_action": "open"},
        {"point": [0.3, 0.1, 0.2], "label": "shift", "gripper_action": "close"},
        {"point": [0.3, 0.1, 0.25], "label": "lift", "gripper_action": "maintain"}
      ],
      "speed": "medium"
    },
    "id": "manual_test_1"
  }'
```

Response:
```json
{
  "success": true,
  "result": {
    "success": true,
    "trajectory_id": "uuid-here",
    "status": "started",
    "total_waypoints": 3
  },
  "call_id": "manual_test_1"
}
```

### Check status
```bash
curl http://localhost:8081/trajectory/{trajectory_id}/status
```

### Cancel trajectory
```bash
curl -X POST http://localhost:8081/trajectory/{trajectory_id}/cancel
```

### List all trajectories
```bash
curl http://localhost:8081/trajectories
```

## Troubleshooting

**"Bridge not responding"**
- Ensure bridge is running: `./run_bridge.sh`
- Check port 8081 is available: `netstat -an | grep 8081`

**"Arm controller not initialized"**
- Check robot power and USB connection
- Verify ROS environment: `source /opt/ros/humble/setup.bash`
- Check bridge terminal for initialization errors

**"Trajectory not found"**
- Trajectory may have completed and been cleaned up
- Check trajectory_id is correct
- Use `/trajectories` endpoint to list active trajectories

**Tests timeout**
- Robot may be in ERROR state after emergency stop
- Restart bridge to reinitialize controllers
- Check physical workspace for obstructions
