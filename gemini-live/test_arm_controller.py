#!/usr/bin/env python3

"""
Test script for the ArmController with various input formats.
Tests automatic unit detection and coordinate conversions.
"""

import time
import sys
from arm_controller import ArmController

def test_arm_controller():
    """Test arm controller with different input formats"""
    
    print("=" * 60)
    print("ARM CONTROLLER TEST SUITE")
    print("=" * 60)
    print()
    
    # Initialize controller
    print("Initializing arm controller...")
    controller = ArmController()
    
    try:
        success = controller.initialize()
        if not success:
            print("✗ Failed to initialize controller")
            print("Make sure the robot is powered on and connected")
            return
        
        print("✓ Controller initialized successfully")
        print()
        
        # Test 1: Named poses
        print("-" * 40)
        print("TEST 1: Named Poses")
        print("-" * 40)
        
        poses = ['home', 'ready', 'sleep', 'ready']
        for pose in poses:
            print(f"\nMoving to {pose} pose...")
            result = controller.move_to_pose(pose, moving_time=3.0)
            print(f"Result: {result['state']}")
            if result['success']:
                print(f"✓ Successfully moved to {pose}")
            else:
                print(f"✗ Failed: {result.get('error', 'unknown error')}")
            time.sleep(2)
        
        # Test 2: Joint control with auto-detection
        print("\n" + "-" * 40)
        print("TEST 2: Joint Control (Auto-Detection)")
        print("-" * 40)
        
        # Test with radians (small values)
        print("\nTesting with radians (auto-detect)...")
        joints_rad = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
        print(f"Input: {joints_rad}")
        result = controller.move_joints(joints_rad, unit='auto', moving_time=2.0)
        print(f"Result: {result['state']}")
        print(f"Detected as: radians (values < 2π)")
        time.sleep(2)
        
        # Test with degrees (large values)
        print("\nTesting with degrees (auto-detect)...")
        joints_deg = [0, -55, 66, 0, -17, 0]
        print(f"Input: {joints_deg}")
        result = controller.move_joints(joints_deg, unit='auto', moving_time=2.0)
        print(f"Result: {result['state']}")
        print(f"Detected as: degrees (values > 2π)")
        time.sleep(2)
        
        # Test with explicit units
        print("\nTesting with explicit degrees...")
        joints_deg = [0, -30, 45, 0, -10, 0]
        print(f"Input: {joints_deg} degrees")
        result = controller.move_joints(joints_deg, unit='degrees', moving_time=2.0)
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        # Test 3: Cartesian control
        print("\n" + "-" * 40)
        print("TEST 3: Cartesian Position Control")
        print("-" * 40)
        
        # Standard [x, y, z] format
        print("\nMoving to Cartesian position [x, y, z]...")
        position = [0.3, 0.0, 0.2]
        print(f"Target: x={position[0]}, y={position[1]}, z={position[2]}")
        result = controller.move_to_position(position, moving_time=3.0)
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        # Dictionary format
        print("\nMoving with dictionary format...")
        position = {'x': 0.25, 'y': 0.1, 'z': 0.25}
        print(f"Target: {position}")
        result = controller.move_to_position(position, moving_time=3.0)
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        # [y, x] format (Gemini trajectory style) - normalized
        print("\nTesting [y, x] normalized format (0-1000)...")
        position = [100, 300]  # y=100/1000, x=300/1000
        print(f"Input: {position} (normalized)")
        result = controller.move_to_position(position, format='auto', moving_time=3.0)
        print(f"Converted to: x=0.3, y=0.1")
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        # Test 4: Speed control
        print("\n" + "-" * 40)
        print("TEST 4: Speed Control")
        print("-" * 40)
        
        print("\nSlow movement (5 seconds)...")
        controller.set_speed(5.0, 0.5)
        result = controller.move_to_pose('home', moving_time=5.0)
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        print("\nFast movement (1 second)...")
        controller.set_speed(1.0, 0.2)
        result = controller.move_to_pose('ready', moving_time=1.0)
        print(f"Result: {result['state']}")
        time.sleep(2)
        
        # Test 5: State reporting
        print("\n" + "-" * 40)
        print("TEST 5: State Reporting")
        print("-" * 40)
        
        state = controller.get_arm_state()
        print(f"\nCurrent arm state:")
        print(f"  State: {state['state']}")
        print(f"  Pose: {state.get('pose', 'custom')}")
        print(f"  Joints (rad): {[f'{j:.3f}' for j in state['joints']]}")
        print(f"  Joints (deg): {[f'{j:.1f}' for j in state['joints_degrees']]}")
        if state.get('ee_position'):
            print(f"  EE Position: x={state['ee_position']['x']:.3f}, "
                  f"y={state['ee_position']['y']:.3f}, z={state['ee_position']['z']:.3f}")
        
        # Test 6: Error handling
        print("\n" + "-" * 40)
        print("TEST 6: Error Handling")
        print("-" * 40)
        
        print("\nTesting invalid joint count...")
        result = controller.move_joints([0, 0, 0], unit='radians')
        print(f"Result: {result['success']} - {result.get('error', 'no error')}")
        
        print("\nTesting out-of-range position...")
        result = controller.move_to_position([5.0, 5.0, 5.0])  # Way outside workspace
        print(f"Result: Will clamp to workspace limits")
        
        print("\nTesting invalid pose name...")
        result = controller.move_to_pose('invalid_pose')
        print(f"Result: {result['success']} - {result.get('error', 'no error')}")
        
        # Return to ready position
        print("\n" + "-" * 40)
        print("Returning to ready position...")
        controller.move_to_pose('ready', moving_time=3.0)
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("\nShutting down controller...")
        controller.shutdown()
        print("✓ Controller shutdown complete")

if __name__ == '__main__':
    # Check if running in correct environment
    try:
        import rclpy
        from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
    except ImportError:
        print("ERROR: ROS2 packages not found!")
        print("Please run:")
        print("  source /opt/ros/humble/setup.bash")
        print("  source ~/interbotix_ws/install/setup.bash")
        sys.exit(1)
    
    test_arm_controller()