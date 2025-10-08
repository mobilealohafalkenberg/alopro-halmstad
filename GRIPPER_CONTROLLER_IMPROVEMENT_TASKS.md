# Gripper Controller Improvement Tasks

This document outlines all tasks needed to bring gripper_controller.py up to the same quality, safety, and feature level as arm_controller.py.

---

## HIGH PRIORITY TASKS (Safety & Consistency)

### Task 2.1: Add Emergency Stop State Management

**Description:**
Implement emergency stop functionality in gripper_controller.py to match arm_controller.py. Currently, there is no way to emergency stop the gripper or prevent operations after an emergency stop. This creates a safety gap and inconsistency with the arm controller.

**Steps to fix:**
1. Add ERROR state to `GripperState` enum
2. Implement `emergency_stop()` method that:
   - Disables gripper torque
   - Sets state to ERROR
   - Returns success status
3. Implement `resume_after_stop()` method that:
   - Validates system is in ERROR state
   - Re-enables gripper torque
   - Validates current position is safe
   - Clears ERROR state
4. Add ERROR state checks to all movement methods:
   - `open_gripper()`
   - `close_gripper()`
   - `set_gripper_position()`
5. Create test file: `test/test_gripper_controller/test_emergency_stop.py`
6. Update CHANGELOG.md with Task 2.1 entry

**Impact:**
- Critical Safety Fix: Prevents gripper operations after emergency stop
- Consistency: Matches arm_controller.py emergency stop behavior
- Better Control: Explicit recovery process with validation

**Files to modify:**
- `gemini-live/gripper_controller.py` (add ERROR state, emergency_stop(), resume_after_stop(), state checks)
- `gemini-live/test/test_gripper_controller/test_emergency_stop.py` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
class GripperState(Enum):
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
    ERROR = "error"      # NEW
    UNKNOWN = "unknown"

def emergency_stop(self) -> Dict:
    """Emergency stop - disable gripper torque and enter ERROR state"""
    if not self.initialized:
        return {"success": False, "error": "Not initialized"}

    try:
        print("[GripperController] ⚠️ EMERGENCY STOP ACTIVATED!")
        self.bot.core.robot_torque_enable('single', 'gripper', False)
        with self.state_lock:
            self.current_state = GripperState.ERROR
        print("[GripperController] System in ERROR state. Call resume_after_stop() to recover.")
        return {"success": True, "state": "emergency_stopped"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def open_gripper(self, blocking: bool = True) -> Dict:
    # Check ERROR state first
    with self.state_lock:
        if self.current_state == GripperState.ERROR:
            return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}
    # ... rest of implementation
```

---

### Task 2.2: Fix Race Condition in Position Monitor

**Description:**
Lines 121-123 in gripper_controller.py have a race condition similar to the one fixed in arm_controller.py (Task 1.1). The `self.gripper_position` variable is updated by the monitor thread without lock protection, while other methods reading this variable use `self.state_lock`. This can lead to inconsistent reads.

**Steps to fix:**
1. Modify `_start_position_monitor()` method (lines 115-142)
2. Use local variable to capture position inside `js_mutex`
3. Update shared state `self.gripper_position` with `self.state_lock`
4. Ensure minimal lock hold time
5. Verify all accesses to `self.gripper_position` are protected
6. Create test to verify thread safety
7. Update CHANGELOG.md with Task 2.2 entry

**Impact:**
- Critical Safety Fix: Prevents incorrect state updates
- Thread Safety: Eliminates race condition between monitor and main thread
- Reliability: Ensures consistent position reads
- No Performance Impact: Minimal lock hold time

**Files to modify:**
- `gemini-live/gripper_controller.py` (lines 115-142)
- `CHANGELOG.md`

**Before:**
```python
def monitor():
    while self.initialized:
        try:
            with self.bot.core.js_mutex:
                gripper_index = self.bot.gripper.left_finger_index
                self.gripper_position = self.bot.core.joint_states.position[gripper_index]
```

**After:**
```python
def monitor():
    while self.initialized:
        try:
            # Get position with robot mutex
            with self.bot.core.js_mutex:
                gripper_index = self.bot.gripper.left_finger_index
                position = self.bot.core.joint_states.position[gripper_index]

            # Update shared state with state lock
            with self.state_lock:
                self.gripper_position = position
```

---

### Task 2.3: Deprecate Global Controller Singleton Pattern

**Description:**
Lines 313-340 implement a module-level singleton pattern with `_global_controller` and convenience functions like `get_controller()`, `open_gripper()`, `close_gripper()`, etc. This is the same anti-pattern that was deprecated in arm_controller.py (Task 1.9). It creates hidden global state, makes testing difficult, and prevents multiple gripper instances.

**Steps to fix:**
1. Add deprecation warnings to all singleton functions:
   - `get_controller()` (line 315)
   - `open_gripper()` (line 323)
   - `close_gripper()` (line 327)
   - `get_gripper_state()` (line 331)
   - `cleanup()` (line 335)
2. Update documentation with deprecation notices and migration examples
3. Create migration guide: `gemini-live/docs/MIGRATION_GUIDE_GRIPPER_SINGLETON_REMOVAL.md`
4. Add examples showing explicit instance creation
5. Specify removal timeline (v2.0)
6. Update CHANGELOG.md with Task 2.3 entry

**Impact:**
- Architecture Improvement: Eliminates hidden global state
- Better Testability: Enables proper mocking and isolation
- Multi-Gripper Support: Allows managing multiple gripper instances
- Consistency: Matches arm_controller.py deprecation pattern
- Backward Compatible: All existing code works in current version (with warnings)

**Files to modify:**
- `gemini-live/gripper_controller.py` (lines 313-340: add deprecation warnings)
- `gemini-live/docs/MIGRATION_GUIDE_GRIPPER_SINGLETON_REMOVAL.md` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
def get_controller() -> GripperController:
    """
    Get or create global controller instance.

    .. deprecated:: 2.3
        The global controller singleton pattern is deprecated and will be removed in version 2.0.
        Instead, create and manage controller instances explicitly:

        Example:
            # Old (deprecated):
            controller = get_controller()

            # New (recommended):
            controller = GripperController(robot_name='vx300s', robot_model='follower_left')
            controller.initialize()

    Returns:
        GripperController: The global controller instance
    """
    import warnings
    warnings.warn(
        "get_controller() is deprecated and will be removed in version 2.0. "
        "Create controller instances explicitly: controller = GripperController(); controller.initialize()",
        DeprecationWarning,
        stacklevel=2
    )
    global _global_controller
    if _global_controller is None:
        _global_controller = GripperController()
        _global_controller.initialize()
    return _global_controller
```

---

### Task 2.4: Add Dry-Run Mode

**Description:**
gripper_controller.py lacks a dry-run mode for hardware-independent testing, unlike arm_controller.py which has this feature. This makes it impossible to test gripper logic without actual robot hardware, slowing down development and testing.

**Steps to fix:**
1. Add `dry_run` parameter to `__init__()` method
2. Skip hardware initialization when `dry_run=True`
3. Mock robot responses in dry-run mode
4. Return simulated position/state updates
5. Allow all methods to work without hardware
6. Update all test files to use dry-run mode
7. Add documentation for dry-run usage
8. Update CHANGELOG.md with Task 2.4 entry

**Impact:**
- Development Speed: Test without hardware
- CI/CD Integration: Run tests in automated pipelines
- Consistency: Matches arm_controller.py feature set
- Safer Development: Test logic before deploying to hardware

**Files to modify:**
- `gemini-live/gripper_controller.py` (__init__, initialize, all movement methods)
- All test files
- `CHANGELOG.md`

**Example Implementation:**
```python
def __init__(self, robot_model='vx300s', robot_name='follower_left', dry_run=False):
    """
    Initialize controller (does not connect to robot yet)

    Args:
        robot_model: Robot model identifier
        robot_name: Robot name identifier
        dry_run: If True, skip hardware initialization for testing
    """
    self.robot_model = robot_model
    self.robot_name = robot_name
    self.dry_run = dry_run
    # ... rest of init

def initialize(self) -> bool:
    """Initialize robot connection and move to starting position"""
    if self.dry_run:
        print("[GripperController] Running in DRY-RUN mode (no hardware)")
        self.initialized = True
        self.current_state = GripperState.CLOSED
        self.gripper_position = FOLLOWER_GRIPPER_JOINT_CLOSE
        return True

    # Normal hardware initialization
    try:
        print("[GripperController] Initializing robot connection...")
        # ... rest of hardware init
```

---

## MEDIUM PRIORITY TASKS (Functionality & Robustness)

### Task 2.5: Add Parameter Validation

**Description:**
Movement methods in gripper_controller.py lack comprehensive parameter validation. Methods accept parameters without type checking or range validation, potentially causing unexpected behavior or crashes.

**Steps to fix:**
1. Add type validation for all parameters
2. Add range validation for position values
3. Add validation for `blocking` parameter
4. Add validation for `moving_time` (if exposed)
5. Provide clear error messages
6. Warn users when values are auto-corrected/clamped
7. Create test file: `test/test_gripper_controller/test_parameter_validation.py`
8. Update CHANGELOG.md with Task 2.5 entry

**Impact:**
- Better Error Messages: Users know what went wrong
- Safer Operation: Invalid inputs rejected before hardware commands
- Consistency: Matches arm_controller.py validation patterns
- Debugging: Easier to identify parameter issues

**Files to modify:**
- `gemini-live/gripper_controller.py` (add validation to all methods)
- `gemini-live/test/test_gripper_controller/test_parameter_validation.py` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
def set_gripper_position(self, position: float, blocking: bool = True) -> Dict:
    """Set gripper to a specific position"""
    if not self.initialized:
        return {"success": False, "error": "Not initialized", "state": "unknown"}

    # Validate position type
    if not isinstance(position, (int, float)):
        raise TypeError(f"position must be numeric, got {type(position).__name__}")

    # Validate blocking type
    if not isinstance(blocking, bool):
        raise TypeError(f"blocking must be bool, got {type(blocking).__name__}")

    # Determine if normalized or absolute
    if 0.0 <= position <= 1.0:
        pos_range = FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE
        actual_position = FOLLOWER_GRIPPER_JOINT_CLOSE + (position * pos_range)
    else:
        actual_position = position

    # Validate range and warn if clamping
    original_position = actual_position
    actual_position = max(FOLLOWER_GRIPPER_JOINT_CLOSE,
                         min(FOLLOWER_GRIPPER_JOINT_OPEN, actual_position))

    if actual_position != original_position:
        print(f"[GripperController] ⚠️ Position {original_position:.3f} clamped to {actual_position:.3f}")

    # ... rest of implementation
```

---

### Task 2.6: Improve Error Handling

**Description:**
Line 136 in gripper_controller.py uses a bare `except: pass` that silently ignores ALL errors in the position monitor thread. This is dangerous as it can hide critical failures like disconnections, communication errors, or hardware faults.

**Steps to fix:**
1. Replace bare `except: pass` with specific exception handling
2. Log errors instead of silently ignoring them
3. Add error recovery mechanism
4. Track consecutive errors and shutdown if threshold exceeded
5. Add health monitoring for position monitor thread
6. Notify main thread of monitor failures
7. Create test for error scenarios
8. Update CHANGELOG.md with Task 2.6 entry

**Impact:**
- Critical Safety Fix: Don't hide hardware failures
- Better Debugging: Know when/why monitor fails
- Reliability: Detect and recover from errors
- Monitoring: Track system health

**Files to modify:**
- `gemini-live/gripper_controller.py` (lines 115-142)
- `CHANGELOG.md`

**Before:**
```python
def monitor():
    while self.initialized:
        try:
            # ... position monitoring code
        except Exception:
            pass  # Silently ignore errors
        time.sleep(0.1)
```

**After:**
```python
def monitor():
    consecutive_errors = 0
    max_errors = 10

    while self.initialized:
        try:
            # ... position monitoring code
            consecutive_errors = 0  # Reset on success

        except AttributeError as e:
            # Robot not fully initialized yet
            if consecutive_errors == 0:
                print(f"[GripperController] Position monitor waiting for initialization: {e}")
        except Exception as e:
            consecutive_errors += 1
            print(f"[GripperController] Position monitor error ({consecutive_errors}/{max_errors}): {e}")

            if consecutive_errors >= max_errors:
                print(f"[GripperController] ✗ Position monitor failed - too many errors")
                with self.state_lock:
                    self.current_state = GripperState.ERROR
                break

        time.sleep(0.1)
```

---

### Task 2.7: Add Safety Constraints and Validation

**Description:**
gripper_controller.py lacks safety constraints similar to arm_controller.py. There are no limits on grip force, no timeout detection for stuck grippers, and no validation of safe operating ranges beyond basic position clamping.

**Steps to fix:**
1. Define safety constraints (max force, timeout limits, position ranges)
2. Add `check_safety_constraints()` method
3. Add timeout detection for movements
4. Add grip force monitoring
5. Add current monitoring for object detection
6. Integrate with safety_validator.py if needed
7. Add safety checks before all movements
8. Create test file: `test/test_gripper_controller/test_safety_constraints.py`
9. Update CHANGELOG.md with Task 2.7 entry

**Impact:**
- Critical Safety: Prevents damage to gripper, objects, or robot
- Object Detection: Know when gripper contacts object
- Reliability: Detect stuck/failed movements
- Consistency: Matches arm_controller.py safety approach

**Files to modify:**
- `gemini-live/gripper_controller.py` (add safety constraints and checks)
- `gemini-live/test/test_gripper_controller/test_safety_constraints.py` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
class GripperController:
    # Safety constraints
    SAFETY_CONSTRAINTS = {
        'max_current': 400,  # mA - maximum safe current
        'normal_current': 300,  # mA - normal operating current
        'movement_timeout': 3.0,  # seconds - max time for movement
        'min_position': FOLLOWER_GRIPPER_JOINT_CLOSE - 0.05,
        'max_position': FOLLOWER_GRIPPER_JOINT_OPEN + 0.05,
        'contact_current_threshold': 350,  # mA - indicates contact with object
    }

    def check_safety_constraints(self, target_position: float) -> Tuple[bool, str]:
        """
        Check if target position is safe

        Returns:
            (is_safe, warning_message)
        """
        if target_position < self.SAFETY_CONSTRAINTS['min_position']:
            return False, f"Position {target_position:.3f} below minimum safe limit"

        if target_position > self.SAFETY_CONSTRAINTS['max_position']:
            return False, f"Position {target_position:.3f} above maximum safe limit"

        return True, ""

    def detect_object_contact(self) -> bool:
        """
        Detect if gripper is in contact with object based on current

        Returns:
            True if contact detected
        """
        try:
            current = self.bot.core.robot_get_motor_registers('single', 'gripper', 'Present_Current')
            return current > self.SAFETY_CONSTRAINTS['contact_current_threshold']
        except:
            return False
```

---

### Task 2.8: Add Movement Timeout Detection

**Description:**
Gripper movements can get stuck if an object prevents closing or if hardware fails. Currently there's no timeout detection, so the controller may wait indefinitely or report success when the movement actually failed.

**Steps to fix:**
1. Add timeout parameter to movement methods
2. Monitor actual position during movements
3. Detect when movement is stuck/stalled
4. Return failure if timeout exceeded
5. Add timeout to blocking mode waits
6. Log timeout failures clearly
7. Set ERROR state on critical timeouts
8. Create test for timeout scenarios
9. Update CHANGELOG.md with Task 2.8 entry

**Impact:**
- Reliability: Detect failed movements
- Better UX: Don't wait forever for stuck gripper
- Error Detection: Know when hardware has issues
- Recovery: Can detect and recover from failures

**Files to modify:**
- `gemini-live/gripper_controller.py` (add timeout to all movement methods)
- `CHANGELOG.md`

**Example Implementation:**
```python
def close_gripper(self, blocking: bool = True, timeout: float = 3.0) -> Dict:
    """
    Close the gripper with timeout detection

    Args:
        blocking: If True, wait for movement to complete
        timeout: Maximum time to wait for movement (seconds)
    """
    if not self.initialized:
        return {"success": False, "error": "Not initialized", "state": "unknown"}

    with self.state_lock:
        self.current_state = GripperState.CLOSING

    print("[GripperController] Closing gripper...")
    move_grippers([self.bot], [FOLLOWER_GRIPPER_JOINT_CLOSE], moving_time=1.0)

    if blocking:
        start_time = time.time()
        while time.time() - start_time < timeout:
            with self.state_lock:
                if self.current_state == GripperState.CLOSED:
                    return self.get_gripper_state()
                # Check if reached close threshold
                if self.gripper_position <= self.CLOSE_THRESHOLD:
                    self.current_state = GripperState.CLOSED
                    return self.get_gripper_state()
            time.sleep(0.05)

        # Timeout occurred
        print(f"[GripperController] ⚠️ Close timeout after {timeout}s")
        return {
            "success": False,
            "error": f"Movement timeout after {timeout}s",
            "state": self.current_state.value,
            "position": self.gripper_position
        }

    return self.get_gripper_state()
```

---

## LOW PRIORITY TASKS (Advanced Features & Polish)

### Task 2.9: Add Force Control and Grasp Detection

**Description:**
Current gripper controller uses position control only. Adding force feedback enables soft grasping, object detection, and adaptive grip strength - useful for handling delicate or varied objects.

**Steps to fix:**
1. Add current monitoring to detect grip force
2. Implement `soft_grasp()` method with force limits
3. Add `detect_grasp()` method to confirm object is held
4. Add configurable force thresholds
5. Implement adaptive grip (adjust based on object)
6. Add grasp quality feedback
7. Create test file: `test/test_gripper_controller/test_force_control.py`
8. Update CHANGELOG.md with Task 2.9 entry

**Impact:**
- Advanced Feature: Enable delicate object handling
- Object Detection: Know when object is grasped
- Adaptive Control: Adjust grip based on object properties
- Better UX: Prevent crushing delicate objects

**Files to modify:**
- `gemini-live/gripper_controller.py` (add force control methods)
- `gemini-live/test/test_gripper_controller/test_force_control.py` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
def soft_grasp(self, max_current: int = 200, timeout: float = 3.0) -> Dict:
    """
    Perform a soft grasp using current-based force control

    Args:
        max_current: Maximum current (mA) for gentle grasp
        timeout: Maximum time to attempt grasp

    Returns:
        Dict with grasp success, force, and object detection
    """
    if not self.initialized:
        return {"success": False, "error": "Not initialized"}

    # Set lower current limit for soft grasp
    self.bot.core.robot_set_motor_registers('single', 'gripper', 'current_limit', max_current)

    # Close until current threshold reached (object contact)
    result = self.close_gripper(blocking=True, timeout=timeout)

    # Check if object was grasped
    object_detected = self.detect_object_contact()

    return {
        "success": result.get('success', False),
        "state": result.get('state'),
        "position": result.get('position'),
        "object_detected": object_detected,
        "grasp_quality": "good" if object_detected else "no_object"
    }

def detect_object_contact(self) -> bool:
    """Detect if gripper is holding an object"""
    try:
        current = self.bot.core.robot_get_motor_registers('single', 'gripper', 'Present_Current')
        # Object detected if current is elevated but gripper not fully closed
        if current > self.SAFETY_CONSTRAINTS['contact_current_threshold']:
            if self.gripper_position > self.CLOSE_THRESHOLD:
                return True
        return False
    except:
        return False
```

---

### Task 2.10: Add Coordinated Arm-Gripper Control

**Description:**
Many manipulation tasks require coordinated arm and gripper movements (e.g., approach → grasp → lift). Currently arm_controller and gripper_controller operate independently. Adding coordination enables higher-level manipulation primitives.

**Steps to fix:**
1. Add reference to arm_controller in gripper_controller (optional)
2. Create `manipulation_primitives.py` module
3. Implement high-level primitives:
   - `pick_object(position)` - approach, grasp, lift
   - `place_object(position)` - lower, release, retract
   - `transfer_object(from_pos, to_pos)` - complete pick and place
4. Add synchronization between arm and gripper
5. Add error recovery for failed manipulation
6. Create test file: `test/test_manipulation_primitives.py`
7. Update CHANGELOG.md with Task 2.10 entry

**Impact:**
- High-Level API: Easier manipulation programming
- Coordination: Synchronized arm and gripper movements
- Error Recovery: Handle failures in multi-step tasks
- Better UX: Simple interface for complex tasks

**Files to modify:**
- `gemini-live/manipulation_primitives.py` (new file)
- `gemini-live/test/test_manipulation_primitives.py` (new file)
- `CHANGELOG.md`

**Example Implementation:**
```python
# manipulation_primitives.py
from arm_controller import ArmController
from gripper_controller import GripperController

class ManipulationController:
    def __init__(self, robot_model='vx300s', robot_name='follower_left'):
        self.arm = ArmController(robot_model=robot_model, robot_name=robot_name)
        self.gripper = GripperController(robot_model=robot_model, robot_name=robot_name)

    def initialize(self):
        self.arm.initialize()
        self.gripper.initialize()

    def pick_object(self, position, approach_height=0.15, grasp_force=200):
        """
        Pick up an object at given position

        Args:
            position: [x, y, z] position of object
            approach_height: Height above object for approach
            grasp_force: Gripper force for grasp (mA)
        """
        # Open gripper
        self.gripper.open_gripper()

        # Approach position (above object)
        approach_pos = [position[0], position[1], position[2] + approach_height]
        result = self.arm.move_to_position(approach_pos)
        if not result['success']:
            return {"success": False, "error": "Failed to reach approach position"}

        # Lower to grasp position
        result = self.arm.move_to_position(position)
        if not result['success']:
            return {"success": False, "error": "Failed to reach grasp position"}

        # Grasp with soft force
        result = self.gripper.soft_grasp(max_current=grasp_force)
        if not result.get('object_detected'):
            return {"success": False, "error": "No object detected in gripper"}

        # Lift object
        lift_pos = [position[0], position[1], position[2] + approach_height]
        result = self.arm.move_to_position(lift_pos)

        return {"success": True, "message": "Object picked successfully"}
```

---

### Task 2.11: Add Comprehensive Testing Infrastructure

**Description:**
gripper_controller.py has no dedicated test files. Adding comprehensive tests ensures reliability, catches regressions, and enables confident refactoring.

**Steps to fix:**
1. Create test directory structure: `test/test_gripper_controller/`
2. Create test files:
   - `test_gripper_controller.py` - Basic functionality tests
   - `test_emergency_stop.py` - Emergency stop tests (from Task 2.1)
   - `test_parameter_validation.py` - Validation tests (from Task 2.5)
   - `test_safety_constraints.py` - Safety tests (from Task 2.7)
   - `test_force_control.py` - Force control tests (from Task 2.9)
   - `test_dry_run_mode.py` - Dry-run mode tests
3. Add integration tests with arm_controller
4. Add test runner script
5. Document testing procedures
6. Update CHANGELOG.md with Task 2.11 entry

**Impact:**
- Quality Assurance: Catch bugs before deployment
- Regression Prevention: Ensure fixes don't break
- Documentation: Tests show usage examples
- CI/CD Ready: Automated testing in pipelines

**Files to create:**
- `gemini-live/test/test_gripper_controller/test_gripper_controller.py`
- `gemini-live/test/test_gripper_controller/test_emergency_stop.py`
- `gemini-live/test/test_gripper_controller/test_parameter_validation.py`
- `gemini-live/test/test_gripper_controller/test_safety_constraints.py`
- `gemini-live/test/test_gripper_controller/test_force_control.py`
- `gemini-live/test/test_gripper_controller/test_dry_run_mode.py`
- `gemini-live/test/test_gripper_controller/run_all_tests.py`
- `CHANGELOG.md`

**Example Test Structure:**
```python
# test/test_gripper_controller/test_gripper_controller.py
import sys
from gripper_controller import GripperController

class TestGripperController:
    """Basic functionality tests for GripperController"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.controller = None

    def setup(self):
        """Initialize controller in dry-run mode"""
        self.controller = GripperController(dry_run=True)
        self.controller.initialize()

    def test_initialization(self):
        """Test controller initializes correctly"""
        assert self.controller.initialized == True
        assert self.controller.current_state.value == 'closed'
        self.passed += 1
        print("✓ Test 1: Initialization")

    def test_open_gripper(self):
        """Test gripper opens"""
        result = self.controller.open_gripper()
        assert result['success'] == True
        assert result['state'] == 'open'
        self.passed += 1
        print("✓ Test 2: Open gripper")

    def test_close_gripper(self):
        """Test gripper closes"""
        result = self.controller.close_gripper()
        assert result['success'] == True
        assert result['state'] == 'closed'
        self.passed += 1
        print("✓ Test 3: Close gripper")

    def run_all_tests(self):
        """Run all tests"""
        print("=== GripperController Tests ===\n")

        self.setup()

        try:
            self.test_initialization()
            self.test_open_gripper()
            self.test_close_gripper()
        except AssertionError as e:
            self.failed += 1
            print(f"✗ Test failed: {e}")
        except Exception as e:
            self.failed += 1
            print(f"✗ Test error: {e}")

        print(f"\n=== Results ===")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        return self.failed == 0

if __name__ == '__main__':
    tester = TestGripperController()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
```

---

### Task 2.12: Add Comprehensive Documentation

**Description:**
gripper_controller.py lacks detailed documentation, migration guides, and usage examples. Adding comprehensive docs helps users understand the API and migrate from deprecated patterns.

**Steps to fix:**
1. Create migration guide for singleton removal (from Task 2.3)
2. Add detailed docstrings with examples to all methods
3. Create usage examples directory: `examples/gripper_controller/`
4. Add example scripts:
   - `basic_gripper_control.py`
   - `force_control_example.py`
   - `coordinated_manipulation.py`
5. Update main README.md with gripper controller section
6. Document all safety constraints
7. Add troubleshooting guide
8. Update CHANGELOG.md with Task 2.12 entry

**Impact:**
- Better UX: Users understand how to use controller
- Migration Support: Clear path from old to new API
- Examples: Working code to learn from
- Reduced Support: Self-service documentation

**Files to create/modify:**
- `gemini-live/docs/MIGRATION_GUIDE_GRIPPER_SINGLETON_REMOVAL.md`
- `gemini-live/examples/gripper_controller/basic_gripper_control.py`
- `gemini-live/examples/gripper_controller/force_control_example.py`
- `gemini-live/examples/gripper_controller/coordinated_manipulation.py`
- `gemini-live/gripper_controller.py` (enhanced docstrings)
- `README.md`
- `CHANGELOG.md`

**Example Documentation:**
```python
def set_gripper_position(self, position: float, blocking: bool = True, timeout: float = 3.0) -> Dict:
    """
    Set gripper to a specific position.

    The gripper can be controlled using either:
    - Normalized position: 0.0 (fully closed) to 1.0 (fully open)
    - Absolute position: Joint angle in radians

    Args:
        position: Target position
                  - If 0.0 <= position <= 1.0: Treated as normalized (0=closed, 1=open)
                  - Otherwise: Treated as absolute angle in radians
        blocking: If True, wait for movement to complete before returning
        timeout: Maximum time to wait for movement completion (seconds)
                 Only applies when blocking=True

    Returns:
        Dictionary containing:
        - success: bool - Whether operation succeeded
        - state: str - Current gripper state
        - position: float - Current position in radians
        - position_normalized: float - Position as 0.0 to 1.0
        - error: str - Error message (only if success=False)

    Raises:
        TypeError: If position is not numeric or blocking is not bool
        ValueError: If position is outside valid range

    Examples:
        >>> # Normalized position (50% open)
        >>> controller.set_gripper_position(0.5)

        >>> # Fully open (normalized)
        >>> controller.set_gripper_position(1.0)

        >>> # Absolute position in radians
        >>> controller.set_gripper_position(0.037, blocking=False)

        >>> # With timeout
        >>> result = controller.set_gripper_position(0.8, blocking=True, timeout=2.0)
        >>> if result['success']:
        >>>     print(f"Gripper at {result['position_normalized']*100:.0f}% open")

    Safety Notes:
        - Position is automatically clamped to safe range
        - Movement will timeout if gripper gets stuck
        - Use blocking=True for sequential operations
        - Use blocking=False for parallel arm+gripper control
    """
    # Implementation...
```

---

### Task 2.13: Add Configurable Parameters

**Description:**
Many parameters in gripper_controller.py are hard-coded (current limits, movement times, thresholds). Making these configurable allows users to tune behavior for different applications and hardware.

**Steps to fix:**
1. Move hard-coded values to class-level constants
2. Add parameters to `__init__()` for key settings:
   - `current_limit` (default 300mA)
   - `default_moving_time` (default 1.0s)
   - `open_threshold`, `close_threshold`
3. Add methods to adjust settings at runtime:
   - `set_current_limit()`
   - `set_movement_speed()`
   - `set_thresholds()`
4. Validate all configuration parameters
5. Save/load configuration from file
6. Document all configurable parameters
7. Update CHANGELOG.md with Task 2.13 entry

**Impact:**
- Flexibility: Tune for different applications
- Customization: Adjust for different hardware
- Better UX: Users control gripper behavior
- Maintainability: Constants in one place

**Files to modify:**
- `gemini-live/gripper_controller.py`
- `CHANGELOG.md`

**Example Implementation:**
```python
class GripperController:
    """Main API class for controlling the Mobile ALOHA gripper"""

    # Default configuration
    DEFAULT_CONFIG = {
        'current_limit': 300,  # mA
        'movement_time': 1.0,  # seconds
        'open_threshold': FOLLOWER_GRIPPER_JOINT_OPEN - 0.1,
        'close_threshold': FOLLOWER_GRIPPER_JOINT_CLOSE + 0.1,
        'max_force': 400,  # mA
        'timeout': 3.0,  # seconds
    }

    def __init__(self,
                 robot_model='vx300s',
                 robot_name='follower_left',
                 dry_run=False,
                 current_limit=None,
                 movement_time=None):
        """
        Initialize controller with optional configuration

        Args:
            robot_model: Robot model identifier
            robot_name: Robot name identifier
            dry_run: If True, skip hardware for testing
            current_limit: Motor current limit in mA (default: 300)
            movement_time: Default movement time in seconds (default: 1.0)
        """
        self.robot_model = robot_model
        self.robot_name = robot_name
        self.dry_run = dry_run

        # Apply configuration
        self.config = self.DEFAULT_CONFIG.copy()
        if current_limit is not None:
            self.config['current_limit'] = current_limit
        if movement_time is not None:
            self.config['movement_time'] = movement_time

        # Set thresholds based on config
        self.OPEN_THRESHOLD = self.config['open_threshold']
        self.CLOSE_THRESHOLD = self.config['close_threshold']

        # ... rest of init

    def set_current_limit(self, current_limit: int) -> Dict:
        """
        Set gripper current limit (force control)

        Args:
            current_limit: Current limit in mA (100-400)

        Returns:
            Dict with success status
        """
        if not 100 <= current_limit <= 400:
            return {
                "success": False,
                "error": f"Current limit must be 100-400mA, got {current_limit}"
            }

        self.config['current_limit'] = current_limit

        if self.initialized and not self.dry_run:
            self.bot.core.robot_set_motor_registers(
                'single', 'gripper', 'current_limit', current_limit
            )

        print(f"[GripperController] Current limit set to {current_limit}mA")
        return {"success": True, "current_limit": current_limit}
```

---

## Task Priority Summary

### **HIGH PRIORITY** (Do First - Safety & Consistency):
1. **Task 2.1**: Add Emergency Stop State Management
2. **Task 2.2**: Fix Race Condition in Position Monitor
3. **Task 2.3**: Deprecate Global Controller Singleton Pattern
4. **Task 2.4**: Add Dry-Run Mode

### **MEDIUM PRIORITY** (Do Second - Functionality):
5. **Task 2.5**: Add Parameter Validation
6. **Task 2.6**: Improve Error Handling
7. **Task 2.7**: Add Safety Constraints and Validation
8. **Task 2.8**: Add Movement Timeout Detection

### **LOW PRIORITY** (Do Last - Polish & Advanced Features):
9. **Task 2.9**: Add Force Control and Grasp Detection
10. **Task 2.10**: Add Coordinated Arm-Gripper Control
11. **Task 2.11**: Add Comprehensive Testing Infrastructure
12. **Task 2.12**: Add Comprehensive Documentation
13. **Task 2.13**: Add Configurable Parameters

---

## Recommended Implementation Order

**Phase 1: Critical Fixes (Tasks 2.1-2.4)**
- Focus on safety and consistency with arm_controller.py
- Estimated time: 2-3 days

**Phase 2: Robustness (Tasks 2.5-2.8)**
- Improve reliability and error handling
- Estimated time: 2-3 days

**Phase 3: Advanced Features (Tasks 2.9-2.13)**
- Add nice-to-have features and polish
- Estimated time: 3-5 days

**Total Estimated Effort:** 7-11 days

---

## Success Criteria

After completing all tasks, gripper_controller.py should:
- ✅ Match arm_controller.py quality and safety standards
- ✅ Have emergency stop functionality
- ✅ Be fully testable without hardware (dry-run mode)
- ✅ Have comprehensive error handling
- ✅ Have deprecation warnings for singleton pattern
- ✅ Have parameter validation on all methods
- ✅ Have safety constraints and timeout detection
- ✅ Have comprehensive test coverage
- ✅ Have detailed documentation and examples
- ✅ Support advanced features (force control, coordination)
