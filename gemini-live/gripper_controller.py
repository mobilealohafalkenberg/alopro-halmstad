#!/usr/bin/env python3

"""
Gripper Controller API for Mobile ALOHA
Designed to be called from external scripts (e.g., Gemini Live API integration)
"""

import time
import threading
import warnings
from enum import Enum
from typing import Dict, Optional, Tuple
import logging

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
    
    Usage:
        controller = GripperController()
        controller.initialize()
        controller.open_gripper()
        state = controller.get_gripper_state()
        controller.close_gripper()
        controller.shutdown()
    """
    
    def __init__(self, robot_model='vx300s', robot_name='follower_left', dry_run=False):
        """Initialize controller (does not connect to robot yet)"""
        self.robot_model = robot_model
        self.robot_name = robot_name
        self.dry_run = dry_run
        self.bot = None
        self.node = None
        self.initialized = False
        self.current_state = GripperState.UNKNOWN
        self.gripper_position = 0.0
        self.state_lock = threading.Lock()
        self.monitor_failure_count = 0
        
        # Gripper position thresholds
        self.OPEN_THRESHOLD = FOLLOWER_GRIPPER_JOINT_OPEN - 0.1
        self.CLOSE_THRESHOLD = FOLLOWER_GRIPPER_JOINT_CLOSE + 0.1
        
    def initialize(self) -> bool:
        """
        Initialize robot connection and move to starting position.
        Returns True if successful, False otherwise.
        """
        # Dry-run mode: Skip hardware initialization
        if self.dry_run:
            print("[GripperController] 🔧 DRY-RUN MODE: Skipping hardware initialization")
            self.initialized = True
            self.current_state = GripperState.CLOSED
            self.gripper_position = FOLLOWER_GRIPPER_JOINT_CLOSE
            print("[GripperController] ✓ Dry-run initialization complete")
            return True

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
        # Dry-run mode: Skip monitoring thread (position is set manually)
        if self.dry_run:
            print("[GripperController] 🔧 DRY-RUN: Skipping position monitor thread")
            return

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
                    # Reset failure counter on success
                    self.monitor_failure_count=0
                except Exception as e:
                    self.monitor_failure_count+=1
                    logging.error(
                        f"Gripper position monitor failed (failure #{self.monitor_failure_count}):"
                        f"{type(e).__name__}: {e}",
                        exc_info=True
                    )
                    #Alert if failures are excessive
                    if self.monitor_failure_count>=5:
                        logging.critical(
                            f"Gripper monitor has failed {self.monitor_failure_count} consecutive times!"
                            "This may indicate a serious hardware or connection issue. "
                        )
                
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
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}
        
        with self.state_lock:
            self.current_state = GripperState.OPENING

        print("[GripperController] Opening gripper...")

        # Dry-run mode: Simulate movement
        if self.dry_run:
            if blocking:
                time.sleep(0.1)  # Simulate brief movement
                with self.state_lock:
                    self.gripper_position = FOLLOWER_GRIPPER_JOINT_OPEN
                    self.current_state = GripperState.OPEN
            print("[GripperController] 🔧 DRY-RUN: Simulated gripper open")
        else:
            # Hardware mode: Execute real movement
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
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}
        
        with self.state_lock:
            self.current_state = GripperState.CLOSING

        print("[GripperController] Closing gripper...")

        # Dry-run mode: Simulate movement
        if self.dry_run:
            if blocking:
                time.sleep(0.1)  # Simulate brief movement
                with self.state_lock:
                    self.gripper_position = FOLLOWER_GRIPPER_JOINT_CLOSE
                    self.current_state = GripperState.CLOSED
            print("[GripperController] 🔧 DRY-RUN: Simulated gripper close")
        else:
            # Hardware mode: Execute real movement
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
    
    def set_gripper_position(self, position: float, blocking: bool = True) -> Dict:
        """
        Set gripper to a specific position.
        
        Args:
            position: Position in radians or normalized (0.0 to 1.0)
            blocking: If True, wait for movement to complete
            
        Returns:
            Dictionary with status and gripper position
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}
        
        # If position is between 0 and 1, treat as normalized
        if 0.0 <= position <= 1.0:
            # Convert normalized to actual position
            pos_range = FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE
            actual_position = FOLLOWER_GRIPPER_JOINT_CLOSE + (position * pos_range)
        else:
            actual_position = position
        
        # Clamp to valid range
        actual_position = max(FOLLOWER_GRIPPER_JOINT_CLOSE,
                             min(FOLLOWER_GRIPPER_JOINT_OPEN, actual_position))

        print(f"[GripperController] Setting gripper to position: {actual_position:.3f}")

        # Dry-run mode: Simulate movement
        if self.dry_run:
            if blocking:
                time.sleep(0.1)  # Simulate brief movement
                with self.state_lock:
                    self.gripper_position = actual_position
                    # Update state based on position
                    if actual_position >= self.OPEN_THRESHOLD:
                        self.current_state = GripperState.OPEN
                    elif actual_position <= self.CLOSE_THRESHOLD:
                        self.current_state = GripperState.CLOSED
                    else:
                        self.current_state = GripperState.UNKNOWN
            print(f"[GripperController] 🔧 DRY-RUN: Simulated gripper position {actual_position:.3f}")
        else:
            # Hardware mode: Execute real movement
            move_grippers([self.bot], [actual_position], moving_time=1.0)

            if blocking:
                time.sleep(1.0)

        return self.get_gripper_state()
    
    def sleep_arm(self) -> bool:
        """
        Move arm to sleep position.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.initialized:
            print("[GripperController] Cannot sleep - not initialized")
            return False
        
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
        print("[GripperController] Shutting down...")
        self.initialized = False

        # Dry-run mode: Skip hardware shutdown
        if self.dry_run:
            print("[GripperController] 🔧 DRY-RUN: Skipping hardware shutdown")
        elif self.node:
            robot_shutdown(self.node)

        print("[GripperController] ✓ Shutdown complete")
    
    def __del__(self):
        """Cleanup on deletion"""
        if self.initialized:
            self.shutdown()


# Convenience functions for simple usage
_global_controller = None

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
            controller = GripperController(robot_model='vx300s', robot_name='follower_left')
            controller.initialize()
    """
    warnings.warn(
        "get_controller() is deprecated and will be removed in version 2.0. "
        "Create controller instances explicitly: controller = GripperController(robot_model='vx300s', robot_name='follower_left'); controller.initialize()",
        DeprecationWarning,
        stacklevel=2
    )
    global _global_controller
    if _global_controller is None:
        _global_controller = GripperController()
        _global_controller.initialize()
    return _global_controller

def open_gripper() -> Dict:
    """
    Simple function to open gripper.

    .. deprecated:: 2.3
        This convenience function is deprecated and will be removed in version 2.0.
        Use an explicit controller instance instead:

        Example:
            # Old (deprecated):
            open_gripper()

            # New (recommended):
            controller = GripperController(robot_model='vx300s', robot_name='follower_left')
            controller.initialize()
            controller.open_gripper()
    """
    warnings.warn(
        "open_gripper() is deprecated and will be removed in version 2.0. "
        "Use controller.open_gripper() with an explicit GripperController instance.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_controller().open_gripper()

def close_gripper() -> Dict:
    """
    Simple function to close gripper.

    .. deprecated:: 2.3
        This convenience function is deprecated and will be removed in version 2.0.
        Use an explicit controller instance instead:

        Example:
            # Old (deprecated):
            close_gripper()

            # New (recommended):
            controller = GripperController(robot_model='vx300s', robot_name='follower_left')
            controller.initialize()
            controller.close_gripper()
    """
    warnings.warn(
        "close_gripper() is deprecated and will be removed in version 2.0. "
        "Use controller.close_gripper() with an explicit GripperController instance.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_controller().close_gripper()

def get_gripper_state() -> Dict:
    """
    Simple function to get gripper state.

    .. deprecated:: 2.3
        This convenience function is deprecated and will be removed in version 2.0.
        Use an explicit controller instance instead:

        Example:
            # Old (deprecated):
            state = get_gripper_state()

            # New (recommended):
            controller = GripperController(robot_model='vx300s', robot_name='follower_left')
            controller.initialize()
            state = controller.get_gripper_state()
    """
    warnings.warn(
        "get_gripper_state() is deprecated and will be removed in version 2.0. "
        "Use controller.get_gripper_state() with an explicit GripperController instance.",
        DeprecationWarning,
        stacklevel=2
    )
    return get_controller().get_gripper_state()

def cleanup():
    """
    Cleanup global controller.

    .. deprecated:: 2.3
        This cleanup function is deprecated and will be removed in version 2.0.
        Manage controller lifecycle explicitly instead:

        Example:
            # Old (deprecated):
            cleanup()

            # New (recommended):
            controller = GripperController(robot_model='vx300s', robot_name='follower_left')
            controller.initialize()
            # ... use controller ...
            controller.shutdown()
    """
    warnings.warn(
        "cleanup() is deprecated and will be removed in version 2.0. "
        "Use controller.shutdown() with an explicit GripperController instance.",
        DeprecationWarning,
        stacklevel=2
    )
    global _global_controller
    if _global_controller:
        _global_controller.shutdown()
        _global_controller = None