#!/usr/bin/env python3

"""
Unit tests for the waypoint conversion helper method in ArmController.
Tests the _convert_waypoint_to_position() method with various input formats.
"""

import unittest
from arm_controller import ArmController


class TestWaypointConversion(unittest.TestCase):
    """Unit tests for _convert_waypoint_to_position() helper method"""

    def setUp(self):
        """Set up test fixture - create controller without initializing hardware"""
        self.controller = ArmController()
        # Don't call initialize() - we're testing the helper method only

    def test_2d_normalized_coordinates(self):
        """Test conversion of 2D normalized coordinates (0-1000 range)"""
        # [y, x] format with normalized values
        point = [500, 300]  # y=500, x=300
        result = self.controller._convert_waypoint_to_position(point)

        # Expected: [x=0.3, y=0.5, z=0.2]
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 0.3, places=3)  # x
        self.assertAlmostEqual(result[1], 0.5, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)  # z (default)

    def test_2d_meters_coordinates(self):
        """Test conversion of 2D coordinates already in meters"""
        # [y, x] format with meter values
        point = [0.5, 0.3]  # y=0.5m, x=0.3m
        result = self.controller._convert_waypoint_to_position(point)

        # Expected: [x=0.3, y=0.5, z=0.2]
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 0.3, places=3)  # x
        self.assertAlmostEqual(result[1], 0.5, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)  # z (default)

    def test_2d_boundary_value_1(self):
        """Test edge case: value exactly 1.0"""
        # Value of 1.0 should be treated as meters (not normalized)
        point = [1.0, 1.0]
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 1.0, places=3)  # x
        self.assertAlmostEqual(result[1], 1.0, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)  # z

    def test_2d_boundary_value_just_over_1(self):
        """Test edge case: value just over 1.0 triggers normalization"""
        # Value > 1.0 should be divided by 1000
        point = [2.0, 1.5]
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 0.0015, places=4)  # x = 1.5/1000
        self.assertAlmostEqual(result[1], 0.002, places=4)   # y = 2.0/1000
        self.assertAlmostEqual(result[2], 0.2, places=3)     # z

    def test_2d_negative_coordinates(self):
        """Test conversion with negative coordinates"""
        # Negative values in meters
        point = [-0.2, -0.3]
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], -0.3, places=3)  # x
        self.assertAlmostEqual(result[1], -0.2, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)   # z

    def test_2d_zero_coordinates(self):
        """Test conversion with zero coordinates"""
        point = [0.0, 0.0]
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 0.0, places=3)  # x
        self.assertAlmostEqual(result[1], 0.0, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)  # z

    def test_3d_coordinates_passthrough(self):
        """Test that 3D coordinates are returned as-is"""
        point = [0.25, 0.1, 0.15]
        result = self.controller._convert_waypoint_to_position(point)

        # Should be unchanged
        self.assertEqual(result, point)
        self.assertAlmostEqual(result[0], 0.25, places=3)
        self.assertAlmostEqual(result[1], 0.1, places=3)
        self.assertAlmostEqual(result[2], 0.15, places=3)

    def test_3d_with_large_values(self):
        """Test that 3D coordinates with large values are not normalized"""
        # Even with values > 1, 3D coordinates should not be normalized
        point = [100, 200, 300]
        result = self.controller._convert_waypoint_to_position(point)

        # Should be unchanged (no normalization for 3D)
        self.assertEqual(result, point)

    def test_2d_mixed_normalized_and_meters(self):
        """Test mixed case: one coordinate > 1, one <= 1"""
        point = [0.5, 100]  # y in meters, x normalized
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 0.1, places=3)    # x = 100/1000
        self.assertAlmostEqual(result[1], 0.5, places=3)    # y as-is
        self.assertAlmostEqual(result[2], 0.2, places=3)    # z

    def test_2d_typical_normalized_range(self):
        """Test typical normalized coordinates in center of range"""
        point = [512, 384]  # Typical normalized values
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 0.384, places=3)  # x
        self.assertAlmostEqual(result[1], 0.512, places=3)  # y
        self.assertAlmostEqual(result[2], 0.2, places=3)    # z

    def test_2d_max_normalized_range(self):
        """Test maximum normalized coordinate values"""
        point = [1000, 1000]  # Max normalized
        result = self.controller._convert_waypoint_to_position(point)

        self.assertAlmostEqual(result[0], 1.0, places=3)  # x = 1000/1000
        self.assertAlmostEqual(result[1], 1.0, places=3)  # y = 1000/1000
        self.assertAlmostEqual(result[2], 0.2, places=3)  # z

    def test_empty_list_returns_empty(self):
        """Test that empty list is returned as-is"""
        point = []
        result = self.controller._convert_waypoint_to_position(point)
        self.assertEqual(result, [])

    def test_single_element_returns_unchanged(self):
        """Test that single-element list is returned as-is"""
        point = [0.5]
        result = self.controller._convert_waypoint_to_position(point)
        self.assertEqual(result, [0.5])

    def test_four_element_returns_unchanged(self):
        """Test that 4+ element lists are returned as-is"""
        point = [0.1, 0.2, 0.3, 0.4]
        result = self.controller._convert_waypoint_to_position(point)
        self.assertEqual(result, point)


class TestWaypointConversionIntegration(unittest.TestCase):
    """Integration tests showing how the helper is used in trajectories"""

    def setUp(self):
        """Set up test fixture"""
        self.controller = ArmController()

    def test_realistic_trajectory_waypoints(self):
        """Test conversion of realistic trajectory waypoints"""
        # Simulate waypoints as they might come from Gemini
        waypoints = [
            {'point': [500, 300], 'label': 'approach'},     # Normalized
            {'point': [0.25, 0.15], 'label': 'grasp'},      # Meters
            {'point': [0.25, 0.15, 0.3], 'label': 'lift'},  # 3D
        ]

        results = []
        for wp in waypoints:
            position = self.controller._convert_waypoint_to_position(wp['point'])
            results.append({
                'label': wp['label'],
                'position': position
            })

        # Verify conversions
        self.assertAlmostEqual(results[0]['position'][0], 0.3, places=3)
        self.assertAlmostEqual(results[0]['position'][1], 0.5, places=3)
        self.assertAlmostEqual(results[0]['position'][2], 0.2, places=3)

        self.assertAlmostEqual(results[1]['position'][0], 0.15, places=3)
        self.assertAlmostEqual(results[1]['position'][1], 0.25, places=3)
        self.assertAlmostEqual(results[1]['position'][2], 0.2, places=3)

        self.assertEqual(results[2]['position'], [0.25, 0.15, 0.3])


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestWaypointConversion))
    suite.addTests(loader.loadTestsFromTestCase(TestWaypointConversionIntegration))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    import sys
    sys.exit(run_tests())
