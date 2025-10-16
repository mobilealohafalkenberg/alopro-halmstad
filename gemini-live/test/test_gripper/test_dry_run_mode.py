#!/usr/bin/env python3

"""
Test script for Task 2.9: Dry-Run Mode for Gripper Controller

This script tests the dry-run functionality that allows hardware-independent testing
of the gripper controller without requiring actual robot hardware.

Test scenarios:
1. Dry-run initialization (should skip hardware setup)
2. Dry-run gripper operations (open/close/set_position)
3. Dry-run arm operations (sleep_arm)
4. Verify state tracking works in dry-run mode
5. Compare dry-run vs normal mode behavior
"""

import sys
import os
import time

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from gripper_controller import GripperController, GripperState


def test_dry_run_initialization():
    """Test 1: Dry-run initialization should skip hardware setup"""
    print("\n=== Test 1: Dry-Run Initialization ===")

    controller = GripperController(dry_run=True)

    # Should initialize successfully without hardware
    start_time = time.time()
    result = controller.initialize()
    elapsed = time.time() - start_time

    print(f"Initialization result: {result}")
    print(f"Initialization time: {elapsed:.3f}s")

    # Should be very fast (no hardware initialization)
    assert result == True, "Dry-run initialization should succeed"
    assert elapsed < 0.5, "Dry-run initialization should be fast"
    assert controller.initialized == True, "Should be marked as initialized"
    assert controller.current_state == GripperState.CLOSED, "Should start in closed state"

    controller.shutdown()
    print("✓ Test 1 PASSED")


def test_dry_run_gripper_operations():
    """Test 2: Dry-run gripper operations should return mock responses"""
    print("\n=== Test 2: Dry-Run Gripper Operations ===")

    controller = GripperController(dry_run=True)
    controller.initialize()

    # Test open gripper
    print("\nTesting open_gripper...")
    result = controller.open_gripper(blocking=True)
    print(f"Open result: {result}")

    assert result["success"] == True, "Open should succeed in dry-run"
    assert result["state"] == "dry_run", "Should indicate dry-run mode"
    assert "message" in result, "Should contain dry-run message"

    # Test close gripper
    print("\nTesting close_gripper...")
    result = controller.close_gripper(blocking=True)
    print(f"Close result: {result}")

    assert result["success"] == True, "Close should succeed in dry-run"
    assert result["state"] == "dry_run", "Should indicate dry-run mode"

    # Test set position
    print("\nTesting set_gripper_position...")
    result = controller.set_gripper_position(0.5, blocking=True)  # Half open
    print(f"Set position result: {result}")

    assert result["success"] == True, "Set position should succeed in dry-run"
    assert result["state"] == "dry_run", "Should indicate dry-run mode"

    controller.shutdown()
    print("✓ Test 2 PASSED")


def test_dry_run_state_tracking():
    """Test 3: State tracking should work correctly in dry-run mode"""
    print("\n=== Test 3: Dry-Run State Tracking ===")

    controller = GripperController(dry_run=True)
    controller.initialize()

    # Initial state should be closed
    state = controller.get_gripper_state()
    print(f"Initial state: {state}")
    assert state["state"] == "closed", "Should start closed"

    # Open gripper - state should update
    controller.open_gripper(blocking=True)
    state = controller.get_gripper_state()
    print(f"After opening: {state}")
    assert state["state"] == "open", "State should update to open"

    # Close gripper - state should update
    controller.close_gripper(blocking=True)
    state = controller.get_gripper_state()
    print(f"After closing: {state}")
    assert state["state"] == "closed", "State should update to closed"

    # Set to mid position - state should be unknown
    controller.set_gripper_position(0.5, blocking=True)
    state = controller.get_gripper_state()
    print(f"After mid position: {state}")
    # State should be unknown (not fully open or closed)

    controller.shutdown()
    print("✓ Test 3 PASSED")


def test_dry_run_arm_operations():
    """Test 4: Arm operations should work in dry-run mode"""
    print("\n=== Test 4: Dry-Run Arm Operations ===")

    controller = GripperController(dry_run=True)
    controller.initialize()

    # Test sleep arm
    print("\nTesting sleep_arm...")
    start_time = time.time()
    result = controller.sleep_arm()
    elapsed = time.time() - start_time

    print(f"Sleep arm result: {result}")
    print(f"Sleep arm time: {elapsed:.3f}s")

    assert result == True, "Sleep arm should succeed in dry-run"
    assert elapsed < 0.5, "Dry-run sleep should be fast"

    controller.shutdown()
    print("✓ Test 4 PASSED")


def test_dry_run_vs_normal_mode():
    """Test 5: Compare dry-run behavior vs normal mode (will fail on normal)"""
    print("\n=== Test 5: Dry-Run vs Normal Mode Comparison ===")

    # Test dry-run mode (should always work)
    print("\nTesting dry-run mode...")
    dry_controller = GripperController(dry_run=True)
    dry_result = dry_controller.initialize()
    print(f"Dry-run initialization: {dry_result}")
    assert dry_result == True, "Dry-run should always work"
    dry_controller.shutdown()

    # Test normal mode (will fail without hardware)
    print("\nTesting normal mode (expected to fail without hardware)...")
    normal_controller = GripperController(dry_run=False)
    normal_result = normal_controller.initialize()
    print(f"Normal initialization: {normal_result}")

    if normal_result:
        print("Normal mode succeeded - hardware is available")
        normal_controller.shutdown()
    else:
        print("Normal mode failed - no hardware available (expected)")

    print("✓ Test 5 PASSED - Dry-run works regardless of hardware availability")


def test_dry_run_performance():
    """Test 6: Dry-run mode should be fast"""
    print("\n=== Test 6: Dry-Run Performance ===")

    controller = GripperController(dry_run=True)

    # Time a complete cycle
    start_time = time.time()

    controller.initialize()
    controller.open_gripper(blocking=True)
    controller.close_gripper(blocking=True)
    controller.set_gripper_position(0.3, blocking=True)
    controller.sleep_arm()
    controller.shutdown()

    total_time = time.time() - start_time
    print(f"Total dry-run cycle time: {total_time:.3f}s")

    # Should complete quickly since it's all mocked
    assert total_time < 2.0, "Dry-run cycle should be fast"

    print("✓ Test 6 PASSED")


def run_all_tests():
    """Run all dry-run mode tests"""
    print("Starting Task 2.9 Dry-Run Mode Tests")
    print("=" * 50)

    try:
        test_dry_run_initialization()
        test_dry_run_gripper_operations()
        test_dry_run_state_tracking()
        test_dry_run_arm_operations()
        test_dry_run_vs_normal_mode()
        test_dry_run_performance()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Task 2.9: Dry-Run Mode implementation is working correctly")
        print("\nDry-run mode benefits:")
        print("✓ Hardware-independent testing")
        print("✓ Fast test execution")
        print("✓ Safe for development environments")
        print("✓ Consistent behavior simulation")

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n💥 TEST ERROR: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)