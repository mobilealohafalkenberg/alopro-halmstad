#!/usr/bin/env python3

"""
Gripper Controller API for Mobile ALOHA
Designed to be called from external scripts (e.g., Gemini Live API integration)
"""

import time
import threading
from enum import Enum
from typing import Dict, Optional, Tuple

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
    
    def __init__(self, robot_model='vx300s', robot_name='follower_left'):
        """Initialize controller (does not connect to robot yet)"""
        self.robot_model = robot_model
        self.robot_name = robot_name
        self.bot = None
        self.node = None
        self.initialized = False
        self.current_state = GripperState.UNKNOWN
        self.gripper_position = 0.0
        self.state_lock = threading.Lock()
        
        # Gripper position thresholds
        self.OPEN_THRESHOLD = FOLLOWER_GRIPPER_JOINT_OPEN - 0.1
        self.CLOSE_THRESHOLD = FOLLOWER_GRIPPER_JOINT_CLOSE + 0.1
        
    def initialize(self) -> bool:
        """
        Initialize robot connection and move to starting position.
        Returns True if successful, False otherwise.
        """
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
                    # Get current gripper position from hardware
                    with self.bot.core.js_mutex:
                        gripper_index = self.bot.gripper.left_finger_index
                        position = self.bot.core.joint_states.position[gripper_index]

                    # Update shared state with lock protection
                    with self.state_lock:
                        self.gripper_position = position

                        # Update state based on position
                        if self.current_state in [GripperState.OPENING, GripperState.CLOSING]:
                            # Check if movement completed
                            if position >= self.OPEN_THRESHOLD:
                                if self.current_state == GripperState.OPENING:
                                    self.current_state = GripperState.OPEN
                            elif position <= self.CLOSE_THRESHOLD:
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
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}
        
        with self.state_lock:
            self.current_state = GripperState.OPENING
        
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
        """
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}
        
        with self.state_lock:
            self.current_state = GripperState.CLOSING
        
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
            # Capture position while holding lock to prevent race condition
            position = self.gripper_position
            state = self.current_state.value

            # Normalize position from 0 (closed) to 1 (open)
            pos_range = FOLLOWER_GRIPPER_JOINT_OPEN - FOLLOWER_GRIPPER_JOINT_CLOSE
            pos_normalized = (position - FOLLOWER_GRIPPER_JOINT_CLOSE) / pos_range
            pos_normalized = max(0.0, min(1.0, pos_normalized))  # Clamp to [0, 1]

            return {
                "success": True,
                "state": state,
                "position": position,
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