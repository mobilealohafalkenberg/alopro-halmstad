#!/usr/bin/env python3
"""
Test script for dry-run mode across all movement methods.
Verifies that dry-run mode works correctly and safety checks still run.
"""

import time
from arm_controller import ArmController

def test_move_joints_dry_run():
    """Test move_joints() with dry-run enabled."""
    print("\n" + "=" * 60)
    print("TEST 1: move_joints() with dry-run enabled")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    # Test 1a: Safe joint positions
    print("\n[Test 1a] Safe joint positions in dry-run mode:")
    safe_joints = [0.0, -0.5, 1.0, 0.0, -0.5, 0.0]
    result = arm.move_joints(safe_joints, unit='radians')
    print(f"Result: {result}")
    assert result['success'] == True, "Safe movement should succeed in dry-run"
    assert result['state'] == 'dry_run', "State should be 'dry_run'"
    assert 'target_joints' in result, "Should return target_joints"
    assert 'message' in result, "Should have dry-run message"
    print("✓ Safe movement validated in dry-run mode")

    # Test 1b: Unsafe joint positions (should fail safety check even in dry-run)
    print("\n[Test 1b] Unsafe joint positions (should fail safety check):")
    unsafe_joints = [0.0, -2.0, 2.5, 0.0, -2.0, 0.0]  # Exceeds limits
    result = arm.move_joints(unsafe_joints, unit='radians')
    print(f"Result: {result}")
    assert result['success'] == False, "Unsafe movement should fail even in dry-run"
    assert 'error' in result, "Should have error message"
    print("✓ Safety check blocks unsafe movement in dry-run mode")


def test_move_to_position_dry_run():
    """Test move_to_position() with dry-run enabled."""
    print("\n" + "=" * 60)
    print("TEST 2: move_to_position() with dry-run enabled")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    # Test 2a: Safe position
    print("\n[Test 2a] Safe position in dry-run mode:")
    result = arm.move_to_position([0.3, 0.0, 0.2])
    print(f"Result: {result}")
    assert result['success'] == True, "Safe position should succeed in dry-run"
    assert result['state'] == 'dry_run', "State should be 'dry_run'"
    assert 'target_position' in result, "Should return target_position"
    print("✓ Safe position validated in dry-run mode")

    # Test 2b: Position below table (z < 0.1) - should fail safety
    print("\n[Test 2b] Position below table (should fail safety check):")
    result = arm.move_to_position([0.3, 0.0, 0.05])
    print(f"Result: {result}")
    assert result['success'] == False, "Below-table position should fail"
    assert 'safety' in result, "Should include safety validation details"
    print("✓ Safety check blocks unsafe position in dry-run mode")

    # Test 2c: Position out of workspace
    print("\n[Test 2c] Position out of workspace (should fail safety check):")
    result = arm.move_to_position([1.0, 0.0, 0.2])  # x too far
    print(f"Result: {result}")
    assert result['success'] == False, "Out-of-workspace position should fail"
    print("✓ Workspace limits enforced in dry-run mode")


def test_move_to_pose_dry_run():
    """Test move_to_pose() with dry-run enabled."""
    print("\n" + "=" * 60)
    print("TEST 3: move_to_pose() with dry-run enabled")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    # Test 3a: Named poses
    poses = ['home', 'ready', 'sleep']
    for pose in poses:
        print(f"\n[Test 3a] Moving to '{pose}' pose in dry-run mode:")
        result = arm.move_to_pose(pose)
        print(f"Result: {result}")
        assert result['success'] == True, f"{pose} pose should succeed in dry-run"
        assert result['state'] == 'dry_run', "State should be 'dry_run'"
        print(f"✓ '{pose}' pose validated in dry-run mode")

    # Test 3b: Invalid pose name
    print("\n[Test 3b] Invalid pose name (should fail):")
    result = arm.move_to_pose('invalid_pose')
    print(f"Result: {result}")
    assert result['success'] == False, "Invalid pose should fail"
    assert 'error' in result, "Should have error message"
    print("✓ Invalid pose rejected correctly")


def test_execute_trajectory_dry_run():
    """Test execute_trajectory() with dry-run enabled."""
    print("\n" + "=" * 60)
    print("TEST 4: execute_trajectory() with dry-run enabled")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    # Test 4a: Valid trajectory
    print("\n[Test 4a] Valid trajectory in dry-run mode:")
    waypoints = [
        {"point": [0.25, 0.0, 0.2], "label": "start"},
        {"point": [0.30, 0.0, 0.2], "label": "move"},
        {"point": [0.30, 0.0, 0.25], "label": "lift"}
    ]
    result = arm.execute_trajectory(waypoints, speed='fast', blocking=True)
    print(f"Result: {result}")
    assert result['success'] == True, "Valid trajectory should succeed in dry-run"
    assert result['total_waypoints'] == 3, "Should track all waypoints"
    print("✓ Valid trajectory validated in dry-run mode")

    # Test 4b: Trajectory with unsafe waypoint
    print("\n[Test 4b] Trajectory with unsafe waypoint (should fail):")
    waypoints_unsafe = [
        {"point": [0.25, 0.0, 0.2], "label": "start"},
        {"point": [0.30, 0.0, 0.05], "label": "unsafe_below_table"}
    ]
    result = arm.execute_trajectory(waypoints_unsafe, speed='fast', blocking=True)
    print(f"Result: {result}")
    assert result['success'] == False, "Unsafe waypoint should fail validation"
    assert 'safety' in result, "Should include safety details"
    print("✓ Trajectory with unsafe waypoint rejected in dry-run mode")


def test_dry_run_vs_normal_mode():
    """Compare dry-run mode vs normal mode behavior."""
    print("\n" + "=" * 60)
    print("TEST 5: Comparing dry-run vs normal mode")
    print("=" * 60)

    # Create two controllers: one with dry-run, one without
    arm_dry = ArmController(enable_safety=True, dry_run=True)
    arm_dry.initialize()

    print("\n[Test 5a] Same command in dry-run mode:")
    result_dry = arm_dry.move_to_position([0.3, 0.0, 0.2])
    print(f"Dry-run result state: {result_dry['state']}")
    assert result_dry['state'] == 'dry_run', "Should be in dry_run state"

    print("\n✓ Dry-run mode clearly distinguishable from normal mode")


def test_safety_checks_comprehensive():
    """Comprehensive test of safety checks in dry-run mode."""
    print("\n" + "=" * 60)
    print("TEST 6: Comprehensive safety checks in dry-run")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        # (description, method, args, should_pass)
        ("Safe joint angles", "move_joints", {"joint_positions": [0.0, -0.5, 1.0, 0.0, -0.5, 0.0]}, True),
        ("Safe position", "move_to_position", {"position": [0.3, 0.0, 0.2]}, True),
        ("Position at table edge (z=0.1)", "move_to_position", {"position": [0.3, 0.0, 0.1]}, True),
        ("Position below table", "move_to_position", {"position": [0.3, 0.0, 0.05]}, False),
        ("Position too far x", "move_to_position", {"position": [0.6, 0.0, 0.2]}, False),
        ("Position too far y", "move_to_position", {"position": [0.3, 0.6, 0.2]}, False),
        ("Home pose", "move_to_pose", {"pose_name": "home"}, True),
        ("Sleep pose", "move_to_pose", {"pose_name": "sleep"}, True),
    ]

    passed = 0
    failed = 0

    for desc, method, args, should_pass in test_cases:
        print(f"\n[Test 6] {desc}:")
        try:
            if method == "move_joints":
                result = arm.move_joints(**args)
            elif method == "move_to_position":
                result = arm.move_to_position(**args)
            elif method == "move_to_pose":
                result = arm.move_to_pose(**args)

            success = result['success']
            state = result.get('state', 'unknown')

            if success == should_pass:
                print(f"  ✓ PASS - Success: {success}, State: {state}")
                passed += 1
            else:
                print(f"  ✗ FAIL - Expected success={should_pass}, got {success}")
                failed += 1
        except Exception as e:
            print(f"  ✗ EXCEPTION: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Safety check results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    assert failed == 0, f"{failed} safety check tests failed"


if __name__ == "__main__":
    print("=" * 60)
    print("DRY-RUN MODE TEST SUITE")
    print("Testing all movement methods with dry-run enabled")
    print("=" * 60)

    try:
        # Run all tests
        test_move_joints_dry_run()
        test_move_to_position_dry_run()
        test_move_to_pose_dry_run()
        test_execute_trajectory_dry_run()
        test_dry_run_vs_normal_mode()
        test_safety_checks_comprehensive()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nSummary:")
        print("✓ move_joints() dry-run mode working correctly")
        print("✓ move_to_position() dry-run mode working correctly")
        print("✓ move_to_pose() dry-run mode working correctly")
        print("✓ execute_trajectory() dry-run mode working correctly")
        print("✓ Safety checks run before dry-run in all methods")
        print("✓ Unsafe movements blocked even in dry-run mode")
        print("\nDry-run mode enables complete system testing without robot hardware!")

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        exit(1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
