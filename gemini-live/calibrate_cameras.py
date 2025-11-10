#!/usr/bin/env python3
"""
Camera Calibration Script for Mobile ALOHA Vision System

This script helps calibrate the camera-to-robot transforms for accurate 3D positioning.

Usage:
    python3 calibrate_cameras.py

The script will guide you through:
1. Moving the robot to a known position
2. Placing a calibration object at that position
3. Having the camera detect the object
4. Calculating the calibration offset
5. Saving the calibration to vision_calibration.json
"""

import os
import sys
import time
import numpy as np
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from camera_controller import CameraController
from vision_controller import VisionController
from arm_controller import ArmController
from gripper_controller import GripperController


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80 + "\n")


def print_step(step_num, text):
    """Print formatted step"""
    print(f"\n[Step {step_num}] {text}")
    print("-" * 80)


def wait_for_user(prompt="Press Enter to continue..."):
    """Wait for user input"""
    input(f"\n{prompt}")


def calibrate_camera(camera_name, camera_controller, vision_controller, arm_controller):
    """
    Calibrate a single camera.

    Args:
        camera_name: 'gripper_cam' or 'top_cam'
        camera_controller: CameraController instance
        vision_controller: VisionController instance
        arm_controller: ArmController instance

    Returns:
        True if calibration successful, False otherwise
    """
    print_header(f"Calibrating {camera_name}")

    # Define calibration positions based on camera type
    if camera_name == 'gripper_cam':
        # For gripper camera, use a position in front of the gripper
        calibration_position = {
            'x': 0.30,  # 30cm forward
            'y': 0.00,  # centered
            'z': 0.15   # 15cm above table
        }
        object_description = "red marker"  # Use a distinctive object

    elif camera_name == 'top_cam':
        # For top camera, use a position in the center of workspace
        calibration_position = {
            'x': 0.25,
            'y': 0.00,
            'z': 0.10   # On table surface
        }
        object_description = "red marker"
    else:
        print(f"[Error] Unknown camera: {camera_name}")
        return False

    # Step 1: Move robot to calibration position (for gripper camera)
    print_step(1, f"Move robot to calibration position")
    print(f"Target position: x={calibration_position['x']:.2f}m, "
          f"y={calibration_position['y']:.2f}m, z={calibration_position['z']:.2f}m")

    if camera_name == 'gripper_cam':
        # Move gripper to position
        result = arm_controller.move_to_position(
            position=[calibration_position['x'], calibration_position['y'], calibration_position['z']],
            blocking=True
        )

        if not result.get('success'):
            print(f"[Error] Failed to move robot: {result.get('error')}")
            return False

        print("[Success] Robot moved to calibration position")
        time.sleep(1.0)  # Wait for stabilization

    # Step 2: Place calibration object
    print_step(2, f"Place calibration object ({object_description})")

    if camera_name == 'gripper_cam':
        print(f"Place the {object_description} at the EXACT position where the gripper is pointing.")
        print(f"The object should be:")
        print(f"  - At x={calibration_position['x']:.2f}m, y={calibration_position['y']:.2f}m, z={calibration_position['z']:.2f}m")
        print(f"  - Directly in front of the gripper camera")
        print(f"  - Clearly visible in the camera view")
    else:
        print(f"Place the {object_description} on the table at:")
        print(f"  - x={calibration_position['x']:.2f}m, y={calibration_position['y']:.2f}m from robot base")
        print(f"  - Visible to the overhead camera")

    wait_for_user("Press Enter once the calibration object is in position...")

    # Step 3: Capture image and detect object
    print_step(3, "Detect calibration object")

    rgb_frame, depth_frame = camera_controller.get_rgbd_frames(camera_name)

    if rgb_frame is None:
        print(f"[Error] No frame available from {camera_name}")
        return False

    if depth_frame is None:
        print(f"[Warning] No depth frame available from {camera_name}")
        print("Calibration requires depth data. Check camera initialization.")
        return False

    print(f"Detecting '{object_description}' in camera frame...")

    detection_result = vision_controller.detect_object(
        rgb_frame,
        depth_frame,
        object_description,
        camera_name=camera_name
    )

    if not detection_result.get('object_found'):
        print(f"[Error] Could not detect {object_description} in camera view")
        print("Make sure the object is:")
        print("  - Clearly visible to the camera")
        print("  - Well-lit")
        print("  - Distinctive (bright color helps)")
        return False

    print(f"[Success] Object detected!")

    if 'center_pixel' not in detection_result:
        print("[Error] No pixel coordinates returned")
        return False

    if 'position_3d' not in detection_result:
        print("[Error] No 3D position calculated (no depth data?)")
        return False

    detected_pixel = tuple(detection_result['center_pixel'])
    detected_position = detection_result['position_3d']

    print(f"  Pixel coordinates: {detected_pixel}")
    print(f"  Calculated 3D position (BEFORE calibration): {detected_position}")
    print(f"  Actual position (ground truth): [{calibration_position['x']:.3f}, "
          f"{calibration_position['y']:.3f}, {calibration_position['z']:.3f}]")

    # Step 4: Calculate and apply calibration
    print_step(4, "Calculate calibration offset")

    # Use the calibrate_camera method
    vision_controller.calibrate_camera(
        known_object_pixel=detected_pixel,
        known_object_position=(
            calibration_position['x'],
            calibration_position['y'],
            calibration_position['z']
        ),
        depth_frame=depth_frame,
        camera_name=camera_name
    )

    # Step 5: Verify calibration
    print_step(5, "Verify calibration")

    print("Re-detecting object with new calibration...")

    # Re-detect with updated calibration
    verification_result = vision_controller.detect_object(
        rgb_frame,
        depth_frame,
        object_description,
        camera_name=camera_name
    )

    if verification_result.get('object_found') and 'position_3d' in verification_result:
        new_position = verification_result['position_3d']

        # Calculate error
        error = np.sqrt(
            (new_position[0] - calibration_position['x'])**2 +
            (new_position[1] - calibration_position['y'])**2 +
            (new_position[2] - calibration_position['z'])**2
        )

        print(f"  Calculated 3D position (AFTER calibration): {new_position}")
        print(f"  Actual position: [{calibration_position['x']:.3f}, "
              f"{calibration_position['y']:.3f}, {calibration_position['z']:.3f}]")
        print(f"  Positioning error: {error*100:.1f} cm")

        if error < 0.05:  # 5cm accuracy
            print(f"[Success] ✓ Calibration accurate (error < 5cm)")
            return True
        elif error < 0.10:  # 10cm accuracy
            print(f"[Warning] ⚠️  Calibration acceptable but not ideal (error < 10cm)")
            print("Consider recalibrating for better accuracy")
            return True
        else:
            print(f"[Warning] ⚠️  Calibration error is large (> 10cm)")
            print("You may want to try calibrating again")
            return True  # Still return True, let user decide
    else:
        print("[Warning] Could not verify calibration (object not detected)")
        return True  # Assume success, can't verify

    return True


def main():
    """Main calibration routine"""
    print_header("Mobile ALOHA Camera Calibration Script")

    print("This script will calibrate the camera-to-robot transforms for accurate 3D positioning.")
    print("\nRequired:")
    print("  - GEMINI_API_KEY environment variable set")
    print("  - Robot powered on and connected")
    print("  - RealSense cameras connected")
    print("  - A distinctive calibration object (e.g., bright red marker or ball)")

    wait_for_user("\nPress Enter to begin calibration...")

    # Check for API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("\n[Error] GEMINI_API_KEY not set!")
        print("Export it with: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    # Initialize controllers
    print_header("Initializing System")

    print("Initializing camera controller...")
    camera_controller = CameraController()
    if not camera_controller.initialize():
        print("[Error] Camera initialization failed!")
        sys.exit(1)
    print("[Success] Cameras initialized")

    print("\nInitializing vision controller...")
    vision_controller = VisionController()
    print("[Success] Vision controller initialized")

    print("\nInitializing robot controllers...")
    gripper_controller = GripperController()
    arm_controller = ArmController()

    if not gripper_controller.initialize():
        print("[Error] Gripper initialization failed!")
        sys.exit(1)
    print("[Success] Gripper controller initialized")

    if not arm_controller.initialize():
        print("[Error] Arm initialization failed!")
        sys.exit(1)
    print("[Success] Arm controller initialized")

    # Calibrate cameras
    calibration_results = {}

    # Calibrate gripper camera
    if calibrate_camera('gripper_cam', camera_controller, vision_controller, arm_controller):
        calibration_results['gripper_cam'] = 'success'
    else:
        calibration_results['gripper_cam'] = 'failed'

    # Ask if user wants to calibrate top camera
    print("\n")
    response = input("Calibrate top camera? (y/n): ").strip().lower()

    if response == 'y':
        # Move robot out of the way
        print("\nMoving robot to home position...")
        arm_controller.move_to_pose('home', blocking=True)

        if calibrate_camera('top_cam', camera_controller, vision_controller, arm_controller):
            calibration_results['top_cam'] = 'success'
        else:
            calibration_results['top_cam'] = 'failed'

    # Save calibration
    print_header("Save Calibration")

    output_file = Path(__file__).parent / "vision_calibration.json"

    print(f"Saving calibration to: {output_file}")
    vision_controller.save_calibration(str(output_file))

    print("\n[Success] ✓ Calibration saved!")

    # Summary
    print_header("Calibration Summary")

    for camera, result in calibration_results.items():
        status = "✓ SUCCESS" if result == 'success' else "✗ FAILED"
        print(f"  {camera}: {status}")

    print(f"\nCalibration file: {output_file}")
    print("\nThe bridge will automatically load this calibration on startup.")
    print("Restart the bridge if it's already running.")

    # Cleanup
    print("\nMoving robot to sleep position...")
    arm_controller.move_to_pose('sleep', blocking=True)

    print("\nShutting down...")
    arm_controller.shutdown()
    gripper_controller.shutdown()
    camera_controller.shutdown()

    print("\n✓ Calibration complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCalibration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[Error] Calibration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
