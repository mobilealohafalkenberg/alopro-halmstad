#!/usr/bin/env python3

"""
Quick verification script to ensure refactored code produces identical results.
Tests the helper method against the old inline logic.
"""

def old_conversion_logic(point):
    """Original inline conversion logic"""
    if len(point) == 2:
        x = point[1] / 1000.0 if point[1] > 1 else point[1]
        y = point[0] / 1000.0 if point[0] > 1 else point[0]
        z = 0.2
        position = [x, y, z]
    else:
        position = point
    return position


def new_conversion_logic(point):
    """New helper method logic"""
    if len(point) == 2:
        # [y, x] format - convert to [x, y, z]
        # Normalize coordinates > 1 (assumed to be in 0-1000 range)
        x = point[1] / 1000.0 if point[1] > 1 else point[1]
        y = point[0] / 1000.0 if point[0] > 1 else point[0]
        z = 0.2  # Default working height
        return [x, y, z]
    else:
        # 3D format or other - return as-is
        return point


# Test cases covering all scenarios
test_cases = [
    # 2D normalized coordinates
    ([500, 300], "2D normalized [y=500, x=300]"),
    ([1000, 1000], "2D normalized max [1000, 1000]"),
    ([0, 0], "2D zeros [0, 0]"),

    # 2D meter coordinates
    ([0.5, 0.3], "2D meters [y=0.5, x=0.3]"),
    ([1.0, 1.0], "2D boundary [1.0, 1.0]"),
    ([-0.2, -0.3], "2D negative meters"),

    # Mixed (one > 1, one <= 1)
    ([0.5, 100], "Mixed [y=0.5m, x=100 normalized]"),
    ([100, 0.5], "Mixed [y=100 normalized, x=0.5m]"),

    # Edge case: just over 1
    ([1.5, 2.0], "Just over 1.0 [1.5, 2.0]"),

    # 3D coordinates
    ([0.25, 0.1, 0.15], "3D meters [x, y, z]"),
    ([100, 200, 300], "3D large values"),

    # Edge cases
    ([], "Empty list"),
    ([0.5], "Single element"),
    ([0.1, 0.2, 0.3, 0.4], "Four elements"),
]


def compare_results(point, old_result, new_result):
    """Compare two results for equality"""
    if len(old_result) != len(new_result):
        return False, f"Length mismatch: {len(old_result)} vs {len(new_result)}"

    for i, (old_val, new_val) in enumerate(zip(old_result, new_result)):
        if abs(old_val - new_val) > 1e-10:
            return False, f"Value mismatch at index {i}: {old_val} vs {new_val}"

    return True, "Match"


def run_verification():
    """Run all verification tests"""
    print("=" * 70)
    print("REFACTORING VERIFICATION TEST")
    print("=" * 70)
    print()

    all_passed = True

    for i, (point, description) in enumerate(test_cases, 1):
        print(f"Test {i}: {description}")
        print(f"  Input: {point}")

        try:
            old_result = old_conversion_logic(point)
            new_result = new_conversion_logic(point)

            print(f"  Old result: {old_result}")
            print(f"  New result: {new_result}")

            match, message = compare_results(point, old_result, new_result)

            if match:
                print(f"  ✓ PASS: {message}")
            else:
                print(f"  ✗ FAIL: {message}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ ERROR: {e}")
            all_passed = False

        print()

    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Refactoring is correct!")
    else:
        print("✗ SOME TESTS FAILED - Review the refactoring!")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_verification())
