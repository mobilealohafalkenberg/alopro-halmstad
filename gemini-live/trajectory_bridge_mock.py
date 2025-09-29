#!/usr/bin/env python3
"""
Mock Trajectory Bridge for testing without hardware dependencies
"""

import os
import sys
import json
import asyncio
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from aiohttp import web
import aiohttp_cors
import logging
from collections import deque
from datetime import datetime, timedelta

# Add path for local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from safety_validator import SafetyValidator, ValidationResult, RiskLevel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trajectory_bridge_mock')

class JobState(Enum):
    """Job lifecycle states"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

@dataclass
class Job:
    """Represents a trajectory job"""
    job_id: str
    type: str  # move_to_pose or follow_cartesian_trajectory
    request: Dict[str, Any]
    created_at: float
    state: JobState
    dry_run: bool
    arm_side: str
    result: Optional[Dict] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    
    def to_dict(self):
        return {
            "jobId": self.job_id,
            "type": self.type,
            "state": self.state.value,
            "dryRun": self.dry_run,
            "armSide": self.arm_side,
            "progress": self.progress,
            "createdAt": self.created_at,
            "result": self.result,
            "error": self.error
        }

class MockArmController:
    """Mock arm controller for testing"""
    def __init__(self):
        self.initialized = True
        self.current_position = [0.25, 0.0, 0.2]
        self.current_joints = [0.0, -0.3, 0.6, 0.0, -0.3, 0.0]
    
    def connect(self):
        logger.info("Mock arm controller connected")
    
    def get_current_state(self):
        return {
            "joints": self.current_joints,
            "ee_position": {
                "x": self.current_position[0],
                "y": self.current_position[1],
                "z": self.current_position[2]
            },
            "pose": "home"
        }
    
    def move_to_position(self, x, y, z, moving_time=2.0):
        """Mock movement - just update position"""
        self.current_position = [x, y, z]
        return {
            "success": True,
            "position": [x, y, z],
            "time": moving_time
        }

class TrajectoryBridge:
    """
    Bridge server for trajectory-based robot control
    Implements job queueing, safety validation, and telemetry
    """
    
    def __init__(self, port=8082):
        self.port = port
        self.app = web.Application()
        self.safety_validator = SafetyValidator()
        self.arm_controller = None
        
        # Job management
        self.jobs: Dict[str, Job] = {}
        self.job_queues = {
            "left": asyncio.Queue(),
            "right": asyncio.Queue(),
            "follower_left": asyncio.Queue()  # Our actual arm
        }
        self.active_jobs = {
            "left": None,
            "right": None,
            "follower_left": None
        }
        
        # Idempotency store (simple in-memory with TTL)
        self.idempotency_store: Dict[str, Tuple[str, float]] = {}
        self.idempotency_ttl = 300  # 5 minutes
        
        # SSE connections
        self.sse_connections = []
        
        # Configuration
        self.driver_mode = 'mock'  # Always mock for this version
        self.default_moving_time = float(os.getenv('DEFAULT_MOVING_TIME', '2.0'))
        self.default_accel_time = float(os.getenv('DEFAULT_ACCEL_TIME', '0.3'))
        
        # Setup routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup HTTP routes with CORS"""
        # Trajectory endpoints
        self.app.router.add_post('/robot/move_to_pose', self.handle_move_to_pose)
        self.app.router.add_post('/robot/follow_cartesian_trajectory', self.handle_follow_trajectory)
        
        # Control endpoints
        self.app.router.add_post('/robot/stop', self.handle_stop)
        self.app.router.add_post('/robot/e_stop', self.handle_e_stop)
        
        # Status endpoints
        self.app.router.add_get('/robot/state', self.handle_get_state)
        self.app.router.add_get('/robot/telemetry', self.handle_telemetry)
        self.app.router.add_get('/robot/job/{job_id}', self.handle_get_job)
        
        # Legacy compatibility
        self.app.router.add_post('/aloha-tool-call', self.handle_legacy_tool_call)
        
        # CORS setup
        cors = aiohttp_cors.setup(self.app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(self.app.router.routes()):
            cors.add(route)
    
    async def initialize(self):
        """Initialize arm controller and start workers"""
        try:
            # Initialize mock arm controller
            self.arm_controller = MockArmController()
            self.arm_controller.connect()
            logger.info(f"Initialized mock arm controller")
            
            # Start queue workers
            for arm_side in self.job_queues.keys():
                asyncio.create_task(self._queue_worker(arm_side))
            
            # Start cleanup task for idempotency store
            asyncio.create_task(self._cleanup_idempotency_store())
            
            logger.info("Trajectory bridge (mock) initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise
    
    async def handle_move_to_pose(self, request):
        """
        Handle move_to_pose trajectory request
        Expected body: {
            arm_side: str,
            x: float, y: float, z: float,
            roll: float, pitch: float, yaw: float,
            moving_time: float (optional),
            accel_time: float (optional),
            options: { dryRun: bool, idempotencyKey: str }
        }
        """
        try:
            data = await request.json()
            
            # Check idempotency
            idempotency_key = data.get('options', {}).get('idempotencyKey')
            if idempotency_key:
                existing_job_id = self._check_idempotency(idempotency_key)
                if existing_job_id:
                    return web.json_response({
                        "accepted": False,
                        "queued": False,
                        "jobId": existing_job_id,
                        "message": "Duplicate request",
                        "requestId": data.get('request_id')
                    }, status=409)
            
            # Extract parameters
            arm_side = data.get('arm_side', 'follower_left')
            x, y, z = data['x'], data['y'], data['z']
            roll = data.get('roll', 0)
            pitch = data.get('pitch', 0)
            yaw = data.get('yaw', 0)
            moving_time = data.get('moving_time', self.default_moving_time)
            accel_time = data.get('accel_time', self.default_accel_time)
            dry_run = data.get('options', {}).get('dryRun', False)
            
            # Validate position
            validation = self.safety_validator.validate_position(x, y, z)
            
            if not validation.valid:
                return web.json_response({
                    "accepted": False,
                    "queued": False,
                    "safety": {
                        "riskLevel": validation.risk_level.value,
                        "message": validation.message
                    },
                    "message": f"Safety blocked: {validation.message}",
                    "requestId": data.get('request_id')
                })
            
            # Create job
            job = Job(
                job_id=str(uuid.uuid4()),
                type="move_to_pose",
                request=data,
                created_at=time.time(),
                state=JobState.QUEUED,
                dry_run=dry_run,
                arm_side=arm_side
            )
            
            # Store job
            self.jobs[job.job_id] = job
            
            # Store idempotency key
            if idempotency_key:
                self.idempotency_store[idempotency_key] = (job.job_id, time.time())
            
            # Queue job
            await self.job_queues[arm_side].put(job)
            
            # Send telemetry
            await self._broadcast_event({
                "event": "job_queued",
                "jobId": job.job_id,
                "type": job.type,
                "armSide": arm_side
            })
            
            return web.json_response({
                "accepted": True,
                "queued": True,
                "jobId": job.job_id,
                "dryRun": dry_run,
                "safety": {
                    "riskLevel": validation.risk_level.value,
                    "notes": validation.details.get('warnings', [])
                },
                "message": "Job queued successfully",
                "requestId": data.get('request_id')
            })
            
        except Exception as e:
            logger.error(f"Error in move_to_pose: {e}")
            return web.json_response({
                "accepted": False,
                "error": str(e)
            }, status=500)
    
    async def handle_follow_trajectory(self, request):
        """
        Handle follow_cartesian_trajectory request
        Expected body: {
            arm_side: str,
            delta_x: float, delta_y: float, delta_z: float,
            delta_roll: float, delta_pitch: float, delta_yaw: float,
            moving_time: float, wp_period: float,
            options: { dryRun: bool, idempotencyKey: str }
        }
        """
        try:
            data = await request.json()
            
            # Check idempotency
            idempotency_key = data.get('options', {}).get('idempotencyKey')
            if idempotency_key:
                existing_job_id = self._check_idempotency(idempotency_key)
                if existing_job_id:
                    return web.json_response({
                        "accepted": False,
                        "queued": False,
                        "jobId": existing_job_id,
                        "message": "Duplicate request",
                        "requestId": data.get('request_id')
                    }, status=409)
            
            # Extract parameters
            arm_side = data.get('arm_side', 'follower_left')
            delta_x = data['delta_x']
            delta_y = data['delta_y']
            delta_z = data['delta_z']
            delta_roll = data.get('delta_roll', 0)
            delta_pitch = data.get('delta_pitch', 0)
            delta_yaw = data.get('delta_yaw', 0)
            moving_time = data.get('moving_time', self.default_moving_time)
            wp_period = data.get('wp_period', 0.02)
            dry_run = data.get('options', {}).get('dryRun', False)
            
            # Get current position (from mock controller)
            current_pos = self.arm_controller.current_position if self.arm_controller else [0.25, 0.0, 0.2]
            end_pos = [
                current_pos[0] + delta_x,
                current_pos[1] + delta_y,
                current_pos[2] + delta_z
            ]
            
            # Validate trajectory
            validation = self.safety_validator.validate_trajectory(
                current_pos, end_pos, moving_time
            )
            
            if not validation.valid:
                return web.json_response({
                    "accepted": False,
                    "queued": False,
                    "safety": {
                        "riskLevel": validation.risk_level.value,
                        "message": validation.message
                    },
                    "message": f"Safety blocked: {validation.message}",
                    "requestId": data.get('request_id')
                })
            
            # Create job
            job = Job(
                job_id=str(uuid.uuid4()),
                type="follow_cartesian_trajectory",
                request=data,
                created_at=time.time(),
                state=JobState.QUEUED,
                dry_run=dry_run,
                arm_side=arm_side
            )
            
            # Store job
            self.jobs[job.job_id] = job
            
            # Store idempotency key
            if idempotency_key:
                self.idempotency_store[idempotency_key] = (job.job_id, time.time())
            
            # Queue job
            await self.job_queues[arm_side].put(job)
            
            # Send telemetry
            await self._broadcast_event({
                "event": "job_queued",
                "jobId": job.job_id,
                "type": job.type,
                "armSide": arm_side
            })
            
            return web.json_response({
                "accepted": True,
                "queued": True,
                "jobId": job.job_id,
                "dryRun": dry_run,
                "safety": {
                    "riskLevel": validation.risk_level.value,
                    "notes": validation.details.get('warnings', [])
                },
                "message": "Job queued successfully",
                "requestId": data.get('request_id')
            })
            
        except Exception as e:
            logger.error(f"Error in follow_trajectory: {e}")
            return web.json_response({
                "accepted": False,
                "error": str(e)
            }, status=500)
    
    async def handle_stop(self, request):
        """Soft stop current motion"""
        try:
            # Stop all active jobs
            stopped_jobs = []
            for arm_side, job in self.active_jobs.items():
                if job and job.state == JobState.RUNNING:
                    job.state = JobState.CANCELED
                    job.error = "Stopped by user"
                    stopped_jobs.append(job.job_id)
            
            # Clear queues
            for queue in self.job_queues.values():
                while not queue.empty():
                    try:
                        job = queue.get_nowait()
                        job.state = JobState.CANCELED
                        job.error = "Canceled - stop requested"
                    except asyncio.QueueEmpty:
                        break
            
            # Send telemetry
            await self._broadcast_event({
                "event": "stop",
                "stoppedJobs": stopped_jobs
            })
            
            return web.json_response({
                "success": True,
                "stoppedJobs": stopped_jobs
            })
            
        except Exception as e:
            logger.error(f"Error in stop: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_e_stop(self, request):
        """Emergency stop - immediate halt"""
        try:
            # Cancel all jobs
            for job in self.jobs.values():
                if job.state in [JobState.QUEUED, JobState.RUNNING]:
                    job.state = JobState.CANCELED
                    job.error = "Emergency stop"
            
            # Clear all queues
            for queue in self.job_queues.values():
                while not queue.empty():
                    queue.get_nowait()
            
            # Clear active jobs
            self.active_jobs = {arm: None for arm in self.active_jobs}
            
            # Send telemetry
            await self._broadcast_event({
                "event": "e_stop",
                "timestamp": time.time()
            })
            
            return web.json_response({
                "success": True,
                "message": "Emergency stop activated"
            })
            
        except Exception as e:
            logger.error(f"Error in e_stop: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def handle_get_state(self, request):
        """Get current system state"""
        try:
            # Get arm states
            arm_states = {}
            if self.arm_controller and self.arm_controller.initialized:
                state = self.arm_controller.get_current_state()
                arm_states['follower_left'] = {
                    "joints": state.get('joints', []),
                    "ee_position": state.get('ee_position', {}),
                    "pose": state.get('pose')
                }
            
            # Get queue lengths
            queue_lengths = {
                arm: queue.qsize() 
                for arm, queue in self.job_queues.items()
            }
            
            # Get active jobs
            active_job_ids = {
                arm: job.job_id if job else None
                for arm, job in self.active_jobs.items()
            }
            
            return web.json_response({
                "connected": self.arm_controller.initialized if self.arm_controller else False,
                "driverMode": self.driver_mode,
                "arms": arm_states,
                "queueLengths": queue_lengths,
                "activeJobs": active_job_ids,
                "safetyProfile": self.safety_validator.safety_profile,
                "workspaceBounds": self.safety_validator.bounds.to_dict()
            })
            
        except Exception as e:
            logger.error(f"Error in get_state: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    async def handle_telemetry(self, request):
        """SSE endpoint for real-time telemetry"""
        response = web.StreamResponse()
        response.headers['Content-Type'] = 'text/event-stream'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        await response.prepare(request)
        
        # Add to connections list
        self.sse_connections.append(response)
        
        try:
            # Send initial ping
            await response.write(b'event: ping\ndata: {}\n\n')
            
            # Keep connection alive
            while True:
                await asyncio.sleep(10)
                await response.write(b'event: ping\ndata: {}\n\n')
                
        except Exception as e:
            logger.debug(f"SSE connection closed: {e}")
        finally:
            if response in self.sse_connections:
                self.sse_connections.remove(response)
        
        return response
    
    async def handle_get_job(self, request):
        """Get specific job status"""
        job_id = request.match_info['job_id']
        
        if job_id not in self.jobs:
            return web.json_response({
                "error": "Job not found"
            }, status=404)
        
        job = self.jobs[job_id]
        return web.json_response(job.to_dict())
    
    async def handle_legacy_tool_call(self, request):
        """Handle legacy tool calls from existing system"""
        try:
            data = await request.json()
            tool_name = data.get('name')
            args = data.get('args', {})
            
            # Map legacy calls to new endpoints
            if tool_name == 'move_arm_trajectory':
                # Convert to move_to_pose
                trajectory = args.get('trajectory', [])
                if trajectory:
                    waypoint = trajectory[0]
                    point = waypoint.get('point', [0, 0, 0])
                    
                    # Convert to new format
                    new_request = {
                        "arm_side": "follower_left",
                        "x": point[0],
                        "y": point[1],
                        "z": point[2],
                        "roll": 0,
                        "pitch": 0,
                        "yaw": 0,
                        "moving_time": args.get('speed_factor', 1.0) * 2.0,
                        "options": {
                            "dryRun": False
                        },
                        "request_id": data.get('request_id')
                    }
                    
                    # Create fake request object
                    class FakeRequest:
                        async def json(self):
                            return new_request
                    
                    result = await self.handle_move_to_pose(FakeRequest())
                    return result
            
            # Default response for unsupported tools
            return web.json_response({
                "success": True,
                "result": {"message": "Tool call received"}
            })
            
        except Exception as e:
            logger.error(f"Error in legacy tool call: {e}")
            return web.json_response({
                "success": False,
                "error": str(e)
            }, status=500)
    
    async def _queue_worker(self, arm_side: str):
        """Worker to process jobs from queue"""
        logger.info(f"Started queue worker for {arm_side}")
        
        while True:
            try:
                # Get next job from queue
                job = await self.job_queues[arm_side].get()
                
                # Skip if already canceled
                if job.state == JobState.CANCELED:
                    continue
                
                # Mark as running
                job.state = JobState.RUNNING
                self.active_jobs[arm_side] = job
                
                # Send telemetry
                await self._broadcast_event({
                    "event": "job_started",
                    "jobId": job.job_id,
                    "type": job.type,
                    "armSide": arm_side
                })
                
                # Execute job (always simulated in mock)
                await self._execute_mock(job)
                
                # Mark as completed (unless already canceled/failed)
                if job.state == JobState.RUNNING:
                    job.state = JobState.COMPLETED
                    job.progress = 1.0
                
                # Send telemetry
                await self._broadcast_event({
                    "event": "job_completed" if job.state == JobState.COMPLETED else "job_failed",
                    "jobId": job.job_id,
                    "state": job.state.value,
                    "error": job.error
                })
                
                # Clear active job
                self.active_jobs[arm_side] = None
                
            except Exception as e:
                logger.error(f"Error in queue worker for {arm_side}: {e}")
                if job:
                    job.state = JobState.FAILED
                    job.error = str(e)
    
    async def _execute_mock(self, job: Job):
        """Simulate job execution"""
        moving_time = job.request.get('moving_time', self.default_moving_time)
        steps = 10
        step_time = moving_time / steps
        
        for i in range(steps):
            if job.state != JobState.RUNNING:
                break
            
            job.progress = (i + 1) / steps
            
            # Send progress update
            await self._broadcast_event({
                "event": "job_progress",
                "jobId": job.job_id,
                "progress": job.progress
            })
            
            await asyncio.sleep(step_time)
        
        # Simulate updating position for move_to_pose
        if job.type == "move_to_pose" and self.arm_controller:
            req = job.request
            self.arm_controller.move_to_position(
                x=req['x'],
                y=req['y'],
                z=req['z'],
                moving_time=req.get('moving_time', self.default_moving_time)
            )
            job.result = {"success": True, "position": [req['x'], req['y'], req['z']]}
    
    async def _broadcast_event(self, event_data: Dict):
        """Broadcast SSE event to all connected clients"""
        if not self.sse_connections:
            return
        
        event_str = f"event: {event_data.get('event', 'message')}\n"
        event_str += f"data: {json.dumps(event_data)}\n\n"
        event_bytes = event_str.encode('utf-8')
        
        # Send to all connections
        disconnected = []
        for connection in self.sse_connections:
            try:
                await connection.write(event_bytes)
            except:
                disconnected.append(connection)
        
        # Remove disconnected
        for conn in disconnected:
            if conn in self.sse_connections:
                self.sse_connections.remove(conn)
    
    def _check_idempotency(self, key: str) -> Optional[str]:
        """Check if idempotency key exists and is still valid"""
        if key in self.idempotency_store:
            job_id, timestamp = self.idempotency_store[key]
            if time.time() - timestamp < self.idempotency_ttl:
                return job_id
            else:
                del self.idempotency_store[key]
        return None
    
    async def _cleanup_idempotency_store(self):
        """Periodic cleanup of expired idempotency keys"""
        while True:
            await asyncio.sleep(60)  # Check every minute
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in self.idempotency_store.items()
                if current_time - timestamp > self.idempotency_ttl
            ]
            for key in expired_keys:
                del self.idempotency_store[key]
    
    async def start(self):
        """Start the bridge server"""
        await self.initialize()
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Trajectory bridge (MOCK) server running on port {self.port}")
        logger.info(f"Driver mode: {self.driver_mode}")
        logger.info(f"Safety profile: {self.safety_validator.safety_profile}")
        
        # Keep running
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("Shutting down trajectory bridge...")
        finally:
            await runner.cleanup()


if __name__ == "__main__":
    # Run the server
    bridge = TrajectoryBridge(port=8082)
    asyncio.run(bridge.start())