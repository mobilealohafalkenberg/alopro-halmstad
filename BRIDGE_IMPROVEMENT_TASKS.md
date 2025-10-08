# Bridge Improvement Tasks - bridge_aloha_real_ANU_prod.py

Complete task list for improving the ALOHA robot bridge server based on comprehensive code analysis.

---

## Task Overview

**File:** `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`

**Total Tasks:** 10
**Estimated Effort:** 18-24 hours (2-3 days)
**Priority Levels:** HIGH (4 tasks), MEDIUM (4 tasks), LOW (2 tasks)

---

## HIGH PRIORITY TASKS (Critical Safety & Architecture)

### Task B.1: Remove Global State Anti-Pattern

**Description:**
Lines 24-28 use global variables for controller instances (`gripper_controller`, `arm_controller`, `camera_controller`, `launch_process`). This is the same anti-pattern deprecated in Task 1.9 (arm_controller) and Task 2.3 (gripper_controller). Global state makes testing difficult, prevents proper dependency injection, and isn't thread-safe for concurrent requests.

**Current Code:**
```python
# Global controller instances
gripper_controller = None
arm_controller = None
camera_controller = None
launch_process = None
```

**Steps to fix:**
1. Remove global variable declarations (lines 24-28)
2. Modify `initialize_robot()` to return controller instances
3. Store controllers in aiohttp app context: `app['controllers']`
4. Update all handler functions to access via `request.app['controllers']`
5. Update `cleanup()` to use `app['controllers']`
6. Update `startup()` to store in app context
7. Test all endpoints still work correctly
8. Update CHANGELOG.md with Task B.1 entry

**Impact:**
- Architecture Improvement: Eliminates hidden global state
- Better Testability: Enables proper mocking and isolation
- Thread Safety: App context is request-safe
- Consistency: Matches controller deprecation efforts

**Priority:** HIGH (Architecture)
**Estimated Time:** 2-3 hours
**Dependencies:** None

**Example Implementation:**
```python
# Remove globals
# gripper_controller = None  # DELETE
# arm_controller = None      # DELETE
# camera_controller = None   # DELETE
# launch_process = None      # DELETE

async def initialize_robot(app):
    """Initialize the robot and store in app context."""
    print("[Bridge] Starting robot driver...")

    controllers = {
        'gripper': None,
        'arm': None,
        'camera': None,
        'launch_process': None
    }

    # ... initialization code ...

    controllers['gripper'] = gripper_controller
    controllers['arm'] = arm_controller
    controllers['camera'] = camera_controller
    controllers['launch_process'] = launch_process

    # Store in app context
    app['controllers'] = controllers

async def handle_tool_call(request: web.Request) -> web.Response:
    """Handle tool calls - access controllers from app context"""
    controllers = request.app['controllers']
    gripper_controller = controllers['gripper']
    arm_controller = controllers['arm']

    # ... rest of handler ...
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

### Task B.2: Fix Error Handling - Remove Bare Except Clauses

**Description:**
Multiple locations use bare `except:` clauses that silently ignore ALL exceptions including KeyboardInterrupt and SystemExit (lines 491-492, 499-500, 508-509, 517-518). Additionally, line 44 silently catches and prints debug log errors. This makes debugging impossible and hides critical failures.

**Current Code:**
```python
# Lines 491-492 (and similar in other places)
except:
    pass
```

**Steps to fix:**
1. Replace all bare `except:` with `except Exception as e:`
2. Add logging for all caught exceptions
3. Log exception details including traceback for errors
4. Add specific exception handling where appropriate (e.g., ConnectionError)
5. Update `log_debug()` error handling (line 44) to log the error
6. Test error scenarios to ensure errors are logged
7. Update CHANGELOG.md with Task B.2 entry

**Impact:**
- Critical Debugging: Errors no longer hidden
- Better Reliability: Know when/why operations fail
- Proper Exception Handling: Don't catch system exceptions
- Monitoring: Can detect and alert on errors

**Priority:** HIGH (Safety & Debugging)
**Estimated Time:** 2-3 hours
**Dependencies:** None (but easier after Task B.5 adds proper logging)

**Example Implementation:**
```python
# Before (lines 486-492)
if arm_controller:
    try:
        arm_controller.move_to_pose('sleep', blocking=True)
        arm_controller.shutdown()
        print("[Bridge] Arm controller shutdown complete")
    except:
        pass

# After
if arm_controller:
    try:
        arm_controller.move_to_pose('sleep', blocking=True)
        arm_controller.shutdown()
        logger.info("Arm controller shutdown complete")
    except ConnectionError as e:
        logger.error(f"Connection error during arm shutdown: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during arm shutdown: {e}", exc_info=True)

# Fix log_debug error handling (line 44)
except Exception as e:
    print(f"[Debug Log Error] Failed to write log: {e}")
    # Don't silently fail - at least print it
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

### Task B.3: Add Input Validation for Tool Calls

**Description:**
Tool call handlers (lines 160-289) don't validate inputs. No type checking, no range validation, no required parameter checking. Invalid inputs can cause crashes, undefined behavior, or send dangerous commands to hardware.

**Steps to fix:**
1. Create validation functions for each tool call type:
   - `validate_control_gripper(args)`
   - `validate_move_arm(args)`
   - `validate_move_arm_trajectory(args)`
   - `validate_emergency_stop(args)`
   - etc.
2. Add type checking for all parameters
3. Add range validation for numeric parameters
4. Add required parameter checking
5. Return clear error messages (HTTP 400) for invalid inputs
6. Add validation middleware for request structure
7. Create test file: `test/test_bridge_validation.py`
8. Update CHANGELOG.md with Task B.3 entry

**Impact:**
- Critical Safety: Prevent invalid/dangerous commands
- Better UX: Clear error messages for users
- Reliability: Prevent crashes from bad inputs
- Documentation: Validation serves as API specification

**Priority:** HIGH (Safety)
**Estimated Time:** 3-4 hours
**Dependencies:** None

**Example Implementation:**
```python
def validate_control_gripper(args: dict) -> dict:
    """
    Validate control_gripper arguments

    Required: action
    Valid values: 'open', 'close'

    Raises:
        ValueError: If validation fails

    Returns:
        Validated arguments
    """
    if not isinstance(args, dict):
        raise ValueError("args must be a dictionary")

    action = args.get('action')

    # Required parameter check
    if not action:
        raise ValueError("Missing required argument: action")

    # Type check
    if not isinstance(action, str):
        raise ValueError(f"action must be string, got {type(action).__name__}")

    # Value check
    action = action.lower()
    if action not in ['open', 'close']:
        raise ValueError(f"Invalid action: '{action}'. Must be 'open' or 'close'")

    return {'action': action}

def validate_move_arm(args: dict) -> dict:
    """
    Validate move_arm arguments

    Required: One of (pose, joints, position)
    Optional: moving_time, unit, orientation, format
    """
    if not isinstance(args, dict):
        raise ValueError("args must be a dictionary")

    # Must have at least one movement target
    has_target = any(key in args for key in ['pose', 'joints', 'position'])
    if not has_target:
        raise ValueError("Must specify one of: pose, joints, or position")

    # Validate pose if provided
    if 'pose' in args:
        pose = args['pose']
        if not isinstance(pose, str):
            raise ValueError(f"pose must be string, got {type(pose).__name__}")
        valid_poses = ['home', 'ready', 'sleep']
        if pose not in valid_poses:
            raise ValueError(f"Invalid pose: '{pose}'. Valid: {valid_poses}")

    # Validate joints if provided
    if 'joints' in args:
        joints = args['joints']
        if not isinstance(joints, list):
            raise ValueError(f"joints must be list, got {type(joints).__name__}")
        if len(joints) != 6:
            raise ValueError(f"joints must have 6 values, got {len(joints)}")
        if not all(isinstance(j, (int, float)) for j in joints):
            raise ValueError("All joint values must be numeric")

    # Validate position if provided
    if 'position' in args:
        position = args['position']
        if not isinstance(position, list):
            raise ValueError(f"position must be list, got {type(position).__name__}")
        if len(position) not in [3, 6]:
            raise ValueError(f"position must have 3 or 6 values, got {len(position)}")
        if not all(isinstance(p, (int, float)) for p in position):
            raise ValueError("All position values must be numeric")

    # Validate optional moving_time
    if 'moving_time' in args:
        moving_time = args['moving_time']
        if not isinstance(moving_time, (int, float)):
            raise ValueError(f"moving_time must be numeric, got {type(moving_time).__name__}")
        if moving_time <= 0:
            raise ValueError(f"moving_time must be positive, got {moving_time}")
        if moving_time > 10:
            raise ValueError(f"moving_time too large (max 10s), got {moving_time}")

    return args

# Usage in handler:
elif name == 'control_gripper':
    try:
        validated_args = validate_control_gripper(args)
        action = validated_args['action']
    except ValueError as e:
        log_debug(f"VALIDATION ERROR: {name}", {"error": str(e), "args": args})
        return web.json_response({
            'success': False,
            'error': f'Invalid arguments: {e}'
        }, status=400)

    # ... rest of handler with validated args ...
```

**Files to create/modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `gemini-live/test/test_bridge_validation.py` (new file)
- `CHANGELOG.md`

---

### Task B.4: Fix Emergency Stop - Add Gripper Support and Resume Handler

**Description:**
Emergency stop handler (lines 325-336) only calls `arm_controller.emergency_stop()` but doesn't stop the gripper. This is inconsistent with Task 2.1 which adds emergency stop to gripper_controller. Additionally, there's no handler for `resume_after_stop` tool call.

**Current Code:**
```python
elif name == 'emergency_stop':
    results = []
    if arm_controller and arm_controller.initialized:
        arm_result = arm_controller.emergency_stop()
        results.append(f"Arm: {arm_result.get('state', 'error')}")
    # Missing: gripper emergency stop
    result = {
        "success": True,
        "results": results,
        "state": "emergency_stopped"
    }
```

**Steps to fix:**
1. Add gripper emergency stop call to emergency_stop handler
2. Handle errors gracefully for each controller
3. Add `resume_after_stop` tool handler
4. Resume both arm and gripper controllers
5. Report status for each controller
6. Test emergency stop with both controllers
7. Test resume after stop
8. Update CHANGELOG.md with Task B.4 entry

**Impact:**
- Critical Safety: Complete emergency stop for all controllers
- Consistency: Matches Task 2.1 gripper e-stop implementation
- Recovery: Proper resume after emergency situations
- User Control: Explicit recovery process

**Priority:** HIGH (Safety)
**Estimated Time:** 1-2 hours
**Dependencies:** Task 2.1 (gripper emergency_stop implementation)

**Example Implementation:**
```python
elif name == 'emergency_stop':
    """Emergency stop all controllers"""
    results = []
    overall_success = True

    # Stop arm controller
    if arm_controller and arm_controller.initialized:
        try:
            arm_result = arm_controller.emergency_stop()
            if arm_result.get('success'):
                results.append(f"Arm: {arm_result.get('state', 'stopped')}")
            else:
                results.append(f"Arm: error - {arm_result.get('error', 'unknown')}")
                overall_success = False
        except Exception as e:
            results.append(f"Arm: exception - {e}")
            logger.error(f"Error during arm emergency stop: {e}", exc_info=True)
            overall_success = False
    else:
        results.append("Arm: not initialized")

    # Stop gripper controller
    if gripper_controller and gripper_controller.initialized:
        try:
            gripper_result = gripper_controller.emergency_stop()
            if gripper_result.get('success'):
                results.append(f"Gripper: {gripper_result.get('state', 'stopped')}")
            else:
                results.append(f"Gripper: error - {gripper_result.get('error', 'unknown')}")
                overall_success = False
        except Exception as e:
            results.append(f"Gripper: exception - {e}")
            logger.error(f"Error during gripper emergency stop: {e}", exc_info=True)
            overall_success = False
    else:
        results.append("Gripper: not initialized")

    result = {
        "success": overall_success,
        "results": results,
        "state": "emergency_stopped"
    }

    logger.warning(f"EMERGENCY STOP executed: {results}")
    print(f"[Bridge] ⚠️ EMERGENCY STOP executed")

elif name == 'resume_after_stop':
    """Resume operations after emergency stop"""
    results = []
    overall_success = True

    # Resume arm controller
    if arm_controller and arm_controller.initialized:
        try:
            arm_result = arm_controller.resume_after_stop()
            if arm_result.get('success'):
                results.append(f"Arm: {arm_result.get('state', 'resumed')}")
                if 'warning' in arm_result:
                    results.append(f"Arm warning: {arm_result['warning']}")
            else:
                results.append(f"Arm: error - {arm_result.get('error', 'unknown')}")
                overall_success = False
        except Exception as e:
            results.append(f"Arm: exception - {e}")
            logger.error(f"Error during arm resume: {e}", exc_info=True)
            overall_success = False
    else:
        results.append("Arm: not initialized")

    # Resume gripper controller
    if gripper_controller and gripper_controller.initialized:
        try:
            gripper_result = gripper_controller.resume_after_stop()
            if gripper_result.get('success'):
                results.append(f"Gripper: {gripper_result.get('state', 'resumed')}")
            else:
                results.append(f"Gripper: error - {gripper_result.get('error', 'unknown')}")
                overall_success = False
        except Exception as e:
            results.append(f"Gripper: exception - {e}")
            logger.error(f"Error during gripper resume: {e}", exc_info=True)
            overall_success = False
    else:
        results.append("Gripper: not initialized")

    result = {
        "success": overall_success,
        "results": results,
        "state": "resumed" if overall_success else "partial_resume"
    }

    logger.info(f"Resume after stop: {results}")
    print(f"[Bridge] Resume after emergency stop completed")
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

## MEDIUM PRIORITY TASKS (Code Quality & Features)

### Task B.5: Replace Print Statements with Structured Logging

**Description:**
File uses `print()` statements throughout for logging (50+ locations). This is unprofessional, makes filtering/searching logs difficult, and doesn't provide log levels, timestamps, or proper formatting. Should use Python's `logging` module.

**Steps to fix:**
1. Import logging module at top of file
2. Configure logging with appropriate format and handlers
3. Create logger instance: `logger = logging.getLogger(__name__)`
4. Replace all `print()` calls with appropriate logger methods:
   - `print("[Bridge] ...")` → `logger.info(...)`
   - `print(f"[Bridge] Error: ...")` → `logger.error(...)`
   - `print(f"[Bridge] ✓ ...")` → `logger.info(...)`
   - `print(f"[Bridge] ⚠️ ...")` → `logger.warning(...)`
5. Add log file rotation (RotatingFileHandler)
6. Configure different log levels for console vs file
7. Test logging output
8. Update CHANGELOG.md with Task B.5 entry

**Impact:**
- Professional Logging: Industry-standard logging
- Better Debugging: Filterable by level and module
- Production Ready: Proper log rotation and management
- Monitoring: Can integrate with log aggregation tools

**Priority:** MEDIUM (Code Quality)
**Estimated Time:** 2 hours
**Dependencies:** None (but makes Task B.2 easier)

**Example Implementation:**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logger = logging.getLogger('bridge')
    logger.setLevel(logging.DEBUG)

    # Console handler - INFO and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler - DEBUG and above with rotation
    file_handler = RotatingFileHandler(
        'bridge.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logging()

# Replace print statements
# Before:
print(f"[Bridge] Tool call: {name} with args: {args}")

# After:
logger.info("Tool call: %s with args: %s", name, args)

# Before:
print(f"[Bridge] ✗ Error initializing controllers: {e}")

# After:
logger.error("Error initializing controllers: %s", e, exc_info=True)

# Before:
print("[Bridge] ⚠️ EMERGENCY STOP ACTIVATED!")

# After:
logger.warning("EMERGENCY STOP ACTIVATED!")
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

### Task B.6: Add Configuration Management

**Description:**
All configuration values are hard-coded throughout the file (port 8081, host 0.0.0.0, robot model vx300s, debug log path, etc.). This makes it difficult to run in different environments, test configurations, or deploy to production.

**Steps to fix:**
1. Create `bridge_config.py` or `bridge_config.json` file
2. Extract all hard-coded values:
   - Server host and port
   - Robot model and name
   - File paths (debug log, launch script)
   - Controller enable flags
   - Timeout values
   - Speed mappings
3. Load configuration on startup
4. Update all references to use config values
5. Add environment variable overrides
6. Document all configuration options
7. Add configuration validation
8. Update CHANGELOG.md with Task B.6 entry

**Impact:**
- Flexibility: Easy to change settings without code changes
- Environment Support: Dev, test, prod configurations
- Deployment: Configuration through environment variables
- Documentation: Config file documents all options

**Priority:** MEDIUM (Infrastructure)
**Estimated Time:** 2-3 hours
**Dependencies:** None

**Example Implementation:**
```python
# bridge_config.py
import os
from pathlib import Path

class BridgeConfig:
    """Bridge server configuration"""

    def __init__(self):
        # Server configuration
        self.server_host = os.getenv('BRIDGE_HOST', '0.0.0.0')
        self.server_port = int(os.getenv('BRIDGE_PORT', '8081'))

        # Robot configuration
        self.robot_model = os.getenv('ROBOT_MODEL', 'vx300s')
        self.robot_name = os.getenv('ROBOT_NAME', 'follower_left')

        # Controller configuration
        self.enable_gripper = os.getenv('ENABLE_GRIPPER', 'true').lower() == 'true'
        self.enable_arm = os.getenv('ENABLE_ARM', 'true').lower() == 'true'
        self.enable_camera = os.getenv('ENABLE_CAMERA', 'true').lower() == 'true'

        # Path configuration
        self.base_dir = Path(__file__).parent.parent.parent
        self.debug_log_path = os.getenv(
            'DEBUG_LOG_PATH',
            str(self.base_dir / 'debug' / 'tool_calls.log')
        )
        self.launch_script_path = os.getenv(
            'LAUNCH_SCRIPT',
            str(self.base_dir / 'minimal_launch.sh')
        )

        # Timing configuration
        self.robot_startup_delay = float(os.getenv('STARTUP_DELAY', '5.0'))
        self.default_moving_time = float(os.getenv('DEFAULT_MOVING_TIME', '1.5'))

        # Speed mapping
        self.speed_map = {
            'slow': float(os.getenv('SPEED_SLOW', '2.5')),
            'medium': float(os.getenv('SPEED_MEDIUM', '1.5')),
            'fast': float(os.getenv('SPEED_FAST', '0.8'))
        }

    def validate(self):
        """Validate configuration"""
        errors = []

        if not 1 <= self.server_port <= 65535:
            errors.append(f"Invalid port: {self.server_port}")

        if not Path(self.launch_script_path).exists():
            errors.append(f"Launch script not found: {self.launch_script_path}")

        if self.robot_startup_delay < 0:
            errors.append(f"Invalid startup delay: {self.robot_startup_delay}")

        return errors

# Usage in main file:
from bridge_config import BridgeConfig

config = BridgeConfig()

# Validate configuration
errors = config.validate()
if errors:
    logger.error("Configuration errors:")
    for error in errors:
        logger.error(f"  - {error}")
    sys.exit(1)

# Use configuration
logger.info(f"Starting bridge on {config.server_host}:{config.server_port}")
web.run_app(make_app(), host=config.server_host, port=config.server_port)
```

**Files to create/modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_config.py` (new file)
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `gemini-live/gemini-live-api-control/bridges/.env.example` (new file - example config)
- `CHANGELOG.md`

---

### Task B.7: Remove or Implement Placeholder Tools

**Description:**
Two tool handlers are placeholders that return fake data: `detect_and_target_object` (lines 286-304) and `analyze_workspace` (lines 306-323). These are misleading - they appear to work but don't actually do anything. Should either remove, properly implement with computer vision, or clearly mark as not implemented.

**Steps to fix:**
1. Decide strategy for each placeholder:
   - Option A: Remove (if not needed)
   - Option B: Implement with real CV (if needed)
   - Option C: Return "not implemented" error (if future feature)
2. If removing:
   - Remove tool handlers
   - Update documentation
3. If implementing:
   - Add CV library integration
   - Implement object detection
   - Add proper error handling
4. If keeping as not implemented:
   - Return HTTP 501 Not Implemented
   - Add clear error message
   - Document as planned feature
5. Update CHANGELOG.md with Task B.7 entry

**Impact:**
- Clarity: Users know what works and what doesn't
- No False Positives: Don't return fake success
- Clean Code: Remove dead/misleading code
- Future Planning: Clear roadmap for features

**Priority:** MEDIUM (Code Clarity)
**Estimated Time:** 1-2 hours (if removing), 8-12 hours (if implementing)
**Dependencies:** None (implementation would need CV library)

**Example Implementation (Option C - Not Implemented):**
```python
elif name == 'detect_and_target_object':
    # Not yet implemented - requires computer vision integration
    return web.json_response({
        'success': False,
        'error': 'Visual object detection not yet implemented',
        'status': 'not_implemented',
        'note': 'This feature is planned for future release. Requires camera and CV integration.'
    }, status=501)  # 501 Not Implemented

elif name == 'analyze_workspace':
    # Not yet implemented - requires computer vision integration
    return web.json_response({
        'success': False,
        'error': 'Workspace analysis not yet implemented',
        'status': 'not_implemented',
        'note': 'This feature is planned for future release. Requires camera and CV integration.'
    }, status=501)
```

**Example Implementation (Option A - Remove):**
```python
# Simply delete lines 286-323
# Remove from tool list documentation
# Update any client code that might call these
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

### Task B.8: Extract Duplicate Status Logic to Shared Function

**Description:**
Status retrieval logic is duplicated in two places: `get_robot_status` tool handler (lines 338-361) and `/status` endpoint handler (lines 446-477). This code duplication violates DRY principle and makes maintenance difficult.

**Steps to fix:**
1. Create `get_combined_status()` helper function
2. Extract common status logic from both locations
3. Function should accept controllers as parameters
4. Update `get_robot_status` tool to use shared function
5. Update `/status` endpoint to use shared function
6. Add optional parameters for including/excluding details
7. Test both endpoints return correct data
8. Update CHANGELOG.md with Task B.8 entry

**Impact:**
- Code Quality: Eliminate duplication
- Maintainability: Single place to update status logic
- Consistency: Both endpoints use same logic
- Testability: Can test status logic in isolation

**Priority:** MEDIUM (Code Quality)
**Estimated Time:** 1 hour
**Dependencies:** Task B.1 (easier after removing globals)

**Example Implementation:**
```python
def get_combined_status(gripper_controller, arm_controller, camera_controller, include_details=True):
    """
    Get combined status of all controllers

    Args:
        gripper_controller: GripperController instance or None
        arm_controller: ArmController instance or None
        camera_controller: CameraController instance or None
        include_details: If True, include detailed state information

    Returns:
        dict: Combined status information
    """
    status = {
        "timestamp": time.time(),
        "controllers_initialized": {
            "gripper": gripper_controller.initialized if gripper_controller else False,
            "arm": arm_controller.initialized if arm_controller else False,
            "camera": camera_controller.initialized if camera_controller else False
        }
    }

    # Gripper status
    if gripper_controller and gripper_controller.initialized:
        try:
            gripper_state = gripper_controller.get_gripper_state()
            status["gripper"] = {
                "state": gripper_state['state'],
                "position_percent": gripper_state['position_normalized'] * 100
            }
            if include_details:
                status["gripper"]["position_raw"] = gripper_state.get('position')
        except Exception as e:
            status["gripper"] = {"state": "error", "error": str(e)}
    else:
        status["gripper"] = {"state": "not_initialized"}

    # Arm status
    if arm_controller and arm_controller.initialized:
        try:
            arm_state = arm_controller.get_arm_state()
            status["arm"] = {
                "state": arm_state['state'],
                "pose": arm_state.get('pose')
            }
            if include_details:
                status["arm"]["joints_degrees"] = arm_state.get('joints_degrees', [0]*6)
            else:
                # Just first 3 joints for summary
                status["arm"]["joints_degrees"] = arm_state.get('joints_degrees', [0]*6)[:3]
        except Exception as e:
            status["arm"] = {"state": "error", "error": str(e)}
    else:
        status["arm"] = {"state": "not_initialized"}

    # Camera status
    if camera_controller and camera_controller.initialized:
        try:
            camera_info = camera_controller.get_camera_info()
            status["cameras"] = list(camera_info['cameras'].keys())
        except Exception as e:
            status["cameras"] = {"error": str(e)}
    else:
        status["cameras"] = []

    return status

# Usage in tool handler:
elif name == 'get_robot_status':
    controllers = request.app['controllers']
    result = get_combined_status(
        controllers['gripper'],
        controllers['arm'],
        controllers['camera'],
        include_details=True
    )

# Usage in status endpoint:
async def handle_status(request: web.Request) -> web.Response:
    controllers = request.app['controllers']
    status = {
        "bridge": "running",
        **get_combined_status(
            controllers['gripper'],
            controllers['arm'],
            controllers['camera'],
            include_details=False  # Summary only
        )
    }
    return web.json_response(status)
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

## LOW PRIORITY TASKS (Features & Documentation)

### Task B.9: Add Health Check Endpoint

**Description:**
The `/status` endpoint (lines 446-477) provides basic status but doesn't actually test controller functionality. Need a proper health check endpoint that validates controllers are working correctly, not just initialized.

**Steps to fix:**
1. Create `/health` endpoint handler
2. Test each controller's functionality (not just initialized flag):
   - Gripper: Try to get state
   - Arm: Try to get state
   - Camera: Try to get frame
3. Return detailed health status for each component
4. Return appropriate HTTP status codes:
   - 200: All healthy
   - 503: Any component unhealthy
5. Add health check to startup validation
6. Document health check endpoint
7. Update CHANGELOG.md with Task B.9 entry

**Impact:**
- Monitoring: Proper health checks for deployment
- Reliability: Detect issues before they cause failures
- Operations: Integration with load balancers/orchestrators
- Debugging: Quick way to check system state

**Priority:** LOW (Operations)
**Estimated Time:** 2 hours
**Dependencies:** Task B.1 (app context)

**Example Implementation:**
```python
async def handle_health(request: web.Request) -> web.Response:
    """
    Detailed health check endpoint

    Tests actual functionality of each controller, not just initialization status.
    Returns 200 if all healthy, 503 if any component unhealthy.
    """
    controllers = request.app['controllers']

    health = {
        "status": "healthy",
        "timestamp": time.time(),
        "controllers": {}
    }

    # Test gripper controller
    if controllers['gripper']:
        try:
            gripper_state = controllers['gripper'].get_gripper_state()
            if gripper_state.get('success'):
                health["controllers"]["gripper"] = {
                    "status": "healthy",
                    "state": gripper_state['state']
                }
            else:
                health["controllers"]["gripper"] = {
                    "status": "unhealthy",
                    "error": gripper_state.get('error', 'Unknown error')
                }
                health["status"] = "degraded"
        except Exception as e:
            health["controllers"]["gripper"] = {
                "status": "error",
                "error": str(e)
            }
            health["status"] = "unhealthy"
    else:
        health["controllers"]["gripper"] = {
            "status": "not_initialized"
        }
        health["status"] = "degraded"

    # Test arm controller
    if controllers['arm']:
        try:
            arm_state = controllers['arm'].get_arm_state()
            if arm_state.get('success'):
                health["controllers"]["arm"] = {
                    "status": "healthy",
                    "state": arm_state['state']
                }
            else:
                health["controllers"]["arm"] = {
                    "status": "unhealthy",
                    "error": arm_state.get('error', 'Unknown error')
                }
                health["status"] = "degraded"
        except Exception as e:
            health["controllers"]["arm"] = {
                "status": "error",
                "error": str(e)
            }
            health["status"] = "unhealthy"
    else:
        health["controllers"]["arm"] = {
            "status": "not_initialized"
        }
        health["status"] = "degraded"

    # Test camera controller
    if controllers['camera']:
        try:
            camera_info = controllers['camera'].get_camera_info()
            if camera_info.get('initialized'):
                health["controllers"]["camera"] = {
                    "status": "healthy",
                    "cameras": list(camera_info['cameras'].keys())
                }
            else:
                health["controllers"]["camera"] = {
                    "status": "unhealthy"
                }
                health["status"] = "degraded"
        except Exception as e:
            health["controllers"]["camera"] = {
                "status": "error",
                "error": str(e)
            }
            health["status"] = "unhealthy"
    else:
        health["controllers"]["camera"] = {
            "status": "not_initialized"
        }

    # Determine HTTP status code
    status_code = 200 if health["status"] == "healthy" else 503

    return web.json_response(health, status=status_code)

# Add route:
app.router.add_get('/health', handle_health)
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

### Task B.10: Add Request Validation Middleware

**Description:**
No middleware validates request structure before it reaches handlers. Invalid JSON, missing fields, or malformed requests only cause errors deep in handler code. Should add middleware to validate early.

**Steps to fix:**
1. Create request validation middleware
2. Validate request structure for POST /aloha-tool-call:
   - Check JSON is valid
   - Check required fields present (name, args)
   - Check field types are correct
3. Return clear error messages (HTTP 400) for invalid requests
4. Add middleware to application
5. Test with various invalid requests
6. Document request format requirements
7. Update CHANGELOG.md with Task B.10 entry

**Impact:**
- Better UX: Clear errors for malformed requests
- Cleaner Code: Handlers don't need to validate structure
- Security: Early rejection of invalid requests
- Performance: Don't process invalid requests

**Priority:** LOW (Code Quality)
**Estimated Time:** 2 hours
**Dependencies:** None

**Example Implementation:**
```python
@web.middleware
async def validate_request_middleware(request, handler):
    """
    Validate request format before passing to handlers

    For POST /aloha-tool-call:
    - Validates JSON format
    - Checks required fields present
    - Validates field types
    """
    # Only validate tool call endpoint
    if request.method == 'POST' and request.path == '/aloha-tool-call':
        # Check content type
        content_type = request.headers.get('Content-Type', '')
        if 'application/json' not in content_type:
            return web.json_response({
                'success': False,
                'error': 'Content-Type must be application/json'
            }, status=400)

        # Try to parse JSON
        try:
            data = await request.json()
        except json.JSONDecodeError as e:
            return web.json_response({
                'success': False,
                'error': f'Invalid JSON: {e}'
            }, status=400)

        # Check required fields
        if 'name' not in data:
            return web.json_response({
                'success': False,
                'error': 'Missing required field: name'
            }, status=400)

        # Validate field types
        if not isinstance(data['name'], str):
            return web.json_response({
                'success': False,
                'error': f"Field 'name' must be string, got {type(data['name']).__name__}"
            }, status=400)

        if 'args' in data and not isinstance(data['args'], dict):
            return web.json_response({
                'success': False,
                'error': f"Field 'args' must be object/dict, got {type(data['args']).__name__}"
            }, status=400)

        if 'id' in data and not isinstance(data['id'], (str, int)):
            return web.json_response({
                'success': False,
                'error': f"Field 'id' must be string or number, got {type(data['id']).__name__}"
            }, status=400)

    # Continue to handler
    return await handler(request)

# Add middleware to app:
def make_app() -> web.Application:
    app = web.Application(middlewares=[validate_request_middleware])
    # ... rest of setup
```

**Files to modify:**
- `gemini-live/gemini-live-api-control/bridges/bridge_aloha_real_ANU_prod.py`
- `CHANGELOG.md`

---

## IMPLEMENTATION ORDER

### **Phase 1: Critical Fixes (Week 1) - Do First**
**Goal:** Fix critical safety and architecture issues

1. ⭐ **Task B.2**: Fix Error Handling (2-3h)
   - *Why first:* Critical for debugging, independent
   - *Blocks:* None

2. ⭐ **Task B.4**: Fix Emergency Stop (1-2h)
   - *Why second:* Critical safety feature
   - *Depends on:* Task 2.1 (gripper e-stop)

3. ⭐ **Task B.3**: Add Input Validation (3-4h)
   - *Why third:* Prevents crashes and dangerous commands
   - *Blocks:* None

4. ⭐ **Task B.1**: Remove Global State (2-3h)
   - *Why fourth:* Architectural foundation
   - *Blocks:* Tasks B.8, B.9 (easier with app context)

**Phase 1 Total:** 8-12 hours (1-1.5 days)

---

### **Phase 2: Code Quality (Week 2) - Do Second**
**Goal:** Improve maintainability and professionalism

5. ✅ **Task B.5**: Structured Logging (2h)
   - *Depends on:* None
   - *Why:* Professional logging, helps debugging

6. ✅ **Task B.6**: Configuration Management (2-3h)
   - *Depends on:* None
   - *Why:* Flexibility for different environments

7. ✅ **Task B.8**: Extract Duplicate Logic (1h)
   - *Depends on:* Task B.1 (app context)
   - *Why:* Clean up duplication

8. ✅ **Task B.7**: Remove Placeholders (1-2h)
   - *Depends on:* None
   - *Why:* Remove misleading code

**Phase 2 Total:** 6-8 hours (1 day)

---

### **Phase 3: Features & Polish (Week 3) - Do Last**
**Goal:** Add nice-to-have features

9. 🎁 **Task B.9**: Health Check (2h)
   - *Depends on:* Task B.1 (app context)
   - *Why:* Better monitoring

10. 🎁 **Task B.10**: Request Validation Middleware (2h)
    - *Depends on:* None
    - *Why:* Clean architecture

**Phase 3 Total:** 4 hours (0.5 days)

---

## TOTAL EFFORT ESTIMATE

| Phase | Tasks | Estimated Time | Calendar Time |
|-------|-------|----------------|---------------|
| Phase 1: Critical Fixes | Tasks B.1-B.4 | 8-12 hours | 1-1.5 days |
| Phase 2: Code Quality | Tasks B.5-B.8 | 6-8 hours | 1 day |
| Phase 3: Features | Tasks B.9-B.10 | 4 hours | 0.5 days |
| **TOTAL** | **10 tasks** | **18-24 hours** | **2.5-3 days** |

---

## QUICK START

### **Start Today (Recommended):**
```bash
# 1. You're already on dev branch
git branch --show-current  # Should show: dev

# 2. Start with Task B.2 (Fix Error Handling)
#    - Quickest safety improvement
#    - Independent (no dependencies)
#    - 2-3 hours
#    - Immediate impact on debugging

# 3. Then Task B.4 (Emergency Stop)
#    - Critical safety
#    - Only 1-2 hours
#    - Depends on Task 2.1 (already done)

# After Day 1: You'll have better error visibility and complete e-stop
```

---

## SUCCESS CRITERIA

After completing all 10 tasks, the bridge should have:

✅ **Architecture:**
- No global state (use app context)
- Proper dependency injection
- Clean separation of concerns

✅ **Safety:**
- Comprehensive error handling (no bare except)
- Complete emergency stop (arm + gripper + resume)
- Input validation preventing dangerous commands

✅ **Code Quality:**
- Structured logging throughout
- No code duplication
- No placeholder/dead code
- Configuration management

✅ **Features:**
- Health check endpoint
- Request validation middleware
- Consistent error responses
- Proper HTTP status codes

✅ **Operations:**
- Environment-based configuration
- Log rotation and management
- Monitoring integration ready
- Production-ready code

---

## NOTES

1. **Dependencies:** Follow the order - Phase 1 tasks unblock later tasks

2. **Testing:** Test each task thoroughly before moving to next

3. **Incremental:** Can commit after each task for progress tracking

4. **Integration:** Tasks B.1 and B.5 affect most other code - do them early

5. **Safety First:** Phase 1 tasks are all safety-critical - prioritize these

---

Ready to start with **Task B.2** (Fix Error Handling)? It's the quickest way to improve system reliability! 🚀
