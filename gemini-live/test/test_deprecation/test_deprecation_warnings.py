#!/usr/bin/env python3

"""
Test script to demonstrate deprecation warnings for gripper controller singleton functions.

This script shows both the deprecated pattern (which triggers warnings) and the recommended pattern.
Run this to verify that deprecation warnings are working correctly.

Usage:
    python3 test_deprecation_warnings.py
"""

import sys
import warnings

def test_deprecated_pattern():
    """Test the deprecated singleton pattern - should trigger warnings"""
    print("\n" + "="*60)
    print("Testing DEPRECATED Pattern (will show warnings)")
    print("="*60)

    # This will trigger deprecation warnings
    from gripper_controller import get_controller, open_gripper, close_gripper, get_gripper_state, cleanup

    print("\n1. Testing get_controller() - DEPRECATED")
    try:
        controller = get_controller()
        print(f"   ✓ Got controller: {controller}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n2. Testing open_gripper() - DEPRECATED")
    try:
        result = open_gripper()
        print(f"   ✓ Result: {result}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n3. Testing close_gripper() - DEPRECATED")
    try:
        result = close_gripper()
        print(f"   ✓ Result: {result}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n4. Testing get_gripper_state() - DEPRECATED")
    try:
        state = get_gripper_state()
        print(f"   ✓ State: {state}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

    print("\n5. Testing cleanup() - DEPRECATED")
    try:
        cleanup()
        print(f"   ✓ Cleanup successful")
    except Exception as e:
        print(f"   ✗ Error: {e}")

def test_recommended_pattern():
    """Test the recommended explicit instance pattern - no warnings"""
    print("\n" + "="*60)
    print("Testing RECOMMENDED Pattern (no warnings)")
    print("="*60)

    from gripper_controller import GripperController

    print("\n1. Creating explicit GripperController instance")
    controller = GripperController(robot_model='vx300s', robot_name='follower_left')
    print(f"   ✓ Controller created: {controller}")

    print("\n2. Initializing controller")
    print("   Note: Initialization will fail without hardware, which is expected")
    try:
        success = controller.initialize()
        print(f"   ✓ Initialization result: {success}")
    except Exception as e:
        print(f"   ✗ Expected error (no hardware): {e}")

    print("\n3. Testing methods (without initialization - just to show API)")
    print("   controller.open_gripper() - would open gripper if initialized")
    print("   controller.close_gripper() - would close gripper if initialized")
    print("   controller.get_gripper_state() - would get state if initialized")
    print("   controller.shutdown() - cleanup")

def main():
    print("="*60)
    print("Gripper Controller Deprecation Warning Test")
    print("="*60)
    print("\nThis script demonstrates:")
    print("1. Deprecated singleton functions (with warnings)")
    print("2. Recommended explicit instance pattern (no warnings)")
    print("\nNote: Actual robot operations will fail without hardware.")
    print("      We're testing the deprecation warnings, not robot functionality.")

    # Test deprecated pattern (will show warnings)
    test_deprecated_pattern()

    # Test recommended pattern (no warnings)
    test_recommended_pattern()

    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print("✓ If you saw DeprecationWarning messages above, the warnings are working!")
    print("✓ The recommended pattern (explicit instances) produces no warnings.")
    print("✓ Migrate your code to the recommended pattern before the functions are removed.")
    print("\nSee docs/MIGRATION_GUIDE_GRIPPER_SINGLETON_REMOVAL.md for migration help.")

if __name__ == "__main__":
    # Show all warnings
    warnings.simplefilter("always", DeprecationWarning)
    main()
