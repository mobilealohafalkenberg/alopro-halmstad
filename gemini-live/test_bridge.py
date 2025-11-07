#!/usr/bin/env python3
"""
gemini_aloha_bridge.py

Listens to Gemini console (WebSocket) for natural language task commands like:
  "pick ball and put it in bowl"

Perceives 'ball' and 'bowl' using the robot camera (simple CV heuristics),
and executes a parameterized pick-and-place on a real ALOHA robot via ROS2 topics.

Adaptations you must make for your robot:
 - joint_pose dictionaries: fill with real-safe poses for approach/grasp/lift/place
 - topic names: if your robot uses different topics or action servers, update send_joint_command()
 - perception thresholds: tune color/size for your ball/bowl
"""

import asyncio
import json
import re
import time
from threading import Thread

import numpy as np
import websockets
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, JointState
from std_msgs.msg import Bool
from cv_bridge import CvBridge
import cv2


# -------------------------
# Simple Command Parser
# -------------------------
class CommandParser:
    """
    Very small NLP-like parser to extract (action, object, target).
    Assumes commands like 'pick ball and put it in bowl' or 'place cube in box'.
    """

    PICK_RE = re.compile(r"(pick|grab|take|pick up)\s+(\w+)", re.IGNORECASE)
    PLACE_RE = re.compile(r"(put|place|drop|set)\s+(?:it\s+)?(?:in|into|on|onto)\s+(the\s+)?(\w+)", re.IGNORECASE)

    @staticmethod
    def parse(text: str):
        text = text.strip()
        pick_m = CommandParser.PICK_RE.search(text)
        place_m = CommandParser.PLACE_RE.search(text)
        pick_obj = pick_m.group(2).lower() if pick_m else None
        place_obj = place_m.group(2).lower() if place_m else None

        # If only "pick ball" given: place target may be missing
        return {
            "raw": text,
            "pick": pick_obj,
            "place": place_obj
        }


# -------------------------
# Perception Node (ROS2)
# -------------------------
class Perception(Node):
    """
    Subscribes to /camera/image_raw and provides simple detection:
      - ball: detect small circular object via Hough or color threshold
      - bowl: detect larger circular/elliptical shape via contour area

    Accessible via methods: locate_object('ball') -> (x,y), radius or None
    """

    def __init__(self, image_topic="/camera/image_raw"):
        super().__init__('aloha_perception')
        self.bridge = CvBridge()
        self.last_frame = None
        self.subscription = self.create_subscription(Image, image_topic, self.image_callback, 10)
        self.get_logger().info(f'Perception node subscribed to {image_topic}')

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            self.get_logger().error(f"cv_bridge conversion failed: {e}")
            return
        self.last_frame = cv_image

    def get_frame(self, timeout=2.0):
        """Wait for a recent frame (blocking up to timeout)."""
        t0 = time.time()
        while self.last_frame is None and (time.time() - t0) < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
        return self.last_frame

    def locate_ball(self, frame):
        """Detect a circular ball. Returns (x_px, y_px, radius_px) or None."""
        if frame is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)

        # Hough Circle parameters - tune for your camera/ball
        circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=50,
                                   param1=50, param2=30, minRadius=5, maxRadius=120)
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            # pick the largest / most central one
            circles = sorted(circles, key=lambda c: (-c[2], abs(c[0] - frame.shape[1] / 2)))
            x, y, r = circles[0]
            return (int(x), int(y), int(r))
        # fallback: color threshold (if ball has distinctive color). Example for orange:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # tune range for your ball color
        lower = np.array([5, 100, 100])
        upper = np.array([20, 255, 255])
        mask = cv2.inRange(hsv, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            c = max(contours, key=cv2.contourArea)
            ((x, y), r) = cv2.minEnclosingCircle(c)
            if cv2.contourArea(c) > 200:
                return (int(x), int(y), int(r))
        return None

    def locate_bowl(self, frame):
        """Detect bowl-like shape: looks for a larger circular or elliptical contour."""
        if frame is None:
            return None
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 5)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        large = [c for c in contours if cv2.contourArea(c) > 2000]
        if not large:
            return None
        # Choose contour with circularity or large area
        best = max(large, key=cv2.contourArea)
        (x, y), r = cv2.minEnclosingCircle(best)
        return (int(x), int(y), int(r))


# -------------------------
# ALOHA Controller (ROS2 Publisher)
# -------------------------
class AlohaController(Node):
    """
    Publishes joint positions and gripper commands.
    Replace joint poses with your robot-safe, tested poses.
    """

    def __init__(self, joint_topic="/aloha/joint_command", gripper_topic="/aloha/gripper_cmd"):
        super().__init__('aloha_controller')
        self.joint_pub = self.create_publisher(JointState, joint_topic, 10)
        self.gripper_pub = self.create_publisher(Bool, gripper_topic, 10)
        self.get_logger().info(f"AlohaController publishing joints->{joint_topic} gripper->{gripper_topic}")

        # === IMPORTANT ===
        # Replace these example poses with the calibrated poses for your ALOHA robot
        # Format: dict of pose_name -> list of 7 joint angles (radians)
        self.poses = {
            "home": [0.0, -0.5, 0.0, 1.1, 0.0, -0.3, 0.0],
            "approach_pick": [0.2, -0.6, 0.2, 1.0, 0.0, -0.2, 0.0],
            "pre_grasp": [0.22, -0.4, 0.35, 0.9, 0.0, -0.1, 0.0],
            "grasp": [0.22, -0.35, 0.4, 0.85, 0.0, -0.05, 0.0],
            "lift": [0.22, -0.8, 0.1, 1.2, 0.0, -0.4, 0.0],
            "approach_place": [-0.2, -0.6, -0.2, 1.0, 0.2, -0.2, 0.0],
            "pre_place": [-0.22, -0.45, -0.35, 0.9, 0.2, -0.1, 0.0],
            "release": [-0.22, -0.4, -0.3, 0.9, 0.2, -0.05, 0.0]
        }

    def send_joint_command(self, joint_positions, wait=1.0):
        """
        Publish JointState with positions. In many setups, a low-level controller will
        convert these to actual joint moves. If you have an action server, call it instead.
        """
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = [f'joint_{i+1}' for i in range(len(joint_positions))]
        msg.position = joint_positions
        self.joint_pub.publish(msg)
        self.get_logger().info(f"Published joint positions: {joint_positions}")
        # Give robot time to move - in real system you should monitor controller feedback
        time.sleep(wait)

    def gripper(self, close: bool, wait=0.5):
        msg = Bool(data=close)
        self.gripper_pub.publish(msg)
        self.get_logger().info(f"Gripper {'close' if close else 'open'}")
        time.sleep(wait)


# -------------------------
# Task Executor
# -------------------------
class TaskExecutor:
    """
    Executes high-level task: pick <obj> place in <target>
    Uses perception to locate objects and the controller to command ALOHA.
    """

    def __init__(self, perception: Perception, controller: AlohaController):
        self.perception = perception
        self.controller = controller

    def pick_and_place(self, pick_name: str, place_name: str):
        self.controller.get_logger().info(f"Starting task: pick {pick_name} place in {place_name}")

        # 1) Acquire frame and locate objects
        frame = self.perception.get_frame(timeout=3.0)
        if frame is None:
            self.controller.get_logger().error("No camera frame received.")
            return False

        ball = self.perception.locate_ball(frame)
        bowl = self.perception.locate_bowl(frame)

        if ball is None:
            self.controller.get_logger().error("Could not locate the ball.")
            return False
        if bowl is None:
            self.controller.get_logger().error("Could not locate the bowl.")
            return False

        self.controller.get_logger().info(f"Ball detected at px {ball}, bowl at px {bowl}")

        # 2) Sequence of motion primitives (highly robot-specific)
        # Move to approach_pick
        self.controller.send_joint_command(self.controller.poses["approach_pick"], wait=1.2)
        # Move to pre_grasp
        self.controller.send_joint_command(self.controller.poses["pre_grasp"], wait=1.0)
        # Move to grasp
        self.controller.send_joint_command(self.controller.poses["grasp"], wait=0.8)
        # Close gripper
        self.controller.gripper(True, wait=0.7)
        # Lift
        self.controller.send_joint_command(self.controller.poses["lift"], wait=1.0)
        # Move to approach_place
        self.controller.send_joint_command(self.controller.poses["approach_place"], wait=1.2)
        # Move to pre_place
        self.controller.send_joint_command(self.controller.poses["pre_place"], wait=1.0)
        # Lower to release pose
        self.controller.send_joint_command(self.controller.poses["release"], wait=0.8)
        # Open gripper
        self.controller.gripper(False, wait=0.5)
        # Return home
        self.controller.send_joint_command(self.controller.poses["home"], wait=1.0)

        self.controller.get_logger().info("Pick-and-place sequence completed.")
        return True


# -------------------------
# WebSocket Server to receive Gemini commands
# -------------------------
class GeminiWebsocketServer:
    """
    Starts a WebSocket server that receives plain-text tasks from Gemini console,
    parses them, and triggers the TaskExecutor.

    Example: send 'pick ball and put it in bowl' to ws://localhost:8765/
    """

    def __init__(self, executor: TaskExecutor, host="localhost", port=8765):
        self.executor = executor
        self.host = host
        self.port = port
        self.loop = None

    async def handler(self, websocket, path):
        async for message in websocket:
            print(f"[Gemini] Received: {message}")
            cmd = CommandParser.parse(message)
            pick = cmd.get("pick")
            place = cmd.get("place")
            if not pick:
                await websocket.send("Could not parse pick object. Try: 'pick ball and put it in bowl'")
                continue
            if not place:
                await websocket.send("Could not parse place target. Try: 'put it in bowl' or include both pick/place")
                continue
            await websocket.send(f"Acknowledged task: pick {pick} -> place {place}. Executing...")
            # Run long-running blocking task in thread to avoid blocking the websocket loop
            Thread(target=self._run_task, args=(pick, place), daemon=True).start()
            await websocket.send("Task started on robot.")

    def _run_task(self, pick, place):
        try:
            success = self.executor.pick_and_place(pick, place)
            print(f"Task finished: success={success}")
        except Exception as e:
            print(f"Task error: {e}")

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        start_server = websockets.serve(self.handler, self.host, self.port)
        print(f"Starting Gemini WebSocket server on ws://{self.host}:{self.port}")
        self.loop.run_until_complete(start_server)
        self.loop.run_forever()


# -------------------------
# Main runner
# -------------------------
def main():
    # Initialize ROS2 nodes in threaded manner so websocket server can run concurrently.
    rclpy.init()

    perception = Perception(image_topic="/camera/image_raw")
    controller = AlohaController(joint_topic="/aloha/joint_command", gripper_topic="/aloha/gripper_cmd")
    executor = TaskExecutor(perception, controller)

    # Run ROS spinning in a background thread
    def ros_spin():
        try:
            while rclpy.ok():
                rclpy.spin_once(perception, timeout_sec=0.1)
                rclpy.spin_once(controller, timeout_sec=0.1)
        except KeyboardInterrupt:
            pass

    t = Thread(target=ros_spin, daemon=True)
    t.start()

    # Start WebSocket server (blocking)
    server = GeminiWebsocketServer(executor, host="0.0.0.0", port=8765)
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        rclpy.shutdown()


if __name__ == "__main__":
    main()
