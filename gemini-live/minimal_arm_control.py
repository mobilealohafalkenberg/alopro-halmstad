#!/usr/bin/env python3

"""
MINIMAL arm control with proper initialization.
Includes: arm positioning, gripper control, and sleep.
"""

import time
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

def initialize_robot(bot):
    """Initialize robot with proper motor modes."""
    print("Rebooting gripper motor...")
    bot.core.robot_reboot_motors('single', 'gripper', True)
    
    print("Setting operating modes...")
    bot.core.robot_set_operating_modes('group', 'arm', 'position')
    bot.core.robot_set_operating_modes('single', 'gripper', 'current_based_position')
    bot.core.robot_set_motor_registers('single', 'gripper', 'current_limit', 300)
    
    print("Enabling torque...")
    torque_on(bot)
    
def move_to_start(bot):
    """Move arm to starting position."""
    print("Moving arm to starting position...")
    start_arm_qpos = START_ARM_POSE[:6]  # [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
    move_arms([bot], [start_arm_qpos], moving_time=4.0)
    
    print("Setting gripper to closed position...")
    move_grippers([bot], [FOLLOWER_GRIPPER_JOINT_CLOSE], moving_time=0.5)

def open_gripper(bot):
    """Open the gripper."""
    move_grippers([bot], [FOLLOWER_GRIPPER_JOINT_OPEN], moving_time=1.0)
    print("Gripper OPEN")

def close_gripper(bot):
    """Close the gripper."""
    move_grippers([bot], [FOLLOWER_GRIPPER_JOINT_CLOSE], moving_time=1.0)
    print("Gripper CLOSED")

def sleep_arm(bot):
    """Move arm to sleep position with corrected wrist angle."""
    print("Moving to home position first...")
    home_position = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
    move_arms([bot], [home_position], moving_time=3.0)
    
    print("Moving to sleep position...")
    # Corrected sleep position - wrist pointing straight up
    # [waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate]
    sleep_positions = [0.0, -1.85, 1.55, 0.0, -1.57, 0.0]  # -1.57 rad = -90 degrees (up)
    print(f"  Sleep positions: {sleep_positions}")
    print(f"  Wrist angle: -1.57 rad (-90 degrees, pointing up)")
    move_arms([bot], [sleep_positions], moving_time=3.0)
    print("Arm in SLEEP position")

def main():
    print("=" * 50)
    print("MINIMAL ARM CONTROL")
    print("=" * 50)
    
    # Create ROS node
    node = create_interbotix_global_node('minimal_arm')
    
    # Create robot interface
    bot = InterbotixManipulatorXS(
        robot_model='vx300s',
        robot_name='follower_left',
        node=node,
        iterative_update_fk=False,
    )
    
    # Start ROS
    robot_startup(node)
    
    try:
        # Initialize robot with proper modes
        print("\n1. INITIALIZING ROBOT")
        initialize_robot(bot)
        time.sleep(1)
        
        # Move to start position
        print("\n2. MOVING TO START POSITION")
        move_to_start(bot)
        time.sleep(2)
        
        # Test gripper
        print("\n3. TESTING GRIPPER")
        print("   Opening gripper...")
        open_gripper(bot)
        time.sleep(2)
        
        print("   Closing gripper...")
        close_gripper(bot)
        time.sleep(2)
        
        print("   Opening gripper again...")
        open_gripper(bot)
        time.sleep(2)
        
        # Sleep the arm
        print("\n4. SLEEPING ARM")
        sleep_arm(bot)
        
        print("\n✓ COMPLETE!")
        
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        robot_shutdown(node)
        print("Shutdown complete")

if __name__ == '__main__':
    main()