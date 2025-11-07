#!/usr/bin/env python3
"""
Test trajectory tracking with non-blocking execution through the bridge.

This script tests:
1. Starting a trajectory with non-blocking execution
2. Polling trajectory status during execution
3. Verifying completion status
4. Testing trajectory cancellation
5. Listing all trajectories
"""

import requests
import json
import time
import sys

BRIDGE_URL = "http://localhost:8081"

def test_trajectory_status_polling():
    """Test trajectory execution with status polling"""
    print("\n=== Test 1: Trajectory Status Polling ===")

    # Define a test trajectory
    trajectory = {
        "name": "move_arm_trajectory",
        "args": {
            "trajectory": [
                {"point": [0.25, 0.0, 0.2], "label": "start", "gripper_action": "open"},
                {"point": [0.30, 0.1, 0.2], "label": "shift_right", "gripper_action": "maintain"},
                {"point": [0.30, 0.1, 0.15], "label": "lower", "gripper_action": "close"},
                {"point": [0.30, 0.1, 0.25], "label": "lift", "gripper_action": "maintain"},
                {"point": [0.25, 0.0, 0.25], "label": "return", "gripper_action": "open"}
            ],
            "speed": "medium"
        },
        "id": "test_trajectory_1"
    }

    # Start trajectory
    print("\n1. Starting trajectory...")
    response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=trajectory)

    if response.status_code != 200:
        print(f"❌ Failed to start trajectory: {response.status_code}")
        print(f"Response: {response.text}")
        return False

    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")

    if not result.get('result', {}).get('success'):
        print("❌ Trajectory failed to start")
        return False

    trajectory_id = result['result'].get('trajectory_id')
    if not trajectory_id:
        print("❌ No trajectory_id returned")
        return False

    print(f"✅ Trajectory started with ID: {trajectory_id}")
    print(f"   Total waypoints: {result['result']['total_waypoints']}")

    # Poll status until completion
    print("\n2. Polling trajectory status...")
    max_polls = 30
    poll_count = 0
    last_waypoint = -1

    while poll_count < max_polls:
        time.sleep(0.5)  # Poll every 500ms
        poll_count += 1

        status_response = requests.get(f"{BRIDGE_URL}/trajectory/{trajectory_id}/status")

        if status_response.status_code != 200:
            print(f"❌ Failed to get status: {status_response.status_code}")
            return False

        status = status_response.json()

        if not status.get('found'):
            print(f"❌ Trajectory not found: {status.get('error')}")
            return False

        current_status = status['status']
        progress = status['progress']
        current_waypoint = status['current_waypoint']
        total_waypoints = status['total_waypoints']

        # Print update when waypoint changes
        if current_waypoint != last_waypoint:
            print(f"   Poll {poll_count}: status={current_status}, waypoint={current_waypoint}/{total_waypoints}, progress={progress*100:.1f}%")
            last_waypoint = current_waypoint

        # Check if completed
        if current_status in ['completed', 'failed', 'canceled']:
            print(f"\n✅ Trajectory finished with status: {current_status}")

            if current_status == 'completed':
                print(f"   Duration: {status['completed_at'] - status['started_at']:.2f}s")
                if status.get('result'):
                    print(f"   Waypoints completed: {len(status['result']['waypoints_completed'])}/{total_waypoints}")
                return True
            else:
                print(f"❌ Trajectory {current_status}")
                if status.get('error'):
                    print(f"   Error: {status['error']}")
                return False

    print(f"❌ Timeout waiting for trajectory completion (polled {poll_count} times)")
    return False

def test_trajectory_cancellation():
    """Test canceling a trajectory mid-execution"""
    print("\n=== Test 2: Trajectory Cancellation ===")

    # Define a longer trajectory
    trajectory = {
        "name": "move_arm_trajectory",
        "args": {
            "trajectory": [
                {"point": [0.25, 0.0, 0.2], "label": "waypoint_1"},
                {"point": [0.30, 0.0, 0.2], "label": "waypoint_2"},
                {"point": [0.30, 0.1, 0.2], "label": "waypoint_3"},
                {"point": [0.30, 0.1, 0.15], "label": "waypoint_4"},
                {"point": [0.25, 0.1, 0.15], "label": "waypoint_5"},
                {"point": [0.25, 0.0, 0.15], "label": "waypoint_6"}
            ],
            "speed": "slow"  # Slow speed to have time to cancel
        },
        "id": "test_trajectory_2"
    }

    # Start trajectory
    print("\n1. Starting long trajectory...")
    response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=trajectory)

    if response.status_code != 200:
        print(f"❌ Failed to start trajectory: {response.status_code}")
        return False

    result = response.json()
    trajectory_id = result['result'].get('trajectory_id')

    if not trajectory_id:
        print("❌ No trajectory_id returned")
        return False

    print(f"✅ Trajectory started with ID: {trajectory_id}")

    # Wait for trajectory to start executing
    print("\n2. Waiting for trajectory to start executing...")
    time.sleep(2)

    # Cancel trajectory
    print("\n3. Canceling trajectory...")
    cancel_response = requests.post(f"{BRIDGE_URL}/trajectory/{trajectory_id}/cancel")

    if cancel_response.status_code != 200:
        print(f"❌ Failed to cancel trajectory: {cancel_response.status_code}")
        return False

    cancel_result = cancel_response.json()
    print(f"Cancel response: {json.dumps(cancel_result, indent=2)}")

    if not cancel_result.get('success'):
        print(f"❌ Cancellation failed: {cancel_result.get('error')}")
        return False

    # Check final status
    print("\n4. Verifying cancellation status...")
    time.sleep(1)  # Give time for cancellation to take effect

    status_response = requests.get(f"{BRIDGE_URL}/trajectory/{trajectory_id}/status")
    status = status_response.json()

    print(f"Final status: {json.dumps(status, indent=2)}")

    if status['status'] == 'canceled':
        print("✅ Trajectory successfully canceled")
        return True
    else:
        print(f"❌ Expected status 'canceled', got '{status['status']}'")
        return False

def test_list_trajectories():
    """Test listing all trajectories"""
    print("\n=== Test 3: List Trajectories ===")

    response = requests.get(f"{BRIDGE_URL}/trajectories")

    if response.status_code != 200:
        print(f"❌ Failed to list trajectories: {response.status_code}")
        return False

    result = response.json()

    if not result.get('success'):
        print(f"❌ List failed: {result.get('error')}")
        return False

    print(f"\nFound {result['count']} trajectories:")
    for traj in result['trajectories']:
        print(f"  - ID: {traj['trajectory_id'][:8]}...")
        print(f"    Status: {traj['status']}")
        print(f"    Progress: {traj['progress']*100:.1f}%")
        print(f"    Waypoints: {traj['current_waypoint']}/{traj['total_waypoints']}")

    print("\n✅ List trajectories successful")
    return True

def test_bridge_connectivity():
    """Test if bridge is running and accessible"""
    print("\n=== Checking Bridge Connectivity ===")

    try:
        response = requests.get(f"{BRIDGE_URL}/status", timeout=2)

        if response.status_code != 200:
            print(f"❌ Bridge not responding properly: {response.status_code}")
            return False

        status = response.json()
        print(f"Bridge status: {json.dumps(status, indent=2)}")

        if not status.get('arm_initialized'):
            print("⚠️  Warning: Arm controller not initialized")
            print("   Make sure robot is powered on and connected")
            return False

        print("✅ Bridge is running and arm controller initialized")
        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to bridge at {BRIDGE_URL}")
        print("   Make sure bridge is running: ./run_bridge.sh")
        return False
    except Exception as e:
        print(f"❌ Error checking bridge: {e}")
        return False

def main():
    print("=" * 60)
    print("Trajectory Tracking Test Suite")
    print("=" * 60)

    # Check connectivity first
    if not test_bridge_connectivity():
        print("\n❌ Bridge connectivity check failed. Exiting.")
        sys.exit(1)

    # Run tests
    tests = [
        ("Trajectory Status Polling", test_trajectory_status_polling),
        ("Trajectory Cancellation", test_trajectory_cancellation),
        ("List Trajectories", test_list_trajectories)
    ]

    results = []

    for test_name, test_func in tests:
        print("\n" + "=" * 60)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
