# Migration Guide: Global Controller Singleton Removal

## Overview

**Version:** 1.9 (deprecation), 2.0 (removal planned)
**Status:** Deprecated in v1.9, will be removed in v2.0
**Impact:** Breaking change for code using global controller functions

The global controller singleton pattern (`get_controller()`, `move_arm()`, `get_arm_state()`, `cleanup()`) is being deprecated and will be removed in version 2.0. This guide helps you migrate your code to use explicit controller instance management.

## Why This Change?

The singleton pattern creates several issues:

1. **Hidden Global State**: Makes testing difficult and code behavior unpredictable
2. **Single Instance Limitation**: Prevents managing multiple robot arms
3. **Poor Testability**: Hard to mock or isolate for unit tests
4. **Unclear Ownership**: Difficult to track controller lifecycle
5. **Thread Safety Concerns**: Shared global state can cause race conditions

## Migration Steps

### 1. Replace `get_controller()`

**Before (deprecated):**
```python
from arm_controller import get_controller

controller = get_controller()
controller.move_to_position([0.3, 0.0, 0.2])
```

**After (recommended):**
```python
from arm_controller import ArmController

controller = ArmController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()
controller.move_to_position([0.3, 0.0, 0.2])

# When done
controller.shutdown()
```

### 2. Replace `move_arm()`

**Before (deprecated):**
```python
from arm_controller import move_arm

# Move to position
move_arm(position=[0.3, 0.0, 0.2])

# Move to named pose
move_arm(pose='home')

# Move to joint angles
move_arm(joints=[0.0, -0.96, 1.16, 0.0, -0.3, 0.0])
```

**After (recommended):**
```python
from arm_controller import ArmController

controller = ArmController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()

# Move to position
controller.move_to_position([0.3, 0.0, 0.2])

# Move to named pose
controller.move_to_pose('home')

# Move to joint angles
controller.move_joints([0.0, -0.96, 1.16, 0.0, -0.3, 0.0])

controller.shutdown()
```

### 3. Replace `get_arm_state()`

**Before (deprecated):**
```python
from arm_controller import get_arm_state

state = get_arm_state()
print(f"Current state: {state['state']}")
print(f"Current joints: {state['joints']}")
```

**After (recommended):**
```python
from arm_controller import ArmController

controller = ArmController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()

state = controller.get_arm_state()
print(f"Current state: {state['state']}")
print(f"Current joints: {state['joints']}")

controller.shutdown()
```

### 4. Replace `cleanup()`

**Before (deprecated):**
```python
from arm_controller import get_controller, cleanup

controller = get_controller()
# ... use controller ...
cleanup()  # Cleanup global controller
```

**After (recommended):**
```python
from arm_controller import ArmController

controller = ArmController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()
# ... use controller ...
controller.shutdown()  # Explicit cleanup
```

## Best Practices

### 1. Use Context Managers (Recommended)

Create a context manager for automatic cleanup:

```python
from contextlib import contextmanager
from arm_controller import ArmController

@contextmanager
def arm_controller_session(robot_model='vx300s', robot_name='follower_left', **kwargs):
    """Context manager for arm controller with automatic cleanup"""
    controller = ArmController(robot_model=robot_model, robot_name=robot_name, **kwargs)
    controller.initialize()
    try:
        yield controller
    finally:
        controller.shutdown()

# Usage
with arm_controller_session() as controller:
    controller.move_to_pose('home')
    controller.move_to_position([0.3, 0.0, 0.2])
    # Automatic cleanup on exit
```

### 2. Class-Based Approach

For applications managing robot lifecycle:

```python
from arm_controller import ArmController

class RobotApplication:
    def __init__(self):
        self.controller = ArmController(
            robot_model='vx300s',
            robot_name='follower_left',
            enable_safety=True
        )
        self.controller.initialize()

    def run(self):
        """Main application logic"""
        self.controller.move_to_pose('ready')
        # ... application logic ...

    def shutdown(self):
        """Clean shutdown"""
        if self.controller:
            self.controller.shutdown()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
        return False

# Usage
with RobotApplication() as app:
    app.run()
```

### 3. Dependency Injection

For better testability:

```python
from arm_controller import ArmController

class PickAndPlaceTask:
    def __init__(self, controller: ArmController):
        """Accept controller as dependency"""
        self.controller = controller

    def execute(self, pick_pos, place_pos):
        """Execute pick and place"""
        self.controller.move_to_position(pick_pos)
        # ... task logic ...
        self.controller.move_to_position(place_pos)

# Usage
controller = ArmController(robot_model='vx300s', robot_name='follower_left')
controller.initialize()

task = PickAndPlaceTask(controller)
task.execute([0.3, 0.0, 0.1], [0.3, 0.2, 0.1])

controller.shutdown()
```

## Migration Checklist

- [ ] Replace all `get_controller()` calls with explicit `ArmController()` instantiation
- [ ] Replace all `move_arm()` calls with instance methods (`move_to_position()`, `move_to_pose()`, `move_joints()`)
- [ ] Replace all `get_arm_state()` calls with `controller.get_arm_state()`
- [ ] Replace all `cleanup()` calls with `controller.shutdown()`
- [ ] Add proper lifecycle management (initialization and cleanup)
- [ ] Consider using context managers or class-based approaches
- [ ] Update tests to use explicit controller instances
- [ ] Remove imports of deprecated functions

## Testing Your Migration

### Before Migration Test:
```python
# This will show deprecation warnings in v1.9
import warnings
warnings.simplefilter('always', DeprecationWarning)

from arm_controller import get_controller, move_arm
controller = get_controller()  # DeprecationWarning shown
move_arm(pose='home')  # DeprecationWarning shown
```

### After Migration Test:
```python
# No deprecation warnings
from arm_controller import ArmController

controller = ArmController(robot_model='vx300s', robot_name='follower_left', dry_run=True)
controller.initialize()
controller.move_to_pose('home')
controller.shutdown()
```

## Timeline

- **v1.9 (Current)**: Deprecation warnings added, old API still works
- **v2.0 (Planned)**: Global singleton functions removed, breaking change

## Getting Help

If you encounter issues during migration:

1. Check the deprecation warning messages for specific guidance
2. Review the examples in this guide
3. Refer to the main [arm_controller.py](../arm_controller.py) documentation
4. Create an issue with your migration question

## Examples

### Complete Migration Example

**Before (v1.8 and earlier):**
```python
#!/usr/bin/env python3
from arm_controller import get_controller, move_arm, get_arm_state, cleanup

def main():
    # Get global controller
    controller = get_controller()

    # Move around
    move_arm(pose='home')
    move_arm(position=[0.3, 0.0, 0.2])

    # Check state
    state = get_arm_state()
    print(f"State: {state}")

    # Cleanup
    cleanup()

if __name__ == '__main__':
    main()
```

**After (v1.9 and later):**
```python
#!/usr/bin/env python3
from arm_controller import ArmController

def main():
    # Create controller explicitly
    controller = ArmController(robot_model='vx300s', robot_name='follower_left')
    controller.initialize()

    try:
        # Move around
        controller.move_to_pose('home')
        controller.move_to_position([0.3, 0.0, 0.2])

        # Check state
        state = controller.get_arm_state()
        print(f"State: {state}")
    finally:
        # Explicit cleanup
        controller.shutdown()

if __name__ == '__main__':
    main()
```

**Best Practice (with context manager):**
```python
#!/usr/bin/env python3
from contextlib import contextmanager
from arm_controller import ArmController

@contextmanager
def arm_controller_session(**kwargs):
    controller = ArmController(**kwargs)
    controller.initialize()
    try:
        yield controller
    finally:
        controller.shutdown()

def main():
    with arm_controller_session(robot_model='vx300s', robot_name='follower_left') as controller:
        controller.move_to_pose('home')
        controller.move_to_position([0.3, 0.0, 0.2])
        state = controller.get_arm_state()
        print(f"State: {state}")

if __name__ == '__main__':
    main()
```

## FAQ

**Q: Why can't I just ignore the warnings?**
A: The deprecated functions will be completely removed in v2.0, causing your code to break.

**Q: Can I use both old and new APIs during migration?**
A: Yes, in v1.9 both work, but you'll see deprecation warnings for old API usage.

**Q: How do I manage multiple arms now?**
A: Create multiple `ArmController` instances with different `robot_name` parameters:

```python
left_arm = ArmController(robot_model='vx300s', robot_name='follower_left')
right_arm = ArmController(robot_model='vx300s', robot_name='follower_right')

left_arm.initialize()
right_arm.initialize()

# Use both arms independently
left_arm.move_to_pose('home')
right_arm.move_to_pose('home')
```

**Q: What about tests that use the global controller?**
A: Update tests to use explicit instances and consider using `dry_run=True`:

```python
import pytest
from arm_controller import ArmController

@pytest.fixture
def controller():
    ctrl = ArmController(robot_model='vx300s', robot_name='follower_left', dry_run=True)
    ctrl.initialize()
    yield ctrl
    ctrl.shutdown()

def test_movement(controller):
    result = controller.move_to_pose('home')
    assert result['success'] is True
```
