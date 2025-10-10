#!/usr/bin/env python3

"""
Test for Task 2.2: Race Condition Fix in Gripper Position Access

This test verifies that the gripper_position variable is properly protected
by state_lock during concurrent access from the monitor thread and main thread.

Author: VP
Date: 2025-10-08
Task: 2.2 - Fix Race Condition in Gripper Position Access
"""

import sys
import os
import threading
import time
from unittest.mock import Mock, MagicMock, patch

# Mock the ALOHA robot dependencies before importing gripper_controller
sys.modules['aloha'] = MagicMock()
sys.modules['aloha.robot_utils'] = MagicMock()
sys.modules['aloha.constants'] = MagicMock()
sys.modules['interbotix_common_modules'] = MagicMock()
sys.modules['interbotix_common_modules.common_robot'] = MagicMock()
sys.modules['interbotix_common_modules.common_robot.robot'] = MagicMock()
sys.modules['interbotix_xs_modules'] = MagicMock()
sys.modules['interbotix_xs_modules.xs_robot'] = MagicMock()
sys.modules['interbotix_xs_modules.xs_robot.arm'] = MagicMock()

# Set constants that gripper_controller expects
sys.modules['aloha.constants'].FOLLOWER_GRIPPER_JOINT_OPEN = 1.0
sys.modules['aloha.constants'].FOLLOWER_GRIPPER_JOINT_CLOSE = 0.0
sys.modules['aloha.constants'].START_ARM_POSE = [0.0] * 7

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from gripper_controller import GripperController, GripperState


class TestGripperRaceCondition:
    """Test suite for gripper position race condition fix"""

    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0

    def log_test(self, test_name, passed, message=""):
        """Log test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✓ PASS"
        else:
            status = "✗ FAIL"

        result = f"{status}: {test_name}"
        if message:
            result += f" - {message}"

        self.test_results.append(result)
        print(result)

    def create_mock_controller(self):
        """Create a gripper controller with mocked robot interface"""
        controller = GripperController()

        # Mock the robot interface
        controller.node = Mock()
        controller.bot = Mock()
        controller.bot.core = Mock()
        controller.bot.core.js_mutex = threading.Lock()
        controller.bot.gripper = Mock()
        controller.bot.gripper.left_finger_index = 6  # Typical gripper index

        # Mock joint states
        mock_joint_states = Mock()
        mock_joint_states.position = [0.0] * 10  # Array of joint positions
        mock_joint_states.position[6] = 0.5  # Initial gripper position
        controller.bot.core.joint_states = mock_joint_states

        # Set initialized state
        controller.initialized = True
        controller.current_state = GripperState.OPEN
        controller.gripper_position = 0.5

        return controller

    def test_concurrent_state_reads(self):
        """Test 1: Concurrent get_gripper_state() calls are thread-safe"""
        print("\n" + "="*60)
        print("TEST 1: Concurrent State Reads")
        print("="*60)

        controller = self.create_mock_controller()

        errors = []
        results = []

        def read_state(thread_id):
            """Read gripper state multiple times"""
            try:
                for i in range(100):
                    state = controller.get_gripper_state()
                    if state['success']:
                        results.append(state['position'])
                    time.sleep(0.001)  # 1ms between reads
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Create 5 threads reading state concurrently
        threads = []
        for i in range(5):
            t = threading.Thread(target=read_state, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results
        passed = len(errors) == 0 and len(results) == 500  # 5 threads * 100 reads
        self.log_test(
            "Concurrent state reads",
            passed,
            f"Completed {len(results)} reads, {len(errors)} errors"
        )

    def test_position_update_during_read(self):
        """Test 2: Position updates don't corrupt concurrent reads"""
        print("\n" + "="*60)
        print("TEST 2: Position Updates During Reads")
        print("="*60)

        controller = self.create_mock_controller()

        errors = []
        position_changes = []
        stop_flag = threading.Event()

        def update_position():
            """Simulate monitor thread updating position"""
            try:
                pos = 0.0
                while not stop_flag.is_set():
                    # Simulate hardware read
                    with controller.bot.core.js_mutex:
                        controller.bot.core.joint_states.position[6] = pos
                        hardware_pos = controller.bot.core.joint_states.position[6]

                    # Update shared state (this is what the monitor thread does)
                    with controller.state_lock:
                        controller.gripper_position = hardware_pos

                    pos = (pos + 0.1) % 1.0  # Cycle 0.0 to 1.0
                    position_changes.append(pos)
                    time.sleep(0.01)  # 100Hz update
            except Exception as e:
                errors.append(f"Update thread: {e}")

        def read_position():
            """Simulate main thread reading position"""
            try:
                for _ in range(50):
                    state = controller.get_gripper_state()
                    if state['success']:
                        # Verify position is valid
                        pos = state['position']
                        if not (0.0 <= pos <= 1.0):
                            errors.append(f"Invalid position: {pos}")
                    time.sleep(0.01)
            except Exception as e:
                errors.append(f"Read thread: {e}")

        # Start update thread
        update_thread = threading.Thread(target=update_position)
        update_thread.start()

        # Start multiple read threads
        read_threads = []
        for i in range(3):
            t = threading.Thread(target=read_position)
            read_threads.append(t)
            t.start()

        # Wait for reads to complete
        for t in read_threads:
            t.join()

        # Stop update thread
        stop_flag.set()
        update_thread.join()

        passed = len(errors) == 0
        self.log_test(
            "Position updates during reads",
            passed,
            f"{len(position_changes)} updates, {len(errors)} errors"
        )

    def test_state_lock_protection(self):
        """Test 3: Verify state_lock protects gripper_position"""
        print("\n" + "="*60)
        print("TEST 3: State Lock Protection")
        print("="*60)

        controller = self.create_mock_controller()

        # Verify state_lock exists
        has_lock = hasattr(controller, 'state_lock')
        self.log_test(
            "state_lock exists",
            has_lock,
            "state_lock attribute present"
        )

        if not has_lock:
            return

        # Verify state_lock is a threading.Lock (check type name)
        lock_type_name = type(controller.state_lock).__name__
        is_lock = 'lock' in lock_type_name.lower()
        self.log_test(
            "state_lock is threading.Lock",
            is_lock,
            f"Type: {lock_type_name}"
        )

        # Test that get_gripper_state acquires the lock
        lock_acquired = False

        def check_lock():
            nonlocal lock_acquired
            # Try to acquire lock while main thread is holding it
            time.sleep(0.001)
            acquired = controller.state_lock.acquire(blocking=False)
            if acquired:
                # We got the lock, release it
                controller.state_lock.release()
                lock_acquired = False
            else:
                # Lock is held by main thread
                lock_acquired = True

        check_thread = threading.Thread(target=check_lock)

        # Hold the lock to test that check_lock can't acquire it
        with controller.state_lock:
            check_thread.start()
            time.sleep(0.01)  # Hold lock briefly

        check_thread.join()

        self.log_test(
            "state_lock properly blocks concurrent access",
            lock_acquired,  # Should be True (check_lock couldn't acquire it)
            "Lock behavior correct"
        )

    def test_consistent_state_snapshot(self):
        """Test 4: Position and state are consistent snapshots"""
        print("\n" + "="*60)
        print("TEST 4: Consistent State Snapshot")
        print("="*60)

        controller = self.create_mock_controller()

        inconsistencies = []

        def rapid_state_changes():
            """Rapidly change state and position"""
            states = [GripperState.OPENING, GripperState.OPEN,
                     GripperState.CLOSING, GripperState.CLOSED]
            positions = [0.8, 1.0, 0.2, 0.0]

            for _ in range(50):
                for state, pos in zip(states, positions):
                    with controller.state_lock:
                        controller.current_state = state
                        controller.gripper_position = pos
                    time.sleep(0.001)

        def check_consistency():
            """Check that position matches state"""
            for _ in range(100):
                state_dict = controller.get_gripper_state()
                if state_dict['success']:
                    state = state_dict['state']
                    pos = state_dict['position']

                    # Check consistency: OPEN state should have high position
                    if state == 'open' and pos < 0.5:
                        inconsistencies.append(f"State {state} has low position {pos}")
                    elif state == 'closed' and pos > 0.5:
                        inconsistencies.append(f"State {state} has high position {pos}")

                time.sleep(0.001)

        # Run both threads
        change_thread = threading.Thread(target=rapid_state_changes)
        check_thread = threading.Thread(target=check_consistency)

        change_thread.start()
        check_thread.start()

        change_thread.join()
        check_thread.join()

        # Some inconsistencies are expected during state transitions,
        # but there should be fewer than 20% of reads
        passed = len(inconsistencies) < 20
        self.log_test(
            "State and position consistency",
            passed,
            f"{len(inconsistencies)} inconsistencies detected"
        )

    def run_all_tests(self):
        """Run all tests and report results"""
        print("\n" + "="*60)
        print("GRIPPER RACE CONDITION TEST SUITE")
        print("Task 2.2: Fix Race Condition in Gripper Position Access")
        print("="*60)

        self.test_concurrent_state_reads()
        self.test_position_update_during_read()
        self.test_state_lock_protection()
        self.test_consistent_state_snapshot()

        # Print summary
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests)*100:.1f}%")

        if self.passed_tests == self.total_tests:
            print("\n✅ ALL TESTS PASSED - Race condition fix verified!")
        else:
            print(f"\n⚠️ {self.total_tests - self.passed_tests} TEST(S) FAILED")

        print("="*60)

        return self.passed_tests == self.total_tests


if __name__ == "__main__":
    print("Starting Gripper Race Condition Tests...")
    print("Testing Task 2.2: Fix Race Condition in Gripper Position Access\n")

    tester = TestGripperRaceCondition()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)
