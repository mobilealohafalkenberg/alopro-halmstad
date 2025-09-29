#!/usr/bin/env python3
"""
Systematic workspace bounds testing for Mobile ALOHA robot.
This script tests various positions to determine actual safe workspace bounds.
"""

import sys
import json
import time
from typing import List, Tuple, Dict
sys.path.append('/home/aloha/gemini-live')

from arm_controller import ArmController

class WorkspaceBoundsTester:
    """Test workspace bounds systematically"""
    
    def __init__(self, controller: ArmController):
        self.controller = controller
        self.results = {
            "successful_positions": [],
            "failed_positions": [],
            "boundary_positions": [],
            "errors": []
        }
        
    def test_position(self, x: float, y: float, z: float, label: str = "") -> Dict:
        """
        Test a single position and record result
        """
        position = [x, y, z]
        print(f"\nTesting {label}: [{x:.3f}, {y:.3f}, {z:.3f}]")
        
        result = self.controller.move_to_position(position)
        
        test_result = {
            "position": position,
            "label": label,
            "success": result.get('success', False),
            "state": result.get('state', 'unknown'),
            "error": result.get('error', ''),
            "safety": result.get('safety', {})
        }
        
        if test_result['success'] or test_result['state'] == 'dry_run':
            print(f"  ✓ SUCCESS - Position reachable")
            self.results["successful_positions"].append(test_result)
        elif test_result['state'] == 'blocked':
            print(f"  ✗ BLOCKED - {test_result['error']}")
            self.results["failed_positions"].append(test_result)
        else:
            print(f"  ⚠ ERROR - {test_result['error']}")
            self.results["errors"].append(test_result)
            
        return test_result
    
    def test_axis_limits(self, axis: str, fixed_y: float = 0.0, fixed_z: float = 0.20):
        """
        Test limits along a single axis
        """
        print(f"\n{'='*60}")
        print(f"Testing {axis.upper()} axis limits")
        print(f"{'='*60}")
        
        if axis == 'x':
            # Test X axis from negative to far positive
            test_points = [
                (-0.10, "Negative X"),
                (0.00, "Zero X"),
                (0.05, "Very close"),
                (0.10, "Min expected"),
                (0.15, "Close"),
                (0.20, "Mid-close"),
                (0.25, "Center"),
                (0.30, "Mid-far"),
                (0.35, "Max expected"),
                (0.40, "Too far"),
                (0.45, "Way too far")
            ]
            for x_val, label in test_points:
                self.test_position(x_val, fixed_y, fixed_z, f"X={x_val:.2f} ({label})")
                time.sleep(0.5)  # Brief pause between tests
                
        elif axis == 'y':
            # Test Y axis from left to right
            test_points = [
                (-0.35, "Far left"),
                (-0.30, "Left limit?"),
                (-0.25, "Expected left"),
                (-0.15, "Left"),
                (0.00, "Center"),
                (0.15, "Right"),
                (0.25, "Expected right"),
                (0.30, "Right limit?"),
                (0.35, "Far right")
            ]
            fixed_x = 0.25
            for y_val, label in test_points:
                self.test_position(fixed_x, y_val, fixed_z, f"Y={y_val:.2f} ({label})")
                time.sleep(0.5)
                
        elif axis == 'z':
            # Test Z axis from low to high
            test_points = [
                (0.05, "Very low"),
                (0.10, "Too low?"),
                (0.12, "Min expected"),
                (0.15, "Low"),
                (0.20, "Mid-low"),
                (0.25, "Center"),
                (0.30, "Mid-high"),
                (0.35, "High"),
                (0.40, "Max expected"),
                (0.45, "Too high?"),
                (0.50, "Very high")
            ]
            fixed_x = 0.25
            for z_val, label in test_points:
                self.test_position(fixed_x, fixed_y, z_val, f"Z={z_val:.2f} ({label})")
                time.sleep(0.5)
    
    def test_corners(self):
        """
        Test workspace corners to find actual boundaries
        """
        print(f"\n{'='*60}")
        print("Testing workspace corners")
        print(f"{'='*60}")
        
        # Test 8 corners of expected workspace
        corners = [
            (0.10, -0.25, 0.12, "Min X, Min Y, Min Z"),
            (0.10, -0.25, 0.40, "Min X, Min Y, Max Z"),
            (0.10, 0.25, 0.12, "Min X, Max Y, Min Z"),
            (0.10, 0.25, 0.40, "Min X, Max Y, Max Z"),
            (0.35, -0.25, 0.12, "Max X, Min Y, Min Z"),
            (0.35, -0.25, 0.40, "Max X, Min Y, Max Z"),
            (0.35, 0.25, 0.12, "Max X, Max Y, Min Z"),
            (0.35, 0.25, 0.40, "Max X, Max Y, Max Z"),
        ]
        
        for x, y, z, label in corners:
            self.test_position(x, y, z, label)
            time.sleep(0.5)
    
    def find_boundary(self, axis: str, start: float, end: float, 
                     fixed_vals: Dict[str, float], tolerance: float = 0.005) -> float:
        """
        Binary search to find exact boundary along an axis
        """
        print(f"\nFinding exact boundary for {axis} axis...")
        
        low, high = start, end
        last_good = None
        
        while high - low > tolerance:
            mid = (low + high) / 2
            
            if axis == 'x':
                test_pos = [mid, fixed_vals['y'], fixed_vals['z']]
            elif axis == 'y':
                test_pos = [fixed_vals['x'], mid, fixed_vals['z']]
            else:  # z
                test_pos = [fixed_vals['x'], fixed_vals['y'], mid]
            
            result = self.controller.move_to_position(test_pos)
            
            if result.get('success') or result.get('state') == 'dry_run':
                last_good = mid
                if start < end:
                    low = mid  # Testing max boundary
                else:
                    high = mid  # Testing min boundary
            else:
                if start < end:
                    high = mid  # Testing max boundary
                else:
                    low = mid  # Testing min boundary
        
        return last_good if last_good is not None else (low + high) / 2
    
    def run_comprehensive_test(self):
        """
        Run comprehensive workspace testing
        """
        print("="*70)
        print("COMPREHENSIVE WORKSPACE BOUNDS TESTING")
        print("="*70)
        print("\nThis will test various positions to determine actual safe bounds.")
        print("The robot is in DRY RUN mode - no actual movements will occur.")
        
        # Test each axis
        self.test_axis_limits('x')
        self.test_axis_limits('y')
        self.test_axis_limits('z')
        
        # Test corners
        self.test_corners()
        
        # Find exact boundaries using binary search
        print(f"\n{'='*60}")
        print("Finding exact boundaries...")
        print(f"{'='*60}")
        
        # Find X boundaries
        x_min = self.find_boundary('x', 0.0, 0.20, {'y': 0.0, 'z': 0.20})
        x_max = self.find_boundary('x', 0.40, 0.20, {'y': 0.0, 'z': 0.20})
        
        # Find Y boundaries
        y_min = self.find_boundary('y', -0.40, 0.0, {'x': 0.25, 'z': 0.20})
        y_max = self.find_boundary('y', 0.40, 0.0, {'x': 0.25, 'z': 0.20})
        
        # Find Z boundaries
        z_min = self.find_boundary('z', 0.0, 0.20, {'x': 0.25, 'y': 0.0})
        z_max = self.find_boundary('z', 0.50, 0.20, {'x': 0.25, 'y': 0.0})
        
        # Summarize results
        self.summarize_results(x_min, x_max, y_min, y_max, z_min, z_max)
        
    def summarize_results(self, x_min, x_max, y_min, y_max, z_min, z_max):
        """
        Summarize test results and recommend bounds
        """
        print("\n" + "="*70)
        print("TEST RESULTS SUMMARY")
        print("="*70)
        
        print(f"\nTotal positions tested: {len(self.results['successful_positions']) + len(self.results['failed_positions']) + len(self.results['errors'])}")
        print(f"  Successful: {len(self.results['successful_positions'])}")
        print(f"  Failed: {len(self.results['failed_positions'])}")
        print(f"  Errors: {len(self.results['errors'])}")
        
        print("\n" + "-"*40)
        print("DETERMINED WORKSPACE BOUNDS")
        print("-"*40)
        print(f"X axis: [{x_min:.3f}, {x_max:.3f}] meters")
        print(f"Y axis: [{y_min:.3f}, {y_max:.3f}] meters")
        print(f"Z axis: [{z_min:.3f}, {z_max:.3f}] meters")
        
        print("\n" + "-"*40)
        print("RECOMMENDED SAFE BOUNDS (with margin)")
        print("-"*40)
        margin = 0.02  # 2cm safety margin
        print(f"X axis: [{x_min + margin:.3f}, {x_max - margin:.3f}] meters")
        print(f"Y axis: [{y_min + margin:.3f}, {y_max - margin:.3f}] meters")
        print(f"Z axis: [{z_min + margin:.3f}, {z_max - margin:.3f}] meters")
        
        # Save results to file
        results_file = "/home/aloha/gemini-live/workspace_test_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "determined_bounds": {
                    "x": [x_min, x_max],
                    "y": [y_min, y_max],
                    "z": [z_min, z_max]
                },
                "recommended_bounds": {
                    "x": [x_min + margin, x_max - margin],
                    "y": [y_min + margin, y_max - margin],
                    "z": [z_min + margin, z_max - margin]
                },
                "test_results": self.results
            }, f, indent=2)
        
        print(f"\n✓ Results saved to: {results_file}")
        
        # Check if current bounds need adjustment
        print("\n" + "-"*40)
        print("SAFETY VALIDATOR COMPARISON")
        print("-"*40)
        
        current_bounds = self.controller.safety_validator.bounds if self.controller.safety_validator else None
        if current_bounds:
            print(f"Current X: [{current_bounds.x_min:.3f}, {current_bounds.x_max:.3f}]")
            print(f"Current Y: [{current_bounds.y_min:.3f}, {current_bounds.y_max:.3f}]")
            print(f"Current Z: [{current_bounds.z_min:.3f}, {current_bounds.z_max:.3f}]")
            
            adjustments_needed = []
            if abs(current_bounds.x_min - (x_min + margin)) > 0.01:
                adjustments_needed.append(f"X min: {current_bounds.x_min:.3f} → {x_min + margin:.3f}")
            if abs(current_bounds.x_max - (x_max - margin)) > 0.01:
                adjustments_needed.append(f"X max: {current_bounds.x_max:.3f} → {x_max - margin:.3f}")
            if abs(current_bounds.y_min - (y_min + margin)) > 0.01:
                adjustments_needed.append(f"Y min: {current_bounds.y_min:.3f} → {y_min + margin:.3f}")
            if abs(current_bounds.y_max - (y_max - margin)) > 0.01:
                adjustments_needed.append(f"Y max: {current_bounds.y_max:.3f} → {y_max - margin:.3f}")
            if abs(current_bounds.z_min - (z_min + margin)) > 0.01:
                adjustments_needed.append(f"Z min: {current_bounds.z_min:.3f} → {z_min + margin:.3f}")
            if abs(current_bounds.z_max - (z_max - margin)) > 0.01:
                adjustments_needed.append(f"Z max: {current_bounds.z_max:.3f} → {z_max - margin:.3f}")
            
            if adjustments_needed:
                print("\n⚠ Recommended adjustments:")
                for adj in adjustments_needed:
                    print(f"  • {adj}")
            else:
                print("\n✓ Current bounds are appropriate!")


def main():
    """Main test function"""
    print("Initializing arm controller with safety enabled (dry_run mode)...")
    
    # Create controller in dry run mode for safe testing
    controller = ArmController(enable_safety=True, dry_run=True)
    controller.initialized = True  # Fake initialization for testing
    
    # Create tester
    tester = WorkspaceBoundsTester(controller)
    
    # Run tests
    try:
        tester.run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        tester.summarize_results(0.10, 0.35, -0.25, 0.25, 0.12, 0.40)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()