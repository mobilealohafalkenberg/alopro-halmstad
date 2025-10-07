#!/usr/bin/env python3
"""
Test script for trajectory bridge endpoints
Tests move_to_pose, follow_cartesian_trajectory, and telemetry
"""

import requests
import json
import time
import asyncio
import aiohttp

BRIDGE_URL = "http://localhost:8082"

def test_move_to_pose(x: float, y: float, z: float, dry_run: bool = True):
    """Test move_to_pose endpoint"""
    print(f"\n📍 Testing move_to_pose to [{x:.2f}, {y:.2f}, {z:.2f}] (dry_run={dry_run})")
    
    payload = {
        "arm_side": "follower_left",
        "x": x,
        "y": y,
        "z": z,
        "roll": 0,
        "pitch": 0,
        "yaw": 0,
        "moving_time": 2.0,
        "accel_time": 0.3,
        "options": {
            "dryRun": dry_run
        },
        "request_id": f"test_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{BRIDGE_URL}/robot/move_to_pose", json=payload, timeout=5)
        result = response.json()
        
        if response.status_code == 200:
            if result.get("accepted"):
                print(f"  ✅ Job accepted: {result.get('jobId')}")
                print(f"     Risk level: {result.get('safety', {}).get('riskLevel')}")
                return result.get('jobId')
            else:
                print(f"  ❌ Job rejected: {result.get('message')}")
                print(f"     Safety: {result.get('safety')}")
        else:
            print(f"  ❌ Error {response.status_code}: {result}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
    
    return None

def test_follow_trajectory(delta_x: float, delta_y: float, delta_z: float, dry_run: bool = True):
    """Test follow_cartesian_trajectory endpoint"""
    print(f"\n🚀 Testing trajectory delta [{delta_x:.2f}, {delta_y:.2f}, {delta_z:.2f}] (dry_run={dry_run})")
    
    payload = {
        "arm_side": "follower_left",
        "delta_x": delta_x,
        "delta_y": delta_y,
        "delta_z": delta_z,
        "delta_roll": 0,
        "delta_pitch": 0,
        "delta_yaw": 0,
        "moving_time": 3.0,
        "wp_period": 0.02,
        "options": {
            "dryRun": dry_run
        },
        "request_id": f"test_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{BRIDGE_URL}/robot/follow_cartesian_trajectory", json=payload, timeout=5)
        result = response.json()
        
        if response.status_code == 200:
            if result.get("accepted"):
                print(f"  ✅ Job accepted: {result.get('jobId')}")
                print(f"     Risk level: {result.get('safety', {}).get('riskLevel')}")
                return result.get('jobId')
            else:
                print(f"  ❌ Job rejected: {result.get('message')}")
                print(f"     Safety: {result.get('safety')}")
        else:
            print(f"  ❌ Error {response.status_code}: {result}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")
    
    return None

def test_get_state():
    """Test getting system state"""
    print("\n📊 Getting system state...")
    
    try:
        response = requests.get(f"{BRIDGE_URL}/robot/state", timeout=5)
        result = response.json()
        
        print(f"  Connected: {result.get('connected')}")
        print(f"  Driver mode: {result.get('driverMode')}")
        print(f"  Safety profile: {result.get('safetyProfile')}")
        print(f"  Queue lengths: {result.get('queueLengths')}")
        print(f"  Active jobs: {result.get('activeJobs')}")
        
        bounds = result.get('workspaceBounds', {})
        print(f"  Workspace bounds:")
        print(f"    X: [{bounds.get('x_min'):.2f}, {bounds.get('x_max'):.2f}]")
        print(f"    Y: [{bounds.get('y_min'):.2f}, {bounds.get('y_max'):.2f}]")
        print(f"    Z: [{bounds.get('z_min'):.2f}, {bounds.get('z_max'):.2f}]")
        
        return result
        
    except Exception as e:
        print(f"  ❌ Failed to get state: {e}")
        return None

def test_get_job(job_id: str):
    """Test getting job status"""
    print(f"\n🔍 Getting job {job_id}...")
    
    try:
        response = requests.get(f"{BRIDGE_URL}/robot/job/{job_id}", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"  State: {result.get('state')}")
            print(f"  Progress: {result.get('progress')*100:.0f}%")
            print(f"  Type: {result.get('type')}")
            if result.get('error'):
                print(f"  Error: {result.get('error')}")
            return result
        else:
            print(f"  ❌ Job not found")
            
    except Exception as e:
        print(f"  ❌ Failed to get job: {e}")
    
    return None

def test_stop():
    """Test soft stop"""
    print("\n🛑 Testing soft stop...")
    
    try:
        response = requests.post(f"{BRIDGE_URL}/robot/stop", timeout=5)
        result = response.json()
        
        if result.get("success"):
            print(f"  ✅ Stop successful")
            print(f"     Stopped jobs: {result.get('stoppedJobs')}")
        else:
            print(f"  ❌ Stop failed: {result}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")

def test_e_stop():
    """Test emergency stop"""
    print("\n🚨 Testing emergency stop...")
    
    try:
        response = requests.post(f"{BRIDGE_URL}/robot/e_stop", timeout=5)
        result = response.json()
        
        if result.get("success"):
            print(f"  ✅ E-stop activated")
        else:
            print(f"  ❌ E-stop failed: {result}")
            
    except Exception as e:
        print(f"  ❌ Request failed: {e}")

async def test_telemetry():
    """Test SSE telemetry stream"""
    print("\n📡 Testing telemetry stream (10 seconds)...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BRIDGE_URL}/robot/telemetry") as response:
                if response.status == 200:
                    print("  ✅ Connected to telemetry stream")
                    
                    # Read for 10 seconds
                    start_time = time.time()
                    async for line in response.content:
                        if time.time() - start_time > 10:
                            break
                        
                        line = line.decode('utf-8').strip()
                        if line.startswith('event:'):
                            event_type = line.split(':', 1)[1].strip()
                            print(f"  📨 Event: {event_type}")
                        elif line.startswith('data:'):
                            data = line.split(':', 1)[1].strip()
                            if data and data != '{}':
                                print(f"     Data: {data[:100]}...")
                else:
                    print(f"  ❌ Failed to connect: {response.status}")
                    
    except Exception as e:
        print(f"  ❌ Telemetry test failed: {e}")

def main():
    """Run all tests"""
    print("=" * 70)
    print("TRAJECTORY BRIDGE TEST SUITE")
    print("=" * 70)
    
    # Test 1: Get initial state
    state = test_get_state()
    if not state:
        print("\n⚠️  Bridge not responding. Is it running on port 8082?")
        return
    
    # Test 2: Safe position (dry run)
    job_id = test_move_to_pose(0.25, 0.0, 0.2, dry_run=True)
    if job_id:
        time.sleep(1)
        test_get_job(job_id)
    
    # Test 3: Near boundary position
    job_id = test_move_to_pose(0.60, 0.0, 0.15, dry_run=True)
    if job_id:
        time.sleep(1)
        test_get_job(job_id)
    
    # Test 4: Outside bounds (should be rejected)
    test_move_to_pose(0.80, 0.0, 0.2, dry_run=True)
    
    # Test 5: Relative trajectory
    job_id = test_follow_trajectory(0.05, 0.0, -0.05, dry_run=True)
    if job_id:
        time.sleep(2)
        test_get_job(job_id)
    
    # Test 6: Stop
    test_stop()
    
    # Test 7: Emergency stop
    test_e_stop()
    
    # Test 8: Telemetry (async)
    print("\n📡 Starting telemetry test (will run for 10 seconds)...")
    asyncio.run(test_telemetry())
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()