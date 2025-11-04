# Migration Guide: Gripper Controller Singleton Pattern Removal

**Task:** 2.3
**Version:** 2.3 deprecation, 2.0 removal
**Status:** Deprecated (functions still work with warnings)

## Overview

The global singleton pattern in `gripper_controller.py` has been deprecated to improve code quality, testability, and consistency with `arm_controller.py`. This guide helps you migrate from the deprecated singleton functions to explicit controller instance management.

##  What's Changed

### Deprecated Functions (Lines 326-460)

These 5 functions are now deprecated:
1. `get_controller()` - Returns global controller instance
2. `open_gripper()` - Opens gripper using global controller
3. `close_gripper()` - Closes gripper using global controller
4. `get_gripper_state()` - Gets gripper state from global controller
5. `cleanup()` - Cleans up global controller

### Why This Change?

**Problems with Singleton Pattern:**
- **Hidden Global State**: Makes code harder to test and debug
- **Testing Difficulties**: Global state causes test isolation issues
- **Single Instance Limitation**: Can't control multiple grippers
- **Inconsistency**: arm_controller.py already deprecated this pattern (Task 1.9)

**Benefits of Explicit Instances:**
- **Clear Ownership**: Controller lifecycle is explicit and traceable
- **Better Testability**: Easy to mock and isolate in tests
- **Multi-Robot Support**: Can manage multiple gripper instances
- **Thread Safety**: Reduces risks from shared global state

## Migration Timeline

- **v1.9 (Current)**: Singleton functions work but emit DeprecationWarning
- **v2.0 (Future)**: Singleton functions will be completely removed

## How to Migrate

### Pattern 1: Basic Usage

**Before (Deprecated):**
```python
from gripper_controller import get_controller, open_gripper, close_gripper

controller = get_controller()  # Uses hidden global
open_gripper()   # Uses hidden global
close_gripper()  # Uses hidden global
```

**After (Recommended):**
```python
from gripper_controller import GripperController

controller = GripperController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()
controller.open_gripper()
controller.close_gripper()
controller.shutdown()
```

### Pattern 2: With Context Manager (Best Practice)

**After (Best Practice):**
```python
from gripper_controller import GripperController
import contextlib

@contextlib.contextmanager
def gripper_context():
    """Context manager for gripper controller lifecycle"""
    controller = GripperController(robot_model='vx300s', robot_name='follower_left')
    try:
        controller.initialize()
        yield controller
    finally:
        controller.shutdown()

# Usage
with gripper_context() as gripper:
    gripper.open_gripper()
    gripper.close_gripper()
    state = gripper.get_gripper_state()
```

### Pattern 3: Class-Based Approach

**Before (Deprecated):**
```python
from gripper_controller import open_gripper, close_gripper, cleanup

class MyRobotTask:
    def run(self):
        open_gripper()
        # ... do work ...
        close_gripper()
        cleanup()
```

**After (Recommended):**
```python
from gripper_controller import GripperController

class MyRobotTask:
    def __init__(self):
        self.gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
        self.gripper.initialize()

    def run(self):
        self.gripper.open_gripper()
        # ... do work ...
        self.gripper.close_gripper()

    def cleanup(self):
        self.gripper.shutdown()
```

### Pattern 4: Function Parameters (Dependency Injection)

**Before (Deprecated):**
```python
from gripper_controller import get_controller, open_gripper

def pick_object():
    open_gripper()
    # ... pick logic ...

pick_object()
```

**After (Recommended):**
```python
from gripper_controller import GripperController

def pick_object(gripper: GripperController):
    gripper.open_gripper()
    # ... pick logic ...

# Usage
controller = GripperController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()
pick_object(controller)
controller.shutdown()
```

## Complete Migration Examples

### Example 1: Simple Script

**Before:**
```python
#!/usr/bin/env python3
from gripper_controller import open_gripper, close_gripper, get_gripper_state, cleanup
import time

# Open gripper
open_gripper()
time.sleep(1)

# Check state
state = get_gripper_state()
print(f"State: {state}")

# Close gripper
close_gripper()

# Cleanup
cleanup()
```

**After:**
```python
#!/usr/bin/env python3
from gripper_controller import GripperController
import time

# Create and initialize controller
gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
gripper.initialize()

try:
    # Open gripper
    gripper.open_gripper()
    time.sleep(1)

    # Check state
    state = gripper.get_gripper_state()
    print(f"State: {state}")

    # Close gripper
    gripper.close_gripper()

finally:
    # Always cleanup
    gripper.shutdown()
```

### Example 2: Integration with Bridge

**Before:**
```python
from gripper_controller import get_controller, open_gripper, close_gripper

def handle_gripper_command(command):
    if command == "open":
        return open_gripper()
    elif command == "close":
        return close_gripper()
```

**After:**
```python
from gripper_controller import GripperController

class GripperBridge:
    def __init__(self):
        self.gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
        self.gripper.initialize()

    def handle_command(self, command):
        if command == "open":
            return self.gripper.open_gripper()
        elif command == "close":
            return self.gripper.close_gripper()

    def shutdown(self):
        self.gripper.shutdown()
```

### Example 3: Multiple Grippers (New Capability!)

**Now Possible:**
```python
from gripper_controller import GripperController

# Control two grippers independently!
left_gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
right_gripper = GripperController(robot_model='vx300s', robot_name='follower_right')

left_gripper.initialize()
right_gripper.initialize()

try:
    left_gripper.open_gripper()
    right_gripper.close_gripper()

finally:
    left_gripper.shutdown()
    right_gripper.shutdown()
```

## Testing Your Migration

### Enable Deprecation Warnings

```python
import warnings
warnings.simplefilter('always', DeprecationWarning)

# Now any deprecated function calls will print warnings
```

### Run Your Code

If you see warnings like:
```
DeprecationWarning: get_controller() is deprecated and will be removed in version 2.0.
Create controller instances explicitly: controller = GripperController(robot_model='vx300s', robot_name='follower_left'); controller.initialize()
```

You need to migrate that code!

### Verify No Warnings

After migration, run again and verify no DeprecationWarning messages appear.

## Common Migration Mistakes

### Mistake 1: Forgetting to Initialize

**Wrong:**
```python
gripper = GripperController()
gripper.open_gripper()  # ERROR: Not initialized!
```

**Correct:**
```python
gripper = GripperController()
gripper.initialize()  # Must call initialize!
gripper.open_gripper()
```

### Mistake 2: Not Cleaning Up

**Wrong:**
```python
gripper = GripperController()
gripper.initialize()
gripper.open_gripper()
# Forgot to call shutdown()!
```

**Correct:**
```python
gripper = GripperController()
gripper.initialize()
try:
    gripper.open_gripper()
finally:
    gripper.shutdown()  # Always cleanup
```

### Mistake 3: Creating Multiple Instances Without Shutdown

**Wrong:**
```python
for i in range(10):
    gripper = GripperController()
    gripper.initialize()  # Creates 10 ROS nodes! Bad!
```

**Correct:**
```python
gripper = GripperController()
gripper.initialize()
try:
    for i in range(10):
        gripper.open_gripper()
        gripper.close_gripper()
finally:
    gripper.shutdown()
```

## FAQ

### Q: Do I have to migrate now?
**A:** No, but you should. The functions still work in v1.9 but will be removed in v2.0.

### Q: Will my code break in v1.9?
**A:** No, it will just print warnings. It will break in v2.0 when functions are removed.

### Q: Can I silence the warnings temporarily?
**A:** Yes, but not recommended:
```python
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
```

### Q: How do I find all deprecated usage in my code?
**A:** Run with warnings enabled:
```bash
python3 -W always::DeprecationWarning your_script.py
```

### Q: What if I'm using dry-run mode for testing?
**A:** Explicit instances make testing easier:
```python
gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
# In tests, you can easily mock or use dry-run mode
```

### Q: Is this the same as the arm_controller migration?
**A:** Yes! This follows the exact same pattern as Task 1.9 (arm controller singleton removal).

## Need Help?

If you encounter issues during migration:

1. Check the deprecation warning message - it includes the fix
2. Review examples in this guide
3. Look at `arm_controller.py` migration guide (same pattern)
4. Check test files for examples of explicit instance usage

## Summary Checklist

- [ ] Replace `get_controller()` with `GripperController()` + `initialize()`
- [ ] Replace `open_gripper()` with `controller.open_gripper()`
- [ ] Replace `close_gripper()` with `controller.close_gripper()`
- [ ] Replace `get_gripper_state()` with `controller.get_gripper_state()`
- [ ] Replace `cleanup()` with `controller.shutdown()`
- [ ] Add proper initialization and cleanup
- [ ] Test with deprecation warnings enabled
- [ ] Verify no warnings appear after migration

## Timeline

- **Now (v1.9)**: Migrate your code while functions still work
- **v2.0**: Singleton functions removed completely

**Migrate now to avoid breaking changes in v2.0!**
