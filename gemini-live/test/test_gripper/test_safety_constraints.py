#!/usr/bin/env python3

"""
Test Safety Constraints and Validation for GripperController (Task 2.12)

Tests comprehensive safety constraints including:
- Max force monitoring and grip force estimation
- Current monitoring for object detection
- Timeout detection and limits
- Position range validation with safety margins
- Safety constraint checking before all movements
- Integration with safety validation systems

Test File: test/test_gripper/test_safety_constraints.py
Task: 2.12 (Safety Constraints & Validation - Phase 2)
"""

import sys
import os
import time
import math

# Add parent directory to path to import controllers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gripper_controller import GripperController, GripperSafetyConfig, SafetyValidationResult


class TestSafetyConstraints:
    """Test suite for safety constraints in GripperController"""

    def __init__(self):
        self.controller = None
        self.test_results = []

    def setup(self):
        """Initialize controller for testing"""
        print("Setting up GripperController for safety constraint tests...")
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

    def test_safety_config_initialization(self):
        """Test 1: Safety configuration initialization"""
        print("\n" + "="*60)
        print("TEST 1: Safety Configuration Initialization")
        print("="*60)

        # Test GripperSafetyConfig exists and has required attributes
        config = GripperSafetyConfig()

        required_attrs = [
            'max_current_limit', 'safe_current_limit', 'object_detection_current',
            'max_grip_force_estimate', 'safe_grip_force_estimate',
            'max_operation_timeout', 'movement_timeout', 'force_stabilization_timeout',
            'position_safety_margin', 'rapid_change_threshold',
            'current_monitor_enabled', 'current_spike_threshold',
            'object_present_threshold', 'object_crush_threshold',
            'emergency_current_threshold', 'emergency_force_threshold'
        ]

        for attr in required_attrs:
            self.assert_test(
                hasattr(config, attr),
                f"Safety config has {attr} attribute",
                expected="attribute exists",
                actual="exists" if hasattr(config, attr) else "missing"
            )

        # Test controller has safety config
        self.assert_test(
            hasattr(self.controller, 'safety_config'),
            "Controller has safety_config instance",
            expected="safety_config exists",
            actual="exists" if hasattr(self.controller, 'safety_config') else "missing"
        )

        # Test safety tracking variables
        safety_vars = [
            'current_readings', 'last_position_change_time', 'last_position',
            'safety_violations', 'object_detected', 'grip_force_estimate',
            'operation_start_time'
        ]

        for var in safety_vars:
            self.assert_test(
                hasattr(self.controller, var),
                f"Controller has {var} tracking variable",
                expected="variable exists",
                actual="exists" if hasattr(self.controller, var) else "missing"
            )

    def test_safety_constraint_checking_method(self):
        """Test 2: Safety constraint checking method"""
        print("\n" + "="*60)
        print("TEST 2: Safety Constraint Checking Method")
        print("="*60)

        # Test check_safety_constraints method exists
        self.assert_test(
            hasattr(self.controller, 'check_safety_constraints'),
            "check_safety_constraints method exists",
            expected="method exists",
            actual="exists" if hasattr(self.controller, 'check_safety_constraints') else "missing"
        )

        if hasattr(self.controller, 'check_safety_constraints'):
            # Test with valid parameters
            result = self.controller.check_safety_constraints("open", target_position=1.0)

            self.assert_test(
                isinstance(result, SafetyValidationResult),
                "Returns SafetyValidationResult object",
                expected="SafetyValidationResult",
                actual=type(result).__name__
            )

            required_result_attrs = ['valid', 'risk_level', 'message', 'constraints_violated', 'safety_metrics']
            for attr in required_result_attrs:
                self.assert_test(
                    hasattr(result, attr),
                    f"Safety result has {attr} attribute",
                    expected=f"{attr} exists",
                    actual="exists" if hasattr(result, attr) else "missing"
                )

    def test_position_safety_constraints(self):
        """Test 3: Position safety constraints"""
        print("\n" + "="*60)
        print("TEST 3: Position Safety Constraints")
        print("="*60)

        # Test valid positions (should pass)
        valid_positions = [0.0, 0.5, 1.0, -0.2, 1.2]  # Mix of normalized and absolute

        for pos in valid_positions:
            result = self.controller.check_safety_constraints("set_position", target_position=pos)
            self.assert_test(
                result.valid or result.risk_level in ["low", "medium"],
                f"Valid position {pos} passes safety check",
                expected="valid or low/medium risk",
                actual=f"valid={result.valid}, risk={result.risk_level}"
            )

        # Test positions outside safety margins (should trigger warnings)
        unsafe_positions = [-0.5, 2.0, -1.0, 3.0]  # Well outside safe ranges

        for pos in unsafe_positions:
            result = self.controller.check_safety_constraints("set_position", target_position=pos)
            self.assert_test(
                not result.valid or result.risk_level in ["medium", "high"],
                f"Unsafe position {pos} triggers safety warning",
                expected="invalid or medium/high risk",
                actual=f"valid={result.valid}, risk={result.risk_level}"
            )

    def test_current_monitoring_and_force_estimation(self):
        """Test 4: Current monitoring and force estimation"""
        print("\n" + "="*60)
        print("TEST 4: Current Monitoring and Force Estimation")
        print("="*60)

        # Test safe current readings
        safe_currents = [50, 100, 150, 200, 240]  # Within safe limits

        for current in safe_currents:
            result = self.controller.check_safety_constraints("monitor", current_reading=current)
            self.assert_test(
                result.valid,
                f"Safe current {current}mA passes safety check",
                expected="valid=True",
                actual=f"valid={result.valid}"
            )

            # Check force estimation
            self.assert_test(
                self.controller.grip_force_estimate >= 0,
                f"Force estimation calculated for {current}mA",
                expected="force >= 0",
                actual=f"force={self.controller.grip_force_estimate:.2f}N"
            )

        # Test object detection thresholds
        result = self.controller.check_safety_constraints("monitor", current_reading=130)
        self.assert_test(
            self.controller.object_detected,
            "Object detected above threshold (130mA > 120mA)",
            expected="object_detected=True",
            actual=f"object_detected={self.controller.object_detected}"
        )

        # Test high current warnings
        high_currents = [280, 320, 350, 400]  # Above safe limits

        for current in high_currents:
            result = self.controller.check_safety_constraints("monitor", current_reading=current)
            has_violations = len(result.constraints_violated) > 0
            self.assert_test(
                has_violations,
                f"High current {current}mA triggers safety violations",
                expected="violations > 0",
                actual=f"violations={len(result.constraints_violated)}"
            )

        # Test emergency current threshold
        result = self.controller.check_safety_constraints("monitor", current_reading=400)
        self.assert_test(
            result.risk_level == "critical",
            "Emergency current threshold triggers critical risk",
            expected="critical",
            actual=result.risk_level
        )

    def test_timeout_monitoring(self):
        """Test 5: Operation timeout monitoring"""
        print("\n" + "="*60)
        print("TEST 5: Operation Timeout Monitoring")
        print("="*60)

        # Start an operation
        self.controller.operation_start_time = time.time()

        # Test normal operation (should pass)
        result = self.controller.check_safety_constraints("open")
        self.assert_test(
            result.valid,
            "Fresh operation passes timeout check",
            expected="valid=True",
            actual=f"valid={result.valid}"
        )

        # Simulate long-running operation
        self.controller.operation_start_time = time.time() - 6.0  # 6 seconds ago

        result = self.controller.check_safety_constraints("open")
        has_timeout_violation = any("timeout" in v.lower() for v in result.constraints_violated)
        self.assert_test(
            has_timeout_violation,
            "Long operation triggers timeout violation",
            expected="timeout violation",
            actual=f"violations: {result.constraints_violated}"
        )

        # Simulate very long operation (emergency timeout)
        self.controller.operation_start_time = time.time() - 12.0  # 12 seconds ago

        result = self.controller.check_safety_constraints("open")
        self.assert_test(
            result.risk_level in ["critical", "high"],
            "Very long operation triggers high/critical risk",
            expected="high/critical risk",
            actual=result.risk_level
        )

    def test_rapid_position_change_detection(self):
        """Test 6: Rapid position change detection"""
        print("\n" + "="*60)
        print("TEST 6: Rapid Position Change Detection")
        print("="*60)

        # Set up initial position
        self.controller.gripper_position = 0.0
        self.controller.last_position_change_time = time.time() - 0.1  # 100ms ago

        # Test normal position change
        result = self.controller.check_safety_constraints("set_position", target_position=0.2)
        change_rate = result.safety_metrics.get("position_change_rate", 0)
        self.assert_test(
            change_rate < self.controller.safety_config.rapid_change_threshold,
            f"Normal position change rate {change_rate:.2f} rad/s within limits",
            expected=f"< {self.controller.safety_config.rapid_change_threshold}",
            actual=f"{change_rate:.2f}"
        )

        # Test rapid position change
        self.controller.last_position_change_time = time.time() - 0.01  # 10ms ago (very recent)
        result = self.controller.check_safety_constraints("set_position", target_position=1.0)

        rapid_change_detected = any("change rate" in v for v in result.constraints_violated)
        self.assert_test(
            rapid_change_detected or result.risk_level in ["medium", "high"],
            "Rapid position change detected or flagged as higher risk",
            expected="rapid change violation or medium/high risk",
            actual=f"violations: {len(result.constraints_violated)}, risk: {result.risk_level}"
        )

    def test_safety_status_method(self):
        """Test 7: Safety status reporting method"""
        print("\n" + "="*60)
        print("TEST 7: Safety Status Reporting")
        print("="*60)

        # Test get_safety_status method exists
        self.assert_test(
            hasattr(self.controller, 'get_safety_status'),
            "get_safety_status method exists",
            expected="method exists",
            actual="exists" if hasattr(self.controller, 'get_safety_status') else "missing"
        )

        if hasattr(self.controller, 'get_safety_status'):
            status = self.controller.get_safety_status()

            required_status_keys = [
                'safety_enabled', 'safety_config', 'current_metrics', 'operation_status'
            ]

            for key in required_status_keys:
                self.assert_test(
                    key in status,
                    f"Safety status contains '{key}'",
                    expected=f"'{key}' in status",
                    actual=f"Keys: {list(status.keys())}"
                )

            # Test safety_config sub-fields
            if 'safety_config' in status:
                config_keys = ['max_current_limit', 'safe_current_limit', 'movement_timeout', 'object_detection_enabled']
                for key in config_keys:
                    self.assert_test(
                        key in status['safety_config'],
                        f"Safety config contains '{key}'",
                        expected=f"'{key}' in config",
                        actual=f"Config keys: {list(status['safety_config'].keys())}"
                    )

    def test_integration_with_gripper_operations(self):
        """Test 8: Safety integration with gripper operations"""
        print("\n" + "="*60)
        print("TEST 8: Safety Integration with Operations")
        print("="*60)

        # Test open_gripper includes safety validation
        result = self.controller.open_gripper()

        self.assert_test(
            result.get("success", False),
            "open_gripper succeeds with safety validation",
            expected="success=True",
            actual=f"success={result.get('success')}"
        )

        # Check if safety status is included in result
        has_safety_info = "safety_status" in result or "safety_result" in result
        self.assert_test(
            has_safety_info,
            "open_gripper result includes safety information",
            expected="safety info in result",
            actual=f"Keys: {list(result.keys())}"
        )

        # Test with safety violations (mock extreme position)
        # This would be caught by parameter validation first, but test the safety layer
        extreme_position = 10.0  # Way outside valid range
        result = self.controller.set_gripper_position(extreme_position)

        # Should be caught by parameter validation or safety constraints
        safety_prevented = not result.get("success", True) or "safety" in result.get("error", "").lower()
        self.assert_test(
            safety_prevented,
            "Extreme position prevented by safety systems",
            expected="operation prevented",
            actual=f"success={result.get('success')}, error='{result.get('error', '')}'"
        )

    def test_error_state_safety_interaction(self):
        """Test 9: Safety interaction with ERROR state"""
        print("\n" + "="*60)
        print("TEST 9: Safety and ERROR State Interaction")
        print("="*60)

        # Test safety check with normal state
        result = self.controller.check_safety_constraints("open")
        normal_state_safe = result.valid or result.risk_level != "critical"

        self.assert_test(
            normal_state_safe,
            "Safety check passes in normal state",
            expected="valid or non-critical",
            actual=f"valid={result.valid}, risk={result.risk_level}"
        )

        # Simulate ERROR state
        from gripper_controller import GripperState
        with self.controller.state_lock:
            original_state = self.controller.current_state
            self.controller.current_state = GripperState.ERROR

        # Test safety check with ERROR state
        result = self.controller.check_safety_constraints("open")
        error_state_unsafe = not result.valid or result.risk_level == "critical"

        self.assert_test(
            error_state_unsafe,
            "Safety check fails in ERROR state",
            expected="invalid or critical",
            actual=f"valid={result.valid}, risk={result.risk_level}"
        )

        # Restore normal state
        with self.controller.state_lock:
            self.controller.current_state = original_state

    def test_current_readings_buffer(self):
        """Test 10: Current readings ring buffer"""
        print("\n" + "="*60)
        print("TEST 10: Current Readings Ring Buffer")
        print("="*60)

        # Test _update_current_readings method
        self.assert_test(
            hasattr(self.controller, '_update_current_readings'),
            "_update_current_readings method exists",
            expected="method exists",
            actual="exists" if hasattr(self.controller, '_update_current_readings') else "missing"
        )

        # Add some current readings
        test_currents = [100, 120, 110, 130, 125, 140, 135]
        for current in test_currents:
            self.controller._update_current_readings(current)

        self.assert_test(
            len(self.controller.current_readings) == len(test_currents),
            f"Current readings buffer stores {len(test_currents)} values",
            expected=len(test_currents),
            actual=len(self.controller.current_readings)
        )

        # Test buffer size limitation
        max_readings = self.controller.safety_config.current_avg_window * 2
        many_currents = list(range(100, 100 + max_readings + 5))  # More than max

        for current in many_currents:
            self.controller._update_current_readings(current)

        self.assert_test(
            len(self.controller.current_readings) <= max_readings,
            f"Current readings buffer limited to {max_readings}",
            expected=f"<= {max_readings}",
            actual=len(self.controller.current_readings)
        )

    def run_all_tests(self):
        """Run all safety constraint tests"""
        print("🧪 STARTING GRIPPER CONTROLLER SAFETY CONSTRAINT TESTS")
        print("Task 2.12: Add Safety Constraints and Validation Phase: 2")
        print("=" * 80)

        start_time = time.time()

        try:
            self.setup()

            # Run all test methods
            self.test_safety_config_initialization()
            self.test_safety_constraint_checking_method()
            self.test_position_safety_constraints()
            self.test_current_monitoring_and_force_estimation()
            self.test_timeout_monitoring()
            self.test_rapid_position_change_detection()
            self.test_safety_status_method()
            self.test_integration_with_gripper_operations()
            self.test_error_state_safety_interaction()
            self.test_current_readings_buffer()

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
            print("🎉 ALL SAFETY CONSTRAINT TESTS PASSED!")
            print("✅ Task 2.12 safety implementation successful")
        else:
            print(f"❌ {failed} test(s) failed - review implementation")

        return failed == 0


def main():
    """Main test execution"""
    tester = TestSafetyConstraints()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Safety constraint tests completed successfully")
        print("💡 GripperController now has comprehensive safety constraints")
        print("🔒 Force monitoring and object detection enabled")
        print("⏱️  Timeout protection and rapid change detection active")
        print("🛡️  Safety validation integrated with all operations")
    else:
        print("\n❌ Some safety constraint tests failed")
        print("🔧 Review the implementation and fix failing tests")

    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)