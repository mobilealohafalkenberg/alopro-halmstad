#!/usr/bin/env python3
"""
Test script for async trajectory execution feature.
Demonstrates blocking vs non-blocking trajectory execution.
"""

import time
import sys
import os

# Add parent directory to path to import arm_controller
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from arm_controller import ArmController

def test_blocking_trajectory(arm):
    """Test traditional blocking trajectory execution."""
    print("\n=== Testing Blocking Trajectory ===")

    waypoints = [
        {"point": [0.25, 0.0, 0.2], "label": "start", "gripper_action": "open"},
        {"point": [0.25, 0.1, 0.2], "label": "shift", "gripper_action": "close"},
        {"point": [0.25, 0.0, 0.25], "label": "lift", "gripper_action": "maintain"}
    ]

    print("Starting blocking trajectory execution...")
    start_time = time.time()
    result = arm.execute_trajectory(waypoints, speed='fast', blocking=True)
    elapsed = time.time() - start_time

    print(f"Trajectory completed in {elapsed:.2f}s")
    print(f"Success: {result['success']}")
    print(f"Waypoints completed: {result['waypoints_completed']}")


def test_async_trajectory(arm):
    """Test new async (non-blocking) trajectory execution."""
    print("\n=== Testing Async Trajectory ===")

    waypoints = [
        {"point": [0.25, 0.0, 0.2], "label": "start", "gripper_action": "open"},
        {"point": [0.25, 0.1, 0.2], "label": "shift", "gripper_action": "close"},
        {"point": [0.25, 0.1, 0.25], "label": "lift", "gripper_action": "maintain"},
        {"point": [0.30, 0.1, 0.25], "label": "move", "gripper_action": "maintain"},
        {"point": [0.30, 0.1, 0.2], "label": "place", "gripper_action": "open"}
    ]

    print("Starting async trajectory execution...")
    result = arm.execute_trajectory(waypoints, speed='medium', blocking=False)

    if result['success']:
        trajectory_id = result['trajectory_id']
        print(f"Trajectory started with ID: {trajectory_id}")
        print(f"Total waypoints: {result['total_waypoints']}")

        # Poll status while trajectory runs
        print("\nPolling trajectory status:")
        while True:
            status = arm.get_trajectory_status(trajectory_id)

            if status['found']:
                print(f"  Status: {status['status']}, Progress: {status['progress']:.1%}, "
                      f"Current waypoint: {status['current_waypoint']}/{status['total_waypoints']}")

                if status['status'] in ['completed', 'failed', 'canceled']:
                    print(f"\nTrajectory finished with status: {status['status']}")
                    if status['result']:
                        print(f"Result: {status['result']}")
                    if status['error']:
                        print(f"Error: {status['error']}")
                    break
            else:
                print(f"Trajectory not found: {status['error']}")
                break

            time.sleep(0.5)  # Poll every 500ms
    else:
        print(f"Failed to start trajectory: {result.get('error')}")


def test_trajectory_cancellation(arm):
    """Test trajectory cancellation."""
    print("\n=== Testing Trajectory Cancellation ===")

    # Long trajectory to have time to cancel
    waypoints = [
        {"point": [0.25, 0.0, 0.2], "label": f"waypoint_{i}"}
        for i in range(10)
    ]

    print("Starting trajectory that will be canceled...")
    result = arm.execute_trajectory(waypoints, speed='slow', blocking=False)

    if result['success']:
        trajectory_id = result['trajectory_id']
        print(f"Trajectory started with ID: {trajectory_id}")

        # Let it run for a bit
        time.sleep(2)

        # Check status before cancellation
        status = arm.get_trajectory_status(trajectory_id)
        print(f"\nBefore cancellation - Progress: {status['progress']:.1%}, "
              f"Waypoint: {status['current_waypoint']}/{status['total_waypoints']}")

        # Cancel the trajectory
        print("\nCanceling trajectory...")
        cancel_result = arm.cancel_trajectory(trajectory_id)
        print(f"Cancellation result: {cancel_result}")

        # Wait a moment for cancellation to take effect
        time.sleep(1)

        # Check final status
        final_status = arm.get_trajectory_status(trajectory_id)
        print(f"\nFinal status: {final_status['status']}")
        print(f"Error message: {final_status['error']}")


def test_multiple_trajectories(arm):
    """Test multiple concurrent trajectories."""
    print("\n=== Testing Multiple Concurrent Trajectories ===")

    # Start multiple trajectories (in dry run mode, these won't conflict)
    trajectory_ids = []

    for i in range(3):
        waypoints = [
            {"point": [0.25 + i*0.01, 0.0, 0.2], "label": f"traj{i}_wp{j}"}
            for j in range(3)
        ]

        result = arm.execute_trajectory(waypoints, speed='fast', blocking=False)
        if result['success']:
            trajectory_ids.append(result['trajectory_id'])
            print(f"Started trajectory {i+1}: {result['trajectory_id'][:8]}...")

    # List all trajectories
    print("\nListing all trajectories:")
    list_result = arm.list_trajectories()
    for traj in list_result['trajectories']:
        print(f"  {traj['trajectory_id'][:8]}... - Status: {traj['status']}, "
              f"Progress: {traj['progress']:.1%}")

    # Wait for all to complete
    print("\nWaiting for all trajectories to complete...")
    time.sleep(3)

    # Check final status
    print("\nFinal status:")
    for traj_id in trajectory_ids:
        status = arm.get_trajectory_status(traj_id)
        print(f"  {traj_id[:8]}... - {status['status']}")


if __name__ == "__main__":
    print("=" * 60)
    print("Async Trajectory Execution Test Suite")
    print("=" * 60)

    # Create single controller instance for all tests
    print("\nInitializing controller (shared across all tests)...")
    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()
    print("✓ Controller initialized\n")

    try:
        # Run tests with shared controller
        test_blocking_trajectory(arm)
        test_async_trajectory(arm)
        test_trajectory_cancellation(arm)
        test_multiple_trajectories(arm)

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
