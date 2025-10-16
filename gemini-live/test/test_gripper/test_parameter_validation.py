#!/usr/bin/env python3

"""
Test Parameter Validation for GripperController (Task 2.10)

Tests comprehensive parameter validation including:
- Type validation for all parameters
- Range validation for position values
- Validation for blocking parameter
- Clear error messages
- Warning when values are auto-corrected/clamped

Test File: test/test_gripper/test_parameter_validation.py
Task: 2.10 (Parameter Validation - Phase 2)
"""

import sys
import os
import time
import math

# Add parent directory to path to import controllers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from gripper_controller import GripperController


class TestParameterValidation:
    """Test suite for parameter validation in GripperController"""

    def __init__(self):
        self.controller = None
        self.test_results = []

    def setup(self):
        """Initialize controller for testing"""
        print("Setting up GripperController for parameter validation tests...")
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

    def test_blocking_parameter_validation(self):
        """Test 1: Validation of blocking parameter"""
        print("\n" + "="*60)
        print("TEST 1: Blocking Parameter Validation")
        print("="*60)

        # Test valid boolean values
        result = self.controller.open_gripper(blocking=True)
        self.assert_test(
            result["success"],
            "Valid blocking=True accepted",
            expected="success=True",
            actual=f"success={result['success']}"
        )

        result = self.controller.close_gripper(blocking=False)
        self.assert_test(
            result["success"],
            "Valid blocking=False accepted",
            expected="success=True",
            actual=f"success={result['success']}"
        )

        # Test invalid types
        invalid_blocking_values = [
            ("string", "True"),
            ("integer", 1),
            ("float", 1.0),
            ("None", None),
            ("list", []),
            ("dict", {}),
        ]

        for value_type, value in invalid_blocking_values:
            result = self.controller.open_gripper(blocking=value)
            self.assert_test(
                not result["success"] and "Parameter validation failed" in result["error"],
                f"Invalid blocking parameter ({value_type}: {value}) rejected with clear error",
                expected="validation error",
                actual=result.get("error", "no error")
            )

    def test_position_parameter_type_validation(self):
        """Test 2: Type validation for position parameter"""
        print("\n" + "="*60)
        print("TEST 2: Position Parameter Type Validation")
        print("="*60)

        # Test valid numeric types
        valid_positions = [
            ("float", 0.5),
            ("integer", 1),
            ("zero", 0),
            ("negative float", -0.1),
        ]

        for pos_type, position in valid_positions:
            result = self.controller.set_gripper_position(position)
            self.assert_test(
                result["success"],
                f"Valid position type ({pos_type}: {position}) accepted",
                expected="success=True",
                actual=f"success={result['success']}"
            )

        # Test invalid types
        invalid_positions = [
            ("string", "0.5"),
            ("boolean", True),
            ("None", None),
            ("list", [0.5]),
            ("dict", {"pos": 0.5}),
            ("complex", 1+2j),
        ]

        for pos_type, position in invalid_positions:
            result = self.controller.set_gripper_position(position)
            self.assert_test(
                not result["success"] and "Parameter validation failed" in result["error"],
                f"Invalid position type ({pos_type}: {position}) rejected with clear error",
                expected="validation error",
                actual=result.get("error", "no error")
            )

    def test_position_special_values(self):
        """Test 3: Special numeric values validation"""
        print("\n" + "="*60)
        print("TEST 3: Position Special Values Validation")
        print("="*60)

        # Test NaN
        result = self.controller.set_gripper_position(float('nan'))
        self.assert_test(
            not result["success"] and "NaN" in result["error"],
            "NaN position rejected with clear error message",
            expected="NaN error",
            actual=result.get("error", "no error")
        )

        # Test positive infinity
        result = self.controller.set_gripper_position(float('inf'))
        self.assert_test(
            not result["success"] and "infinity" in result["error"],
            "Positive infinity position rejected with clear error message",
            expected="infinity error",
            actual=result.get("error", "no error")
        )

        # Test negative infinity
        result = self.controller.set_gripper_position(float('-inf'))
        self.assert_test(
            not result["success"] and "infinity" in result["error"],
            "Negative infinity position rejected with clear error message",
            expected="infinity error",
            actual=result.get("error", "no error")
        )

    def test_position_range_validation_and_clamping(self):
        """Test 4: Position range validation and auto-clamping"""
        print("\n" + "="*60)
        print("TEST 4: Position Range Validation and Auto-Clamping")
        print("="*60)

        # Test normalized positions (should work)
        normalized_positions = [0.0, 0.25, 0.5, 0.75, 1.0]
        for pos in normalized_positions:
            result = self.controller.set_gripper_position(pos)
            self.assert_test(
                result["success"],
                f"Normalized position {pos} accepted",
                expected="success=True",
                actual=f"success={result['success']}"
            )

        # Test positions that should be clamped (above maximum)
        print("\n--- Testing positions above maximum (should be clamped) ---")
        high_positions = [2.0, 5.0, 10.0, 100.0]
        for pos in high_positions:
            # Capture printed output to verify warning
            result = self.controller.set_gripper_position(pos)
            self.assert_test(
                result["success"],
                f"High position {pos} accepted with clamping",
                expected="success=True with clamping",
                actual=f"success={result['success']}, clamped={result.get('clamped', False)}"
            )

            self.assert_test(
                result.get("clamped", False),
                f"High position {pos} marked as clamped in response",
                expected="clamped=True",
                actual=f"clamped={result.get('clamped', False)}"
            )

        # Test positions that should be clamped (below minimum)
        print("\n--- Testing positions below minimum (should be clamped) ---")
        low_positions = [-1.0, -2.0, -10.0]
        for pos in low_positions:
            result = self.controller.set_gripper_position(pos)
            self.assert_test(
                result["success"],
                f"Low position {pos} accepted with clamping",
                expected="success=True with clamping",
                actual=f"success={result['success']}, clamped={result.get('clamped', False)}"
            )

            self.assert_test(
                result.get("clamped", False),
                f"Low position {pos} marked as clamped in response",
                expected="clamped=True",
                actual=f"clamped={result.get('clamped', False)}"
            )

    def test_error_message_clarity(self):
        """Test 5: Error message clarity and informativeness"""
        print("\n" + "="*60)
        print("TEST 5: Error Message Clarity")
        print("="*60)

        # Test type error message contains helpful information
        result = self.controller.set_gripper_position("invalid")
        error_msg = result.get("error", "")

        required_info = [
            "Parameter validation failed",
            "position",
            "must be numeric",
            "float",
            "0.0-1.0",
            "radians"
        ]

        for info in required_info:
            self.assert_test(
                info in error_msg,
                f"Error message contains '{info}'",
                expected=f"'{info}' in error message",
                actual=f"Error: {error_msg}"
            )

        # Test blocking parameter error message
        result = self.controller.open_gripper(blocking="invalid")
        error_msg = result.get("error", "")

        blocking_required_info = [
            "Parameter validation failed",
            "blocking",
            "must be a boolean",
            "True",
            "False"
        ]

        for info in blocking_required_info:
            self.assert_test(
                info in error_msg,
                f"Blocking error message contains '{info}'",
                expected=f"'{info}' in error message",
                actual=f"Error: {error_msg}"
            )

    def test_combined_parameter_validation(self):
        """Test 6: Multiple invalid parameters"""
        print("\n" + "="*60)
        print("TEST 6: Combined Parameter Validation")
        print("="*60)

        # Test both invalid position and invalid blocking
        result = self.controller.set_gripper_position("invalid_position", blocking="invalid_blocking")

        # Should catch position error first (order matters)
        self.assert_test(
            not result["success"] and "position" in result["error"],
            "Multiple invalid parameters caught with position error first",
            expected="position validation error",
            actual=result.get("error", "no error")
        )

    def test_edge_case_positions(self):
        """Test 7: Edge case positions"""
        print("\n" + "="*60)
        print("TEST 7: Edge Case Positions")
        print("="*60)

        # Test very small numbers
        result = self.controller.set_gripper_position(1e-10)
        self.assert_test(
            result["success"],
            "Very small positive number accepted",
            expected="success=True",
            actual=f"success={result['success']}"
        )

        # Test very large numbers (should be clamped)
        result = self.controller.set_gripper_position(1e10)
        self.assert_test(
            result["success"] and result.get("clamped", False),
            "Very large number clamped successfully",
            expected="success=True, clamped=True",
            actual=f"success={result['success']}, clamped={result.get('clamped', False)}"
        )

        # Test precise boundary values
        # Note: These are mock values for dry-run mode
        close_pos = -0.37  # FOLLOWER_GRIPPER_JOINT_CLOSE
        open_pos = 1.4     # FOLLOWER_GRIPPER_JOINT_OPEN

        result = self.controller.set_gripper_position(close_pos)
        self.assert_test(
            result["success"],
            f"Exact close position {close_pos} accepted",
            expected="success=True",
            actual=f"success={result['success']}"
        )

        result = self.controller.set_gripper_position(open_pos)
        self.assert_test(
            result["success"],
            f"Exact open position {open_pos} accepted",
            expected="success=True",
            actual=f"success={result['success']}"
        )

    def run_all_tests(self):
        """Run all parameter validation tests"""
        print("🧪 STARTING GRIPPER CONTROLLER PARAMETER VALIDATION TESTS")
        print("Task 2.10: Add Parameter Validation Phase: 2")
        print("=" * 80)

        start_time = time.time()

        try:
            self.setup()

            # Run all test methods
            self.test_blocking_parameter_validation()
            self.test_position_parameter_type_validation()
            self.test_position_special_values()
            self.test_position_range_validation_and_clamping()
            self.test_error_message_clarity()
            self.test_combined_parameter_validation()
            self.test_edge_case_positions()

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
            print("🎉 ALL PARAMETER VALIDATION TESTS PASSED!")
            print("✅ Task 2.10 validation implementation successful")
        else:
            print(f"❌ {failed} test(s) failed - review implementation")

        return failed == 0


def main():
    """Main test execution"""
    tester = TestParameterValidation()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Parameter validation tests completed successfully")
        print("💡 GripperController now has comprehensive parameter validation")
    else:
        print("\n❌ Some parameter validation tests failed")
        print("🔧 Review the implementation and fix failing tests")

    return 0 if success else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)