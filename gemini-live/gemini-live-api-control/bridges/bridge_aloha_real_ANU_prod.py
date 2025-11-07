#!/usr/bin/env python3
"""
Real ALOHA robot bridge for Gemini Live API.
Controls the actual Mobile ALOHA gripper and arm through voice commands.
"""

import asyncio
import json
import subprocess
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions

# Add parent directory to path to import controllers
sys.path.append(str(Path(__file__).parent.parent.parent))
from gripper_controller import GripperController
from arm_controller import ArmController
from camera_controller import CameraController

# Global controller instances
gripper_controller = None
arm_controller = None
camera_controller = None
launch_process = None

# Debug logging
DEBUG_LOG_PATH = "/home/aloha/gemini-live/debug/tool_calls.log"

def log_debug(message, data=None):
    """Log debug information to file"""
    try:
        os.makedirs(os.path.dirname(DEBUG_LOG_PATH), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
            if data:
                f.write(f"  Data: {json.dumps(data, indent=2)}\n")
            f.write("-" * 80 + "\n")
    except Exception as e:
        print(f"[Debug Log Error] {e}")

async def initialize_robot():
    """Initialize the robot on startup."""
    global gripper_controller, arm_controller, camera_controller, launch_process
    
    print("[Bridge] Starting robot driver...")
    
    # Launch the minimal robot driver
    launch_script = Path(__file__).parent.parent.parent / "minimal_launch.sh"
    if launch_script.exists():
        try:
            cmd = f"source /opt/ros/humble/setup.bash && source ~/interbotix_ws/install/setup.bash && bash {str(launch_script)}"
            # Start the launch script in background
            launch_process = subprocess.Popen(
                ['bash','-c',cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Create new process group for clean shutdown
            )
            print(f"[Bridge] Robot driver launched (PID: {launch_process.pid})")
            
            # Wait a bit for driver to start
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"[Bridge] Warning: Could not launch robot driver: {e}")
            print("[Bridge] Make sure to run minimal_launch.sh manually")
    else:
        print(f"[Bridge] Launch script not found at {launch_script}")
        print("[Bridge] Please run minimal_launch.sh manually in another terminal")
    
    # Initialize the gripper controller first
    print("[Bridge] Initializing gripper controller...")
    gripper_controller = GripperController()
    
    # Try to connect to robot
    try:
        # Initialize gripper first
        gripper_success = gripper_controller.initialize()
        if gripper_success:
            print("[Bridge] ✓ Gripper controller initialized successfully")
            # Get initial state
            state = gripper_controller.get_gripper_state()
            print(f"[Bridge] Initial gripper state: {state['state']} ({state['position_normalized']*100:.1f}% open)")
            
            # Initialize arm controller sharing the same bot and node
            print("[Bridge] Initializing arm controller (sharing robot interface)...")
            arm_controller = ArmController(
                robot_model='vx300s',
                robot_name='follower_left',
                node=gripper_controller.node,  # Share the node
                bot=gripper_controller.bot      # Share the bot
            )
            
            # Initialize arm (will use existing bot)
            arm_success = arm_controller.initialize()
            if arm_success:
                print("[Bridge] ✓ Arm controller initialized successfully")
                # Get initial state
                arm_state = arm_controller.get_arm_state()
                if arm_state['pose']:
                    print(f"[Bridge] Arm at {arm_state['pose']} pose")
                else:
                    print(f"[Bridge] Arm joints: {[f'{j:.2f}' for j in arm_state['joints_degrees']]}°")
            else:
                print("[Bridge] ✗ Failed to initialize arm controller")
        else:
            print("[Bridge] ✗ Failed to initialize gripper controller")
            # Still create arm controller for mock mode
            arm_controller = ArmController()
            
        if not (gripper_success and arm_success):
            print("[Bridge] Make sure the robot is powered on and connected")
    except Exception as e:
        print(f"[Bridge] ✗ Error initializing controllers: {e}")
        print("[Bridge] Running in mock mode - no real robot control")
    
    # Initialize camera controller (separate from robot control)
    print("[Bridge] Initializing camera controller...")
    camera_controller = CameraController()
    try:
        camera_success = camera_controller.initialize()
        if camera_success:
            print("[Bridge] ✓ Camera controller initialized successfully")
            info = camera_controller.get_camera_info()
            for cam_name in info['cameras'].keys():
                print(f"[Bridge]   - {cam_name} ready")
        else:
            print("[Bridge] ✗ Camera controller initialization failed")
            print("[Bridge] Camera feeds will not be available")
    except Exception as e:
        print(f"[Bridge] ✗ Error initializing cameras: {e}")

async def handle_tool_call(request: web.Request) -> web.Response:
    """Handle tool calls from Gemini Live API via React bridge."""
    global gripper_controller, arm_controller
    
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
        
        print(f"[Bridge] Tool call: {name} with args: {args}")
        
        result = None
        
        if name == 'control_gripper':
            action = args.get('action', 'open').lower()
            
            if gripper_controller and gripper_controller.initialized:
                # Control real gripper
                if action == 'open':
                    result = gripper_controller.open_gripper()
                elif action == 'close':
                    result = gripper_controller.close_gripper()
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown action: {action}",
                        "state": "unknown"
                    }
            else:
                # Mock response if no real robot
                result = {
                    "success": True,
                    "state": action,
                    "position_normalized": 1.0 if action == 'open' else 0.0,
                    "note": "mock mode - no real robot"
                }
            
            print(f"[Bridge] Gripper action '{action}' completed: {result['state']}")
            
        elif name == 'get_gripper_status':
            if gripper_controller and gripper_controller.initialized:
                # Get real gripper status
                result = gripper_controller.get_gripper_state()
            else:
                # Mock response
                result = {
                    "success": True,
                    "state": "open",
                    "position": 1.62,
                    "position_normalized": 1.0,
                    "note": "mock mode - no real robot"
                }
            
            percentage = result.get('position_normalized', 0) * 100
            print(f"[Bridge] Gripper status: {result['state']} ({percentage:.1f}% open)")
            
        elif name == 'move_arm':
            # Handle arm movement with flexible input
            if arm_controller and arm_controller.initialized:
                # Check what type of movement is requested
                if 'pose' in args:
                    # Named pose
                    result = arm_controller.move_to_pose(
                        args['pose'],
                        moving_time=args.get('moving_time'),
                        blocking=False  # Don't block HTTP response
                    )
                elif 'joints' in args:
                    # Joint space control
                    result = arm_controller.move_joints(
                        args['joints'],
                        unit=args.get('unit', 'auto'),
                        moving_time=args.get('moving_time'),
                        blocking=False
                    )
                elif 'position' in args:
                    # Cartesian space control
                    result = arm_controller.move_to_position(
                        args['position'],
                        orientation=args.get('orientation'),
                        format=args.get('format', 'auto'),
                        moving_time=args.get('moving_time'),
                        blocking=False
                    )
                else:
                    result = {
                        "success": False,
                        "error": "No target specified (need 'pose', 'joints', or 'position')"
                    }
            else:
                # Mock response
                result = {
                    "success": True,
                    "state": "moving",
                    "note": "mock mode - no real robot"
                }
            
            print(f"[Bridge] Arm movement: {result.get('state', 'error')}")
            
        elif name == 'get_arm_status':
            # Get current arm state
            if arm_controller and arm_controller.initialized:
                result = arm_controller.get_arm_state()
            else:
                # Mock response
                result = {
                    "success": True,
                    "state": "idle",
                    "joints": [0.0] * 6,
                    "joints_degrees": [0.0] * 6,
                    "pose": "home",
                    "note": "mock mode - no real robot"
                }
            
            print(f"[Bridge] Arm status: {result['state']}")
            
        elif name == 'move_arm_trajectory':
            # Execute multi-waypoint trajectory with gripper coordination
            trajectory = args.get('trajectory', [])
            speed = args.get('speed', 'slow')  # Default to slow for safety

            if arm_controller and arm_controller.initialized:
                # Use non-blocking execution to get trajectory_id
                result = arm_controller.execute_trajectory(
                    waypoints=trajectory,
                    speed=speed,
                    coordinate_with_gripper=gripper_controller if gripper_controller and gripper_controller.initialized else None,
                    blocking=False  # Non-blocking - returns trajectory_id immediately
                )

                if result.get('success'):
                    trajectory_id = result['trajectory_id']
                    print(f"[Bridge] Started trajectory {trajectory_id} ({result['total_waypoints']} waypoints)")

                    # Return trajectory_id for status polling
                    result = {
                        'success': True,
                        'trajectory_id': trajectory_id,
                        'status': 'started',
                        'total_waypoints': result['total_waypoints']
                    }
            else:
                result = {
                    'success': False,
                    'error': 'Arm controller not initialized'
                }
            
        elif name == 'detect_and_target_object':
            # Visual object detection and targeting (placeholder for now)
            object_desc = args.get('object_description', '')
            action = args.get('action', 'approach')
            approach_height = args.get('approach_height', 0.05)
            
            # For now, return a mock trajectory based on current visual input
            # In future, this would use actual computer vision
            result = {
                'success': True,
                'object_found': True,
                'object_description': object_desc,
                'suggested_trajectory': [
                    {'point': [0.3, 0.0, 0.25], 'label': 'approach'},
                    {'point': [0.3, 0.0, 0.15], 'label': 'target'}
                ],
                'note': 'Visual detection placeholder - using default trajectory'
            }
            print(f"[Bridge] Object detection for: {object_desc}")
            
        elif name == 'analyze_workspace':
            # Analyze workspace using camera feeds
            analysis_type = args.get('analysis_type', 'object_detection')
            
            # Get current camera frames for analysis
            camera_info = {}
            if camera_controller and camera_controller.initialized:
                camera_info = camera_controller.get_camera_info()
            
            result = {
                'success': True,
                'analysis_type': analysis_type,
                'camera_status': camera_info,
                'workspace_clear': True,
                'objects_detected': [],
                'note': 'Workspace analysis placeholder'
            }
            print(f"[Bridge] Workspace analysis: {analysis_type}")
            
        elif name == 'emergency_stop':
            # Emergency stop for safety
            results = []
            if arm_controller and arm_controller.initialized:
                arm_result = arm_controller.emergency_stop()
                results.append(f"Arm: {arm_result.get('state', 'error')}")
            result = {
                "success": True,
                "results": results,
                "state": "emergency_stopped"
            }
            print(f"[Bridge] EMERGENCY STOP executed")
            
        elif name == 'get_robot_status':
            # For compatibility with existing UI - combined status
            status_result = {"ts": time.time()}
            
            if gripper_controller and gripper_controller.initialized:
                gripper_state = gripper_controller.get_gripper_state()
                status_result["gripper"] = {
                    "state": gripper_state['state'],
                    "position_percent": gripper_state['position_normalized'] * 100
                }
            else:
                status_result["gripper"] = {"state": "unknown", "position_percent": 0}
            
            if arm_controller and arm_controller.initialized:
                arm_state = arm_controller.get_arm_state()
                status_result["arm"] = {
                    "state": arm_state['state'],
                    "pose": arm_state.get('pose'),
                    "joints_degrees": arm_state.get('joints_degrees', [0]*6)
                }
            else:
                status_result["arm"] = {"state": "unknown", "pose": None}
            
            result = status_result
            
        else:
            # Log unknown tool
            log_debug(f"UNKNOWN TOOL: {name}", {
                "name": name,
                "args": args,
                "error": "Tool not recognized"
            })
            return web.json_response({
                'success': False,
                'error': f'Unknown tool: {name}'
            }, status=400)
        
        # Return response
        response = {
            'success': True,
            'result': result,
            'call_id': call_id
        }
        
        # Log response
        log_debug(f"TOOL RESPONSE: {name}", {
            "name": name,
            "success": response.get('success'),
            "result_summary": str(result)[:200] if result else None
        })
        
        return web.json_response(response)
        
    except Exception as e:
        print(f"[Bridge] Error handling tool call: {e}")
        log_debug(f"TOOL ERROR", {
            "error": str(e),
            "name": name if 'name' in locals() else 'unknown'
        })
        return web.json_response({
            'success': False,
            'error': str(e)
        }, status=500)

async def handle_camera_frame(request: web.Request) -> web.Response:
    """Get a frame from a specific camera."""
    global camera_controller
    
    camera_name = request.match_info.get('camera_name', 'gripper_cam')
    
    if not camera_controller or not camera_controller.initialized:
        return web.json_response({
            'success': False,
            'error': 'Camera controller not initialized'
        }, status=503)
    
    # Get frame as base64 JPEG
    frame_b64 = camera_controller.get_frame_base64(camera_name)
    
    if frame_b64:
        return web.json_response({
            'success': True,
            'camera': camera_name,
            'frame': frame_b64,
            'format': 'jpeg_base64'
        })
    else:
        return web.json_response({
            'success': False,
            'error': f'No frame available from {camera_name}'
        }, status=404)

async def handle_camera_info(request: web.Request) -> web.Response:
    """Get information about available cameras."""
    global camera_controller
    
    if not camera_controller:
        return web.json_response({
            'success': False,
            'error': 'Camera controller not initialized'
        }, status=503)
    
    info = camera_controller.get_camera_info()
    return web.json_response({
        'success': True,
        **info
    })

async def handle_trajectory_status(request: web.Request) -> web.Response:
    """Get status of trajectory execution."""
    global arm_controller

    trajectory_id = request.match_info.get('trajectory_id')

    if not trajectory_id:
        return web.json_response({
            'success': False,
            'error': 'Missing trajectory_id parameter'
        }, status=400)

    if arm_controller and arm_controller.initialized:
        status = arm_controller.get_trajectory_status(trajectory_id)
        return web.json_response(status)
    else:
        return web.json_response({
            'success': False,
            'error': 'Arm controller not initialized'
        }, status=503)

async def handle_cancel_trajectory(request: web.Request) -> web.Response:
    """Cancel trajectory execution."""
    global arm_controller

    trajectory_id = request.match_info.get('trajectory_id')

    if not trajectory_id:
        return web.json_response({
            'success': False,
            'error': 'Missing trajectory_id parameter'
        }, status=400)

    if arm_controller and arm_controller.initialized:
        result = arm_controller.cancel_trajectory(trajectory_id)
        return web.json_response(result)
    else:
        return web.json_response({
            'success': False,
            'error': 'Arm controller not initialized'
        }, status=503)

async def handle_list_trajectories(request: web.Request) -> web.Response:
    """List all tracked trajectories (active and completed)."""
    global arm_controller

    if arm_controller and arm_controller.initialized:
        result = arm_controller.list_trajectories()
        return web.json_response(result)
    else:
        return web.json_response({
            'success': False,
            'error': 'Arm controller not initialized'
        }, status=503)

async def handle_status(request: web.Request) -> web.Response:
    """Simple status endpoint to check if bridge is running."""
    global gripper_controller, arm_controller, camera_controller
    
    status = {
        "bridge": "running",
        "gripper_initialized": gripper_controller.initialized if gripper_controller else False,
        "arm_initialized": arm_controller.initialized if arm_controller else False,
        "camera_initialized": camera_controller.initialized if camera_controller else False,
        "timestamp": time.time()
    }
    
    if gripper_controller and gripper_controller.initialized:
        gripper_state = gripper_controller.get_gripper_state()
        status["gripper"] = {
            "state": gripper_state['state'],
            "position_percent": gripper_state['position_normalized'] * 100
        }
    
    if arm_controller and arm_controller.initialized:
        arm_state = arm_controller.get_arm_state()
        status["arm"] = {
            "state": arm_state['state'],
            "pose": arm_state.get('pose'),
            "joints_degrees": arm_state.get('joints_degrees', [0]*6)[:3]  # Show first 3 joints
        }
    
    if camera_controller and camera_controller.initialized:
        camera_info = camera_controller.get_camera_info()
        status["cameras"] = list(camera_info['cameras'].keys())
    
    return web.json_response(status)

async def cleanup(app):
    """Cleanup on shutdown."""
    global gripper_controller, arm_controller, camera_controller, launch_process
    
    print("\n[Bridge] Shutting down...")
    
    # Shutdown arm controller
    if arm_controller:
        try:
            arm_controller.move_to_pose('sleep', blocking=True)
            arm_controller.shutdown()
            print("[Bridge] Arm controller shutdown complete")
        except:
            pass
    
    # Shutdown camera controller
    if camera_controller:
        try:
            camera_controller.shutdown()
            print("[Bridge] Camera controller shutdown complete")
        except:
            pass
    
    # Shutdown gripper controller
    if gripper_controller:
        try:
            gripper_controller.sleep_arm()
            gripper_controller.shutdown()
            print("[Bridge] Gripper controller shutdown complete")
        except:
            pass
    
    # Terminate launch process
    if launch_process:
        try:
            import signal
            os.killpg(os.getpgid(launch_process.pid), signal.SIGTERM)
            print("[Bridge] Robot driver terminated")
        except:
            pass

async def startup(app):
    """Initialize robot on startup."""
    await initialize_robot()

def make_app() -> web.Application:
    """Create the aiohttp application."""
    app = web.Application()
    
    
    # Setup CORS for browser access
    cors = setup(app, defaults={
        '*': ResourceOptions(
            allow_credentials=True,
            expose_headers='*',
            allow_headers='*',
            allow_methods='*'
        )
    })
    
    # Add routes
    app.router.add_post('/aloha-tool-call', handle_tool_call)
    app.router.add_get('/status', handle_status)
    app.router.add_get('/camera/{camera_name}/frame', handle_camera_frame)
    app.router.add_get('/camera/info', handle_camera_info)

    # Trajectory management routes
    app.router.add_get('/trajectory/{trajectory_id}/status', handle_trajectory_status)
    app.router.add_post('/trajectory/{trajectory_id}/cancel', handle_cancel_trajectory)
    app.router.add_get('/trajectories', handle_list_trajectories)
    
    # Add CORS to routes
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Add startup and cleanup handlers
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    
    return app

if __name__ == '__main__':
    print("=" * 60)
    print("ALOHA Robot Bridge for Gemini Live API")
    print("=" * 60)
    print()
    print("This bridge controls the REAL Mobile ALOHA robot.")
    print("Make sure the robot is powered on and connected.")
    print()
    print("Starting bridge server on http://localhost:8081")
    print("Endpoint: POST /aloha-tool-call")
    print("Status: GET /status")
    print()
    
    # Check for dependencies
    try:
        import aiohttp
        import aiohttp_cors
    except ImportError:
        print("ERROR: Missing dependencies!")
        print("Please install: pip install aiohttp aiohttp-cors")
        sys.exit(1)
    
    # Source ROS environment
    print("Sourcing ROS environment...")
    # os.system("source /opt/ros/humble/setup.bash")
    # os.system("source ~/interbotix_ws/install/setup.bash")
    
    # Run the server
    web.run_app(make_app(), host='0.0.0.0', port=8081)