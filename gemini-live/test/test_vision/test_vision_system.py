#!/usr/bin/env python3
"""
Test script for vision system with Gemini API integration.
Tests object detection and workspace analysis with real cameras.
"""

import sys
import os
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from camera_controller import CameraController
from vision_controller import VisionController


def test_camera_initialization():
    """Test camera controller initialization."""
    print("\n" + "="*60)
    print("TEST 1: Camera Initialization")
    print("="*60)

    camera_controller = CameraController()
    success = camera_controller.initialize()

    if success:
        print("✓ Camera controller initialized")

        # Get camera info
        info = camera_controller.get_camera_info()
        print(f"\nCameras found: {len(info['cameras'])}")
        for cam_name, cam_info in info['cameras'].items():
            print(f"  - {cam_name}: {'Active' if cam_info['active'] else 'Inactive'}")

        # Wait for a few frames
        print("\nWaiting for frames...")
        time.sleep(2)

        # Test frame capture
        for cam_name in info['cameras'].keys():
            rgb, depth = camera_controller.get_rgbd_frames(cam_name)
            if rgb is not None:
                print(f"✓ {cam_name}: RGB shape {rgb.shape}, Depth {'available' if depth is not None else 'unavailable'}")
            else:
                print(f"✗ {cam_name}: No frame")

        return camera_controller
    else:
        print("✗ Camera initialization failed")
        return None


def test_vision_initialization():
    """Test vision controller initialization."""
    print("\n" + "="*60)
    print("TEST 2: Vision Controller Initialization")
    print("="*60)

    # Check for API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("✗ GEMINI_API_KEY not set")
        print("  Export it with: export GEMINI_API_KEY='your-key-here'")
        return None

    try:
        vision_controller = VisionController(api_key=api_key)
        print("✓ Vision controller initialized with Gemini API")
        return vision_controller
    except Exception as e:
        print(f"✗ Vision controller initialization failed: {e}")
        return None


def test_object_detection(camera_controller, vision_controller, object_name="apple"):
    """Test object detection."""
    print("\n" + "="*60)
    print(f"TEST 3: Object Detection - '{object_name}'")
    print("="*60)

    if not camera_controller or not vision_controller:
        print("✗ Skipping (missing controllers)")
        return

    # Get frame from gripper camera
    print("Capturing frame from gripper camera...")
    rgb_frame, depth_frame = camera_controller.get_rgbd_frames('gripper_cam')

    if rgb_frame is None:
        print("✗ No frame available")
        return

    print(f"✓ Frame captured: {rgb_frame.shape}")
    if depth_frame is not None:
        print(f"✓ Depth data available: {depth_frame.shape}")
    else:
        print("⚠️  No depth data")

    # Run detection
    print(f"\nDetecting '{object_name}' using Gemini API...")
    start_time = time.time()

    result = vision_controller.detect_object(
        rgb_frame,
        depth_frame,
        object_name,
        camera_name='gripper_cam'
    )

    elapsed = time.time() - start_time

    # Print results
    print(f"\nDetection completed in {elapsed:.2f}s")
    print(json.dumps(result, indent=2))

    if result.get('object_found'):
        print(f"\n✓ Object '{object_name}' FOUND!")
        if 'position_3d' in result:
            pos = result['position_3d']
            print(f"  3D Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        if 'confidence' in result:
            print(f"  Confidence: {result['confidence']*100:.1f}%")
    else:
        print(f"\n✗ Object '{object_name}' NOT FOUND")
        if 'reason' in result:
            print(f"  Reason: {result['reason']}")

    # Visualize detection
    if result.get('object_found'):
        print("\nSaving visualization...")
        vis_image = vision_controller.visualize_detection(
            rgb_frame,
            result,
            output_path='/tmp/detection_result.jpg'
        )
        print("✓ Visualization saved to /tmp/detection_result.jpg")


def test_workspace_analysis(camera_controller, vision_controller):
    """Test workspace analysis."""
    print("\n" + "="*60)
    print("TEST 4: Workspace Analysis")
    print("="*60)

    if not camera_controller or not vision_controller:
        print("✗ Skipping (missing controllers)")
        return

    # Get frame from top camera
    print("Capturing frame from top camera...")
    rgb_frame, depth_frame = camera_controller.get_rgbd_frames('top_cam')

    if rgb_frame is None:
        print("⚠️  Top camera unavailable, using gripper camera...")
        rgb_frame, depth_frame = camera_controller.get_rgbd_frames('gripper_cam')

    if rgb_frame is None:
        print("✗ No frame available")
        return

    print(f"✓ Frame captured: {rgb_frame.shape}")

    # Run analysis
    print("\nAnalyzing workspace...")
    start_time = time.time()

    result = vision_controller.analyze_workspace(
        rgb_frame,
        depth_frame,
        analysis_type='objects'
    )

    elapsed = time.time() - start_time

    # Print results
    print(f"\nAnalysis completed in {elapsed:.2f}s")
    print(json.dumps(result, indent=2))


def test_multiple_objects(camera_controller, vision_controller):
    """Test detection of multiple objects."""
    print("\n" + "="*60)
    print("TEST 5: Multiple Object Detection")
    print("="*60)

    if not camera_controller or not vision_controller:
        print("✗ Skipping (missing controllers)")
        return

    objects_to_find = ["apple", "banana", "cup", "bowl"]

    print(f"Testing detection of: {', '.join(objects_to_find)}")

    # Get frame once
    rgb_frame, depth_frame = camera_controller.get_rgbd_frames('gripper_cam')

    if rgb_frame is None:
        print("✗ No frame available")
        return

    results = {}

    for obj in objects_to_find:
        print(f"\nSearching for '{obj}'...")
        result = vision_controller.detect_object(
            rgb_frame,
            depth_frame,
            obj,
            camera_name='gripper_cam'
        )

        results[obj] = result.get('object_found', False)

        if result.get('object_found'):
            print(f"  ✓ FOUND")
            if 'position_3d' in result:
                pos = result['position_3d']
                print(f"    Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        else:
            print(f"  ✗ Not found")

    # Summary
    print("\n" + "-"*60)
    print("SUMMARY:")
    found_count = sum(1 for found in results.values() if found)
    print(f"  Found {found_count}/{len(objects_to_find)} objects")
    for obj, found in results.items():
        status = "✓" if found else "✗"
        print(f"    {status} {obj}")


def test_calibration_helper(camera_controller, vision_controller):
    """Interactive calibration helper."""
    print("\n" + "="*60)
    print("TEST 6: Calibration Helper")
    print("="*60)

    if not camera_controller or not vision_controller:
        print("✗ Skipping (missing controllers)")
        return

    print("""
This test helps calibrate the camera-to-robot transform.

STEPS:
1. Place a known object at a known position in the robot workspace
2. Enter the object name and actual position
3. The system will detect it and calculate calibration offset
""")

    try:
        obj_name = input("\nObject name (e.g., 'red cube'): ").strip()
        if not obj_name:
            print("Skipping calibration test")
            return

        print("Enter actual position in robot frame (meters):")
        x = float(input("  X: "))
        y = float(input("  Y: "))
        z = float(input("  Z: "))

        actual_pos = (x, y, z)

        print(f"\nDetecting '{obj_name}'...")
        rgb_frame, depth_frame = camera_controller.get_rgbd_frames('gripper_cam')

        if rgb_frame is None or depth_frame is None:
            print("✗ Need both RGB and depth frames for calibration")
            return

        result = vision_controller.detect_object(
            rgb_frame,
            depth_frame,
            obj_name,
            camera_name='gripper_cam'
        )

        if not result.get('object_found'):
            print(f"✗ Could not find '{obj_name}'")
            return

        if 'center_pixel' not in result:
            print("✗ No pixel coordinates")
            return

        # Run calibration
        vision_controller.calibrate_camera(
            result['center_pixel'],
            actual_pos,
            depth_frame
        )

    except KeyboardInterrupt:
        print("\nCalibration cancelled")
    except Exception as e:
        print(f"✗ Calibration error: {e}")


def main():
    """Run all tests."""
    print("="*60)
    print("VISION SYSTEM TEST SUITE")
    print("="*60)
    print("\nThis will test:")
    print("  1. Camera initialization and frame capture")
    print("  2. Vision controller with Gemini API")
    print("  3. Object detection with 3D positioning")
    print("  4. Workspace analysis")
    print("  5. Multiple object detection")
    print("  6. Calibration helper (optional)")

    # Initialize controllers
    camera_controller = test_camera_initialization()
    vision_controller = test_vision_initialization()

    if not camera_controller:
        print("\n✗ Cannot proceed without camera controller")
        return

    if not vision_controller:
        print("\n⚠️  Proceeding without vision controller (limited tests)")

    # Run tests
    test_object_detection(camera_controller, vision_controller, "apple")
    test_workspace_analysis(camera_controller, vision_controller)
    test_multiple_objects(camera_controller, vision_controller)

    # Optional calibration
    print("\n" + "="*60)
    response = input("\nRun calibration test? (y/N): ").strip().lower()
    if response == 'y':
        test_calibration_helper(camera_controller, vision_controller)

    # Cleanup
    print("\n" + "="*60)
    print("Cleaning up...")
    if camera_controller:
        camera_controller.shutdown()

    print("\n✓ All tests complete!")
    print("\nNOTES:")
    print("  - If objects not detected, try adjusting lighting")
    print("  - Depth accuracy depends on camera distance (optimal: 20-60cm)")
    print("  - Run calibration test to improve 3D positioning accuracy")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
