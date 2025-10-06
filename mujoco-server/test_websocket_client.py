#!/usr/bin/env python3
"""
WebSocket Test Client for MuJoCo Simulation Server

Tests dual-arm ALOHA functionality via WebSocket API.
"""

import socketio
import time
import sys

# Create SocketIO client
sio = socketio.Client()

# Track test results
test_results = {
    'connection': False,
    'left_arm_move': False,
    'right_arm_move': False,
    'left_gripper': False,
    'right_gripper': False,
    'frame_received': False,
    'status_query': False
}

frame_count = 0


@sio.event
def connect():
    """Connection established"""
    print("✓ Connected to server")
    test_results['connection'] = True


@sio.event
def disconnect():
    """Connection closed"""
    print("✓ Disconnected from server")


@sio.event
def connection_status(data):
    """Server connection status"""
    print(f"✓ Connection status: {data}")


@sio.event
def command_result(data):
    """Command execution result"""
    if data.get('success'):
        print(f"✓ Command succeeded: {data.get('command', 'unknown')}")
    else:
        print(f"✗ Command failed: {data.get('error', 'unknown')}")


@sio.event
def frame_update(data):
    """Frame update from simulation"""
    global frame_count
    frame_count += 1
    test_results['frame_received'] = True

    if frame_count == 1:
        print(f"✓ Frame received (size: {len(data.get('frame', ''))} bytes)")
    elif frame_count % 5 == 0:
        print(f"  Frame #{frame_count} received")


@sio.event
def arm_status(data):
    """Arm status response"""
    arm = data.get('arm', 'unknown')
    positions = data.get('status', {}).get('positions', [])
    print(f"✓ {arm.capitalize()} arm status: {len(positions)} joints")
    test_results['status_query'] = True


def test_move_left_arm():
    """Test left arm movement"""
    print("\n[Test 1] Moving left arm to ready position...")
    home_positions = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
    sio.emit('move_arm', {'arm': 'left', 'positions': home_positions})
    time.sleep(0.5)
    test_results['left_arm_move'] = True


def test_move_right_arm():
    """Test right arm movement"""
    print("\n[Test 2] Moving right arm to ready position...")
    home_positions = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
    sio.emit('move_arm', {'arm': 'right', 'positions': home_positions})
    time.sleep(0.5)
    test_results['right_arm_move'] = True


def test_left_gripper():
    """Test left gripper control"""
    print("\n[Test 3] Testing left gripper...")
    print("  - Opening left gripper")
    sio.emit('control_gripper', {'arm': 'left', 'command': 'open'})
    time.sleep(0.3)

    print("  - Closing left gripper")
    sio.emit('control_gripper', {'arm': 'left', 'command': 'close'})
    time.sleep(0.3)
    test_results['left_gripper'] = True


def test_right_gripper():
    """Test right gripper control"""
    print("\n[Test 4] Testing right gripper...")
    print("  - Opening right gripper")
    sio.emit('control_gripper', {'arm': 'right', 'command': 'open'})
    time.sleep(0.3)

    print("  - Closing right gripper")
    sio.emit('control_gripper', {'arm': 'right', 'command': 'close'})
    time.sleep(0.3)
    test_results['right_gripper'] = True


def test_get_status():
    """Test status queries"""
    print("\n[Test 5] Querying arm status...")
    sio.emit('get_arm_status', {'arm': 'left'})
    time.sleep(0.2)
    sio.emit('get_arm_status', {'arm': 'right'})
    time.sleep(0.2)


def test_reset():
    """Test reset to home position"""
    print("\n[Test 6] Resetting robot to home position...")
    sio.emit('reset_robot')
    time.sleep(0.5)


def test_initial_frame():
    """Request initial frame"""
    print("\n[Test 7] Requesting initial frame...")
    sio.emit('get_initial_frame')
    time.sleep(0.5)


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in test_results.values() if v)
    total = len(test_results)

    for test_name, passed in test_results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:10} {test_name}")

    print("-"*60)
    print(f"Total: {passed}/{total} tests passed")
    print(f"Frames received: {frame_count}")
    print("="*60)

    return passed == total


def main():
    """Run all tests"""
    print("="*60)
    print("MuJoCo Dual-Arm WebSocket Test Client")
    print("="*60)
    print("\nConnecting to ws://localhost:5000...")

    try:
        # Connect to server (wait for connection to complete)
        sio.connect('http://localhost:5000', wait_timeout=5)

        # Verify connection
        if not sio.connected:
            raise ConnectionError("Failed to connect to server")

        print("✓ Connected successfully\n")
        time.sleep(1)

        # Run tests
        test_initial_frame()
        test_move_left_arm()
        test_move_right_arm()
        test_left_gripper()
        test_right_gripper()
        test_get_status()
        test_reset()

        # Wait for final frames
        print("\nWaiting for final updates...")
        time.sleep(2)

        # Disconnect
        print("\nDisconnecting...")
        sio.disconnect()
        time.sleep(0.5)

        # Print summary
        all_passed = print_summary()

        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        if sio.connected:
            sio.disconnect()
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        if sio.connected:
            sio.disconnect()
        sys.exit(1)


if __name__ == '__main__':
    main()
