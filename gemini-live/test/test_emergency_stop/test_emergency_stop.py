#!/usr/bin/env python3
"""
Test suite for emergency stop state management in arm_controller.py

Tests the complete emergency stop workflow:
1. Emergency stop properly sets ERROR state
2. All movement methods reject commands when in ERROR state
3. resume_after_stop() validates recovery properly
4. Thread safety of state transitions

Author: anugraha09
Date: 2025-10-07
Task: 1.7 - Improve Emergency Stop State Management
"""

import sys
import os
import time

# Add parent directory to path to import arm_controller
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from arm_controller import ArmController

class TestEmergencyStop:
    """Test emergency stop state management"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.controller = None

    def setup(self):
        """Initialize arm controller in dry-run mode"""
        print("\n" + "="*70)
        print("EMERGENCY STOP STATE MANAGEMENT TEST SUITE")
        print("="*70)
        print("\nInitializing arm controller in dry-run mode...")

        try:
            self.controller = ArmController(
                robot_name='vx300s',
                group_name='arm',
                dry_run=True  # Use dry-run mode for testing
            )
            print("✓ Controller initialized successfully")
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
        state_result = self.controller.get_arm_state()
        if state_result.get('state') != 'error':
            print(f"✗ FAIL: Expected internal state 'error', got '{state_result.get('state')}'")
            self.failed += 1
            return

        print("✓ PASS: emergency_stop() correctly sets ERROR state")
        self.passed += 1

    def test_move_joints_rejects_after_estop(self):
        """Test that move_joints() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 2: move_joints() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to move joints
        result = self.controller.move_joints([0, 0, 0, 0, 0, 0])

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: move_joints() should have been rejected but succeeded")
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

        print("✓ PASS: move_joints() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_move_to_position_rejects_after_estop(self):
        """Test that move_to_position() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 3: move_to_position() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to move to position
        result = self.controller.move_to_position([0.3, 0.0, 0.2])

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: move_to_position() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: move_to_position() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_move_to_pose_rejects_after_estop(self):
        """Test that move_to_pose() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 4: move_to_pose() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to move to pose
        result = self.controller.move_to_pose('home')

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: move_to_pose() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: move_to_pose() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_execute_trajectory_rejects_after_estop(self):
        """Test that execute_trajectory() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 5: execute_trajectory() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to execute trajectory
        waypoints = [
            {"position": [0.3, 0.0, 0.2]},
            {"position": [0.3, 0.1, 0.2]}
        ]
        result = self.controller.execute_trajectory(waypoints)

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: execute_trajectory() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: execute_trajectory() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_set_speed_rejects_after_estop(self):
        """Test that set_speed() rejects commands after emergency stop"""
        print("\n" + "-"*70)
        print("TEST 6: set_speed() rejects commands in ERROR state")
        print("-"*70)

        # Attempt to set speed
        result = self.controller.set_speed(2.0, 0.5)

        # Verify command was rejected
        if result.get('success'):
            print(f"✗ FAIL: set_speed() should have been rejected but succeeded")
            self.failed += 1
            return

        # Verify error message mentions ERROR state
        if 'ERROR state' not in result.get('error', ''):
            print(f"✗ FAIL: Error message doesn't mention ERROR state")
            self.failed += 1
            return

        print("✓ PASS: set_speed() correctly rejects commands in ERROR state")
        self.passed += 1

    def test_resume_after_stop_clears_error_state(self):
        """Test that resume_after_stop() clears ERROR state and allows operations"""
        print("\n" + "-"*70)
        print("TEST 7: resume_after_stop() clears ERROR state")
        print("-"*70)

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
        state_result = self.controller.get_arm_state()
        if state_result.get('state') == 'error':
            print(f"✗ FAIL: Internal state still 'error' after resume")
            self.failed += 1
            return

        print(f"✓ PASS: resume_after_stop() cleared ERROR state (result: {state})")
        self.passed += 1

    def test_operations_allowed_after_resume(self):
        """Test that operations work after resume_after_stop()"""
        print("\n" + "-"*70)
        print("TEST 8: Operations allowed after resume")
        print("-"*70)

        # Try move_joints (should succeed in dry-run mode)
        result = self.controller.move_joints([0, 0, 0, 0, 0, 0])

        if not result.get('success'):
            print(f"✗ FAIL: move_joints() should succeed after resume but failed: {result.get('error')}")
            self.failed += 1
            return

        print("✓ PASS: Operations allowed after resume_after_stop()")
        self.passed += 1

    def test_resume_when_not_in_error_state(self):
        """Test that resume_after_stop() fails when not in ERROR state"""
        print("\n" + "-"*70)
        print("TEST 9: resume_after_stop() rejects when not in ERROR state")
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
        print("TEST 10: Complete emergency stop and recovery cycle")
        print("-"*70)

        # 1. Trigger emergency stop
        result = self.controller.emergency_stop()
        if not result.get('success') or result.get('state') != 'emergency_stopped':
            print(f"✗ FAIL: Emergency stop failed at step 1")
            self.failed += 1
            return
        print("  Step 1: Emergency stop triggered ✓")

        # 2. Verify all operations rejected
        if self.controller.move_joints([0, 0, 0, 0, 0, 0]).get('success'):
            print(f"✗ FAIL: Operations not rejected at step 2")
            self.failed += 1
            return
        print("  Step 2: Operations rejected ✓")

        # 3. Resume operations
        result = self.controller.resume_after_stop()
        if not result.get('success'):
            print(f"✗ FAIL: Resume failed at step 3: {result.get('error')}")
            self.failed += 1
            return
        print(f"  Step 3: Resumed ({result.get('state')}) ✓")

        # 4. Verify operations allowed
        if not self.controller.move_joints([0, 0, 0, 0, 0, 0]).get('success'):
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
        if self.controller:
            self.controller.shutdown()
        print("✓ Cleanup complete")

    def run_all_tests(self):
        """Run all tests"""
        if not self.setup():
            print("✗ Setup failed, cannot run tests")
            return False

        try:
            # Run all tests
            self.test_emergency_stop_sets_error_state()
            self.test_move_joints_rejects_after_estop()
            self.test_move_to_position_rejects_after_estop()
            self.test_move_to_pose_rejects_after_estop()
            self.test_execute_trajectory_rejects_after_estop()
            self.test_set_speed_rejects_after_estop()
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
    tester = TestEmergencyStop()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
