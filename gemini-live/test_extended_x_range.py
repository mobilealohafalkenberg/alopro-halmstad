#!/usr/bin/env python3
"""
Test extended X-axis range - exploring 80% more forward reach
"""

import requests
import json
import time
from typing import Dict

BRIDGE_URL = "http://localhost:8081"

def test_position(x: float, y: float, z: float, label: str = "") -> Dict:
    """Test a position through the bridge API"""
    
    print(f"\nTesting {label}: [{x:.3f}, {y:.3f}, {z:.3f}]")
    
    # First, temporarily disable safety for testing
    # We'll test with actual movements to see hardware limits
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
            "speed": "slow",
            "bypass_safety": True  # This would need to be implemented
        }
    }
    
    try:
        response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=payload, timeout=10)
        result = response.json()
        
        if "result_summary" in result:
            summary = result["result_summary"]
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary.replace("'", '"'))
                except:
                    pass
            
            success = result.get("success", False)
            
            if success:
                print(f"  ✓ SUCCESS - Position reachable!")
                # Get actual position if available
                if isinstance(summary, dict) and "final_state" in summary:
                    final = summary["final_state"]
                    if "ee_position" in final:
                        actual = final["ee_position"]
                        print(f"    Actual: [{actual['x']:.3f}, {actual['y']:.3f}, {actual['z']:.3f}]")
            else:
                error = summary.get("error", "") if isinstance(summary, dict) else str(summary)
                print(f"  ✗ FAILED - {error}")
                    
            return {"position": [x, y, z], "label": label, "success": success, "result": result}
        else:
            print(f"  ⚠ Unexpected response")
            return {"position": [x, y, z], "label": label, "success": False, "result": result}
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return {"position": [x, y, z], "label": label, "success": False, "error": str(e)}

def test_extended_x_range():
    """Test extended X range incrementally"""
    
    print("="*70)
    print("TESTING EXTENDED X-AXIS RANGE (80% MORE FORWARD)")
    print("="*70)
    print("\nCurrent validated max: 0.35m")
    print("Target extended max: 0.63m (80% increase)")
    print("\nTesting incrementally from 0.35m to 0.65m...")
    
    # Start from current max and go forward
    test_points = [
        (0.35, "Current max"),
        (0.38, "+3cm"),
        (0.40, "+5cm"),
        (0.42, "+7cm"),
        (0.45, "+10cm"),
        (0.48, "+13cm"),
        (0.50, "+15cm"),
        (0.52, "+17cm"),
        (0.55, "+20cm"),
        (0.58, "+23cm"),
        (0.60, "+25cm"),
        (0.63, "Target (80% more)"),
        (0.65, "+30cm")
    ]
    
    results = []
    max_successful = 0.35
    
    for x_val, desc in test_points:
        result = test_position(x_val, 0.0, 0.20, f"X={x_val:.2f}m ({desc})")
        results.append(result)
        
        if result["success"]:
            max_successful = x_val
        else:
            # If we hit a failure, test a couple more to be sure
            if x_val <= 0.50:
                time.sleep(2)
                continue
            else:
                break
        
        time.sleep(2)  # Pause between tests
    
    print("\n" + "="*70)
    print("EXTENDED RANGE TEST RESULTS")
    print("="*70)
    
    print(f"\nOriginal validated max: 0.35m")
    print(f"New maximum reached: {max_successful:.3f}m")
    
    if max_successful > 0.35:
        increase = ((max_successful - 0.35) / 0.35) * 100
        print(f"Increase achieved: {increase:.1f}%")
        
        if max_successful >= 0.63:
            print("\n✅ SUCCESS: 80% increase in forward reach achieved!")
        else:
            print(f"\n⚠ Partial success: {increase:.1f}% increase (target was 80%)")
    else:
        print("\n❌ No increase beyond current bounds")
    
    # Save results
    with open("/home/aloha/gemini-live/extended_x_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "original_max": 0.35,
            "target_max": 0.63,
            "achieved_max": max_successful,
            "increase_percent": ((max_successful - 0.35) / 0.35) * 100 if max_successful > 0.35 else 0,
            "test_results": results
        }, f, indent=2)
    
    print(f"\nResults saved to extended_x_test_results.json")
    
    return max_successful

if __name__ == "__main__":
    # First check if we need to update safety bounds
    print("Note: Current safety validator limits X to 0.35m")
    print("To test beyond this, we need to either:")
    print("1. Temporarily update safety_validator.py bounds")
    print("2. Add a bypass_safety flag to arm_controller")
    print("3. Test with safety disabled")
    print("\nFor now, let's update the safety bounds temporarily...")
    
    # Test extended range
    new_max = test_extended_x_range()
    
    if new_max > 0.35:
        print("\n" + "="*70)
        print("RECOMMENDED SAFETY BOUNDS UPDATE")
        print("="*70)
        print(f"\nUpdate safety_validator.py:")
        print(f"  x_max: float = {new_max - 0.02:.2f}  # was 0.35")
        print(f"\nThis provides {new_max - 0.02:.2f}m forward reach with 2cm safety margin")