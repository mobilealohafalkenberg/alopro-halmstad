#!/usr/bin/env python3

"""
Example of how to use the GripperController as a tool for Gemini Live API.
This simulates how Gemini could call gripper functions and get feedback.

Task 2.9: Updated to support dry-run mode for hardware-independent testing.
"""

import time
import json
import sys
import os
# Add parent directory to path to import controllers
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from gripper_controller import GripperController


def process_gemini_command(command: str, controller: GripperController) -> dict:
    """
    Process a command from Gemini and return result.
    This simulates how Gemini Live API would interact with the gripper.
    
    Commands:
        - "open": Open the gripper
        - "close": Close the gripper
        - "status": Get current gripper state
        - "set_position <value>": Set gripper to specific position (0.0 to 1.0)
        - "sleep": Move arm to sleep position
    """
    
    command = command.lower().strip()
    
    if command == "open":
        result = controller.open_gripper()
        return {
            "action": "open_gripper",
            "result": result,
            "message": f"Gripper is now {result['state']}"
        }
    
    elif command == "close":
        result = controller.close_gripper()
        return {
            "action": "close_gripper", 
            "result": result,
            "message": f"Gripper is now {result['state']}"
        }
    
    elif command == "status":
        result = controller.get_gripper_state()
        percentage = result['position_normalized'] * 100
        return {
            "action": "get_status",
            "result": result,
            "message": f"Gripper is {result['state']} ({percentage:.1f}% open)"
        }
    
    elif command.startswith("set_position"):
        try:
            # Extract position value
            parts = command.split()
            if len(parts) > 1:
                position = float(parts[1])
                result = controller.set_gripper_position(position)
                percentage = result['position_normalized'] * 100
                return {
                    "action": "set_position",
                    "result": result,
                    "message": f"Gripper moved to {percentage:.1f}% open"
                }
            else:
                return {
                    "action": "set_position",
                    "error": "Missing position value",
                    "message": "Please specify position (0.0 to 1.0)"
                }
        except ValueError:
            return {
                "action": "set_position",
                "error": "Invalid position value",
                "message": "Position must be a number between 0.0 and 1.0"
            }
    
    elif command == "sleep":
        success = controller.sleep_arm()
        return {
            "action": "sleep_arm",
            "success": success,
            "message": "Arm moved to sleep position" if success else "Failed to sleep arm"
        }
    
    else:
        return {
            "action": "unknown",
            "error": "Unknown command",
            "message": f"Unknown command: {command}",
            "available_commands": ["open", "close", "status", "set_position <0-1>", "sleep"]
        }


def stream_gripper_state(controller: GripperController, duration: float = 5.0):
    """
    Stream gripper state for a duration (simulates real-time feedback).
    This could be used for continuous monitoring during Gemini Live sessions.
    """
    print("\n=== STREAMING GRIPPER STATE ===")
    start_time = time.time()
    
    while time.time() - start_time < duration:
        state = controller.get_gripper_state()
        percentage = state['position_normalized'] * 100
        
        # Format as JSON for easy parsing
        stream_data = {
            "timestamp": time.time(),
            "state": state['state'],
            "position_percent": round(percentage, 1),
            "position_rad": round(state['position'], 3)
        }
        
        print(f"STREAM: {json.dumps(stream_data)}")
        time.sleep(0.2)  # Stream at 5Hz
    
    print("=== STREAM ENDED ===\n")


def main():
    """
    Demonstrate how Gemini Live API could interact with the gripper.
    """
    print("=" * 60)
    print("GEMINI LIVE API - GRIPPER CONTROL EXAMPLE")
    print("=" * 60)

    # Check for dry-run mode
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "--dry-run"
    if dry_run:
        print("🧪 RUNNING IN DRY-RUN MODE (Task 2.9)")
        print("   No hardware required - all operations are simulated")

    # Initialize controller (this would be done once at startup)
    print("\n1. INITIALIZING GRIPPER CONTROLLER...")
    controller = GripperController(dry_run=dry_run)
    if not controller.initialize():
        print("Failed to initialize controller!")
        if not dry_run:
            print("💡 TIP: Try running with --dry-run flag for hardware-independent testing")
        return
    
    print("\n2. SIMULATING GEMINI COMMANDS...")
    print("-" * 40)
    
    # Simulate various Gemini commands
    test_commands = [
        "status",           # Check initial state
        "open",            # Open gripper
        "status",          # Check after opening
        "set_position 0.5", # Half open
        "status",          # Check position
        "close",           # Close gripper
        "status",          # Final check
    ]
    
    for cmd in test_commands:
        print(f"\nGemini command: '{cmd}'")
        response = process_gemini_command(cmd, controller)
        print(f"Response: {response['message']}")
        if 'result' in response and 'position_normalized' in response['result']:
            print(f"  Position: {response['result']['position_normalized']*100:.1f}% open")
        time.sleep(1.5)
    
    # Demonstrate streaming
    print("\n3. DEMONSTRATING REAL-TIME STREAMING...")
    print("-" * 40)
    print("Opening gripper while streaming state...")
    
    # Start opening in non-blocking mode
    controller.open_gripper(blocking=False)
    # Stream state while opening
    stream_gripper_state(controller, duration=2.0)
    
    # Interactive mode
    print("\n4. INTERACTIVE MODE (type 'quit' to exit)")
    print("-" * 40)
    print("Available commands: open, close, status, set_position <0-1>, sleep, quit")
    
    while True:
        try:
            cmd = input("\nEnter command: ").strip()
            if cmd.lower() == 'quit':
                break
            
            response = process_gemini_command(cmd, controller)
            print(f"Response: {json.dumps(response, indent=2)}")
            
        except KeyboardInterrupt:
            break
    
    # Cleanup
    print("\n5. CLEANING UP...")
    controller.sleep_arm()
    controller.shutdown()
    print("\n✓ Example complete!")


if __name__ == '__main__':
    # Check for dry-run mode first
    dry_run = len(sys.argv) > 1 and sys.argv[1] == "--dry-run"

    if dry_run:
        print("Running in dry-run mode - skipping ROS environment check")
        main()
    else:
        # Ensure ROS environment is sourced for hardware mode
        import subprocess

        # Check if ROS is sourced
        try:
            subprocess.run(['ros2', 'topic', 'list'],
                          capture_output=True, check=True, timeout=1)
        except:
            print("ERROR: ROS2 environment not sourced!")
            print("Please run:")
            print("  source /opt/ros/humble/setup.bash")
            print("  source ~/interbotix_ws/install/setup.bash")
            print("\nOR use dry-run mode for testing without hardware:")
            print("  python3 example_gemini_integration.py --dry-run")
            sys.exit(1)

        main()