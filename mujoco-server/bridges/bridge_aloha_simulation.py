#!/usr/bin/env python3
"""
Simulation ALOHA robot bridge for Gemini Live API.
Translates Gemini tool calls to MuJoCo WebSocket commands.

This bridge provides the same API as bridge_aloha_real.py but connects to
the MuJoCo simulation server instead of real robot hardware.
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions
import socketio

# Global WebSocket client for MuJoCo server
mujoco_client = None
connected = False

# Debug logging
DEBUG_LOG_PATH = Path(__file__).parent.parent / "debug" / "simulation_tool_calls.log"

def log_debug(message, data=None):
    """Log debug information to file"""
    try:
        DEBUG_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
            if data:
                f.write(f"  Data: {json.dumps(data, indent=2)}\n")
            f.write("-" * 80 + "\n")
    except Exception as e:
        print(f"[Debug Log Error] {e}")


async def connect_to_mujoco():
    """Connect to MuJoCo simulation server via WebSocket"""
    global mujoco_client, connected

    print("[SimBridge] Connecting to MuJoCo server...")

    mujoco_client = socketio.Client()

    @mujoco_client.on('connect')
    def on_connect():
        global connected
        connected = True
        print("[SimBridge] ✓ Connected to MuJoCo server (localhost:5000)")

    @mujoco_client.on('disconnect')
    def on_disconnect():
        global connected
        connected = False
        print("[SimBridge] ✗ Disconnected from MuJoCo server")

    @mujoco_client.on('command_result')
    def on_command_result(data):
        if data.get('success'):
            print(f"[SimBridge] ✓ Command succeeded: {data.get('command', 'unknown')}")
        else:
            print(f"[SimBridge] ✗ Command failed: {data.get('error', 'unknown error')}")

    @mujoco_client.on('connection_status')
    def on_status(data):
        print(f"[SimBridge] MuJoCo status: {data.get('message', 'unknown')}")

    try:
        mujoco_client.connect('http://localhost:5000')
        await asyncio.sleep(1)  # Give connection time to establish
        return connected
    except Exception as e:
        print(f"[SimBridge] ✗ Failed to connect to MuJoCo server: {e}")
        print("[SimBridge] Make sure simulation_server.py is running on port 5000")
        return False


async def handle_tool_call(request: web.Request) -> web.Response:
    """Handle tool calls from Gemini Live API via React bridge."""
    global mujoco_client, connected

    try:
        data = await request.json()
        name = data.get('name')
        args = data.get('args', {})
        call_id = data.get('id')

        # Log incoming tool call
        log_debug(f"TOOL CALL RECEIVED: {name}", {
            "name": name,
            "args": args,
            "call_id": call_id,
            "timestamp": datetime.now().isoformat()
        })

        print(f"[SimBridge] Tool call: {name} with args: {args}")

        if not connected:
            print("[SimBridge] ✗ Not connected to MuJoCo server")
            return web.json_response({
                "success": False,
                "error": "Not connected to simulation server"
            })

        result = None

        if name == 'control_gripper':
            # Map Gemini's gripper action to MuJoCo command
            action = args.get('action', 'open').lower()
            arm = args.get('arm', 'left')  # Default to left arm

            mujoco_client.emit('control_gripper', {
                'arm': arm,
                'command': action  # 'open' or 'close'
            })

            result = {
                "success": True,
                "state": action,
                "arm": arm,
                "note": "simulation mode"
            }
            print(f"[SimBridge] Gripper action '{action}' sent to {arm} arm")

        elif name == 'get_gripper_status':
            arm = args.get('arm', 'left')

            # Request status from MuJoCo
            mujoco_client.emit('get_gripper_status', {'arm': arm})

            # Return mock status for now (async status updates come via WebSocket events)
            result = {
                "success": True,
                "state": "unknown",
                "arm": arm,
                "note": "simulation mode - status requested"
            }
            print(f"[SimBridge] Gripper status requested for {arm} arm")

        elif name == 'move_arm':
            arm = args.get('arm', 'left')

            # Handle different movement types
            if 'pose' in args:
                # Named pose - map to predefined positions
                pose = args['pose'].lower()
                if pose == 'home':
                    positions = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
                elif pose == 'ready':
                    positions = [0.0, -0.5, 0.8, 0.0, -0.5, 0.0]
                elif pose == 'sleep':
                    positions = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown pose: {pose}"
                    }
                    print(f"[SimBridge] ✗ Unknown pose: {pose}")
                    return web.json_response(result)

                mujoco_client.emit('move_arm', {
                    'arm': arm,
                    'positions': positions
                })

                result = {
                    "success": True,
                    "state": "moving",
                    "pose": pose,
                    "arm": arm,
                    "note": "simulation mode"
                }
                print(f"[SimBridge] Moving {arm} arm to '{pose}' pose")

            elif 'joints' in args:
                # Joint space control
                joints = args['joints']
                mujoco_client.emit('move_arm', {
                    'arm': arm,
                    'positions': joints
                })

                result = {
                    "success": True,
                    "state": "moving",
                    "joints": joints,
                    "arm": arm,
                    "note": "simulation mode"
                }
                print(f"[SimBridge] Moving {arm} arm to joint positions: {joints}")

            elif 'position' in args:
                # Cartesian space control - not directly supported by current MuJoCo server
                # Would need IK solver
                result = {
                    "success": False,
                    "error": "Cartesian control not yet implemented in simulation",
                    "note": "Use joint space control instead"
                }
                print(f"[SimBridge] ✗ Cartesian control not implemented")
            else:
                result = {
                    "success": False,
                    "error": "No target specified (need 'pose', 'joints', or 'position')"
                }
                print(f"[SimBridge] ✗ No movement target specified")

        elif name == 'get_arm_status':
            arm = args.get('arm', 'left')

            # Request status from MuJoCo
            mujoco_client.emit('get_arm_status', {'arm': arm})

            # Return mock status (async updates come via WebSocket)
            result = {
                "success": True,
                "state": "idle",
                "arm": arm,
                "note": "simulation mode - status requested"
            }
            print(f"[SimBridge] Arm status requested for {arm} arm")

        elif name == 'move_arm_trajectory':
            # Multi-waypoint trajectory execution
            arm = args.get('arm', 'left')
            trajectory = args.get('trajectory', [])
            speed = args.get('speed', 'medium')

            if not trajectory:
                result = {
                    "success": False,
                    "error": "No trajectory waypoints provided"
                }
            else:
                # Execute trajectory sequentially
                print(f"[SimBridge] Executing trajectory with {len(trajectory)} waypoints")

                for i, waypoint in enumerate(trajectory):
                    point = waypoint.get('point')
                    label = waypoint.get('label', f'waypoint_{i}')
                    gripper_action = waypoint.get('gripper_action', 'maintain')

                    print(f"[SimBridge]   {i+1}. {label}: point={point}, gripper={gripper_action}")

                    # Move arm (if point is joint positions)
                    if point and len(point) >= 3:
                        # Assume point is [x, y, z] or joint positions
                        if len(point) == 3:
                            # Would need IK for Cartesian - skip for now
                            print(f"[SimBridge]      (Cartesian control not implemented)")
                        else:
                            # Joint positions
                            mujoco_client.emit('move_arm', {
                                'arm': arm,
                                'positions': point
                            })

                    # Control gripper
                    if gripper_action in ['open', 'close']:
                        mujoco_client.emit('control_gripper', {
                            'arm': arm,
                            'command': gripper_action
                        })

                    # Wait between waypoints (speed-dependent)
                    speed_delays = {'slow': 2.5, 'medium': 1.5, 'fast': 0.8}
                    await asyncio.sleep(speed_delays.get(speed, 1.5))

                result = {
                    "success": True,
                    "waypoints_executed": len(trajectory),
                    "arm": arm,
                    "note": "simulation mode"
                }
                print(f"[SimBridge] ✓ Trajectory execution complete")

        elif name == 'reset_robot':
            # Reset both arms to home position
            print(f"[SimBridge] Resetting robot to home position")
            mujoco_client.emit('reset_robot')

            result = {
                "success": True,
                "state": "reset",
                "note": "simulation mode"
            }

        else:
            # Unknown tool
            result = {
                "success": False,
                "error": f"Unknown tool: {name}"
            }
            print(f"[SimBridge] ✗ Unknown tool: {name}")

        # Log result
        log_debug(f"TOOL RESULT: {name}", result)

        # Fire-and-forget pattern - return immediately
        return web.json_response(result)

    except Exception as e:
        error_msg = f"Error handling tool call: {e}"
        print(f"[SimBridge] ✗ {error_msg}")
        log_debug(f"ERROR: {error_msg}")
        return web.json_response({
            "success": False,
            "error": error_msg
        })


async def handle_status(request: web.Request) -> web.Response:
    """Health check endpoint"""
    global connected
    return web.json_response({
        "bridge": "simulation",
        "connected_to_mujoco": connected,
        "server": "localhost:5000",
        "timestamp": datetime.now().isoformat()
    })


async def on_startup(app):
    """Initialize connections on startup"""
    print("=" * 60)
    print("Starting Gemini-MuJoCo Simulation Bridge")
    print("  Bridge Port: 8082")
    print("  MuJoCo Server: localhost:5000")
    print("=" * 60)

    # Connect to MuJoCo server
    success = await connect_to_mujoco()
    if success:
        print("[SimBridge] ✓ Bridge ready to receive Gemini tool calls")
    else:
        print("[SimBridge] ⚠ Running without MuJoCo connection")
        print("[SimBridge] Start simulation_server.py on port 5000")


async def on_cleanup(app):
    """Cleanup on shutdown"""
    global mujoco_client, connected
    if mujoco_client and connected:
        mujoco_client.disconnect()
        print("[SimBridge] Disconnected from MuJoCo server")


def main():
    # Create web application
    app = web.Application()

    # Add routes
    app.router.add_post('/aloha-tool-call', handle_tool_call)
    app.router.add_get('/status', handle_status)

    # Setup CORS
    cors = setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Configure CORS for all routes
    for route in list(app.router.routes()):
        cors.add(route)

    # Setup lifecycle handlers
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    # Run server
    print("\n[SimBridge] Starting HTTP server on port 8082...")
    print("[SimBridge] Press Ctrl+C to stop\n")
    web.run_app(app, host='0.0.0.0', port=8082)


if __name__ == '__main__':
    main()
