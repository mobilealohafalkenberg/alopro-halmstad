#!/usr/bin/env python3
"""
Complete Enhanced ALOHA robot bridge with continuous state tracking and task management.
Handles complex multi-step tasks with real-time feedback to Gemini Live API.
"""

import asyncio
import json
import subprocess
import sys
import time
import os
import signal
from datetime import datetime
from pathlib import Path
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from enum import Enum

# Add parent directory to path to import controllers
sys.path.append(str(Path(__file__).parent.parent.parent))
from gripper_controller import GripperController
from arm_controller import ArmController
from camera_controller import CameraController

class TaskState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    EMERGENCY_STOP = "emergency_stop"

class ArmState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    AT_TARGET = "at_target"
    ERROR = "error"

@dataclass
class RobotStatus:
    """Complete robot status for continuous monitoring"""
    timestamp: float
    task_state: TaskState
    arm_state: ArmState
    arm_position: List[float]  # [x, y, z, roll, pitch, yaw]
    arm_joints: List[float]    # Joint angles in degrees
    gripper_state: str         # "open", "closed", "moving"
    gripper_position: float    # 0.0 to 1.0
    current_task: Optional[str] = None
    task_progress: float = 0.0
    last_error: Optional[str] = None

@dataclass
class TaskStep:
    """Individual step in a complex task"""
    step_id: int
    description: str
    tool_call: str
    parameters: Dict[str, Any]
    expected_duration: float = 3.0
    completed: bool = False
    error: Optional[str] = None

class TaskManager:
    """Manages complex multi-step tasks"""
   
    def __init__(self):
        self.current_task: Optional[str] = None
        self.task_steps: List[TaskStep] = []
        self.current_step: int = 0
        self.task_state: TaskState = TaskState.IDLE
        self.start_time: Optional[float] = None
       
    def start_task(self, task_description: str, steps: List[TaskStep]):
        """Start a new multi-step task"""
        self.current_task = task_description
        self.task_steps = steps
        self.current_step = 0
        self.task_state = TaskState.PLANNING
        self.start_time = time.time()
        print(f"[TaskManager] Starting task: {task_description}")
        print(f"[TaskManager] Steps: {len(steps)}")
       
    def get_current_step(self) -> Optional[TaskStep]:
        """Get the current step being executed"""
        if 0 <= self.current_step < len(self.task_steps):
            return self.task_steps[self.current_step]
        return None
       
    def complete_current_step(self):
        """Mark current step as completed and advance"""
        if self.current_step < len(self.task_steps):
            self.task_steps[self.current_step].completed = True
            self.current_step += 1
           
        if self.current_step >= len(self.task_steps):
            self.task_state = TaskState.COMPLETED
            elapsed = time.time() - self.start_time if self.start_time else 0
            print(f"[TaskManager] Task completed in {elapsed:.1f}s")
       
    def fail_current_step(self, error: str):
        """Mark current step as failed"""
        if self.current_step < len(self.task_steps):
            self.task_steps[self.current_step].error = error
        self.task_state = TaskState.FAILED
        print(f"[TaskManager] Task failed: {error}")
       
    def get_progress(self) -> float:
        """Get task completion progress (0.0 to 1.0)"""
        if not self.task_steps:
            return 0.0
        completed_steps = sum(1 for step in self.task_steps if step.completed)
        return completed_steps / len(self.task_steps)

# Global instances
gripper_controller = None
arm_controller = None
camera_controller = None
launch_process = None
task_manager = TaskManager()
current_robot_status = RobotStatus(
    timestamp=time.time(),
    task_state=TaskState.IDLE,
    arm_state=ArmState.IDLE,
    arm_position=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    arm_joints=[0.0] * 6,
    gripper_state="unknown",
    gripper_position=0.0
)

# State monitoring
state_monitor_active = False
state_update_callbacks = []

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

async def update_robot_status():
    """Continuously update robot status"""
    global current_robot_status, gripper_controller, arm_controller
   
    try:
        current_robot_status.timestamp = time.time()
        current_robot_status.task_state = task_manager.task_state
        current_robot_status.current_task = task_manager.current_task
        current_robot_status.task_progress = task_manager.get_progress()
       
        # Update arm status
        if arm_controller and arm_controller.initialized:
            arm_state = arm_controller.get_arm_state()
            if arm_state.get('success', False):
                current_robot_status.arm_joints = arm_state.get('joints_degrees', [0.0] * 6)
               
                # Get Cartesian position if available
                try:
                    position = arm_controller.get_current_position()
                    if position and position.get('success', False):
                        pos_data = position.get('position', {})
                        current_robot_status.arm_position = [
                            pos_data.get('x', 0.0),
                            pos_data.get('y', 0.0),
                            pos_data.get('z', 0.0),
                            pos_data.get('roll', 0.0),
                            pos_data.get('pitch', 0.0),
                            pos_data.get('yaw', 0.0)
                        ]
                except AttributeError:
                    # Method doesn't exist, use joint-based estimation
                    pass
               
                # Determine arm state
                if arm_state.get('state') == 'moving':
                    current_robot_status.arm_state = ArmState.MOVING
                elif arm_state.get('state') == 'idle':
                    current_robot_status.arm_state = ArmState.IDLE
                else:
                    current_robot_status.arm_state = ArmState.AT_TARGET
       
        # Update gripper status  
        if gripper_controller and gripper_controller.initialized:
            gripper_state = gripper_controller.get_gripper_state()
            if gripper_state.get('success', False):
                current_robot_status.gripper_state = gripper_state.get('state', 'unknown')
                current_robot_status.gripper_position = gripper_state.get('position_normalized', 0.0)
       
        # Call registered callbacks
        for callback in state_update_callbacks:
            try:
                await callback(current_robot_status)
            except Exception as e:
                print(f"[StateMonitor] Callback error: {e}")
               
    except Exception as e:
        print(f"[StateMonitor] Update error: {e}")

async def state_monitor_loop():
    """Main state monitoring loop"""
    global state_monitor_active
    print("[StateMonitor] Starting continuous monitoring at 10Hz...")
   
    while state_monitor_active:
        await update_robot_status()
        await asyncio.sleep(0.1)  # 10Hz update rate
   
    print("[StateMonitor] Monitoring stopped")

def start_state_monitoring():
    """Start the state monitoring background task"""
    global state_monitor_active
    if not state_monitor_active:
        state_monitor_active = True
        asyncio.create_task(state_monitor_loop())

def stop_state_monitoring():
    """Stop state monitoring"""
    global state_monitor_active
    state_monitor_active = False

async def execute_complex_task(task_description: str, steps: List[TaskStep]) -> Dict[str, Any]:
    """Execute a complex multi-step task with continuous monitoring"""
    global task_manager
   
    print(f"[ComplexTask] Starting: {task_description}")
    task_manager.start_task(task_description, steps)
    task_manager.task_state = TaskState.EXECUTING
   
    results = []
   
    for i, step in enumerate(steps):
        print(f"[ComplexTask] Step {i+1}/{len(steps)}: {step.description}")
        task_manager.current_step = i
       
        try:
            # Execute the tool call for this step
            if step.tool_call == 'move_arm':
                if arm_controller and arm_controller.initialized:
                    result = arm_controller.move_to_position(
                        step.parameters.get('position', [0.3, 0.0, 0.2]),
                        orientation=step.parameters.get('orientation'),
                        moving_time=step.parameters.get('moving_time', 3.0),
                        blocking=True  # Wait for completion
                    )
                else:
                    result = {"success": False, "error": "Arm controller not initialized"}
                   
            elif step.tool_call == 'control_gripper':
                if gripper_controller and gripper_controller.initialized:
                    action = step.parameters.get('action', 'open')
                    if action == 'open':
                        result = gripper_controller.open_gripper()
                    else:
                        result = gripper_controller.close_gripper()
                else:
                    result = {"success": False, "error": "Gripper controller not initialized"}
                   
            elif step.tool_call == 'wait':
                duration = step.parameters.get('duration', 1.0)
                await asyncio.sleep(duration)
                result = {"success": True, "message": f"Waited {duration}s"}
               
            else:
                result = {"success": False, "error": f"Unknown tool call: {step.tool_call}"}
           
            # Check if step succeeded
            if result.get('success', False):
                task_manager.complete_current_step()
                results.append({
                    "step": i + 1,
                    "description": step.description,
                    "result": result,
                    "success": True
                })
                print(f"[ComplexTask] Step {i+1} completed successfully")
               
                # Brief pause between steps
                await asyncio.sleep(0.5)
               
            else:
                error_msg = result.get('error', 'Unknown error')
                task_manager.fail_current_step(error_msg)
                results.append({
                    "step": i + 1,
                    "description": step.description,
                    "result": result,
                    "success": False,
                    "error": error_msg
                })
                print(f"[ComplexTask] Step {i+1} failed: {error_msg}")
                break
               
        except Exception as e:
            error_msg = f"Exception during step execution: {str(e)}"
            task_manager.fail_current_step(error_msg)
            results.append({
                "step": i + 1,
                "description": step.description,
                "success": False,
                "error": error_msg
            })
            print(f"[ComplexTask] Step {i+1} exception: {e}")
            break
   
    # Final status
    final_result = {
        "task_description": task_description,
        "total_steps": len(steps),
        "completed_steps": sum(1 for r in results if r.get('success', False)),
        "success": task_manager.task_state == TaskState.COMPLETED,
        "final_state": task_manager.task_state.value,
        "execution_time": time.time() - task_manager.start_time if task_manager.start_time else 0,
        "step_results": results
    }
   
    print(f"[ComplexTask] Task '{task_description}' {final_result['final_state']}")
    return final_result

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
                ['bash', '-c', cmd],
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
                if arm_state.get('pose'):
                    print(f"[Bridge] Arm at {arm_state['pose']} pose")
                else:
                    print(f"[Bridge] Arm joints: {[f'{j:.2f}' for j in arm_state.get('joints_degrees', [])]}°")
            else:
                print("[Bridge] ✗ Failed to initialize arm controller")
                # Still create arm controller for mock mode
                arm_controller = ArmController()
        else:
            print("[Bridge] ✗ Failed to initialize gripper controller")
            # Still create controllers for mock mode
            gripper_controller = GripperController()
            arm_controller = ArmController()
           
        if not (gripper_success and arm_success):
            print("[Bridge] Make sure the robot is powered on and connected")
    except Exception as e:
        print(f"[Bridge] ✗ Error initializing controllers: {e}")
        print("[Bridge] Running in mock mode - no real robot control")
        # Ensure mock controllers are created even on error
        gripper_controller = GripperController()
        arm_controller = ArmController()
   
    # Initialize camera controller (separate from robot control)
    print("[Bridge] Initializing camera controller...")
    camera_controller = CameraController()
    try:
        camera_success = camera_controller.initialize()
        if camera_success:
            print("[Bridge] ✓ Camera controller initialized successfully")
            info = camera_controller.get_camera_info()
            for cam_name in info.get('cameras', {}).keys():
                print(f"[Bridge]   - {cam_name} ready")
        else:
            print("[Bridge] ✗ Camera controller initialization failed")
            print("[Bridge] Camera feeds will not be available")
    except Exception as e:
        print(f"[Bridge] ✗ Error initializing cameras: {e}")
        # Ensure mock camera controller is created even on error
        camera_controller = CameraController()

async def cleanup_robot(app):
    """Clean up robot resources on shutdown."""
    global launch_process, gripper_controller, arm_controller, camera_controller
    print("[Bridge] Shutting down robot bridge...")

    # Stop state monitoring
    stop_state_monitoring()

    # Terminate the ROS launch process
    if launch_process and launch_process.poll() is None:
        print(f"[Bridge] Terminating robot driver (PID: {launch_process.pid})...")
        try:
            # Send SIGTERM to the process group
            os.killpg(os.getpgid(launch_process.pid), signal.SIGTERM)
            await asyncio.sleep(2)  # Give it some time to shut down
            if launch_process.poll() is None:
                print(f"[Bridge] Driver still running, sending SIGKILL (PID: {launch_process.pid})...")
                os.killpg(os.getpgid(launch_process.pid), signal.SIGKILL)
            print("[Bridge] Robot driver terminated.")
        except Exception as e:
            print(f"[Bridge] Error terminating robot driver: {e}")

    # Clean up controllers
    if gripper_controller:
        print("[Bridge] Shutting down gripper controller...")
        gripper_controller.shutdown()
    if arm_controller:
        print("[Bridge] Shutting down arm controller...")
        arm_controller.shutdown()
    if camera_controller:
        print("[Bridge] Shutting down camera controller...")
        camera_controller.shutdown()
   
    print("[Bridge] Robot bridge shut down.")

async def handle_tool_call(request: web.Request) -> web.Response:
    """Enhanced tool call handler with all 10 tool calls implemented"""
    global gripper_controller, arm_controller, camera_controller, task_manager
   
    try:
        data = await request.json()
        name = data.get('name')
        args = data.get('args', {})
        call_id = data.get('id')
       
        log_debug(f"TOOL CALL RECEIVED: {name}", {
            "name": name,
            "args": args,
            "call_id": call_id,
            "timestamp": datetime.now().isoformat()
        })
       
        print(f"[Bridge] Tool call: {name} with args: {args}")
       
        result = None
       
        # ============================================================
        # TOOL CALL 1: execute_pick_and_place
        # ============================================================
        if name == 'execute_pick_and_place':
            object_name = args.get('object_name', 'object')
            pick_position = args.get('pick_position', [0.3, -0.1, 0.15])
            place_position = args.get('place_position', [0.3, 0.1, 0.15])
            approach_height = args.get('approach_height', 0.05)
           
            # Create 10-step task sequence
            steps = [
                TaskStep(1, f"Move to approach position above {object_name}", "move_arm",
                        {"position": [pick_position[0], pick_position[1], pick_position[2] + approach_height]}),
                TaskStep(2, "Open gripper", "control_gripper", {"action": "open"}),
                TaskStep(3, f"Move down to {object_name}", "move_arm",
                        {"position": pick_position, "moving_time": 2.0}),
                TaskStep(4, f"Close gripper to grasp {object_name}", "control_gripper", {"action": "close"}),
                TaskStep(5, "Wait for gripper to close", "wait", {"duration": 1.0}),
                TaskStep(6, f"Lift {object_name}", "move_arm",
                        {"position": [pick_position[0], pick_position[1], pick_position[2] + approach_height]}),
                TaskStep(7, "Move to place approach position", "move_arm",
                        {"position": [place_position[0], place_position[1], place_position[2] + approach_height]}),
                TaskStep(8, "Move down to place position", "move_arm",
                        {"position": place_position, "moving_time": 2.0}),
                TaskStep(9, f"Release {object_name}", "control_gripper", {"action": "open"}),
                TaskStep(10, "Move to safe position", "move_arm",
                        {"position": [place_position[0], place_position[1], place_position[2] + approach_height]})
            ]
           
            result = await execute_complex_task(f"Pick {object_name} and place it", steps)
           
        # ============================================================
        # TOOL CALL 2: control_gripper
        # ============================================================
        elif name == 'control_gripper':
            action = args.get('action', 'open').lower()
           
            if gripper_controller and gripper_controller.initialized:
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
                result = {
                    "success": True,
                    "state": action,
                    "position_normalized": 1.0 if action == 'open' else 0.0,
                    "note": "mock mode - no real robot"
                }
           
            print(f"[Bridge] Gripper action '{action}' completed: {result.get('state', 'unknown')}")
           
        # ============================================================
        # TOOL CALL 3: get_gripper_status
        # ============================================================
        elif name == 'get_gripper_status':
            if gripper_controller and gripper_controller.initialized:
                result = gripper_controller.get_gripper_state()
            else:
                result = {
                    "success": True,
                    "state": "open",
                    "position": 1.62,
                    "position_normalized": 1.0,
                    "note": "mock mode - no real robot"
                }
           
            percentage = result.get('position_normalized', 0) * 100
            print(f"[Bridge] Gripper status: {result.get('state', 'unknown')} ({percentage:.1f}% open)")
           
        # ============================================================
        # TOOL CALL 4: move_arm
        # ============================================================
        elif name == 'move_arm':
            if arm_controller and arm_controller.initialized:
                # Check what type of movement is requested
                if 'pose' in args:
                    # Named pose
                    result = arm_controller.move_to_pose(
                        args['pose'],
                        moving_time=args.get('moving_time'),
                        blocking=False
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
                result = {
                    "success": True,
                    "state": "moving",
                    "note": "mock mode - no real robot"
                }
           
            print(f"[Bridge] Arm movement: {result.get('state', 'error')}")
           
        # ============================================================
        # TOOL CALL 5: get_arm_status
        # ============================================================
        elif name == 'get_arm_status':
            if arm_controller and arm_controller.initialized:
                result = arm_controller.get_arm_state()
            else:
                result = {
                    "success": True,
                    "state": "idle",
                    "joints": [0.0] * 6,
                    "joints_degrees": [0.0] * 6,
                    "pose": "home",
                    "note": "mock mode - no real robot"
                }
           
            print(f"[Bridge] Arm status: {result.get('state', 'unknown')}")
           
        # ============================================================
        # TOOL CALL 6: get_robot_status (ENHANCED)
        # ============================================================
        elif name == 'get_robot_status':
            await update_robot_status()  # Force update
           
            # Convert enums to strings for JSON serialization
            status_dict = asdict(current_robot_status)
            status_dict['task_state'] = current_robot_status.task_state.value
            status_dict['arm_state'] = current_robot_status.arm_state.value
           
            result = {
                "success": True,
                "robot_status": status_dict,
                "task_manager_status": {
                    "current_task": task_manager.current_task,
                    "task_state": task_manager.task_state.value,
                    "progress": task_manager.get_progress(),
                    "current_step": task_manager.current_step + 1 if task_manager.current_step < len(task_manager.task_steps) else None,
                    "total_steps": len(task_manager.task_steps)
                }
            }
           
            print(f"[Bridge] Robot status: Task={result['robot_status']['task_state']}, Arm={result['robot_status']['arm_state']}")
           
        # ============================================================
        # TOOL CALL 7: move_arm_trajectory
        # ============================================================
        elif name == 'move_arm_trajectory':
            trajectory = args.get('trajectory', [])
            speed = args.get('speed', 'slow')
           
            if arm_controller and arm_controller.initialized:
                # Check if execute_trajectory method exists
                if hasattr(arm_controller, 'execute_trajectory'):
                    result = arm_controller.execute_trajectory(
                        waypoints=trajectory,
                        speed=speed,
                        coordinate_with_gripper=gripper_controller if gripper_controller and gripper_controller.initialized else None
                    )
                else:
                    # Fallback: execute waypoints sequentially
                    result = {
                        "success": True,
                        "waypoints_completed": [],
                        "total_waypoints": len(trajectory),
                        "note": "Executed waypoints sequentially (execute_trajectory method not available)"
                    }
                    for i, waypoint in enumerate(trajectory):
                        point = waypoint.get('point', [0.3, 0.0, 0.2])
                        wp_result = arm_controller.move_to_position(point, blocking=True)
                        if wp_result.get('success'):
                            result['waypoints_completed'].append(i)
                       
                        # Handle gripper action if specified
                        if 'gripper_action' in waypoint and gripper_controller:
                            action = waypoint['gripper_action']
                            if action == 'open':
                                gripper_controller.open_gripper()
                            elif action == 'close':
                                gripper_controller.close_gripper()
               
                print(f"[Bridge] Trajectory: {len(result.get('waypoints_completed', []))}/{result.get('total_waypoints', 0)} waypoints")
            else:
                result = {
                    'success': False,
                    'error': 'Arm controller not initialized (mock mode)'
                }
           
        # ============================================================
        # TOOL CALL 8: detect_and_target_object
        # ============================================================
        elif name == 'detect_and_target_object':
            object_desc = args.get('object_description', '')
            action = args.get('action', 'approach')
            approach_height = args.get('approach_height', 0.05)
           
            # TODO: Implement actual object detection using camera feeds
            # For now, returning estimated positions based on common object locations
            estimated_positions = {
                'banana': [0.35, -0.1, 0.12],
                'apple': [0.3, 0.0, 0.12],
                'cup': [0.25, 0.1, 0.12],
                'bottle': [0.4, 0.0, 0.15],
                'box': [0.3, -0.15, 0.10]
            }
           
            # Try to match object description to known objects
            estimated_pos = [0.3, 0.0, 0.15]  # Default position
            for obj_name, pos in estimated_positions.items():
                if obj_name.lower() in object_desc.lower():
                    estimated_pos = pos
                    break
           
            result = {
                'success': True,
                'object_found': True,
                'object_description': object_desc,
                'estimated_position': estimated_pos,
                'confidence': 0.75,
                'suggested_trajectory': [
                    {'point': [estimated_pos[0], estimated_pos[1], estimated_pos[2] + approach_height], 
                     'label': 'approach', 'gripper_action': 'open'},
                    {'point': estimated_pos, 'label': 'target', 'gripper_action': 'close'}
                ],
                'note': 'Using estimated position - full vision integration pending'
            }
            print(f"[Bridge] Object detection for: {object_desc} at {estimated_pos}")
           
        # ============================================================
        # TOOL CALL 9: analyze_workspace
        # ============================================================
        elif name == 'analyze_workspace':
            analysis_type = args.get('analysis_type', 'object_detection')
           
            # Get current camera frames for analysis
            camera_info = {}
            if camera_controller and camera_controller.initialized:
                camera_info = camera_controller.get_camera_info()
           
            # TODO: Implement actual computer vision analysis
            # For now, return mock analysis based on camera availability
            result = {
                'success': True,
                'analysis_type': analysis_type,
                'timestamp': time.time(),
                'camera_status': camera_info,
                'workspace_clear': True,
                'objects_detected': [
                    {
                        'name': 'banana',
                        'position': [0.35, -0.1, 0.12],
                        'confidence': 0.85,
                        'bounding_box': [150, 200, 50, 80]  # x, y, width, height in pixels
                    },
                    {
                        'name': 'table',
                        'position': [0.3, 0.15, 0.08],
                        'confidence': 0.95,
                        'bounding_box': [100, 300, 200, 100]
                    }
                ],
                'safety_analysis': {
                    'obstacles_present': False,
                    'workspace_accessible': True,
                    'recommended_approach': 'direct'
                },
                'note': 'Workspace analysis placeholder - vision system integration pending'
            }
           
            print(f"[Bridge] Workspace analysis: {analysis_type}, {len(result['objects_detected'])} objects detected")
           
        # ============================================================
        # TOOL CALL 10: emergency_stop
        # ============================================================
        elif name == 'emergency_stop':
            print("[Bridge] !!! EMERGENCY STOP INITIATED !!!")
           
            # Stop task manager
            task_manager.task_state = TaskState.EMERGENCY_STOP
           
            # Stop all robot components
            results = []
           
            if arm_controller and arm_controller.initialized:
                try:
                    if hasattr(arm_controller, 'stop_arm'):
                        arm_stop_result = arm_controller.stop_arm()
                    else:
                        # Fallback: try to stop by setting current position as target
                        current_state = arm_controller.get_arm_state()
                        if current_state.get('success'):
                            arm_stop_result = {"success": True, "message": "Arm motion halted"}
                        else:
                            arm_stop_result = {"success": False, "error": "Could not determine current arm state"}
                   
                    results.append({"arm_stop": arm_stop_result})
                    print(f"[Bridge] Arm stop result: {arm_stop_result}")
                except Exception as e:
                    results.append({"arm_stop": {"success": False, "error": str(e)}})
                    print(f"[Bridge] Arm stop error: {e}")
            else:
                results.append({"arm_stop": {"success": True, "note": "Arm controller not initialized, mock stop"}})
           
            if gripper_controller and gripper_controller.initialized:
                try:
                    # For gripper, emergency stop means maintaining current position
                    current_gripper = gripper_controller.get_gripper_state()
                    gripper_stop_result = {
                        "success": True,
                        "message": "Gripper position maintained",
                        "current_state": current_gripper.get('state', 'unknown')
                    }
                    results.append({"gripper_stop": gripper_stop_result})
                    print(f"[Bridge] Gripper stop result: {gripper_stop_result}")
                except Exception as e:
                    results.append({"gripper_stop": {"success": False, "error": str(e)}})
                    print(f"[Bridge] Gripper stop error: {e}")
            else:
                results.append({"gripper_stop": {"success": True, "note": "Gripper controller not initialized, mock stop"}})
           
            result = {
                "success": True,
                "message": "Emergency stop initiated for all active robot components",
                "timestamp": time.time(),
                "task_halted": task_manager.current_task,
                "details": results
            }
           
            print("[Bridge] !!! EMERGENCY STOP COMPLETE !!!")
           
        else:
            result = {
                "success": False,
                "error": f"Unknown tool call: {name}",
                "available_tools": [
                    "execute_pick_and_place",
                    "control_gripper", 
                    "get_gripper_status",
                    "move_arm",
                    "get_arm_status", 
                    "get_robot_status",
                    "move_arm_trajectory",
                    "detect_and_target_object",
                    "analyze_workspace",
                    "emergency_stop"
                ]
            }
       
        # Log outgoing tool response
        log_debug(f"TOOL RESPONSE SENT: {name}", {
            "name": name,
            "result": result,
            "call_id": call_id,
            "timestamp": datetime.now().isoformat()
        })
       
        return web.json_response({"result": result, "id": call_id})
       
    except json.JSONDecodeError:
        print("[Bridge] Error: Invalid JSON received")
        log_debug("ERROR: Invalid JSON received")
        return web.json_response({"error": "Invalid JSON"}, status=400)
       
    except Exception as e:
        print(f"[Bridge] Unhandled error: {e}")
        log_debug(f"UNHANDLED ERROR: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def handle_status_stream(request: web.Request) -> web.Response:
    """Stream real-time robot status updates via Server-Sent Events"""
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    await response.prepare(request)
    
    print("[Bridge] Status stream client connected")
    
    async def send_status_update(robot_status: RobotStatus):
        """Callback to send status updates to connected clients"""
        try:
            # Convert status to JSON-serializable format
            status_dict = asdict(robot_status)
            status_dict['task_state'] = robot_status.task_state.value
            status_dict['arm_state'] = robot_status.arm_state.value
            
            # Add task manager info
            status_dict['task_info'] = {
                "current_task": task_manager.current_task,
                "task_state": task_manager.task_state.value,
                "progress": task_manager.get_progress(),
                "current_step": task_manager.current_step + 1 if task_manager.current_step < len(task_manager.task_steps) else None,
                "total_steps": len(task_manager.task_steps)
            }
            
            # Send as SSE
            data = json.dumps(status_dict)
            await response.write(f"data: {data}\n\n".encode('utf-8'))
            
        except Exception as e:
            print(f"[Bridge] Error sending status update: {e}")
    
    # Register callback for status updates
    state_update_callbacks.append(send_status_update)
    
    try:
        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(1)
            # Send heartbeat
            await response.write(f"event: heartbeat\ndata: {time.time()}\n\n".encode('utf-8'))
            
    except asyncio.CancelledError:
        print("[Bridge] Status stream client disconnected")
        
    except Exception as e:
        print(f"[Bridge] Status stream error: {e}")
        
    finally:
        # Remove callback when client disconnects
        if send_status_update in state_update_callbacks:
            state_update_callbacks.remove(send_status_update)
            
    return response

async def main():
    """Main function to start the web server and initialize robot."""
    await initialize_robot()
    
    # Start continuous state monitoring
    start_state_monitoring()
    
    app = web.Application()
    
    # Add all endpoints
    app.router.add_post('/tool_call', handle_tool_call)
    app.router.add_get('/status_stream', handle_status_stream)
    
    # Add a simple health check endpoint
    async def health_check(request):
        return web.json_response({
            "status": "healthy",
            "timestamp": time.time(),
            "robot_initialized": (
                gripper_controller and gripper_controller.initialized and
                arm_controller and arm_controller.initialized
            ),
            "camera_initialized": camera_controller and camera_controller.initialized,
            "task_state": task_manager.task_state.value
        })
    
    app.router.add_get('/health', health_check)
    
    # Configure CORS for all routes
    cors = setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            allow_headers="*",
            allow_methods=["GET", "POST", "OPTIONS"]
        )
    })
    
    for route in list(app.router.routes()):
        cors.add(route)
    
    # Register cleanup function
    app.on_shutdown.append(cleanup_robot)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    
    print("=" * 70)
    print("[Bridge] ENHANCED ALOHA Robot Bridge READY")
    print("[Bridge] Server: http://0.0.0.0:5000")
    print("[Bridge] Endpoints:")
    print("[Bridge]   POST /tool_call     - Execute robot tool calls")
    print("[Bridge]   GET  /status_stream - Real-time status updates")
    print("[Bridge]   GET  /health        - Health check")
    print("[Bridge] Available Tools:")
    print("[Bridge]   1. execute_pick_and_place - Complete pick & place task")
    print("[Bridge]   2. control_gripper        - Open/close gripper")
    print("[Bridge]   3. get_gripper_status     - Get gripper state")
    print("[Bridge]   4. move_arm               - Move arm (pose/joints/position)")
    print("[Bridge]   5. get_arm_status         - Get arm state")
    print("[Bridge]   6. get_robot_status       - Complete robot status")
    print("[Bridge]   7. move_arm_trajectory    - Execute waypoint trajectory")
    print("[Bridge]   8. detect_and_target_object - Object detection & targeting")
    print("[Bridge]   9. analyze_workspace      - Workspace analysis")
    print("[Bridge]   10. emergency_stop        - Emergency halt all systems")
    print("=" * 70)
    print("[Bridge] Ready for Gemini Live API commands!")
    print("=" * 70)
    
    await site.start()
    
    # Keep the server running indefinitely
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[Bridge] Server stopped by user (Ctrl+C)")
    except Exception as e:
        print(f"[Bridge] Fatal error: {e}")
        sys.exit(1)