#!/usr/bin/env python3
"""
Test workspace bounds via HTTP API
"""

import requests
import json
import time
from typing import List, Tuple, Dict

BRIDGE_URL = "http://localhost:8081"

def test_position(x: float, y: float, z: float, label: str = "") -> Dict:
    """Test a position through the bridge API"""
    
    print(f"\nTesting {label}: [{x:.3f}, {y:.3f}, {z:.3f}]")
    
    # Send move_arm_trajectory command
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
        response = requests.post(f"{BRIDGE_URL}/aloha-tool-call", json=payload, timeout=5)
        result = response.json()
        
        # Parse the response
        if "result_summary" in result:
            summary = result["result_summary"]
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary.replace("'", '"'))
                except:
                    pass
            
            success = result.get("success", False)
            
            if success:
                print(f"  ✓ SUCCESS - Position reachable")
            else:
                error = summary.get("error", "") if isinstance(summary, dict) else str(summary)
                if "outside bounds" in error.lower() or "blocked" in error.lower():
                    print(f"  ✗ BLOCKED - {error}")
                else:
                    print(f"  ⚠ ERROR - {error}")
                    
            return {"position": [x, y, z], "label": label, "success": success, "result": result}
        else:
            print(f"  ⚠ Unexpected response: {result}")
            return {"position": [x, y, z], "label": label, "success": False, "result": result}
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
        return {"position": [x, y, z], "label": label, "success": False, "error": str(e)}

def test_axis_limits():
    """Test limits along each axis"""
    
    results = {
        "x_tests": [],
        "y_tests": [], 
        "z_tests": []
    }
    
    print("="*60)
    print("TESTING X AXIS LIMITS")
    print("="*60)
    
    # Test X axis
    for x_val in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40]:
        result = test_position(x_val, 0.0, 0.20, f"X={x_val:.2f}")
        results["x_tests"].append(result)
        time.sleep(1)
    
    print("\n" + "="*60)
    print("TESTING Y AXIS LIMITS")
    print("="*60)
    
    # Test Y axis
    for y_val in [-0.30, -0.25, -0.15, 0.0, 0.15, 0.25, 0.30]:
        result = test_position(0.25, y_val, 0.20, f"Y={y_val:.2f}")
        results["y_tests"].append(result)
        time.sleep(1)
    
    print("\n" + "="*60)
    print("TESTING Z AXIS LIMITS")
    print("="*60)
    
    # Test Z axis
    for z_val in [0.08, 0.10, 0.12, 0.15, 0.20, 0.30, 0.40, 0.45, 0.50]:
        result = test_position(0.25, 0.0, z_val, f"Z={z_val:.2f}")
        results["z_tests"].append(result)
        time.sleep(1)
    
    # Summarize results
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    # Find boundaries
    x_min = min([r["position"][0] for r in results["x_tests"] if r["success"]], default=0.10)
    x_max = max([r["position"][0] for r in results["x_tests"] if r["success"]], default=0.35)
    
    y_min = min([r["position"][1] for r in results["y_tests"] if r["success"]], default=-0.25)
    y_max = max([r["position"][1] for r in results["y_tests"] if r["success"]], default=0.25)
    
    z_min = min([r["position"][2] for r in results["z_tests"] if r["success"]], default=0.12)
    z_max = max([r["position"][2] for r in results["z_tests"] if r["success"]], default=0.40)
    
    print(f"\nDetermined workspace bounds:")
    print(f"  X: [{x_min:.3f}, {x_max:.3f}] meters")
    print(f"  Y: [{y_min:.3f}, {y_max:.3f}] meters")
    print(f"  Z: [{z_min:.3f}, {z_max:.3f}] meters")
    
    print(f"\nRecommended safe bounds (with 2cm margin):")
    print(f"  X: [{x_min + 0.02:.3f}, {x_max - 0.02:.3f}] meters")
    print(f"  Y: [{y_min + 0.02:.3f}, {y_max - 0.02:.3f}] meters")
    print(f"  Z: [{z_min + 0.02:.3f}, {z_max - 0.02:.3f}] meters")
    
    # Save results
    with open("/home/aloha/gemini-live/bounds_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": results,
            "determined_bounds": {
                "x": [x_min, x_max],
                "y": [y_min, y_max],
                "z": [z_min, z_max]
            },
            "recommended_bounds": {
                "x": [x_min + 0.02, x_max - 0.02],
                "y": [y_min + 0.02, y_max - 0.02],
                "z": [z_min + 0.02, z_max - 0.02]
            }
        }, f, indent=2)
        
    print(f"\n✓ Results saved to bounds_test_results.json")

if __name__ == "__main__":
    # Check if bridge is running
    try:
        response = requests.get(f"{BRIDGE_URL}/status", timeout=2)
        print(f"Bridge status: {response.json()}")
    except:
        print("❌ Bridge not responding on port 8081")
        print("Please ensure bridge is running with: ./run_bridge.sh")
        exit(1)
    
    # Run tests
    test_axis_limits()