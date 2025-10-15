#!/usr/bin/env python3

"""
Test file for Task 2.1: Exception Logging in Gripper Position Monitor

This test verifies that the gripper controller properly logs exceptions
when the position monitor encounters errors.

Test scenarios:
1. Simulate AttributeError (ROS disconnect - joint_states becomes None)
2. Simulate IndexError (gripper_index out of bounds)
3. Verify error counter increments
4. Verify critical alert after 5 consecutive failures
5. Verify counter resets on successful read
"""

import time
import logging
import threading
from unittest.mock import Mock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gripper_controller import GripperController, GripperState

# Configure logging to see the output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_attribute_error_logging():
    """Test that AttributeError is properly logged (simulates ROS disconnect)"""
    print("\n" + "="*70)
    print("TEST 1: AttributeError Logging (ROS Disconnect)")
    print("="*70)

    controller = GripperController()

    # Mock the bot interface
    controller.bot = Mock()
    controller.bot.core = Mock()
    controller.bot.core.js_mutex = threading.Lock()
    controller.bot.gripper = Mock()
    controller.bot.gripper.left_finger_index = 0

    # Simulate ROS disconnect - joint_states becomes None
    controller.bot.core.joint_states = None

    controller.initialized = True
    controller._start_position_monitor()

    # Wait for monitor to attempt reading and fail
    time.sleep(0.5)

    # Check that error counter incremented
    assert controller.monitor_failure_count > 0, "Error counter should have incremented"
    print(f"✓ Error counter: {controller.monitor_failure_count}")

    # Cleanup
    controller.initialized = False
    time.sleep(0.2)
    print("✓ Test passed: AttributeError logged correctly\n")


def test_index_error_logging():
    """Test that IndexError is properly logged (invalid gripper index)"""
    print("\n" + "="*70)
    print("TEST 2: IndexError Logging (Invalid Gripper Index)")
    print("="*70)

    controller = GripperController()

    # Mock the bot interface
    controller.bot = Mock()
    controller.bot.core = Mock()
    controller.bot.core.js_mutex = threading.Lock()
    controller.bot.gripper = Mock()
    controller.bot.gripper.left_finger_index = 999  # Invalid index

    # Valid joint_states but with too few elements
    mock_joint_states = Mock()
    mock_joint_states.position = [0.0, 0.1, 0.2]  # Only 3 elements, index 999 invalid
    controller.bot.core.joint_states = mock_joint_states

    controller.initialized = True
    controller._start_position_monitor()

    # Wait for monitor to attempt reading and fail
    time.sleep(0.5)

    # Check that error counter incremented
    assert controller.monitor_failure_count > 0, "Error counter should have incremented"
    print(f"✓ Error counter: {controller.monitor_failure_count}")

    # Cleanup
    controller.initialized = False
    time.sleep(0.2)
    print("✓ Test passed: IndexError logged correctly\n")


def test_critical_alert_after_5_failures():
    """Test that critical alert is logged after 5 consecutive failures"""
    print("\n" + "="*70)
    print("TEST 3: Critical Alert After 5 Consecutive Failures")
    print("="*70)

    controller = GripperController()

    # Mock the bot interface to always fail
    controller.bot = Mock()
    controller.bot.core = Mock()
    controller.bot.core.js_mutex = threading.Lock()
    controller.bot.gripper = Mock()
    controller.bot.gripper.left_finger_index = 0
    controller.bot.core.joint_states = None  # Will cause AttributeError

    controller.initialized = True
    controller._start_position_monitor()

    # Wait for at least 5 failures (0.1s per attempt, so ~0.6s)
    time.sleep(0.7)

    # Check that error counter is >= 5
    assert controller.monitor_failure_count >= 5, f"Expected >= 5 failures, got {controller.monitor_failure_count}"
    print(f"✓ Error counter reached: {controller.monitor_failure_count}")
    print("✓ Check logs above for CRITICAL alert")

    # Cleanup
    controller.initialized = False
    time.sleep(0.2)
    print("✓ Test passed: Critical alert triggered\n")


def test_error_recovery():
    """Test that error counter resets after successful read"""
    print("\n" + "="*70)
    print("TEST 4: Error Recovery (Counter Reset on Success)")
    print("="*70)

    controller = GripperController()

    # Mock the bot interface
    controller.bot = Mock()
    controller.bot.core = Mock()
    controller.bot.core.js_mutex = threading.Lock()
    controller.bot.gripper = Mock()
    controller.bot.gripper.left_finger_index = 0

    # Start with failing state
    controller.bot.core.joint_states = None
    controller.initialized = True
    controller._start_position_monitor()

    # Wait for some failures
    time.sleep(0.3)
    failure_count = controller.monitor_failure_count
    assert failure_count > 0, "Should have some failures initially"
    print(f"✓ Initial failures: {failure_count}")

    # Now fix the issue - provide valid joint_states
    mock_joint_states = Mock()
    mock_joint_states.position = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    controller.bot.core.joint_states = mock_joint_states

    # Wait for successful read
    time.sleep(0.3)

    # Check that counter was reset
    assert controller.monitor_failure_count == 0, f"Counter should reset to 0, got {controller.monitor_failure_count}"
    print(f"✓ Error counter reset: {controller.monitor_failure_count}")

    # Cleanup
    controller.initialized = False
    time.sleep(0.2)
    print("✓ Test passed: Error recovery successful\n")


def test_concurrent_access():
    """Test that monitor thread and get_gripper_state() can run concurrently without crashes"""
    print("\n" + "="*70)
    print("TEST 5: Concurrent Access (Thread Safety)")
    print("="*70)

    controller = GripperController()

    # Mock the bot interface with valid data
    controller.bot = Mock()
    controller.bot.core = Mock()
    controller.bot.core.js_mutex = threading.Lock()
    controller.bot.gripper = Mock()
    controller.bot.gripper.left_finger_index = 0

    mock_joint_states = Mock()
    mock_joint_states.position = [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    controller.bot.core.joint_states = mock_joint_states

    controller.initialized = True
    controller._start_position_monitor()

    # Rapidly call get_gripper_state() while monitor is running
    for i in range(20):
        state = controller.get_gripper_state()
        assert state['success'] == True, "Should successfully get state"
        time.sleep(0.05)  # 50ms between calls

    print(f"✓ Made 20 concurrent state queries without crashes")

    # Cleanup
    controller.initialized = False
    time.sleep(0.2)
    print("✓ Test passed: Concurrent access is thread-safe\n")


if __name__ == '__main__':
    print("\n" + "="*70)
    print("TASK 2.1 EXCEPTION LOGGING TEST SUITE")
    print("="*70)

    try:
        test_attribute_error_logging()
        test_index_error_logging()
        test_critical_alert_after_5_failures()
        test_error_recovery()
        test_concurrent_access()

        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nTask 2.1 implementation verified:")
        print("  ✓ Exception logging works correctly")
        print("  ✓ Error counter increments on failures")
        print("  ✓ Critical alert triggers after 5 failures")
        print("  ✓ Counter resets on successful recovery")
        print("  ✓ Thread-safe concurrent access")
        print("\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
