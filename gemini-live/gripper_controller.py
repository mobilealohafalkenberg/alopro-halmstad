#!/usr/bin/env python3

"""
Gripper Controller API for Mobile ALOHA
Designed to be called from external scripts (e.g., Gemini Live API integration)
"""

import time
import threading
from enum import Enum
from typing import Dict, Optional, Tuple, Union
import warnings

# Try to import robot dependencies, but allow dry-run mode without them
try:
    from aloha.robot_utils import move_arms, move_grippers, torque_on
    from aloha.constants import (
        FOLLOWER_GRIPPER_JOINT_OPEN,
        FOLLOWER_GRIPPER_JOINT_CLOSE,
        START_ARM_POSE
    )
    from interbotix_common_modules.common_robot.robot import (
        create_interbotix_global_node,
        robot_shutdown,
        robot_startup,
    )
    from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
    ROBOT_DEPS_AVAILABLE = True
except ImportError:
    # Mock constants for dry-run mode when robot dependencies are not available
    FOLLOWER_GRIPPER_JOINT_OPEN = 1.4
    FOLLOWER_GRIPPER_JOINT_CLOSE = -0.37
    START_ARM_POSE = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0, 0.0]  # 7 elements for full pose
    ROBOT_DEPS_AVAILABLE = False
    print("Robot dependencies not available - only dry-run mode supported")


class GripperState(Enum):
    """Gripper states for easy status checking"""
    OPEN = "open"
    CLOSED = "closed"
    OPENING = "opening"
    CLOSING = "closing"
    UNKNOWN = "unknown"


class GripperController:
    """
    Main API class for controlling the Mobile ALOHA gripper.

    Features:
    - Thread-safe gripper control with position monitoring
    - Current-based position control (300mA limit)
    - State tracking (open/closed/opening/closing/unknown)
    - Dry-run mode for hardware-independent testing (Task 2.9)

    Usage:
        # Normal hardware mode
        controller = GripperController()
        controller.initialize()
        controller.open_gripper()
        state = controller.get_gripper_state()
        controller.close_gripper()
        controller.shutdown()

        # Dry-run mode (no hardware required)
        controller = GripperController(dry_run=True)
        controller.initialize()  # Skips hardware setup
        result = controller.open_gripper()  # Returns mock response
        print(result["state"])  # "dry_run"
    """
    
    def __init__(self, robot_model='vx300s', robot_name='follower_left', dry_run=False):
        """Initialize controller (does not connect to robot yet)

        Args:
            robot_model: Robot model type (default: 'vx300s')
            robot_name: Robot name (default: 'follower_left')
            dry_run: If True, validate but don't execute movements or hardware initialization
        """
        self.robot_model = robot_model
        self.robot_name = robot_name
        self.bot = None
        self.node = None
        self.initialized = False
        self.current_state = GripperState.UNKNOWN
        self.gripper_position = 0.0
        self.state_lock = threading.Lock()
        self.dry_run = dry_run

        # Gripper position thresholds
        self.OPEN_THRESHOLD = FOLLOWER_GRIPPER_JOINT_OPEN - 0.1
        self.CLOSE_THRESHOLD = FOLLOWER_GRIPPER_JOINT_CLOSE + 0.1

    def _validate_blocking_parameter(self, blocking) -> bool:
        """
        Validate the blocking parameter.

        Args:
            blocking: Parameter to validate

        Returns:
            bool: Validated blocking value

        Raises:
            TypeError: If blocking is not a boolean
        """
        if not isinstance(blocking, bool):
            raise TypeError(
                f"Parameter 'blocking' must be a boolean, got {type(blocking).__name__}: {blocking}. "
                "Use True to wait for movement completion, False for non-blocking operation."
            )
        return blocking

    def _validate_position_parameter(self, position) -> float:
        """
        Validate and convert position parameter.

        Args:
            position: Position value to validate

        Returns:
            float: Validated position value

        Raises:
            TypeError: If position is not numeric
            ValueError: If position is invalid (NaN, infinity)
        """
        # Type validation - exclude bool even though bool is a subclass of int
        if isinstance(position, bool) or not isinstance(position, (int, float)):
            raise TypeError(
                f"Parameter 'position' must be numeric (int or float), got {type(position).__name__}: {position}. "
                "Valid range: 0.0-1.0 (normalized) or -0.37 to 1.4 radians (absolute)."
            )

        # Convert to float
        position = float(position)

        # Check for invalid values
        if not (position == position):  # NaN check
            raise ValueError(
                "Parameter 'position' cannot be NaN. "
                "Valid range: 0.0-1.0 (normalized) or -0.37 to 1.4 radians (absolute)."
            )

        if position == float('inf') or position == float('-inf'):
            raise ValueError(
                "Parameter 'position' cannot be infinity. "
                "Valid range: 0.0-1.0 (normalized) or -0.37 to 1.4 radians (absolute)."
            )

        return position

    def _validate_and_convert_position(self, position: Union[int, float]) -> Tuple[float, bool]:
        """
        Validate, convert and clamp position to valid range with warnings.

        Args:
            position: Position value (normalized 0-1 or absolute radians)

        Returns:
            Tuple[float, bool]: (validated_position, was_clamped)
        """
        # Basic validation first
        position = self._validate_position_parameter(position)

        was_clamped = False
        original_position = position

        # If position is between 0 and 1, treat as normalized
        if 0.0 <= position <= 1.0:
            # Convert normalized to actual position
            pos_range = FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE
            actual_position = FOLLOWER_GRIPPER_JOINT_CLOSE + (position * pos_range)
        else:
            actual_position = position

        # Clamp to valid range and warn if needed
        if actual_position < FOLLOWER_GRIPPER_JOINT_CLOSE:
            print(f"[GripperController] WARNING: Position {original_position:.3f} below minimum. "
                  f"Clamping to {FOLLOWER_GRIPPER_JOINT_CLOSE:.3f} (closed position).")
            actual_position = FOLLOWER_GRIPPER_JOINT_CLOSE
            was_clamped = True
        elif actual_position > FOLLOWER_GRIPPER_JOINT_OPEN:
            print(f"[GripperController] WARNING: Position {original_position:.3f} above maximum. "
                  f"Clamping to {FOLLOWER_GRIPPER_JOINT_OPEN:.3f} (open position).")
            actual_position = FOLLOWER_GRIPPER_JOINT_OPEN
            was_clamped = True

        return actual_position, was_clamped
        
    def initialize(self) -> bool:
        """
        Initialize robot connection and move to starting position.
        Returns True if successful, False otherwise.
        """
        if self.dry_run:
            print("[GripperController] DRY RUN: Skipping hardware initialization")
            self.initialized = True
            self.current_state = GripperState.CLOSED
            self.gripper_position = FOLLOWER_GRIPPER_JOINT_CLOSE
            print("[GripperController] ✓ Dry run initialization complete")
            return True

        if not ROBOT_DEPS_AVAILABLE:
            print("[GripperController] ✗ Robot dependencies not available")
            print("Use dry_run=True for hardware-independent testing")
            return False

        try:
            print("[GripperController] Initializing robot connection...")

            # Create ROS node
            self.node = create_interbotix_global_node('gripper_controller')

            # Create robot interface
            self.bot = InterbotixManipulatorXS(
                robot_model=self.robot_model,
                robot_name=self.robot_name,
                node=self.node,
                iterative_update_fk=False,
            )

            # Start ROS
            robot_startup(self.node)

            # Configure motors
            print("[GripperController] Configuring motors...")
            self.bot.core.robot_reboot_motors('single', 'gripper', True)
            self.bot.core.robot_set_operating_modes('group', 'arm', 'position')
            self.bot.core.robot_set_operating_modes('single', 'gripper', 'current_based_position')
            self.bot.core.robot_set_motor_registers('single', 'gripper', 'current_limit', 300)

            # Enable torque
            torque_on(self.bot)

            # Move to starting position
            print("[GripperController] Moving to starting position...")
            start_arm_qpos = START_ARM_POSE[:6]
            move_arms([self.bot], [start_arm_qpos], moving_time=4.0)
            move_grippers([self.bot], [FOLLOWER_GRIPPER_JOINT_CLOSE], moving_time=0.5)

            self.initialized = True
            self.current_state = GripperState.CLOSED

            # Start position monitoring thread
            self._start_position_monitor()

            print("[GripperController] ✓ Initialization complete")
            return True

        except Exception as e:
            print(f"[GripperController] ✗ Initialization failed: {e}")
            return False
    
    def _start_position_monitor(self):
        """Start background thread to monitor gripper position"""
        def monitor():
            while self.initialized:
                try:
                    # Get current gripper position
                    with self.bot.core.js_mutex:
                        gripper_index = self.bot.gripper.left_finger_index
                        self.gripper_position = self.bot.core.joint_states.position[gripper_index]
                    
                    # Update state based on position
                    with self.state_lock:
                        if self.current_state in [GripperState.OPENING, GripperState.CLOSING]:
                            # Check if movement completed
                            if self.gripper_position >= self.OPEN_THRESHOLD:
                                if self.current_state == GripperState.OPENING:
                                    self.current_state = GripperState.OPEN
                            elif self.gripper_position <= self.CLOSE_THRESHOLD:
                                if self.current_state == GripperState.CLOSING:
                                    self.current_state = GripperState.CLOSED
                    
                except Exception:
                    pass  # Silently ignore errors in monitor thread
                
                time.sleep(0.1)  # Check 10 times per second
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def open_gripper(self, blocking: bool = True) -> Dict:
        """
        Open the gripper.

        Args:
            blocking: If True, wait for movement to complete

        Returns:
            Dictionary with status and gripper position

        Raises:
            TypeError: If blocking is not a boolean
        """
        # Parameter validation (Task 2.10)
        try:
            blocking = self._validate_blocking_parameter(blocking)
        except (TypeError, ValueError) as e:
            return {"success": False, "error": f"Parameter validation failed: {str(e)}", "state": "unknown"}

        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}

        with self.state_lock:
            self.current_state = GripperState.OPENING

        if self.dry_run:
            print("[GripperController] DRY RUN: Would open gripper")
            if blocking:
                time.sleep(0.1)  # Brief delay to simulate movement
                with self.state_lock:
                    self.current_state = GripperState.OPEN
                    self.gripper_position = FOLLOWER_GRIPPER_JOINT_OPEN

            gripper_state = self.get_gripper_state()
            gripper_state.update({
                "state": "dry_run",
                "message": "Dry run - gripper opening validated but not executed"
            })
            return gripper_state

        print("[GripperController] Opening gripper...")
        move_grippers([self.bot], [FOLLOWER_GRIPPER_JOINT_OPEN], moving_time=1.0)

        if blocking:
            time.sleep(1.0)
            with self.state_lock:
                self.current_state = GripperState.OPEN

        return self.get_gripper_state()
    
    def close_gripper(self, blocking: bool = True) -> Dict:
        """
        Close the gripper.

        Args:
            blocking: If True, wait for movement to complete

        Returns:
            Dictionary with status and gripper position

        Raises:
            TypeError: If blocking is not a boolean
        """
        # Parameter validation (Task 2.10)
        try:
            blocking = self._validate_blocking_parameter(blocking)
        except (TypeError, ValueError) as e:
            return {"success": False, "error": f"Parameter validation failed: {str(e)}", "state": "unknown"}

        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}

        with self.state_lock:
            self.current_state = GripperState.CLOSING

        if self.dry_run:
            print("[GripperController] DRY RUN: Would close gripper")
            if blocking:
                time.sleep(0.1)  # Brief delay to simulate movement
                with self.state_lock:
                    self.current_state = GripperState.CLOSED
                    self.gripper_position = FOLLOWER_GRIPPER_JOINT_CLOSE

            gripper_state = self.get_gripper_state()
            gripper_state.update({
                "state": "dry_run",
                "message": "Dry run - gripper closing validated but not executed"
            })
            return gripper_state

        print("[GripperController] Closing gripper...")
        move_grippers([self.bot], [FOLLOWER_GRIPPER_JOINT_CLOSE], moving_time=1.0)

        if blocking:
            time.sleep(1.0)
            with self.state_lock:
                self.current_state = GripperState.CLOSED

        return self.get_gripper_state()
    
    def get_gripper_state(self) -> Dict:
        """
        Get current gripper state and position.
        
        Returns:
            Dictionary containing:
            - success: bool
            - state: current state (open/closed/opening/closing/unknown)
            - position: current position in radians
            - position_normalized: 0.0 (closed) to 1.0 (open)
        """
        if not self.initialized:
            return {
                "success": False,
                "error": "Not initialized",
                "state": GripperState.UNKNOWN.value,
                "position": 0.0,
                "position_normalized": 0.0
            }
        
        with self.state_lock:
            # Normalize position from 0 (closed) to 1 (open)
            pos_range = FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE
            pos_normalized = (self.gripper_position - FOLLOWER_GRIPPER_JOINT_CLOSE) / pos_range
            pos_normalized = max(0.0, min(1.0, pos_normalized))  # Clamp to [0, 1]
            
            return {
                "success": True,
                "state": self.current_state.value,
                "position": self.gripper_position,
                "position_normalized": pos_normalized,
                "position_open": FOLLOWER_GRIPPER_JOINT_OPEN,
                "position_closed": FOLLOWER_GRIPPER_JOINT_CLOSE
            }
    
    def set_gripper_position(self, position: Union[int, float], blocking: bool = True) -> Dict:
        """
        Set gripper to a specific position.

        Args:
            position: Position in radians or normalized (0.0 to 1.0)
            blocking: If True, wait for movement to complete

        Returns:
            Dictionary with status and gripper position

        Raises:
            TypeError: If position is not numeric or blocking is not a boolean
            ValueError: If position is NaN or infinity
        """
        # Parameter validation (Task 2.10) - validate position first for consistent error reporting
        try:
            actual_position, was_clamped = self._validate_and_convert_position(position)
            blocking = self._validate_blocking_parameter(blocking)
        except (TypeError, ValueError) as e:
            return {"success": False, "error": f"Parameter validation failed: {str(e)}", "state": "unknown"}

        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}

        if self.dry_run:
            print(f"[GripperController] DRY RUN: Would set gripper to position: {actual_position:.3f}")
            if blocking:
                time.sleep(0.1)  # Brief delay to simulate movement
                with self.state_lock:
                    self.gripper_position = actual_position
                    # Update state based on position
                    if actual_position >= self.OPEN_THRESHOLD:
                        self.current_state = GripperState.OPEN
                    elif actual_position <= self.CLOSE_THRESHOLD:
                        self.current_state = GripperState.CLOSED
                    else:
                        self.current_state = GripperState.UNKNOWN

            gripper_state = self.get_gripper_state()
            message = f"Dry run - gripper position {actual_position:.3f} validated but not executed"
            if was_clamped:
                message += " (value was clamped to valid range)"
            gripper_state.update({
                "state": "dry_run",
                "message": message,
                "clamped": was_clamped
            })
            return gripper_state

        print(f"[GripperController] Setting gripper to position: {actual_position:.3f}")
        move_grippers([self.bot], [actual_position], moving_time=1.0)

        if blocking:
            time.sleep(1.0)

        result = self.get_gripper_state()
        if was_clamped:
            result["clamped"] = True
            result["message"] = f"Position set to {actual_position:.3f} (value was clamped to valid range)"
        return result
    
    def sleep_arm(self) -> bool:
        """
        Move arm to sleep position.

        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            print("[GripperController] Cannot sleep - not initialized")
            return False

        if self.dry_run:
            print("[GripperController] DRY RUN: Would move arm to sleep position")
            time.sleep(0.1)  # Brief delay to simulate movement
            print("[GripperController] ✓ Dry run - arm sleep position validated")
            return True

        try:
            print("[GripperController] Moving arm to sleep position...")

            # Home position first
            home_position = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
            move_arms([self.bot], [home_position], moving_time=3.0)

            # Sleep position with wrist pointing up
            sleep_positions = [0.0, -1.85, 1.55, 0.0, -1.57, 0.0]
            move_arms([self.bot], [sleep_positions], moving_time=3.0)

            print("[GripperController] ✓ Arm in sleep position")
            return True

        except Exception as e:
            print(f"[GripperController] ✗ Sleep failed: {e}")
            return False
    
    def shutdown(self):
        """
        Shutdown robot connection and cleanup.
        """
        if self.dry_run:
            print("[GripperController] DRY RUN: Would shutdown robot connection")
            self.initialized = False
            print("[GripperController] ✓ Dry run shutdown complete")
            return

        print("[GripperController] Shutting down...")
        self.initialized = False

        if self.node:
            robot_shutdown(self.node)

        print("[GripperController] ✓ Shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.initialized:
            self.shutdown()


# Convenience functions for simple usage
_global_controller = None

def get_controller() -> GripperController:
    """Get or create global controller instance"""
    global _global_controller
    if _global_controller is None:
        _global_controller = GripperController()
        _global_controller.initialize()
    return _global_controller

def open_gripper() -> Dict:
    """Simple function to open gripper"""
    return get_controller().open_gripper()

def close_gripper() -> Dict:
    """Simple function to close gripper"""
    return get_controller().close_gripper()

def get_gripper_state() -> Dict:
    """Simple function to get gripper state"""
    return get_controller().get_gripper_state()

def cleanup():
    """Cleanup global controller"""
    global _global_controller
    if _global_controller:
        _global_controller.shutdown()
        _global_controller = None