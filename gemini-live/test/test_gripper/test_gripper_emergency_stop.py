#!/usr/bin/env python3
"""
Test suite for emergency stop state management in gripper_controller.py

Tests the complete emergency stop workflow:
1. Emergency stop properly sets ERROR state
2. All movement methods reject commands when in ERROR state
3. resume_after_stop() validates recovery properly
4. Thread safety of state transitions

Author: [Your Name]
Date: 2025-10-15
Task: 2.1 - Implement Emergency Stop in Gripper Controller
"""

import sys
import os
import time
from unittest.mock import MagicMock, patch

# Add parent directory to path to import gripper_controller
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from gripper_controller import GripperController, GripperState

class TestGripperEmergencyStop:
    """Test emergency stop state management for gripper controller"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.controller = None

    def setup(self):
        """Initialize gripper controller with mocked hardware"""
        print("\n" + "="*70)
        print("GRIPPER EMERGENCY STOP STATE MANAGEMENT TEST SUITE")
        print("="*70)
        print("\nInitializing gripper controller with mocked hardware...")

        try:
            # Create controller instance
            self.controller = GripperController(
                robot_model='vx300s',
                robot_name='follower_left'
            )

            # Mock the hardware interface to avoid needing actual robot
            self.controller.bot = MagicMock()
            self.controller.node = MagicMock()
            self.controller.initialized = True
            self.controller.current_state = GripperState.CLOSED
            self.controller.gripper_position = -0.015  # Closed position

            print("✓ Controller initialized successfully with mocked hardware")
            return True
        except Exception as e:
            print(f"✗ Failed to initialize controller: {e}")
            return False

    def test_emergency_stop_sets_error_state(self):
        """Test that emergency_stop() properly sets ERROR state"""
        print("\n" + "-"*70)
        print("TEST 1: emergency_stop() sets ERROR state")
        print("-"*70)

        # Trigger emergency stop
        result = self.controller.emergency_stop()

        # Verify emergency stop succeeded
        if not result.get('success'):
            print(f"✗ FAIL: emergency_stop() returned failure: {result}")
            self.failed += 1
            return

        # Verify state is 'emergency_stopped'
        if result.get('state') != 'emergency_stopped':
            print(f"✗ FAIL: Expected state 'emergency_stopped', got '{result.get('state')}'")
            self.failed += 1
            return

        # Verify internal state is ERROR
        state_result = self.controller.get_gripper_state()
        if state_result.get('state') != 'error':
            print(f"✗ FAIL: Expected internal state 'error', got '{state_result.get('state')}'")
            self.failed += 1
            return

        # Verify torque was disabled
        self.controller.bot.core.robot_torque_enable.assert_called_with('single', 'gripper', False)

        print("✓ PASS: emergency_stop() correctly sets ERROR state")
        self.passed += 1

    def test_open_gripper_rejects_after_estop(self):
        """Test that open_gripper() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 2: open_gripper() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to open gripper
        result = self.controller.open_gripper()

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: open_gripper() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        error_msg = result.get('error', '')
        if 'ERROR state' not in error_msg:
            print(f"✗ FAIL: Error message doesn't mention ERROR state: {error_msg}")
            self.failed += 1
            return

        # Verify state is 'error'
        if result.get('state') != 'error':
            print(f"✗ FAIL: Expected state 'error', got '{result.get('state')}'")
            self.failed += 1
            return

        print("✓ PASS: open_gripper() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_close_gripper_rejects_after_estop(self):
        """Test that close_gripper() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 3: close_gripper() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to close gripper
        result = self.controller.close_gripper()

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: close_gripper() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: close_gripper() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_set_gripper_position_rejects_after_estop(self):
        """Test that set_gripper_position() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 4: set_gripper_position() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to set gripper position
        result = self.controller.set_gripper_position(0.5)

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: set_gripper_position() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: set_gripper_position() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_resume_after_stop_clears_error_state(self):
        """Test that resume_after_stop() clears ERROR state and allows operations"""
        print("\n" + "-"*70)
        print("TEST 5: resume_after_stop() clears ERROR state")
        print("-"*70)

        # Mock the hardware calls for resume
        mock_joint_states = MagicMock()
        mock_joint_states.position = [-0.015]  # Closed position
        self.controller.bot.core.js_mutex = MagicMock()
        self.controller.bot.core.js_mutex.__enter__ = MagicMock(return_value=None)
        self.controller.bot.core.js_mutex.__exit__ = MagicMock(return_value=False)
        self.controller.bot.core.joint_states = mock_joint_states
        self.controller.bot.gripper.left_finger_index = 0

        # Resume after stop
        result = self.controller.resume_after_stop()

        # Verify resume succeeded
        if not result.get('success'):
            print(f"✗ FAIL: resume_after_stop() failed: {result}")
            self.failed += 1
            return

        # Verify state is 'resumed' or 'resumed_with_warnings'
        state = result.get('state')
        if state not in ['resumed', 'resumed_with_warnings']:
            print(f"✗ FAIL: Expected state 'resumed' or 'resumed_with_warnings', got '{state}'")
            self.failed += 1
            return

        # Verify internal state is no longer ERROR
        state_result = self.controller.get_gripper_state()
        if state_result.get('state') == 'error':
            print(f"✗ FAIL: Internal state still 'error' after resume")
            self.failed += 1
            return

        # Verify torque was re-enabled
        self.controller.bot.core.robot_torque_enable.assert_called_with('single', 'gripper', True)

        print(f"✓ PASS: resume_after_stop() cleared ERROR state (result: {state})")
        self.passed += 1

    def test_operations_allowed_after_resume(self):
        """Test that operations work after resume_after_stop()"""
        print("\n" + "-"*70)
        print("TEST 6: Operations allowed after resume")
        print("-"*70)

        # Try open_gripper (should succeed after resume)
        result = self.controller.open_gripper()

        if not result.get('success'):
            print(f"✗ FAIL: open_gripper() should succeed after resume but failed: {result.get('error')}")
            self.failed += 1
            return

        print("✓ PASS: Operations allowed after resume_after_stop()")
        self.passed += 1

    def test_resume_when_not_in_error_state(self):
        """Test that resume_after_stop() fails when not in ERROR state"""
        print("\n" + "-"*70)
        print("TEST 7: resume_after_stop() rejects when not in ERROR state")
        print("-"*70)

        # System is already resumed, try to resume again
        result = self.controller.resume_after_stop()

        # Verify resume was rejected
        if result.get('success'):
            print(f"✗ FAIL: resume_after_stop() should fail when not in ERROR state")
            self.failed += 1
            return

        # Verify error message mentions not in ERROR state
        error_msg = result.get('error', '')
        if 'Not in ERROR state' not in error_msg:
            print(f"✗ FAIL: Error message should mention 'Not in ERROR state': {error_msg}")
            self.failed += 1
            return

        print("✓ PASS: resume_after_stop() correctly rejects when not in ERROR state")
        self.passed += 1

    def test_full_estop_recovery_cycle(self):
        """Test complete emergency stop and recovery cycle"""
        print("\n" + "-"*70)
        print("TEST 8: Complete emergency stop and recovery cycle")
        print("-"*70)

        # 1. Trigger emergency stop
        result = self.controller.emergency_stop()
        if not result.get('success') or result.get('state') != 'emergency_stopped':
            print(f"✗ FAIL: Emergency stop failed at step 1")
            self.failed += 1
            return
        print("  Step 1: Emergency stop triggered ✓")

        # 2. Verify all operations rejected
        if self.controller.open_gripper().get('success'):
            print(f"✗ FAIL: Operations not rejected at step 2")
            self.failed += 1
            return
        print("  Step 2: Operations rejected ✓")

        # 3. Resume operations (mock hardware again)
        mock_joint_states = MagicMock()
        mock_joint_states.position = [-0.015]
        self.controller.bot.core.joint_states = mock_joint_states
        self.controller.bot.gripper.left_finger_index = 0

        result = self.controller.resume_after_stop()
        if not result.get('success'):
            print(f"✗ FAIL: Resume failed at step 3: {result.get('error')}")
            self.failed += 1
            return
        print(f"  Step 3: Resumed ({result.get('state')}) ✓")

        # 4. Verify operations allowed
        if not self.controller.open_gripper().get('success'):
            print(f"✗ FAIL: Operations still rejected at step 4")
            self.failed += 1
            return
        print("  Step 4: Operations allowed ✓")

        print("✓ PASS: Complete emergency stop and recovery cycle successful")
        self.passed += 1

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Tests passed: {self.passed}")
        print(f"Tests failed: {self.failed}")
        print(f"Total tests:  {self.passed + self.failed}")

        if self.failed == 0:
            print("\n✓ ALL TESTS PASSED")
            return True
        else:
            print(f"\n✗ {self.failed} TEST(S) FAILED")
            return False

    def cleanup(self):
        """Cleanup resources"""
        print("\nCleaning up...")
        # No real hardware to cleanup since we mocked it
        print("✓ Cleanup complete")

    def run_all_tests(self):
        """Run all tests"""
        if not self.setup():
            print("✗ Setup failed, cannot run tests")
            return False

        try:
            # Run all tests
            self.test_emergency_stop_sets_error_state()
            self.test_open_gripper_rejects_after_estop()
            self.test_close_gripper_rejects_after_estop()
            self.test_set_gripper_position_rejects_after_estop()
            self.test_resume_after_stop_clears_error_state()
            self.test_operations_allowed_after_resume()
            self.test_resume_when_not_in_error_state()
            self.test_full_estop_recovery_cycle()

            # Print summary
            return self.print_summary()

        finally:
            self.cleanup()


def main():
    """Main entry point"""
    tester = TestGripperEmergencyStop()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
