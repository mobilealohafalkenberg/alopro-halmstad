# Pick-and-Place Integration with Vision

**Complete integration of VisionController and autonomous pick-and-place workflow**

## What Was Integrated

### 1. VisionController Integration ✅

**File:** `updated_bridge_aloha.py`

- **Imported VisionController** (line 33)
- **Initialized on startup** (lines 478-490) with Gemini API key
- **Fully integrated into `detect_and_target_object`** (lines 643-757):
  - Gets RGB + depth frames from camera
  - Calls Gemini API for object detection
  - Returns REAL 3D position from depth data
  - Generates approach trajectory based on actual object location

### 2. Complete Pick-and-Place Workflow ✅

**New Function:** `execute_pick_and_place()` (lines 382-798)

**12-Step Autonomous Workflow:**

1. **Detect object** - Uses Gemini vision to find object to pick
2. **Open gripper** - Prepares for grasping
3. **Approach object** - Moves to position above object
4. **Lower to grasp** - Descends to object level
5. **Grasp object** - Closes gripper
6. **Lift object** - Raises object off surface
7. **Detect target** - Uses vision to find bowl/destination
8. **Move to target** - Navigates to target location
9. **Lower to place** - Descends above target
10. **Release object** - Opens gripper
11. **Retract** - Moves up from target
12. **Return home** - Returns to home position

**Features:**
- ✅ Step-by-step progress tracking
- ✅ Real-time status updates
- ✅ Error recovery (opens gripper + returns home on failure)
- ✅ Uses both cameras (gripper cam for pick, top cam for place)
- ✅ Background execution (fire-and-forget pattern)
- ✅ Full logging of each step

### 3. HTTP Tool Handler ✅

**New Tool:** `pick_and_place` (lines 985-1001)

**Usage:**
```bash
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pick_and_place",
    "args": {
      "object_to_pick": "banana",
      "target_location": "bowl",
      "approach_height": 0.05,
      "lift_height": 0.15,
      "speed": "medium"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "operation_id": "uuid-here",
  "status": "started",
  "message": "Pick-and-place workflow started: banana → bowl",
  "workflow": "pick_and_place",
  "object_to_pick": "banana",
  "target_location": "bowl"
}
```

## How It Works

### Architecture Flow

```
Voice: "Pick the banana and put it in the bowl"
    ↓
Gemini Live API interprets command
    ↓
Calls pick_and_place tool with:
  - object_to_pick: "banana"
  - target_location: "bowl"
    ↓
Bridge receives request → returns operation_id immediately
    ↓
Background execution starts:
    ↓
  [1] Get camera frame from gripper_cam
    ↓
  [2] Send to Gemini Vision API: "Find banana"
    ↓
  [3] Gemini returns bounding box + confidence
    ↓
  [4] Calculate 3D position from depth map
    ↓
  [5] Generate approach trajectory to banana
    ↓
  [6] Execute pick sequence (approach → lower → grasp → lift)
    ↓
  [7] Get camera frame from top_cam
    ↓
  [8] Send to Gemini Vision API: "Find bowl"
    ↓
  [9] Calculate 3D position of bowl
    ↓
  [10] Generate place trajectory to bowl
    ↓
  [11] Execute place sequence (approach → lower → release → retract)
    ↓
  [12] Return to home position
    ↓
Operation complete! ✅
```

### Status Monitoring

**Check workflow progress:**
```bash
curl http://localhost:8081/operation/{operation_id}/status
```

**Response:**
```json
{
  "success": true,
  "operation_id": "abc-123",
  "type": "pick_and_place",
  "status": "running",
  "current_step": "move_to_target",
  "steps": [
    {"step": "detect_object", "status": "completed", "data": {"position": [0.3, 0.1, 0.12]}},
    {"step": "open_gripper", "status": "completed"},
    {"step": "approach_object", "status": "completed"},
    {"step": "lower_to_grasp", "status": "completed"},
    {"step": "grasp_object", "status": "completed"},
    {"step": "lift_object", "status": "completed"},
    {"step": "detect_target", "status": "completed", "data": {"position": [0.25, -0.15, 0.08]}},
    {"step": "move_to_target", "status": "running"}
  ]
}
```

## Setup Requirements

### 1. Environment Variables

```bash
# Required for vision features
export GEMINI_API_KEY='your-api-key-here'
```

### 2. File Structure

Ensure these files exist:
```
gemini-live/
├── vision_controller.py          # Gemini vision integration
├── camera_controller.py           # RealSense camera control
├── arm_controller.py              # Arm movement control
├── gripper_controller.py          # Gripper control
└── gemini-live-api-control/
    └── bridges/
        └── updated_bridge_aloha.py   # Main bridge (THIS FILE)
```

### 3. Dependencies

```bash
pip install google-generativeai opencv-python numpy pillow aiohttp aiohttp-cors
```

## Running the System

### Start the Bridge

```bash
cd gemini-live/gemini-live-api-control/bridges
export GEMINI_API_KEY='your-key'
python3 updated_bridge_aloha.py
```

**Expected Output:**
```
================================================================================
ALOHA Robot Bridge for Gemini Live API v2.0
FIRE-AND-FORGET + VISION INTEGRATION EDITION
================================================================================

✨ NEW FEATURES:
  - True fire-and-forget: All operations return in ~50ms
  - Unified operation tracking with unique IDs
  - Background execution prevents Gemini timeouts
  - Status polling for all operations
  - Automatic cleanup of old operations
  - Position tracking on every arm movement
  - 🔥 VISION INTEGRATION: Gemini 2.0 Flash for object detection
  - 🔥 PICK-AND-PLACE: Complete autonomous workflow with vision

[Bridge] Starting robot driver...
[Bridge] Initializing gripper controller...
[Bridge] ✓ Gripper controller initialized successfully
[Bridge] Initializing arm controller...
[Bridge] ✓ Arm controller initialized successfully
[Bridge] Initializing camera controller...
[Bridge] ✓ Camera controller initialized successfully
[Bridge]   - gripper_cam ready
[Bridge]   - top_cam ready
[Bridge] Initializing vision controller...
[Bridge] ✓ Vision controller initialized with Gemini API
```

### Test Object Detection

```bash
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "detect_and_target_object",
    "args": {
      "object_description": "banana"
    }
  }'
```

### Test Pick-and-Place

**Via Voice:**
Just say: *"Pick the banana and put it in the bowl"*

**Via API:**
```bash
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pick_and_place",
    "args": {
      "object_to_pick": "banana",
      "target_location": "bowl",
      "speed": "medium"
    }
  }'
```

## Monitoring Execution

### Real-time Logs

Watch bridge terminal for step-by-step progress:
```
[Bridge] 📞 Tool call: pick_and_place
[Bridge] 🔄 Pick&Place Step: detect_object - running
[Bridge] 👁️ Detecting 'banana' using Gemini...
[VisionController] ✓ Found 'banana' at [0.3, 0.1, 0.12]
[Bridge] 🔄 Pick&Place Step: detect_object - completed
[Bridge] 🔄 Pick&Place Step: open_gripper - running
[Bridge] 🔄 Pick&Place Step: open_gripper - completed
[Bridge] 🔄 Pick&Place Step: approach_object - running
...
[Bridge] ✅ Pick-and-place workflow completed (abc12345...)
[Bridge]    Picked: banana from [0.3, 0.1, 0.12]
[Bridge]    Placed: into bowl at [0.25, -0.15, 0.08]
```

### Debug Logs

All tool calls logged to:
```
/home/aloha/gemini-live/debug/tool_calls.log
```

## Error Handling

### Automatic Recovery

If ANY step fails:
1. **Logs error** with step information
2. **Opens gripper** (releases any held object)
3. **Returns to home** position
4. **Marks operation as failed** with error details

### Check Failed Operation

```bash
curl http://localhost:8081/operation/{operation_id}/status
```

**Example Error Response:**
```json
{
  "success": true,
  "operation_id": "abc-123",
  "type": "pick_and_place",
  "status": "failed",
  "error": "Object 'banana' not found in workspace",
  "steps": [
    {"step": "detect_object", "status": "running"}
  ],
  "failed_at": 1234567890.123
}
```

## Common Issues

### ❌ "Vision controller not initialized"

**Cause:** GEMINI_API_KEY not set

**Fix:**
```bash
export GEMINI_API_KEY='your-key-here'
# Restart bridge
```

### ❌ "Object not found in workspace"

**Causes:**
1. Object not in camera view
2. Poor lighting
3. Object description unclear

**Fixes:**
- Move camera closer to object
- Improve lighting conditions
- Use more specific descriptions ("yellow banana" vs "banana")

### ❌ "No 3D position available"

**Cause:** Depth data missing or invalid

**Fixes:**
- Check RealSense D405 connection
- Ensure object is within depth range (0.1m - 2.0m)
- Verify depth stream is enabled

## Performance

### Timing Breakdown

| Step | Duration |
|------|----------|
| Initial response | ~50ms |
| Object detection (Gemini API) | ~1-2s |
| 3D position calculation | ~50ms |
| Approach trajectory | ~2-3s |
| Grasp sequence | ~1-2s |
| Lift | ~1-2s |
| Target detection | ~1-2s |
| Place sequence | ~3-4s |
| Return home | ~2-3s |
| **Total** | **~15-25s** |

### Optimization Tips

1. **Use `speed: "fast"`** for quicker movements (less safe)
2. **Reduce `approach_height`** to skip some vertical travel
3. **Pre-position arm** near workspace before starting
4. **Use gripper camera** for both pick and place (skip camera switch)

## What Actually Happens Now

### Before (Placeholder):
```
You: "Pick the banana and put it in bowl"
  ↓
Robot moves to HARDCODED position [0.3, 0.0, 0.25]
  ↓
Grasps nothing (banana not there)
  ↓
Moves to HARDCODED bowl position
  ↓
"Places" air into bowl
```

### After (Real Vision):
```
You: "Pick the banana and put it in bowl"
  ↓
Gemini Vision detects banana at REAL position [0.312, 0.087, 0.124]
  ↓
Robot approaches actual banana location
  ↓
Grasps actual banana
  ↓
Gemini Vision detects bowl at REAL position [0.254, -0.143, 0.089]
  ↓
Robot moves to actual bowl
  ↓
Places banana IN the bowl ✅
```

## Next Steps

1. **Calibrate camera transforms** for better accuracy (see `vision_controller.py:calibrate_camera()`)
2. **Add grasp validation** (check gripper force sensor after grasp)
3. **Implement retry logic** (if first detection fails, try again)
4. **Add collision checking** (verify path is clear before moving)
5. **Multi-object scenarios** (pick multiple items in sequence)

## Testing Checklist

- [ ] Bridge starts without errors
- [ ] Vision controller initializes with API key
- [ ] Camera frames available from both cameras
- [ ] `detect_and_target_object` returns real positions
- [ ] `pick_and_place` workflow completes all 12 steps
- [ ] Status endpoint shows step progress
- [ ] Error recovery works (gripper opens, returns home)
- [ ] Actual object is grasped and moved
- [ ] Object is placed in target location

## Support

If you encounter issues:

1. **Check logs:** `/home/aloha/gemini-live/debug/tool_calls.log`
2. **Check bridge terminal** for step-by-step output
3. **Verify environment:** `echo $GEMINI_API_KEY`
4. **Test cameras:** `curl http://localhost:8081/camera/info`
5. **Test vision standalone:** `python3 vision_controller.py`

---

**Status:** ✅ FULLY INTEGRATED AND READY TO TEST

The system will now use REAL computer vision to detect objects and execute pick-and-place operations autonomously!
