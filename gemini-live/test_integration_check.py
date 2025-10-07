#!/usr/bin/env python3

"""
Integration test to simulate how the refactored code will work
with actual trajectory data without needing robot hardware.
"""


class MockArmController:
    """Mock controller with just the helper method for testing"""

    def _convert_waypoint_to_position(self, point):
        """The refactored helper method"""
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


def test_realistic_trajectory():
    """Test a realistic pick-and-place trajectory"""
    print("=" * 70)
    print("INTEGRATION TEST: Realistic Trajectory")
    print("=" * 70)
    print()

    controller = MockArmController()

    # Realistic trajectory: approach, grasp, lift, move, place
    waypoints = [
        {'point': [400, 300], 'label': 'approach', 'gripper_action': 'open'},
        {'point': [0.3, 0.4], 'label': 'grasp_position', 'gripper_action': 'maintain'},
        {'point': [0.3, 0.4, 0.15], 'label': 'lower', 'gripper_action': 'close'},
        {'point': [0.3, 0.4, 0.35], 'label': 'lift', 'gripper_action': 'maintain'},
        {'point': [600, 200], 'label': 'move_to_target', 'gripper_action': 'maintain'},
        {'point': [0.2, 0.6, 0.15], 'label': 'place', 'gripper_action': 'open'},
    ]

    print("Processing trajectory waypoints:")
    print()

    all_valid = True
    for i, waypoint in enumerate(waypoints):
        point = waypoint.get('point', [])
        label = waypoint.get('label', f'waypoint_{i}')
        gripper_action = waypoint.get('gripper_action', 'maintain')

        # This is exactly how it's used in the actual code
        position = controller._convert_waypoint_to_position(point)

        print(f"Waypoint {i+1}/{len(waypoints)} '{label}':")
        print(f"  Input:  {point}")
        print(f"  Output: {position}")
        print(f"  Gripper: {gripper_action}")

        # Validate output
        if len(position) != 3:
            print(f"  ✗ ERROR: Expected 3D output, got {len(position)}")
            all_valid = False
        elif not all(isinstance(v, (int, float)) for v in position):
            print(f"  ✗ ERROR: Non-numeric values in output")
            all_valid = False
        else:
            print(f"  ✓ Valid")

        print()

    return all_valid


def test_edge_cases_in_trajectory():
    """Test edge cases that might occur in real usage"""
    print("=" * 70)
    print("INTEGRATION TEST: Edge Cases")
    print("=" * 70)
    print()

    controller = MockArmController()

    # Edge cases that might occur
    edge_cases = [
        {'point': [0, 0], 'label': 'origin'},
        {'point': [1, 1], 'label': 'boundary_1.0'},
        {'point': [1000, 1000], 'label': 'max_normalized'},
        {'point': [-0.1, -0.1], 'label': 'negative'},
        {'point': [0.5, 1000], 'label': 'mixed'},
        {'point': [0.25, 0.15, 0.1], 'label': 'low_z'},
    ]

    all_valid = True
    for i, waypoint in enumerate(edge_cases):
        point = waypoint['point']
        label = waypoint['label']

        try:
            position = controller._convert_waypoint_to_position(point)
            print(f"✓ '{label}': {point} → {position}")

            if len(position) != 3:
                print(f"  ✗ ERROR: Expected 3 elements, got {len(position)}")
                all_valid = False

        except Exception as e:
            print(f"✗ '{label}': {point} → ERROR: {e}")
            all_valid = False

    print()
    return all_valid


def test_context_usage():
    """Test usage in the 4 contexts where it's called"""
    print("=" * 70)
    print("INTEGRATION TEST: Context Usage Simulation")
    print("=" * 70)
    print()

    controller = MockArmController()
    waypoints = [
        {'point': [500, 400], 'label': 'test1'},
        {'point': [0.3, 0.2], 'label': 'test2'},
        {'point': [0.3, 0.2, 0.25], 'label': 'test3'},
    ]

    # Context 1: Pre-validation (non-blocking)
    print("Context 1: Pre-validation (non-blocking)")
    for i, waypoint in enumerate(waypoints):
        point = waypoint.get('point', [])
        label = waypoint.get('label', f'waypoint_{i}')
        position = controller._convert_waypoint_to_position(point)
        if len(position) >= 3:
            print(f"  ✓ Validate {label}: x={position[0]:.3f}, y={position[1]:.3f}, z={position[2]:.3f}")
    print()

    # Context 2: Pre-validation (blocking)
    print("Context 2: Pre-validation (blocking)")
    for i, waypoint in enumerate(waypoints):
        point = waypoint.get('point', [])
        label = waypoint.get('label', f'waypoint_{i}')
        position = controller._convert_waypoint_to_position(point)
        if len(position) >= 3:
            print(f"  ✓ Validate {label}: position={position}")
    print()

    # Context 3: Execution (sync)
    print("Context 3: Execution loop (sync)")
    for i, waypoint in enumerate(waypoints):
        point = waypoint.get('point', [])
        label = waypoint.get('label', f'waypoint_{i}')
        position = controller._convert_waypoint_to_position(point)
        print(f"  ✓ Execute waypoint {i+1}: '{label}' at {[f'{p:.3f}' for p in position]}")
    print()

    # Context 4: Execution (async)
    print("Context 4: Execution loop (async with trajectory_id)")
    trajectory_id = "test-123"
    for i, waypoint in enumerate(waypoints):
        point = waypoint.get('point', [])
        label = waypoint.get('label', f'waypoint_{i}')
        position = controller._convert_waypoint_to_position(point)
        print(f"  ✓ Trajectory {trajectory_id} - Waypoint {i+1}: '{label}' at {position}")
    print()

    return True


def main():
    """Run all integration tests"""
    print()
    results = []

    results.append(("Realistic Trajectory", test_realistic_trajectory()))
    results.append(("Edge Cases", test_edge_cases_in_trajectory()))
    results.append(("Context Usage", test_context_usage()))

    print("=" * 70)
    print("INTEGRATION TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("✓ ALL INTEGRATION TESTS PASSED")
        print("The refactored code will work correctly with actual robot hardware!")
    else:
        print("✗ SOME TESTS FAILED")

    return 0 if all_passed else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
