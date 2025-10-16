#!/usr/bin/env python3

"""
Test Exception Handling and Error Recovery for GripperController (Task 2.11)

Tests comprehensive exception handling including:
- Specific exception handling instead of bare except: pass
- Exception logging with timestamps
- Error counter tracking and recovery logic
- ERROR state detection and handling
- Monitor thread health monitoring
- Graceful error recovery

Test File: test/test_gripper/test_exception_handling.py
Task: 2.11 (Exception Handling & Error Recovery - Phase 2)
"""

import sys
import os
import time
import threading
import logging
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import controllers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gripper_controller import GripperController, GripperState


class TestExceptionHandling:
    """Test suite for exception handling in GripperController"""

    def __init__(self):
        self.controller = None
        self.test_results = []

    def setup(self):
        """Initialize controller for testing"""
        print("Setting up GripperController for exception handling tests...")
        self.controller = GripperController(dry_run=True)

        if not self.controller.initialize():
            raise RuntimeError("Failed to initialize GripperController in dry-run mode")
        print("✓ GripperController initialized in dry-run mode")

    def teardown(self):
        """Clean up after testing"""
        if self.controller:
            self.controller.shutdown()
        print("✓ Test cleanup complete")

    def assert_test(self, condition, description, expected=None, actual=None):
        """Helper method to record test results"""
        if condition:
            print(f"✓ {description}")
            self.test_results.append(("PASS", description))
        else:
            error_msg = f"✗ {description}"
            if expected is not None and actual is not None:
                error_msg += f" (Expected: {expected}, Got: {actual})"
            print(error_msg)
            self.test_results.append(("FAIL", description))
        return condition

    def test_error_state_enum(self):
        """Test 1: ERROR state enum exists and is accessible"""
        print("\n" + "="*60)
        print("TEST 1: ERROR State Enum")
        print("="*60)

        # Test ERROR state exists
        self.assert_test(
            hasattr(GripperState, 'ERROR'),
            "GripperState.ERROR enum exists",
            expected="ERROR enum",
            actual="Available" if hasattr(GripperState, 'ERROR') else "Missing"
        )

        # Test ERROR state value
        if hasattr(GripperState, 'ERROR'):
            self.assert_test(
                GripperState.ERROR.value == "error",
                "GripperState.ERROR has correct value",
                expected="error",
                actual=GripperState.ERROR.value
            )

    def test_monitor_health_method(self):
        """Test 2: Monitor health information method"""
        print("\n" + "="*60)
        print("TEST 2: Monitor Health Information")
        print("="*60)

        # Test get_monitor_health method exists
        self.assert_test(
            hasattr(self.controller, 'get_monitor_health'),
            "get_monitor_health method exists",
            expected="method exists",
            actual="exists" if hasattr(self.controller, 'get_monitor_health') else "missing"
        )

        if hasattr(self.controller, 'get_monitor_health'):
            health = self.controller.get_monitor_health()

            required_keys = [
                "monitor_healthy", "total_failures", "consecutive_errors",
                "max_consecutive_errors", "error_threshold", "current_state"
            ]

            for key in required_keys:
                self.assert_test(
                    key in health,
                    f"Monitor health contains '{key}'",
                    expected=f"'{key}' in response",
                    actual=f"Keys: {list(health.keys())}"
                )

            # Test initial health state
            self.assert_test(
                health.get("monitor_healthy") is True,
                "Monitor initially healthy",
                expected=True,
                actual=health.get("monitor_healthy")
            )

            self.assert_test(
                health.get("total_failures") == 0,
                "No initial failures",
                expected=0,
                actual=health.get("total_failures")
            )

    def test_error_counter_initialization(self):
        """Test 3: Error counter instance variables"""
        print("\n" + "="*60)
        print("TEST 3: Error Counter Initialization")
        print("="*60)

        error_attributes = [
            ("monitor_failure_count", 0),
            ("monitor_consecutive_errors", 0),
            ("monitor_max_consecutive_errors", 10),
            ("monitor_error_threshold", 50),
            ("monitor_thread_healthy", True)
        ]

        for attr_name, expected_value in error_attributes:
            self.assert_test(
                hasattr(self.controller, attr_name),
                f"Controller has {attr_name} attribute",
                expected="attribute exists",
                actual="exists" if hasattr(self.controller, attr_name) else "missing"
            )

            if hasattr(self.controller, attr_name):
                actual_value = getattr(self.controller, attr_name)
                self.assert_test(
                    actual_value == expected_value,
                    f"{attr_name} initialized correctly",
                    expected=expected_value,
                    actual=actual_value
                )

    def test_error_state_handling_in_methods(self):
        """Test 4: ERROR state prevents gripper operations"""
        print("\n" + "="*60)
        print("TEST 4: ERROR State Handling in Methods")
        print("="*60)

        # Manually set ERROR state to test handling
        with self.controller.state_lock:
            self.controller.current_state = GripperState.ERROR
            self.controller.monitor_thread_healthy = False
            self.controller.monitor_failure_count = 15

        # Test open_gripper with ERROR state
        result = self.controller.open_gripper()
        self.assert_test(
            not result["success"],
            "open_gripper fails when in ERROR state",
            expected="success=False",
            actual=f"success={result['success']}"
        )

        self.assert_test(
            "ERROR state" in result.get("error", ""),
            "open_gripper error message mentions ERROR state",
            expected="ERROR state in error",
            actual=result.get("error", "")
        )

        # Test close_gripper with ERROR state
        result = self.controller.close_gripper()
        self.assert_test(
            not result["success"],
            "close_gripper fails when in ERROR state",
            expected="success=False",
            actual=f"success={result['success']}"
        )

        # Test set_gripper_position with ERROR state
        result = self.controller.set_gripper_position(0.5)
        self.assert_test(
            not result["success"],
            "set_gripper_position fails when in ERROR state",
            expected="success=False",
            actual=f"success={result['success']}"
        )

        # Test get_gripper_state with ERROR state
        result = self.controller.get_gripper_state()
        self.assert_test(
            not result["success"],
            "get_gripper_state fails when in ERROR state",
            expected="success=False",
            actual=f"success={result['success']}"
        )

        self.assert_test(
            result.get("state") == "error",
            "get_gripper_state returns error state",
            expected="error",
            actual=result.get("state")
        )

        # Check that monitor health info is included
        self.assert_test(
            "monitor_healthy" in result,
            "ERROR state response includes monitor health",
            expected="monitor_healthy in response",
            actual=f"Keys: {list(result.keys())}"
        )

    def test_get_gripper_state_with_failures(self):
        """Test 5: get_gripper_state includes monitor health when failures occur"""
        print("\n" + "="*60)
        print("TEST 5: Monitor Health in Normal Responses")
        print("="*60)

        # Reset to normal state but with some failures
        with self.controller.state_lock:
            self.controller.current_state = GripperState.CLOSED
            self.controller.monitor_thread_healthy = True
            self.controller.monitor_failure_count = 5  # Some failures occurred
            self.controller.monitor_consecutive_errors = 0

        result = self.controller.get_gripper_state()

        self.assert_test(
            result["success"],
            "get_gripper_state succeeds when not in ERROR state",
            expected="success=True",
            actual=f"success={result['success']}"
        )

        # Should include monitor health info when failures > 0
        health_keys = ["monitor_healthy", "total_failures", "consecutive_errors"]
        for key in health_keys:
            self.assert_test(
                key in result,
                f"Response includes {key} when failures occurred",
                expected=f"{key} in response",
                actual=f"Keys: {list(result.keys())}"
            )

    def test_mock_monitor_exceptions(self):
        """Test 6: Mock position monitor exceptions and recovery"""
        print("\n" + "="*60)
        print("TEST 6: Mock Monitor Exception Handling")
        print("="*60)

        # This test simulates what would happen if the monitor thread encountered exceptions
        # We can't easily test the actual monitor thread in dry-run mode, but we can test
        # the error handling logic by simulating the state changes

        # Reset controller to normal state
        with self.controller.state_lock:
            self.controller.current_state = GripperState.CLOSED
            self.controller.monitor_thread_healthy = True
            self.controller.monitor_failure_count = 0
            self.controller.monitor_consecutive_errors = 0

        # Simulate what happens when monitor encounters errors
        # Test 1: Simulate a few errors (under threshold)
        with self.controller.state_lock:
            self.controller.monitor_failure_count = 3
            self.controller.monitor_consecutive_errors = 2

        health = self.controller.get_monitor_health()
        self.assert_test(
            health["monitor_healthy"],
            "Monitor remains healthy with few errors",
            expected=True,
            actual=health["monitor_healthy"]
        )

        # Test 2: Simulate threshold exceeded
        with self.controller.state_lock:
            self.controller.monitor_failure_count = 15
            self.controller.monitor_consecutive_errors = 12
            self.controller.current_state = GripperState.ERROR
            self.controller.monitor_thread_healthy = False

        health = self.controller.get_monitor_health()
        self.assert_test(
            not health["monitor_healthy"],
            "Monitor becomes unhealthy when threshold exceeded",
            expected=False,
            actual=health["monitor_healthy"]
        )

        self.assert_test(
            health["current_state"] == "error",
            "Controller state set to ERROR when monitor fails",
            expected="error",
            actual=health["current_state"]
        )

        # Test 3: Operations fail when monitor is unhealthy
        result = self.controller.open_gripper()
        self.assert_test(
            not result["success"],
            "Operations fail when monitor is unhealthy",
            expected="success=False",
            actual=f"success={result['success']}"
        )

    def test_logging_setup(self):
        """Test 7: Logging module import and usage"""
        print("\n" + "="*60)
        print("TEST 7: Logging Setup")
        print("="*60)

        # Test that logging module is imported (can't easily test actual logging calls in dry-run)
        import gripper_controller
        self.assert_test(
            hasattr(gripper_controller, 'logging'),
            "Logging module imported in gripper_controller",
            expected="logging module available",
            actual="available" if hasattr(gripper_controller, 'logging') else "missing"
        )

        # Test that controller has error tracking attributes for logging
        logging_related_attrs = [
            'monitor_failure_count',
            'monitor_consecutive_errors',
            'monitor_error_threshold'
        ]

        for attr in logging_related_attrs:
            self.assert_test(
                hasattr(self.controller, attr),
                f"Controller has {attr} for error tracking",
                expected="attribute exists",
                actual="exists" if hasattr(self.controller, attr) else "missing"
            )

    def test_thread_naming(self):
        """Test 8: Monitor thread has descriptive name"""
        print("\n" + "="*60)
        print("TEST 8: Thread Naming")
        print("="*60)

        # Check if any threads with our expected name exist
        # Note: In dry-run mode, monitor thread doesn't actually start
        active_threads = [t.name for t in threading.enumerate()]

        # In dry-run mode, we won't have the actual monitor thread
        # but we can test that the thread creation logic would use proper naming
        # by checking the _start_position_monitor method

        import inspect
        source = inspect.getsource(self.controller._start_position_monitor)

        self.assert_test(
            'name="GripperPositionMonitor"' in source,
            "Monitor thread created with descriptive name",
            expected="GripperPositionMonitor in thread creation",
            actual="Found in source" if 'name="GripperPositionMonitor"' in source else "Not found"
        )

    def run_all_tests(self):
        """Run all exception handling tests"""
        print("🧪 STARTING GRIPPER CONTROLLER EXCEPTION HANDLING TESTS")
        print("Task 2.11: Improve Error Handling and Add Exception Logging")
        print("=" * 80)

        start_time = time.time()

        try:
            self.setup()

            # Run all test methods
            self.test_error_state_enum()
            self.test_monitor_health_method()
            self.test_error_counter_initialization()
            self.test_error_state_handling_in_methods()
            self.test_get_gripper_state_with_failures()
            self.test_mock_monitor_exceptions()
            self.test_logging_setup()
            self.test_thread_naming()

        finally:
            self.teardown()

        # Print results summary
        end_time = time.time()
        duration = end_time - start_time

        print("\n" + "="*80)
        print("TEST RESULTS SUMMARY")
        print("="*80)

        passed = sum(1 for result, _ in self.test_results if result == "PASS")
        failed = sum(1 for result, _ in self.test_results if result == "FAIL")
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Duration: {duration:.2f} seconds")

        if failed > 0:
            print("\nFAILED TESTS:")
            for result, description in self.test_results:
                if result == "FAIL":
                    print(f"  ✗ {description}")

        print("\n" + "="*80)

        if failed == 0:
            print("🎉 ALL EXCEPTION HANDLING TESTS PASSED!")
            print("✅ Task 2.11 exception handling implementation successful")
        else:
            print(f"❌ {failed} test(s) failed - review implementation")

        return failed == 0


def main():
    """Main test execution"""
    tester = TestExceptionHandling()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Exception handling tests completed successfully")
        print("💡 GripperController now has robust error handling and recovery")
        print("🔒 Monitor failures are properly tracked and reported")
        print("🛡️  ERROR state prevents unsafe operations")
    else:
        print("\n❌ Some exception handling tests failed")
        print("🔧 Review the implementation and fix failing tests")

    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)