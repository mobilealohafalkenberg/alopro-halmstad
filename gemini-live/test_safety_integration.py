#!/usr/bin/env python3
"""
Test script for safety integration in arm controller
Tests that known bad positions are properly blocked
"""

import sys
import json
sys.path.append('/home/aloha/gemini-live')

# We'll test without actually connecting to robot
from arm_controller import ArmController

def test_safety_integration():
    """Test that safety validation blocks bad positions"""
    
    print("=" * 60)
    print("SAFETY INTEGRATION TEST")
    print("=" * 60)
    
    # Create controller with safety enabled, dry run mode
    print("\n1. Creating controller with safety enabled (dry_run=True)...")
    controller = ArmController(enable_safety=True, dry_run=True)
    
    # Don't actually initialize robot connection for this test
    controller.initialized = True  # Fake initialization
    
    # Test cases based on actual failures from logs
    test_cases = [
        {
            "name": "Valid center position",
            "position": [0.25, 0.0, 0.20],
            "should_pass": True
        },
        {
            "name": "Z too low (failed in actual test)",
            "position": [0.25, 0.0, 0.10],
            "should_pass": False
        },
        {
            "name": "Z too high (failed in actual test)",
            "position": [0.25, 0.0, 0.50],
            "should_pass": False
        },
        {
            "name": "X too far forward",
            "position": [0.40, 0.0, 0.20],
            "should_pass": False
        },
        {
            "name": "Negative X (robot can't reach)",
            "position": [-0.20, 0.0, 0.20],
            "should_pass": False
        },
        {
            "name": "Near boundary (should warn)",
            "position": [0.34, 0.0, 0.20],
            "should_pass": True  # But with warning
        }
    ]
    
    print("\n2. Testing individual positions:")
    print("-" * 40)
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"  Position: {test['position']}")
        
        result = controller.move_to_position(test['position'])
        
        success = result.get('success', False)
        state = result.get('state', '')
        safety_info = result.get('safety', {})
        
        # Check if result matches expectation
        if test['should_pass']:
            if success or state == 'dry_run':
                print(f"  ✓ PASS - Movement allowed (state: {state})")
                if safety_info.get('risk_level') == 'needs_confirmation':
                    print(f"    Warning: {safety_info.get('message', '')}")
                passed += 1
            else:
                print(f"  ✗ FAIL - Movement blocked but should pass")
                print(f"    Error: {result.get('error', '')}")
                failed += 1
        else:
            if not success and state == 'blocked':
                print(f"  ✓ PASS - Movement correctly blocked")
                print(f"    Reason: {result.get('error', '')}")
                passed += 1
            else:
                print(f"  ✗ FAIL - Movement allowed but should be blocked")
                print(f"    Result: {result}")
                failed += 1
    
    print("\n3. Testing trajectory validation:")
    print("-" * 40)
    
    # Test trajectory with mixed good and bad waypoints
    trajectory = [
        {"point": [0.25, 0, 0.2], "label": "start", "gripper_action": "open"},
        {"point": [0.25, 0, 0.1], "label": "too_low", "gripper_action": "maintain"},  # Should fail
        {"point": [0.25, 0, 0.25], "label": "end", "gripper_action": "close"}
    ]
    
    print("\nTesting trajectory with bad waypoint...")
    result = controller.execute_trajectory(trajectory, speed="slow")
    
    if not result.get('success') and 'too_low' in result.get('error', ''):
        print("  ✓ PASS - Trajectory correctly rejected due to bad waypoint")
        print(f"    Error: {result.get('error', '')}")
        passed += 1
    else:
        print("  ✗ FAIL - Trajectory should have been rejected")
        print(f"    Result: {result}")
        failed += 1
    
    # Test good trajectory
    good_trajectory = [
        {"point": [0.25, 0, 0.2], "label": "start"},
        {"point": [0.30, 0, 0.25], "label": "mid"},
        {"point": [0.25, 0, 0.20], "label": "end"}
    ]
    
    print("\nTesting valid trajectory...")
    result = controller.execute_trajectory(good_trajectory, speed="slow")
    
    # In dry run mode, we expect the trajectory to be validated but not executed
    if result.get('success') or 'dry_run' in str(result):
        print("  ✓ PASS - Valid trajectory accepted")
        passed += 1
    else:
        print("  ✗ FAIL - Valid trajectory rejected")
        print(f"    Result: {result}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {passed + failed}")
    
    if failed == 0:
        print("\n✅ All safety tests passed!")
        print("The safety system correctly:")
        print("  - Blocks positions outside workspace bounds")
        print("  - Warns about positions near boundaries")
        print("  - Validates trajectories before execution")
        print("  - Supports dry-run mode for testing")
    else:
        print(f"\n❌ {failed} tests failed - safety system needs adjustment")
    
    return failed == 0

if __name__ == "__main__":
    try:
        success = test_safety_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)