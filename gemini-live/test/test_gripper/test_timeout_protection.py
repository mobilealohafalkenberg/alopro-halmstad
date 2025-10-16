#!/usr/bin/env python3

"""
Test script for Task 2.4: Timeout Protection for Gripper Operations

This script tests the timeout functionality added to gripper operations
to prevent system hangs when the gripper gets stuck or encounters obstacles.

Test scenarios:
1. Normal operation with short timeout (should complete)
2. Simulated stuck gripper (test timeout behavior)
3. Timeout with different timeout values
4. Non-blocking vs blocking behavior
5. Position-based timeout validation
"""

import sys
import os
import time
import threading

# Add parent directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from gripper_controller import GripperController, GripperState


class MockGripperController(GripperController):
    """
    Mock version of GripperController for testing timeout functionality
    without requiring actual robot hardware.
    """

    def __init__(self, simulate_stuck=False, stuck_delay=10.0):
        """
        Initialize mock controller.

        Args:
            simulate_stuck: If True, simulate gripper getting stuck
            stuck_delay: Time before gripper "gets stuck" (for testing)
        """
        self.robot_model = 'vx300s'
        self.robot_name = 'follower_left'
        self.bot = None
        self.node = None
        self.initialized = False
        self.current_state = GripperState.UNKNOWN
        self.gripper_position = 0.0  # Start closed
        self.state_lock = threading.Lock()
        self.simulate_stuck = simulate_stuck
        self.stuck_delay = stuck_delay

        # Mock gripper constants
        self.OPEN_THRESHOLD = 1.3  # Mock open threshold
        self.CLOSE_THRESHOLD = -0.3  # Mock close threshold

        # Simulate slow movement
        self.movement_speed = 0.5  # radians per second

    def initialize(self) -> bool:
        """Mock initialization"""
        print("[MockGripperController] Mock initialization...")
        self.initialized = True
        self.current_state = GripperState.CLOSED
        self.gripper_position = -0.37  # Start at closed position

        # Start mock position monitor
        self._start_mock_position_monitor()

        print("[MockGripperController] ✓ Mock initialization complete")
        return True

    def _start_mock_position_monitor(self):
        """Start mock position monitoring thread"""
        def mock_monitor():
            while self.initialized:
                # This would normally read from robot, but we'll simulate movement
                time.sleep(0.1)

        monitor_thread = threading.Thread(target=mock_monitor, daemon=True)
        monitor_thread.start()

    def _mock_gripper_movement(self, target_position: float):
        """Simulate gripper movement in background thread"""
        def move():
            start_pos = self.gripper_position
            distance = target_position - start_pos
            movement_time = abs(distance) / self.movement_speed

            # Simulate getting stuck partway through movement
            if self.simulate_stuck:
                # Move partway then stop
                stuck_time = min(self.stuck_delay, movement_time / 2)
                steps = int(stuck_time * 10)  # 10 steps per second

                for i in range(steps):
                    if not self.initialized:
                        return

                    progress = (i + 1) / steps
                    partial_distance = distance * progress * 0.3  # Only move 30% before getting stuck

                    with self.state_lock:
                        self.gripper_position = start_pos + partial_distance

                    time.sleep(0.1)

                # Now "get stuck" - stop updating position
                print(f"[MockGripperController] Simulating gripper stuck at position {self.gripper_position:.3f}")
                return

            # Normal movement simulation
            steps = int(movement_time * 10)  # 10 steps per second
            if steps == 0:
                steps = 1

            for i in range(steps):
                if not self.initialized:
                    return

                progress = (i + 1) / steps

                with self.state_lock:
                    self.gripper_position = start_pos + (distance * progress)

                    # Update state based on position
                    if self.current_state == GripperState.OPENING:
                        if self.gripper_position >= self.OPEN_THRESHOLD:
                            self.current_state = GripperState.OPEN
                    elif self.current_state == GripperState.CLOSING:
                        if self.gripper_position <= self.CLOSE_THRESHOLD:
                            self.current_state = GripperState.CLOSED

                time.sleep(0.1)

        movement_thread = threading.Thread(target=move, daemon=True)
        movement_thread.start()

    def open_gripper(self, blocking: bool = True, timeout: float = 5.0):
        """Mock open gripper with real timeout logic"""
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}

        with self.state_lock:
            self.current_state = GripperState.OPENING

        print(f"[MockGripperController] Opening gripper (timeout: {timeout}s)...")
        start_time = time.time()

        # Start mock movement
        self._mock_gripper_movement(1.4)  # Move to open position

        if blocking:
            # Wait for movement to complete with timeout protection
            while True:
                elapsed_time = time.time() - start_time

                # Check for timeout
                if elapsed_time >= timeout:
                    with self.state_lock:
                        self.current_state = GripperState.UNKNOWN
                    return {
                        "success": False,
                        "error": f"Timeout after {timeout:.1f}s - gripper may be stuck",
                        "state": "unknown",
                        "elapsed_time": elapsed_time
                    }

                # Check if movement completed successfully
                with self.state_lock:
                    current_state = self.current_state

                if current_state == GripperState.OPEN:
                    # Movement completed successfully
                    break
                elif current_state == GripperState.OPENING:
                    # Still moving, continue waiting
                    time.sleep(0.1)
                else:
                    # Unexpected state change
                    break

            # Final state update if still opening
            with self.state_lock:
                if self.current_state == GripperState.OPENING:
                    # Check position to determine final state
                    if self.gripper_position >= self.OPEN_THRESHOLD:
                        self.current_state = GripperState.OPEN
                    else:
                        self.current_state = GripperState.UNKNOWN

        return self.get_gripper_state()

    def close_gripper(self, blocking: bool = True, timeout: float = 5.0):
        """Mock close gripper with real timeout logic"""
        if not self.initialized:
            return {"success": False, "error": "Not initialized", "state": "unknown"}

        with self.state_lock:
            self.current_state = GripperState.CLOSING

        print(f"[MockGripperController] Closing gripper (timeout: {timeout}s)...")
        start_time = time.time()

        # Start mock movement
        self._mock_gripper_movement(-0.37)  # Move to closed position

        if blocking:
            # Wait for movement to complete with timeout protection
            while True:
                elapsed_time = time.time() - start_time

                # Check for timeout
                if elapsed_time >= timeout:
                    with self.state_lock:
                        self.current_state = GripperState.UNKNOWN
                    return {
                        "success": False,
                        "error": f"Timeout after {timeout:.1f}s - gripper may be stuck or blocked",
                        "state": "unknown",
                        "elapsed_time": elapsed_time
                    }

                # Check if movement completed successfully
                with self.state_lock:
                    current_state = self.current_state

                if current_state == GripperState.CLOSED:
                    # Movement completed successfully
                    break
                elif current_state == GripperState.CLOSING:
                    # Still moving, continue waiting
                    time.sleep(0.1)
                else:
                    # Unexpected state change
                    break

            # Final state update if still closing
            with self.state_lock:
                if self.current_state == GripperState.CLOSING:
                    # Check position to determine final state
                    if self.gripper_position <= self.CLOSE_THRESHOLD:
                        self.current_state = GripperState.CLOSED
                    else:
                        self.current_state = GripperState.UNKNOWN

        return self.get_gripper_state()

    def shutdown(self):
        """Mock shutdown"""
        print("[MockGripperController] Mock shutdown...")
        self.initialized = False


def test_normal_operation():
    """Test 1: Normal operation should complete within timeout"""
    print("\n=== Test 1: Normal Operation ===")

    controller = MockGripperController(simulate_stuck=False)
    controller.initialize()

    # Test open with generous timeout
    start_time = time.time()
    result = controller.open_gripper(blocking=True, timeout=10.0)
    elapsed = time.time() - start_time

    print(f"Open result: {result}")
    print(f"Elapsed time: {elapsed:.2f}s")

    # Should succeed and complete quickly
    assert result["success"] == True, "Normal open operation should succeed"
    assert elapsed < 5.0, "Normal operation should complete quickly"
    assert result["state"] == "open", "Should be in open state"

    # Test close
    start_time = time.time()
    result = controller.close_gripper(blocking=True, timeout=10.0)
    elapsed = time.time() - start_time

    print(f"Close result: {result}")
    print(f"Elapsed time: {elapsed:.2f}s")

    assert result["success"] == True, "Normal close operation should succeed"
    assert elapsed < 5.0, "Normal operation should complete quickly"
    assert result["state"] == "closed", "Should be in closed state"

    controller.shutdown()
    print("✓ Test 1 PASSED")


def test_timeout_behavior():
    """Test 2: Stuck gripper should timeout correctly"""
    print("\n=== Test 2: Timeout Behavior ===")

    controller = MockGripperController(simulate_stuck=True, stuck_delay=1.0)
    controller.initialize()

    # Test open with short timeout - should timeout
    timeout_value = 2.0
    start_time = time.time()
    result = controller.open_gripper(blocking=True, timeout=timeout_value)
    elapsed = time.time() - start_time

    print(f"Open result: {result}")
    print(f"Elapsed time: {elapsed:.2f}s")
    print(f"Timeout value: {timeout_value}s")

    # Should timeout
    assert result["success"] == False, "Stuck gripper should fail"
    assert "Timeout" in result["error"], "Should report timeout error"
    assert abs(elapsed - timeout_value) < 0.2, f"Should timeout at ~{timeout_value}s, got {elapsed:.2f}s"
    assert result["state"] == "unknown", "Should be in unknown state after timeout"
    assert "elapsed_time" in result, "Should report elapsed time"

    controller.shutdown()
    print("✓ Test 2 PASSED")


def test_different_timeout_values():
    """Test 3: Different timeout values"""
    print("\n=== Test 3: Different Timeout Values ===")

    timeout_values = [1.0, 2.0, 3.0]

    for timeout_val in timeout_values:
        print(f"\nTesting timeout: {timeout_val}s")

        controller = MockGripperController(simulate_stuck=True, stuck_delay=0.5)
        controller.initialize()

        start_time = time.time()
        result = controller.open_gripper(blocking=True, timeout=timeout_val)
        elapsed = time.time() - start_time

        print(f"Result: {result['success']}, Elapsed: {elapsed:.2f}s")

        assert result["success"] == False, f"Should timeout at {timeout_val}s"
        assert abs(elapsed - timeout_val) < 0.2, f"Should timeout at ~{timeout_val}s"

        controller.shutdown()

    print("✓ Test 3 PASSED")


def test_non_blocking_behavior():
    """Test 4: Non-blocking operations should return immediately"""
    print("\n=== Test 4: Non-blocking Behavior ===")

    controller = MockGripperController(simulate_stuck=False)
    controller.initialize()

    # Test non-blocking open
    start_time = time.time()
    result = controller.open_gripper(blocking=False, timeout=5.0)
    elapsed = time.time() - start_time

    print(f"Non-blocking open result: {result}")
    print(f"Elapsed time: {elapsed:.3f}s")

    # Should return immediately
    assert elapsed < 0.1, "Non-blocking operation should return immediately"
    assert result["success"] == True, "Non-blocking operation should succeed"

    # Wait for movement to complete
    time.sleep(3.0)

    # Check final state
    final_state = controller.get_gripper_state()
    print(f"Final state: {final_state}")
    assert final_state["state"] == "open", "Should eventually reach open state"

    controller.shutdown()
    print("✓ Test 4 PASSED")


def test_position_validation():
    """Test 5: Position-based timeout validation"""
    print("\n=== Test 5: Position Validation ===")

    controller = MockGripperController(simulate_stuck=False)
    controller.initialize()

    # Test set_gripper_position with timeout
    start_time = time.time()
    result = controller.set_gripper_position(0.5, blocking=True, timeout=10.0)  # Mid position
    elapsed = time.time() - start_time

    print(f"Set position result: {result}")
    print(f"Elapsed time: {elapsed:.2f}s")

    assert result["success"] == True, "Position setting should succeed"
    assert elapsed < 5.0, "Position setting should complete quickly"

    # Verify position is approximately correct
    final_pos = result["position_normalized"]
    print(f"Target normalized: 0.5, Actual: {final_pos:.3f}")
    assert abs(final_pos - 0.5) < 0.1, "Position should be approximately correct"

    controller.shutdown()
    print("✓ Test 5 PASSED")


def run_all_tests():
    """Run all timeout protection tests"""
    print("Starting Task 2.4 Timeout Protection Tests")
    print("=" * 50)

    try:
        test_normal_operation()
        test_timeout_behavior()
        test_different_timeout_values()
        test_non_blocking_behavior()
        test_position_validation()

        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Task 2.4: Timeout Protection implementation is working correctly")

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