#!/usr/bin/env python3
"""
Test extended reach capabilities - forward and down
"""

import requests
import json
import time

BRIDGE_URL = "http://localhost:8081"

def test_position(x: float, y: float, z: float, label: str = ""):
    """Test a position through the bridge API"""
    
    print(f"\n{label}:")
    print(f"  Testing position: [{x:.2f}, {y:.2f}, {z:.2f}]")
    
    payload = {
        "name": "move_arm_trajectory", 
        "args": {
            "trajectory": [
                {
                    "point": [x, y, z],
                    "label": label,
                    "gripper_action": "maintain"
                }
            ],
            "speed": "slow"
        }
    }
    
    try:
        response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=payload, timeout=10)
        result = response.json()
        
        if result.get("success"):
            print(f"  ✓ SUCCESS - Position reached")
        else:
            print(f"  ✗ FAILED")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def test_pose(pose_name: str):
    """Test moving to a named pose"""
    
    print(f"\nMoving to {pose_name} pose (should be slow)...")
    
    payload = {
        "name": "move_arm", 
        "args": {
            "pose": pose_name
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=payload, timeout=10)
        elapsed = time.time() - start_time
        result = response.json()
        
        if result.get("success"):
            print(f"  ✓ SUCCESS - Reached {pose_name} in {elapsed:.1f}s")
        else:
            print(f"  ✗ FAILED")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

def main():
    print("="*70)
    print("TESTING EXTENDED REACH CAPABILITIES")
    print("="*70)
    
    # Wait for bridge
    print("\nWaiting for bridge to be ready...")
    time.sleep(3)
    
    # Test moving to home (should be slow)
    test_pose("home")
    time.sleep(1)
    
    print("\n" + "-"*50)
    print("Testing forward reach positions:")
    print("-"*50)
    
    # Test forward reach at normal height
    test_position(0.40, 0.0, 0.20, "Forward 40cm")
    time.sleep(2)
    
    test_position(0.50, 0.0, 0.20, "Forward 50cm")
    time.sleep(2)
    
    test_position(0.55, 0.0, 0.20, "Forward 55cm")
    time.sleep(2)
    
    print("\n" + "-"*50)
    print("Testing reaching down (negative Z):")
    print("-"*50)
    
    # Test reaching down
    test_position(0.30, 0.0, 0.0, "Table level (z=0)")
    time.sleep(2)
    
    test_position(0.35, 0.0, -0.10, "Below table (z=-0.1)")
    time.sleep(2)
    
    print("\n" + "-"*50)
    print("Testing extreme reach (forward and down):")
    print("-"*50)
    
    # Test extreme reach
    test_position(0.60, 0.0, -0.15, "Far forward and down (60cm, -15cm)")
    time.sleep(2)
    
    test_position(0.65, 0.0, -0.20, "Maximum reach (65cm, -20cm)")
    time.sleep(2)
    
    # Return to safe position
    print("\n" + "-"*50)
    print("Returning to safe position...")
    print("-"*50)
    
    test_position(0.25, 0.0, 0.20, "Safe center position")
    time.sleep(2)
    
    # Test sleep pose (should be slow)
    test_pose("sleep")
    
    print("\n" + "="*70)
    print("EXTENDED REACH TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()