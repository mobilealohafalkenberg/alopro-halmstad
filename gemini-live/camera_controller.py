#!/usr/bin/env python3
"""
Camera controller for Mobile ALOHA - captures from RealSense cameras
and provides video feed for Gemini Live API.
"""

import cv2
import numpy as np
import threading
import time
import base64
from typing import Optional, Dict, List, Tuple
import pyrealsense2 as rs

class CameraController:
    """
    Controls camera feeds from Mobile ALOHA's RealSense cameras.
    Provides RGB streams from gripper and top cameras.
    """
    
    def __init__(self):
        """Initialize camera controller"""
        self.pipelines = {}
        self.configs = {}
        self.cameras = {}
        self.frames = {}
        self.frame_locks = {}
        self.capture_threads = {}
        self.running = False
        self.initialized = False
        
        # Camera configuration
        self.camera_config = {
            'resolution': (640, 480),
            'fps': 30,
            'format': rs.format.rgb8
        }
        
    def initialize(self) -> bool:
        """
        Initialize RealSense cameras.
        
        Returns:
            True if at least one camera initialized successfully
        """
        try:
            # Create context to query devices
            ctx = rs.context()
            devices = ctx.query_devices()
            
            if len(devices) == 0:
                print("[CameraController] No RealSense devices found")
                return False
            
            print(f"[CameraController] Found {len(devices)} RealSense devices")
            
            # Map cameras by serial number to correct positions
            # CORRECTED based on actual visual feedback:
            camera_mapping = {
                '130322273629': 'top_cam',      # Actually the top overhead camera
                '130322273632': 'gripper_cam',  # Actually the LEFT arm gripper camera  
                '130322270224': 'unused_cam',   # Right arm camera (looking at ceiling)
            }
            
            for dev in devices:
                serial = dev.get_info(rs.camera_info.serial_number)
                name = camera_mapping.get(serial, None)
                
                # Skip if this camera is not one we want to use
                if not name or name == 'unused_cam':
                    print(f"[CameraController] Skipping camera {serial} ({name or 'unknown'})")
                    continue
                
                print(f"[CameraController] Initializing {name} (serial: {serial})")
                
                # Create pipeline for this camera
                pipeline = rs.pipeline()
                config = rs.config()
                
                # Configure the specific device
                config.enable_device(serial)
                config.enable_stream(
                    rs.stream.color,
                    self.camera_config['resolution'][0],
                    self.camera_config['resolution'][1],
                    self.camera_config['format'],
                    self.camera_config['fps']
                )
                
                try:
                    # Start the pipeline
                    profile = pipeline.start(config)
                    
                    # Store references
                    self.pipelines[name] = pipeline
                    self.configs[name] = config
                    self.cameras[name] = serial
                    self.frames[name] = None
                    self.frame_locks[name] = threading.Lock()
                    
                    print(f"[CameraController] ✓ {name} initialized")
                    
                except Exception as e:
                    print(f"[CameraController] ✗ Failed to initialize {name}: {e}")
                    continue
            
            if len(self.pipelines) > 0:
                self.initialized = True
                self.running = True
                self.start_capture_threads()
                print(f"[CameraController] ✓ Initialized {len(self.pipelines)} cameras")
                return True
            else:
                print("[CameraController] ✗ No cameras could be initialized")
                return False
                
        except Exception as e:
            print(f"[CameraController] ✗ Initialization error: {e}")
            # Try fallback to regular USB cameras
            return self.initialize_usb_cameras()
    
    def initialize_usb_cameras(self) -> bool:
        """
        Fallback initialization for regular USB cameras.
        """
        try:
            print("[CameraController] Trying USB camera fallback...")
            
            # Try to open video devices directly
            camera_indices = [2, 8]  # Based on v4l2 output
            camera_names = ['gripper_cam', 'top_cam']
            
            for name, idx in zip(camera_names, camera_indices):
                try:
                    cap = cv2.VideoCapture(f'/dev/video{idx}')
                    if cap.isOpened():
                        # Set resolution
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        
                        self.pipelines[name] = cap
                        self.frames[name] = None
                        self.frame_locks[name] = threading.Lock()
                        
                        print(f"[CameraController] ✓ {name} initialized (USB fallback)")
                    else:
                        print(f"[CameraController] ✗ Could not open /dev/video{idx}")
                except Exception as e:
                    print(f"[CameraController] ✗ Error opening camera {idx}: {e}")
            
            if len(self.pipelines) > 0:
                self.initialized = True
                self.running = True
                self.start_capture_threads()
                print(f"[CameraController] ✓ Initialized {len(self.pipelines)} USB cameras")
                return True
                
        except Exception as e:
            print(f"[CameraController] ✗ USB fallback failed: {e}")
        
        return False
    
    def start_capture_threads(self):
        """Start capture threads for each camera"""
        for name in self.pipelines.keys():
            thread = threading.Thread(
                target=self.capture_loop,
                args=(name,),
                daemon=True
            )
            thread.start()
            self.capture_threads[name] = thread
    
    def capture_loop(self, camera_name: str):
        """
        Continuous capture loop for a camera.
        
        Args:
            camera_name: Name of the camera to capture from
        """
        pipeline = self.pipelines[camera_name]
        
        while self.running:
            try:
                if isinstance(pipeline, rs.pipeline):
                    # RealSense camera
                    frames = pipeline.wait_for_frames(timeout_ms=1000)
                    color_frame = frames.get_color_frame()
                    
                    if color_frame:
                        # Convert to numpy array
                        frame = np.asanyarray(color_frame.get_data())
                        
                        # Store frame
                        with self.frame_locks[camera_name]:
                            self.frames[camera_name] = frame
                else:
                    # USB camera (OpenCV)
                    ret, frame = pipeline.read()
                    if ret:
                        # Convert BGR to RGB
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Store frame
                        with self.frame_locks[camera_name]:
                            self.frames[camera_name] = frame
                
            except Exception as e:
                if self.running:  # Only print if we're still supposed to be running
                    print(f"[CameraController] Capture error on {camera_name}: {e}")
                time.sleep(0.1)
    
    def get_frame(self, camera_name: str) -> Optional[np.ndarray]:
        """
        Get the latest frame from a camera.
        
        Args:
            camera_name: Name of the camera
            
        Returns:
            RGB frame as numpy array or None
        """
        if camera_name not in self.frames:
            return None
        
        with self.frame_locks[camera_name]:
            return self.frames[camera_name].copy() if self.frames[camera_name] is not None else None
    
    def get_frame_base64(self, camera_name: str, quality: int = 85) -> Optional[str]:
        """
        Get frame as base64-encoded JPEG.
        
        Args:
            camera_name: Name of the camera
            quality: JPEG quality (1-100)
            
        Returns:
            Base64-encoded JPEG string or None
        """
        frame = self.get_frame(camera_name)
        if frame is None:
            return None
        
        try:
            # Convert RGB to BGR for OpenCV
            bgr_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            
            # Encode as JPEG
            _, buffer = cv2.imencode('.jpg', bgr_frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            
            # Convert to base64
            jpg_as_text = base64.b64encode(buffer).decode('utf-8')
            return jpg_as_text
            
        except Exception as e:
            print(f"[CameraController] Error encoding frame: {e}")
            return None
    
    def get_all_frames(self) -> Dict[str, np.ndarray]:
        """
        Get frames from all active cameras.
        
        Returns:
            Dictionary mapping camera names to frames
        """
        frames = {}
        for name in self.pipelines.keys():
            frame = self.get_frame(name)
            if frame is not None:
                frames[name] = frame
        return frames
    
    def get_camera_info(self) -> Dict:
        """
        Get information about available cameras.
        
        Returns:
            Dictionary with camera information
        """
        info = {
            'initialized': self.initialized,
            'running': self.running,
            'cameras': {}
        }
        
        for name in self.pipelines.keys():
            has_frame = self.frames.get(name) is not None
            info['cameras'][name] = {
                'active': has_frame,
                'serial': self.cameras.get(name, 'USB'),
                'resolution': self.camera_config['resolution'],
                'fps': self.camera_config['fps']
            }
        
        return info
    
    def shutdown(self):
        """Shutdown all cameras and cleanup"""
        print("[CameraController] Shutting down cameras...")
        self.running = False
        
        # Wait for capture threads to stop
        time.sleep(0.5)
        
        # Stop all pipelines
        for name, pipeline in self.pipelines.items():
            try:
                if isinstance(pipeline, rs.pipeline):
                    pipeline.stop()
                else:
                    pipeline.release()
                print(f"[CameraController] Stopped {name}")
            except:
                pass
        
        self.pipelines.clear()
        self.frames.clear()
        self.initialized = False
        print("[CameraController] ✓ Shutdown complete")


# Test script
if __name__ == "__main__":
    print("Testing Camera Controller...")
    controller = CameraController()
    
    if controller.initialize():
        print("\nCamera Info:")
        info = controller.get_camera_info()
        for cam_name, cam_info in info['cameras'].items():
            print(f"  {cam_name}: {cam_info}")
        
        print("\nCapturing frames for 5 seconds...")
        for i in range(5):
            time.sleep(1)
            frames = controller.get_all_frames()
            print(f"  Frame {i+1}: {list(frames.keys())}")
            
            # Test base64 encoding
            for name in frames.keys():
                b64 = controller.get_frame_base64(name)
                if b64:
                    print(f"    {name}: {len(b64)} bytes (base64)")
        
        controller.shutdown()
    else:
        print("Failed to initialize cameras")