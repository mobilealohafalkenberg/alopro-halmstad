#!/usr/bin/env python3
"""
Test script for set_speed() parameter validation.
Validates that invalid parameters are properly rejected.
"""

import sys
from arm_controller import ArmController

def test_valid_inputs():
    """Test that valid inputs are accepted."""
    print("\n" + "=" * 60)
    print("TEST 1: Valid Inputs")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        (2.0, None, "Default moving_time only"),
        (1.5, 0.3, "Normal moving_time and accel_time"),
        (0.5, 0.1, "Fast movement"),
        (5.0, 1.0, "Slow movement"),
        (10.0, 5.0, "Maximum allowed values"),
        (0.01, None, "Minimum moving_time"),
    ]

    for moving_time, accel_time, description in test_cases:
        try:
            print(f"\n[Test] {description}: moving_time={moving_time}, accel_time={accel_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✓ PASS - Accepted valid input")
        except ValueError as e:
            print(f"  ✗ FAIL - Rejected valid input: {e}")
            sys.exit(1)


def test_invalid_moving_time():
    """Test that invalid moving_time values are rejected."""
    print("\n" + "=" * 60)
    print("TEST 2: Invalid moving_time Values")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        (0.0, None, "Zero moving_time"),
        (-1.0, None, "Negative moving_time"),
        (-0.5, None, "Small negative moving_time"),
        (0.001, None, "Below minimum (0.01s)"),
        (15.0, None, "Above maximum (10s)"),
        (100.0, None, "Far above maximum"),
    ]

    for moving_time, accel_time, description in test_cases:
        try:
            print(f"\n[Test] {description}: moving_time={moving_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✗ FAIL - Accepted invalid input (should have raised ValueError)")
            sys.exit(1)
        except ValueError as e:
            print(f"  ✓ PASS - Correctly rejected: {e}")


def test_invalid_accel_time():
    """Test that invalid accel_time values are rejected."""
    print("\n" + "=" * 60)
    print("TEST 3: Invalid accel_time Values")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        (2.0, 0.0, "Zero accel_time"),
        (2.0, -0.5, "Negative accel_time"),
        (2.0, -1.0, "Large negative accel_time"),
        (2.0, 0.001, "Below minimum (0.01s)"),
        (2.0, 6.0, "Above maximum (5s)"),
        (2.0, 10.0, "Far above maximum"),
    ]

    for moving_time, accel_time, description in test_cases:
        try:
            print(f"\n[Test] {description}: accel_time={accel_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✗ FAIL - Accepted invalid input (should have raised ValueError)")
            sys.exit(1)
        except ValueError as e:
            print(f"  ✓ PASS - Correctly rejected: {e}")


def test_accel_time_relationship():
    """Test that accel_time >= moving_time is rejected."""
    print("\n" + "=" * 60)
    print("TEST 4: accel_time vs moving_time Relationship")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        (2.0, 2.0, "accel_time equals moving_time"),
        (2.0, 2.5, "accel_time greater than moving_time"),
        (1.0, 1.0, "Both equal at 1 second"),
        (0.5, 0.6, "accel_time slightly greater"),
        (2.0, 3.0, "accel_time much greater"),
    ]

    for moving_time, accel_time, description in test_cases:
        try:
            print(f"\n[Test] {description}: moving={moving_time}, accel={accel_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✗ FAIL - Accepted invalid relationship (should have raised ValueError)")
            sys.exit(1)
        except ValueError as e:
            print(f"  ✓ PASS - Correctly rejected: {e}")


def test_edge_cases():
    """Test edge cases and boundary values."""
    print("\n" + "=" * 60)
    print("TEST 5: Edge Cases")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    # Valid edge cases
    valid_cases = [
        (0.01, 0.009, "Minimum moving_time with slightly smaller accel_time"),
        (10.0, 4.99, "Maximum moving_time with just under max accel_time"),
        (5.0, 4.99, "accel_time just below moving_time"),
    ]

    print("\n[Valid Edge Cases]")
    for moving_time, accel_time, description in valid_cases:
        try:
            print(f"\n[Test] {description}: moving={moving_time}, accel={accel_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✓ PASS - Accepted valid edge case")
        except ValueError as e:
            print(f"  ✗ FAIL - Rejected valid edge case: {e}")
            sys.exit(1)

    # Invalid edge cases
    invalid_cases = [
        (0.01, 0.01, "Both at minimum (equal)"),
        (10.0, 5.0, "Max moving_time, max accel_time (equal boundary)"),
    ]

    print("\n[Invalid Edge Cases]")
    for moving_time, accel_time, description in invalid_cases:
        try:
            print(f"\n[Test] {description}: moving={moving_time}, accel={accel_time}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✗ FAIL - Accepted invalid edge case")
            sys.exit(1)
        except ValueError as e:
            print(f"  ✓ PASS - Correctly rejected: {e}")


def test_error_messages():
    """Test that error messages are clear and informative."""
    print("\n" + "=" * 60)
    print("TEST 6: Error Message Quality")
    print("=" * 60)

    arm = ArmController(enable_safety=True, dry_run=True)
    arm.initialize()

    test_cases = [
        (-1.0, None, "negative moving_time", ["positive", "-1"]),
        (0.0, None, "zero moving_time", ["positive", "0"]),
        (15.0, None, "excessive moving_time", ["maximum", "10", "15"]),
        (2.0, -0.5, "negative accel_time", ["positive", "-0.5"]),
        (2.0, 2.5, "accel_time >= moving_time", ["less than", "2.0", "2.5"]),
    ]

    for moving_time, accel_time, description, expected_keywords in test_cases:
        try:
            print(f"\n[Test] {description}")
            arm.set_speed(moving_time, accel_time)
            print(f"  ✗ FAIL - No error raised")
            sys.exit(1)
        except ValueError as e:
            error_msg = str(e).lower()
            missing_keywords = [kw for kw in expected_keywords if kw.lower() not in error_msg]

            if missing_keywords:
                print(f"  ✗ FAIL - Error message missing keywords: {missing_keywords}")
                print(f"     Got: {e}")
                sys.exit(1)
            else:
                print(f"  ✓ PASS - Clear error message: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("SET_SPEED() VALIDATION TEST SUITE")
    print("=" * 60)

    try:
        test_valid_inputs()
        test_invalid_moving_time()
        test_invalid_accel_time()
        test_accel_time_relationship()
        test_edge_cases()
        test_error_messages()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nValidation Summary:")
        print("✓ Valid inputs accepted correctly")
        print("✓ Invalid moving_time values rejected")
        print("✓ Invalid accel_time values rejected")
        print("✓ accel_time >= moving_time relationship enforced")
        print("✓ Edge cases handled properly")
        print("✓ Error messages are clear and informative")
        print("\nParameter validation prevents robot malfunction from invalid configurations!")

    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
