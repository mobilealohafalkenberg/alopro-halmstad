# Warp ALOHA Live API MVP Guide

Build a real-time system where Gemini Live API uses spatial understanding from Mobile ALOHA robot's video feed to control robot arms through tool calls.

## System Architecture

```
Mobile ALOHA → Video Feed → Gemini Live API → Tool Calls → Robot Control → Arm Movement
```

## Prerequisites

- Mobile ALOHA robot with camera access
- Google Cloud project with Gemini API access
- Python 3.8+
- ROS/ROS2 (for Mobile ALOHA integration)
- OpenCV for video processing
- WebSocket libraries

## Step 1: Gemini Live API WebSocket Connection

### 1.1 Install Dependencies

```bash
pip install google-cloud-aiplatform websockets opencv-python asyncio aiohttp pillow
```

### 1.2 Basic Live API WebSocket Client

Create `gemini_live_client.py`:

```python
import asyncio
import websockets
import json
import base64
import cv2
from google.oauth2 import service_account
from google.auth.transport.requests import Request

class GeminiLiveClient:
    def __init__(self, project_id, location="us-central1"):
        self.project_id = project_id
        self.location = location
        self.websocket = None
        self.credentials = None
        
    async def authenticate(self):
        """Get authentication token for Gemini API"""
        # Use your service account key or default credentials
        credentials, _ = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        credentials.refresh(Request())
        return credentials.token
    
    async def connect(self):
        """Establish WebSocket connection to Gemini Live API"""
        token = await self.authenticate()
        
        # Construct WebSocket URL for Live API
        ws_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.StreamGenerateContent"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        self.websocket = await websockets.connect(ws_url, extra_headers=headers)
        print("Connected to Gemini Live API")
    
    async def send_video_frame(self, frame):
        """Send video frame to Gemini Live API"""
        # Encode frame as base64
        _, buffer = cv2.imencode('.jpg', frame)
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        
        message = {
            "setup": {
                "model": "models/gemini-2.5-pro-latest",
                "generation_config": {
                    "response_modalities": ["TEXT"]
                },
                "tools": self.get_robot_tools()
            },
            "client_content": {
                "turns": [{
                    "parts": [{
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": frame_b64
                        }
                    }]
                }]
            }
        }
        
        await self.websocket.send(json.dumps(message))
    
    def get_robot_tools(self):
        """Define robot control tool functions for Gemini"""
        return {
            "function_declarations": [
                {
                    "name": "detect_object",
                    "description": "Detect and locate objects in the robot's view",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "object_name": {
                                "type": "string",
                                "description": "Name of object to detect (e.g., 'banana', 'cup')"
                            }
                        },
                        "required": ["object_name"]
                    }
                },
                {
                    "name": "move_arm_to_object",
                    "description": "Move robot arm to grasp specified object",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "arm": {
                                "type": "string",
                                "enum": ["left", "right"],
                                "description": "Which arm to use"
                            },
                            "object_name": {
                                "type": "string",
                                "description": "Object to move arm towards"
                            },
                            "action": {
                                "type": "string",
                                "enum": ["approach", "grasp", "lift", "release"],
                                "description": "Action to perform"
                            }
                        },
                        "required": ["arm", "object_name", "action"]
                    }
                }
            ]
        }
    
    async def listen_for_responses(self, robot_controller):
        """Listen for Gemini responses and execute tool calls"""
        while True:
            response = await self.websocket.recv()
            data = json.loads(response)
            
            if "server_content" in data:
                content = data["server_content"]
                
                # Handle tool calls
                if "tool_call" in content:
                    await self.handle_tool_call(content["tool_call"], robot_controller)
                
                # Handle text responses
                if "text" in content:
                    print(f"Gemini: {content['text']}")
    
    async def handle_tool_call(self, tool_call, robot_controller):
        """Execute robot actions based on Gemini tool calls"""
        function_name = tool_call["function_call"]["name"]
        args = tool_call["function_call"]["args"]
        
        if function_name == "detect_object":
            result = await robot_controller.detect_object(args["object_name"])
            
        elif function_name == "move_arm_to_object":
            result = await robot_controller.move_arm_to_object(
                args["arm"], 
                args["object_name"], 
                args["action"]
            )
        
        # Send tool call result back to Gemini
        response_message = {
            "tool_response": {
                "function_response": {
                    "name": function_name,
                    "response": result
                }
            }
        }
        await self.websocket.send(json.dumps(response_message))
```

## Step 2: Mobile ALOHA Robot Interface

### 2.1 Robot Controller Class

Create `aloha_controller.py`:

```python
import rospy
import numpy as np
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Float64MultiArray
from cv_bridge import CvBridge
import cv2

class ALOHARobotController:
    def __init__(self):
        rospy.init_node('aloha_gemini_controller', anonymous=True)
        
        # Initialize CV bridge for image conversion
        self.bridge = CvBridge()
        
        # Camera subscribers
        self.camera_sub = rospy.Subscriber(
            '/camera/color/image_raw', 
            Image, 
            self.camera_callback
        )
        
        # Joint state subscriber
        self.joint_sub = rospy.Subscriber(
            '/joint_states', 
            JointState, 
            self.joint_callback
        )
        
        # Arm control publishers
        self.left_arm_pub = rospy.Publisher(
            '/aloha/left_arm/joint_commands', 
            Float64MultiArray, 
            queue_size=10
        )
        
        self.right_arm_pub = rospy.Publisher(
            '/aloha/right_arm/joint_commands', 
            Float64MultiArray, 
            queue_size=10
        )
        
        # Current state
        self.current_frame = None
        self.joint_states = None
        self.detected_objects = {}
        
    def camera_callback(self, msg):
        """Process incoming camera frames"""
        try:
            self.current_frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception as e:
            rospy.logerr(f"Camera callback error: {e}")
    
    def joint_callback(self, msg):
        """Process joint state updates"""
        self.joint_states = msg
    
    def get_current_frame(self):
        """Get the latest camera frame"""
        return self.current_frame
    
    async def detect_object(self, object_name):
        """Detect object using computer vision or external detection service"""
        if self.current_frame is None:
            return {"success": False, "message": "No camera feed available"}
        
        # Simple object detection placeholder
        # In practice, you'd use YOLO, or rely on Gemini's spatial understanding
        result = {
            "success": True,
            "object": object_name,
            "position": {"x": 0.3, "y": -0.1, "z": 0.1},  # Example coordinates
            "confidence": 0.85
        }
        
        self.detected_objects[object_name] = result
        return result
    
    async def move_arm_to_object(self, arm, object_name, action):
        """Move specified arm to perform action on object"""
        if object_name not in self.detected_objects:
            return {"success": False, "message": f"Object '{object_name}' not detected"}
        
        obj_pos = self.detected_objects[object_name]["position"]
        
        # Generate joint commands based on inverse kinematics
        joint_commands = self.calculate_joint_commands(arm, obj_pos, action)
        
        # Publish joint commands
        msg = Float64MultiArray()
        msg.data = joint_commands
        
        if arm == "left":
            self.left_arm_pub.publish(msg)
        else:
            self.right_arm_pub.publish(msg)
        
        rospy.loginfo(f"Moving {arm} arm to {action} {object_name}")
        
        return {
            "success": True,
            "arm": arm,
            "action": action,
            "object": object_name,
            "joint_commands": joint_commands
        }
    
    def calculate_joint_commands(self, arm, target_pos, action):
        """Calculate joint commands using inverse kinematics"""
        # This is a simplified placeholder
        # You'll need to implement proper IK for your ALOHA robot
        
        base_pose = [0, -0.3, 0.1, 0, 0.5, 0]  # Example 6-DOF joint angles
        
        if action == "approach":
            # Move arm near object
            return [x + 0.1 for x in base_pose]
        elif action == "grasp":
            # Close gripper and grasp
            return [x + 0.05 for x in base_pose] + [0.8]  # Close gripper
        elif action == "lift":
            # Lift object up
            return [x for x in base_pose[:2]] + [base_pose[2] + 0.2] + base_pose[3:]
        elif action == "release":
            # Open gripper
            return base_pose + [0.0]  # Open gripper
        
        return base_pose
```

## Step 3: Video Streaming Pipeline

### 3.1 Real-time Video Streamer

Create `video_streamer.py`:

```python
import asyncio
import cv2
import time
from threading import Thread

class VideoStreamer:
    def __init__(self, robot_controller, gemini_client, fps=10):
        self.robot_controller = robot_controller
        self.gemini_client = gemini_client
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.running = False
        
    async def start_streaming(self):
        """Start streaming video frames to Gemini Live API"""
        self.running = True
        
        while self.running:
            frame = self.robot_controller.get_current_frame()
            
            if frame is not None:
                # Resize frame for efficient transmission
                frame = cv2.resize(frame, (640, 480))
                
                # Send frame to Gemini
                await self.gemini_client.send_video_frame(frame)
                
                # Optional: Display frame locally
                cv2.imshow('ALOHA Camera Feed', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            await asyncio.sleep(self.frame_interval)
        
        cv2.destroyAllWindows()
    
    def stop_streaming(self):
        """Stop video streaming"""
        self.running = False
```

## Step 4: Integration and Main Application

### 4.1 Main Application

Create `main.py`:

```python
import asyncio
import rospy
from gemini_live_client import GeminiLiveClient
from aloha_controller import ALOHARobotController
from video_streamer import VideoStreamer

async def main():
    # Initialize components
    print("Initializing ALOHA-Gemini Live API system...")
    
    # Initialize robot controller
    robot_controller = ALOHARobotController()
    print("✓ Robot controller initialized")
    
    # Initialize Gemini Live API client
    gemini_client = GeminiLiveClient(project_id="your-project-id")
    await gemini_client.connect()
    print("✓ Connected to Gemini Live API")
    
    # Initialize video streamer
    video_streamer = VideoStreamer(robot_controller, gemini_client, fps=5)
    print("✓ Video streamer initialized")
    
    # Start concurrent tasks
    print("Starting system...")
    
    try:
        await asyncio.gather(
            video_streamer.start_streaming(),
            gemini_client.listen_for_responses(robot_controller),
        )
    except KeyboardInterrupt:
        print("\nShutting down...")
        video_streamer.stop_streaming()
        rospy.signal_shutdown("User interrupt")

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Configuration and Setup

### 5.1 Environment Setup

Create `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account-key.json
ROS_MASTER_URI=http://localhost:11311
```

### 5.2 Launch Script

Create `launch.sh`:

```bash
#!/bin/bash

# Start ROS master
roscore &

# Wait for ROS to start
sleep 2

# Launch ALOHA robot nodes
roslaunch aloha_bringup robot.launch &

# Wait for robot to initialize
sleep 5

# Start Gemini Live API integration
python main.py
```

## Usage Instructions

### 5.3 Running the MVP

1. **Setup environment:**
   ```bash
   chmod +x launch.sh
   source /opt/ros/noetic/setup.bash  # or melodic
   ```

2. **Configure credentials:**
   - Set up Google Cloud service account
   - Download credentials JSON
   - Set environment variables

3. **Launch system:**
   ```bash
   ./launch.sh
   ```

4. **Test with voice commands:**
   - "Can you see the banana on the table?"
   - "Please grab the banana with the right arm"
   - "Move the banana to the bowl"

## Expected Behavior

1. **Video streaming:** Robot camera feed streams to Gemini Live API
2. **Spatial understanding:** Gemini analyzes the video and identifies objects
3. **Tool calls:** Gemini generates tool calls to control robot arms
4. **Robot execution:** ALOHA robot executes the commanded actions

## Next Steps for Production

- **Improve object detection** with dedicated vision models
- **Implement proper inverse kinematics** for ALOHA robot
- **Add safety checks** and collision avoidance
- **Optimize video compression** for lower latency
- **Add error handling** and recovery mechanisms
- **Implement task planning** and multi-step operations

## Troubleshooting

**Common Issues:**

1. **WebSocket connection fails:** Check authentication and API quotas
2. **Video frames not streaming:** Verify camera topics and ROS setup
3. **Robot not responding:** Check joint command topics and ALOHA drivers
4. **High latency:** Reduce video resolution or frame rate

This MVP provides the foundation for real-time spatial understanding and robot control using Gemini Live API with your Mobile ALOHA robot!
