# Migration Guide: Gripper Controller Singleton Removal

## Overview

The global singleton pattern for `GripperController` has been deprecated and will be removed in a future version. This guide helps you migrate to the recommended explicit instance management pattern.

## Why This Change?

The singleton pattern has several drawbacks:
- **Testability**: Hard to test multiple scenarios in isolation
- **Resource Management**: Unclear ownership and lifecycle
- **Flexibility**: Cannot easily manage multiple controllers
- **State Sharing**: Hidden global state leads to unexpected behavior

## What's Being Deprecated?

The following module-level convenience functions are deprecated:

- `get_controller()` - Returns global singleton instance
- `open_gripper()` - Opens gripper using global instance
- `close_gripper()` - Closes gripper using global instance
- `get_gripper_state()` - Gets state from global instance
- `cleanup()` - Cleans up global instance

## Migration Steps

### Before (Deprecated Pattern)

```python
from gripper_controller import open_gripper, close_gripper, get_gripper_state, cleanup

# Use global singleton functions
open_gripper()
state = get_gripper_state()
close_gripper()
cleanup()
```

### After (Recommended Pattern)

```python
from gripper_controller import GripperController

# Create explicit controller instance
controller = GripperController(robot_model='vx300s', robot_name='follower_left')

# Initialize connection
if not controller.initialize():
    print("Failed to initialize gripper controller")
    exit(1)

# Use instance methods
controller.open_gripper()
state = controller.get_gripper_state()
controller.close_gripper()

# Explicit cleanup
controller.shutdown()
```

## Common Migration Patterns

### Pattern 1: Simple Script

**Before:**
```python
from gripper_controller import open_gripper, close_gripper

def main():
    open_gripper()
    # Do something
    close_gripper()

if __name__ == "__main__":
    main()
```

**After:**
```python
from gripper_controller import GripperController

def main():
    controller = GripperController(robot_model='vx300s', robot_name='follower_left')

    if not controller.initialize():
        print("Failed to initialize")
        return

    try:
        controller.open_gripper()
        # Do something
        controller.close_gripper()
    finally:
        controller.shutdown()

if __name__ == "__main__":
    main()
```

### Pattern 2: Class-Based Usage

**Before:**
```python
from gripper_controller import get_controller

class RobotTask:
    def execute(self):
        gripper = get_controller()
        gripper.open_gripper()
```

**After:**
```python
from gripper_controller import GripperController

class RobotTask:
    def __init__(self):
        self.gripper = GripperController(robot_model='vx300s', robot_name='follower_left')
        self.gripper.initialize()

    def execute(self):
        self.gripper.open_gripper()

    def cleanup(self):
        self.gripper.shutdown()
```

### Pattern 3: Integration with Arm Controller

**Before:**
```python
from gripper_controller import open_gripper, close_gripper
from arm_controller import move_arm

move_arm(position=[0.3, 0.0, 0.2])
close_gripper()
```

**After:**
```python
from gripper_controller import GripperController
from arm_controller import ArmController

# Create instances
arm = ArmController(robot_model='vx300s', robot_name='follower_left')
gripper = GripperController(robot_model='vx300s', robot_name='follower_left')

# Initialize both
arm.initialize()
gripper.initialize()

# Use explicit instances
arm.move_to_position([0.3, 0.0, 0.2])
gripper.close_gripper()

# Clean up both
arm.shutdown()
gripper.shutdown()
```

### Pattern 4: Shared Robot Interface (Advanced)

If you need to share the robot interface between arm and gripper controllers:

```python
from interbotix_common_modules.common_robot.robot import create_interbotix_global_node
from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
from arm_controller import ArmController
from gripper_controller import GripperController

# Create shared resources
node = create_interbotix_global_node('robot_controller')
bot = InterbotixManipulatorXS(
    robot_model='vx300s',
    robot_name='follower_left',
    node=node
)

# Pass shared resources to controllers
arm = ArmController(robot_model='vx300s', robot_name='follower_left', node=node, bot=bot)
gripper = GripperController(robot_model='vx300s', robot_name='follower_left')

# Manually set bot for gripper (if needed)
gripper.bot = bot
gripper.node = node

# Initialize
arm.initialize()
gripper.initialize()
```

## Handling Deprecation Warnings

When you use deprecated functions, Python will emit warnings:

```
DeprecationWarning: get_controller() is deprecated and will be removed in a future version.
```

### Options for Handling Warnings:

1. **Fix immediately** (recommended): Migrate to new pattern
2. **Suppress temporarily** (during transition):
   ```python
   import warnings
   warnings.filterwarnings("ignore", category=DeprecationWarning, module="gripper_controller")
   ```

## Testing Your Migration

### Unit Tests

**Before:**
```python
def test_gripper():
    from gripper_controller import open_gripper
    result = open_gripper()
    assert result['success']
```

**After:**
```python
def test_gripper():
    from gripper_controller import GripperController
    controller = GripperController()
    controller.initialize()

    try:
        result = controller.open_gripper()
        assert result['success']
    finally:
        controller.shutdown()
```

### Mock Testing

**After (with mocking):**
```python
from unittest.mock import Mock, patch

def test_gripper_with_mock():
    mock_bot = Mock()
    controller = GripperController()
    controller.bot = mock_bot
    controller.initialized = True

    controller.open_gripper()
    mock_bot.gripper.move.assert_called()
```

## Timeline

- **Now**: Deprecation warnings added, old pattern still works
- **Future version**: Singleton functions will be removed entirely

## Getting Help

If you encounter issues during migration:

1. Check this guide for common patterns
2. Review the updated class docstring in `gripper_controller.py`
3. Look at example usage in test files
4. Check CHANGELOG.md for Task 2.8 details

## Benefits After Migration

- **Better testability**: Easy to mock and test in isolation
- **Clearer ownership**: Explicit instance lifecycle
- **More flexible**: Can create multiple controllers if needed
- **Consistent with arm_controller**: Same pattern across both controllers
- **Better resource management**: Explicit initialization and cleanup
