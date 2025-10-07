#!/usr/bin/env python3
"""
Workspace Bounds Tester for ViperX 300s
Tests safe working positions to determine actual robot workspace limits
"""

import sys
import time
import json
import os
# Add parent directory to path to import controllers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from arm_controller import ArmController

def test_workspace_bounds():
    """
    Test various positions to determine safe workspace bounds
    """
    controller = ArmController()
    controller.initialize()
    
    results = {
        "robot_model": "vx300s",
        "tested_positions": [],
        "bounds": {
            "x": {"min": float('inf'), "max": float('-inf')},
            "y": {"min": float('inf'), "max": float('-inf')},
            "z": {"min": float('inf'), "max": float('-inf')}
        }
    }
    
    # Test positions - conservative starting points based on typical ViperX 300s reach
    # Max reach is ~450mm from base, but we'll test conservatively
    test_positions = [
        # Center positions at different heights
        {"x": 0.25, "y": 0.0, "z": 0.15, "label": "center_low"},
        {"x": 0.25, "y": 0.0, "z": 0.25, "label": "center_mid"},
        {"x": 0.25, "y": 0.0, "z": 0.35, "label": "center_high"},
        
        # Forward reach tests
        {"x": 0.30, "y": 0.0, "z": 0.20, "label": "forward_1"},
        {"x": 0.35, "y": 0.0, "z": 0.20, "label": "forward_2"},
        {"x": 0.40, "y": 0.0, "z": 0.20, "label": "forward_3"},
        
        # Backward reach tests (closer to base)
        {"x": 0.20, "y": 0.0, "z": 0.20, "label": "backward_1"},
        {"x": 0.15, "y": 0.0, "z": 0.20, "label": "backward_2"},
        
        # Side reach tests
        {"x": 0.25, "y": 0.15, "z": 0.20, "label": "left_1"},
        {"x": 0.25, "y": 0.20, "z": 0.20, "label": "left_2"},
        {"x": 0.25, "y": -0.15, "z": 0.20, "label": "right_1"},
        {"x": 0.25, "y": -0.20, "z": 0.20, "label": "right_2"},
        
        # Height limits
        {"x": 0.25, "y": 0.0, "z": 0.10, "label": "low_1"},
        {"x": 0.25, "y": 0.0, "z": 0.40, "label": "high_1"},
        {"x": 0.25, "y": 0.0, "z": 0.45, "label": "high_2"},
    ]
    
    print("=" * 60)
    print("WORKSPACE BOUNDS TESTER FOR VIPERX 300s")
    print("=" * 60)
    print("\nStarting from home position...")
    
    # Start from home
    controller.move_to_pose("home", blocking=True)
    time.sleep(2)
    
    for pos in test_positions:
        print(f"\nTesting {pos['label']}: x={pos['x']:.2f}, y={pos['y']:.2f}, z={pos['z']:.2f}")
        
        result = controller.move_to_position(
            [pos['x'], pos['y'], pos['z']],
            moving_time=2.0,
            blocking=True
        )
        
        test_result = {
            "position": {"x": pos['x'], "y": pos['y'], "z": pos['z']},
            "label": pos['label'],
            "success": result.get('success', False),
            "error": result.get('error', None)
        }
        
        if result.get('success'):
            print(f"  ✓ SUCCESS - Position reachable")
            # Update bounds
            results["bounds"]["x"]["min"] = min(results["bounds"]["x"]["min"], pos['x'])
            results["bounds"]["x"]["max"] = max(results["bounds"]["x"]["max"], pos['x'])
            results["bounds"]["y"]["min"] = min(results["bounds"]["y"]["min"], pos['y'])
            results["bounds"]["y"]["max"] = max(results["bounds"]["y"]["max"], pos['y'])
            results["bounds"]["z"]["min"] = min(results["bounds"]["z"]["min"], pos['z'])
            results["bounds"]["z"]["max"] = max(results["bounds"]["z"]["max"], pos['z'])
            
            # Get actual position
            state = controller.get_arm_state()
            if state.get('ee_position'):
                test_result['actual_position'] = state['ee_position']
        else:
            print(f"  ✗ FAILED - {result.get('error', 'Unknown error')}")
        
        results["tested_positions"].append(test_result)
        
        # Return to safe position between tests
        if not result.get('success'):
            print("  Returning to home...")
            controller.move_to_pose("home", blocking=True)
            time.sleep(1)
        else:
            time.sleep(0.5)
    
    # Return to home
    print("\nReturning to home position...")
    controller.move_to_pose("home", blocking=True)
    
    # Summary
    print("\n" + "=" * 60)
    print("WORKSPACE BOUNDS SUMMARY")
    print("=" * 60)
    
    successful_tests = [t for t in results["tested_positions"] if t["success"]]
    failed_tests = [t for t in results["tested_positions"] if not t["success"]]
    
    print(f"\nTests passed: {len(successful_tests)}/{len(test_positions)}")
    
    if successful_tests:
        print(f"\nDetermined workspace bounds (meters):")
        print(f"  X: [{results['bounds']['x']['min']:.3f}, {results['bounds']['x']['max']:.3f}]")
        print(f"  Y: [{results['bounds']['y']['min']:.3f}, {results['bounds']['y']['max']:.3f}]")
        print(f"  Z: [{results['bounds']['z']['min']:.3f}, {results['bounds']['z']['max']:.3f}]")
        
        # Suggest conservative bounds (90% of tested range)
        x_range = results['bounds']['x']['max'] - results['bounds']['x']['min']
        y_range = results['bounds']['y']['max'] - results['bounds']['y']['min']
        z_range = results['bounds']['z']['max'] - results['bounds']['z']['min']
        
        conservative_bounds = {
            "x": [
                results['bounds']['x']['min'] + 0.05 * x_range,
                results['bounds']['x']['max'] - 0.05 * x_range
            ],
            "y": [
                results['bounds']['y']['min'] + 0.05 * y_range,
                results['bounds']['y']['max'] - 0.05 * y_range
            ],
            "z": [
                max(0.12, results['bounds']['z']['min']),  # Never go below 12cm for safety
                results['bounds']['z']['max'] - 0.05 * z_range
            ]
        }
        
        print(f"\nRecommended conservative bounds (with safety margin):")
        print(f"  X: [{conservative_bounds['x'][0]:.3f}, {conservative_bounds['x'][1]:.3f}]")
        print(f"  Y: [{conservative_bounds['y'][0]:.3f}, {conservative_bounds['y'][1]:.3f}]")
        print(f"  Z: [{conservative_bounds['z'][0]:.3f}, {conservative_bounds['z'][1]:.3f}]")
        
        results["conservative_bounds"] = conservative_bounds
    
    if failed_tests:
        print(f"\nFailed positions:")
        for test in failed_tests:
            print(f"  - {test['label']}: {test['error']}")
    
    # Save results
    with open('/home/aloha/gemini-live/workspace_bounds_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to workspace_bounds_results.json")
    
    controller.shutdown()
    return results

if __name__ == "__main__":
    try:
        results = test_workspace_bounds()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during testing: {e}")
        sys.exit(1)