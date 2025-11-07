#!/usr/bin/env python3
"""
Vision controller for Mobile ALOHA using Gemini API for object detection.
Combines Gemini's vision understanding with RealSense depth data for 3D localization.
"""

import os
import cv2
import numpy as np
import base64
import json
import time
from typing import Optional, Dict, List, Tuple
import google.generativeai as genai
from PIL import Image
import io


class VisionController:
    """
    Uses Gemini API for object detection and RealSense depth data for 3D positioning.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize vision controller with Gemini API.

        Args:
            api_key: Gemini API key (or set GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not provided. Set via env var or constructor.")

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Use Gemini 2.0 Flash for vision (fast and accurate)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

        # Camera intrinsics (RealSense D405 - 640x480)
        # These are approximate - calibrate for better accuracy
        self.fx = 460.0  # Focal length X (pixels)
        self.fy = 460.0  # Focal length Y (pixels)
        self.cx = 320.0  # Principal point X (image center)
        self.cy = 240.0  # Principal point Y (image center)

        # Camera-to-robot transform (gripper camera)
        # These need to be calibrated for your specific setup
        self.camera_to_robot_offset = np.array([0.15, 0.0, 0.05])  # [x, y, z] in meters
        self.camera_rotation = 0  # Rotation around Z axis (radians)

        print("[VisionController] Initialized with Gemini 2.0 Flash")

    def detect_object(
        self,
        rgb_frame: np.ndarray,
        depth_frame: Optional[np.ndarray],
        object_description: str,
        camera_name: str = 'gripper_cam'
    ) -> Dict:
        """
        Detect an object in the image using Gemini API.

        Args:
            rgb_frame: RGB image (H, W, 3) numpy array
            depth_frame: Depth image (H, W) in meters, or None
            object_description: Description of object to find (e.g., "banana", "red cup")
            camera_name: Which camera the frame is from

        Returns:
            Dictionary with detection results:
            {
                'success': bool,
                'object_found': bool,
                'object_description': str,
                'confidence': float,
                'bbox': [x, y, w, h],  # Bounding box in pixels
                'center_pixel': [u, v],  # Center point in image
                'position_3d': [x, y, z],  # 3D position in robot coords (if depth available)
                'depth_meters': float,  # Depth at object center
                'detection_method': str
            }
        """
        start_time = time.time()

        try:
            # Convert numpy array to PIL Image for Gemini
            pil_image = Image.fromarray(rgb_frame)

            # Create prompt for Gemini
            prompt = self._create_detection_prompt(object_description)

            print(f"[VisionController] Detecting '{object_description}' using Gemini...")

            # Call Gemini API
            response = self.model.generate_content([prompt, pil_image])

            # Parse response
            detection_result = self._parse_gemini_response(
                response.text,
                object_description,
                rgb_frame.shape
            )

            if not detection_result['object_found']:
                print(f"[VisionController] Object '{object_description}' not found")
                return detection_result

            # If we have depth data, calculate 3D position
            if depth_frame is not None and detection_result['center_pixel']:
                position_3d, depth_meters = self._calculate_3d_position(
                    detection_result['center_pixel'],
                    depth_frame,
                    camera_name
                )

                detection_result['position_3d'] = position_3d
                detection_result['depth_meters'] = depth_meters

                print(f"[VisionController] ✓ Found '{object_description}' at {position_3d}")
            else:
                print(f"[VisionController] ✓ Found '{object_description}' (no depth data)")

            elapsed = time.time() - start_time
            detection_result['processing_time'] = elapsed

            return detection_result

        except Exception as e:
            print(f"[VisionController] Detection error: {e}")
            return {
                'success': False,
                'object_found': False,
                'error': str(e),
                'object_description': object_description
            }

    def _create_detection_prompt(self, object_description: str) -> str:
        """Create prompt for Gemini to detect object."""
        prompt = f"""You are a robot vision system. Analyze this image and find the '{object_description}'.

INSTRUCTIONS:
1. Look for the {object_description} in the image
2. If found, provide the bounding box coordinates as percentages (0-100)
3. Estimate confidence level (0-100)
4. Describe what you see

Respond in this EXACT JSON format:
{{
    "found": true/false,
    "confidence": 0-100,
    "bbox_percent": {{"x": 0-100, "y": 0-100, "width": 0-100, "height": 0-100}},
    "description": "brief description of what you see"
}}

If the {object_description} is NOT visible, respond with found=false.
Be precise with the bounding box - it should tightly contain the object."""

        return prompt

    def _parse_gemini_response(
        self,
        response_text: str,
        object_description: str,
        image_shape: Tuple[int, int, int]
    ) -> Dict:
        """
        Parse Gemini's response into structured detection result.

        Args:
            response_text: Raw text from Gemini
            object_description: What we were looking for
            image_shape: (height, width, channels)

        Returns:
            Detection result dictionary
        """
        height, width = image_shape[:2]

        try:
            # Try to extract JSON from response
            # Gemini might wrap it in markdown code blocks
            response_clean = response_text.strip()

            # Remove markdown code blocks if present
            if response_clean.startswith('```'):
                lines = response_clean.split('\n')
                response_clean = '\n'.join(lines[1:-1])  # Remove first and last line

            # Remove any "json" label
            response_clean = response_clean.replace('```json', '').replace('```', '').strip()

            # Parse JSON
            data = json.loads(response_clean)

            if not data.get('found', False):
                return {
                    'success': True,
                    'object_found': False,
                    'object_description': object_description,
                    'reason': data.get('description', 'Object not found in image')
                }

            # Convert percentage bbox to pixel coordinates
            bbox_percent = data.get('bbox_percent', {})
            x_percent = bbox_percent.get('x', 50)
            y_percent = bbox_percent.get('y', 50)
            w_percent = bbox_percent.get('width', 10)
            h_percent = bbox_percent.get('height', 10)

            # Convert to pixels
            x_px = int((x_percent / 100.0) * width)
            y_px = int((y_percent / 100.0) * height)
            w_px = int((w_percent / 100.0) * width)
            h_px = int((h_percent / 100.0) * height)

            # Calculate center point
            center_x = x_px + w_px // 2
            center_y = y_px + h_px // 2

            # Clamp to image bounds
            center_x = max(0, min(width - 1, center_x))
            center_y = max(0, min(height - 1, center_y))

            return {
                'success': True,
                'object_found': True,
                'object_description': object_description,
                'confidence': data.get('confidence', 80) / 100.0,
                'bbox': [x_px, y_px, w_px, h_px],
                'center_pixel': [center_x, center_y],
                'description': data.get('description', ''),
                'detection_method': 'gemini_api'
            }

        except json.JSONDecodeError as e:
            print(f"[VisionController] Could not parse JSON response: {e}")
            print(f"[VisionController] Raw response: {response_text}")

            # Fallback: Try to infer from text
            response_lower = response_text.lower()

            if 'not found' in response_lower or 'no' in response_lower or 'cannot see' in response_lower:
                return {
                    'success': True,
                    'object_found': False,
                    'object_description': object_description,
                    'reason': 'Object not detected (inferred from text response)'
                }

            # If response seems positive but we couldn't parse coordinates,
            # return center of image as fallback
            if 'see' in response_lower or 'found' in response_lower or object_description.lower() in response_lower:
                print("[VisionController] Object seems present but couldn't parse coordinates, using image center")
                return {
                    'success': True,
                    'object_found': True,
                    'object_description': object_description,
                    'confidence': 0.5,
                    'bbox': [width // 4, height // 4, width // 2, height // 2],
                    'center_pixel': [width // 2, height // 2],
                    'description': 'Detected but coordinates unavailable',
                    'detection_method': 'gemini_text_inference'
                }

            return {
                'success': False,
                'object_found': False,
                'error': f'Could not parse response: {str(e)}',
                'object_description': object_description
            }

        except Exception as e:
            print(f"[VisionController] Error parsing response: {e}")
            return {
                'success': False,
                'object_found': False,
                'error': str(e),
                'object_description': object_description
            }

    def _calculate_3d_position(
        self,
        pixel_coords: Tuple[int, int],
        depth_frame: np.ndarray,
        camera_name: str
    ) -> Tuple[List[float], float]:
        """
        Convert 2D pixel + depth to 3D position in robot coordinates.

        Args:
            pixel_coords: (u, v) pixel coordinates
            depth_frame: Depth image in meters
            camera_name: Which camera (for transform lookup)

        Returns:
            (position_3d, depth_meters) where position_3d is [x, y, z] in robot frame
        """
        u, v = pixel_coords

        # Get depth at this pixel (with small window average for robustness)
        window_size = 5
        u_min = max(0, u - window_size // 2)
        u_max = min(depth_frame.shape[1], u + window_size // 2 + 1)
        v_min = max(0, v - window_size // 2)
        v_max = min(depth_frame.shape[0], v + window_size // 2 + 1)

        depth_window = depth_frame[v_min:v_max, u_min:u_max]

        # Filter out zeros and invalid depths
        valid_depths = depth_window[(depth_window > 0.1) & (depth_window < 2.0)]

        if len(valid_depths) == 0:
            # Fallback to single pixel
            depth_meters = float(depth_frame[v, u])
        else:
            # Use median for robustness
            depth_meters = float(np.median(valid_depths))

        # Convert pixel + depth to 3D point in camera frame
        # Using pinhole camera model: X = (u - cx) * Z / fx
        x_cam = (u - self.cx) * depth_meters / self.fx
        y_cam = (v - self.cy) * depth_meters / self.fy
        z_cam = depth_meters

        # Transform from camera frame to robot frame
        # This depends on camera mounting position
        if camera_name == 'gripper_cam':
            # Gripper camera: mounted on gripper looking forward
            # Camera X (right) → Robot Y (right)
            # Camera Y (down) → Robot Z (down)
            # Camera Z (forward) → Robot X (forward)
            x_robot = z_cam + self.camera_to_robot_offset[0]
            y_robot = x_cam + self.camera_to_robot_offset[1]
            z_robot = -y_cam + self.camera_to_robot_offset[2]

        elif camera_name == 'top_cam':
            # Top camera: mounted above looking down
            # Camera X (right) → Robot Y (right)
            # Camera Y (down) → Robot X (forward)
            # Camera Z (forward) → Robot -Z (down)
            x_robot = y_cam + self.camera_to_robot_offset[0]
            y_robot = x_cam + self.camera_to_robot_offset[1]
            z_robot = -z_cam + self.camera_to_robot_offset[2]

        else:
            # Unknown camera, use identity
            x_robot = x_cam
            y_robot = y_cam
            z_robot = z_cam

        position_3d = [float(x_robot), float(y_robot), float(z_robot)]

        return position_3d, depth_meters

    def analyze_workspace(
        self,
        rgb_frame: np.ndarray,
        depth_frame: Optional[np.ndarray],
        analysis_type: str = 'objects'
    ) -> Dict:
        """
        Perform general workspace analysis.

        Args:
            rgb_frame: RGB image
            depth_frame: Depth image (optional)
            analysis_type: Type of analysis ('objects', 'safety', 'scene_description')

        Returns:
            Analysis results
        """
        try:
            pil_image = Image.fromarray(rgb_frame)

            if analysis_type == 'objects':
                prompt = """Analyze this workspace image. List ALL objects you can see.

Respond in JSON format:
{
    "objects": [
        {"name": "object1", "color": "red", "position": "left side"},
        {"name": "object2", "color": "blue", "position": "center"}
    ],
    "workspace_clear": true/false,
    "notes": "any relevant observations"
}"""

            elif analysis_type == 'safety':
                prompt = """Analyze this workspace for safety concerns.

Check for:
- Obstacles in the way
- Objects too close to edge
- Unstable items
- Any hazards

Respond in JSON format:
{
    "workspace_safe": true/false,
    "concerns": ["concern1", "concern2"],
    "recommendations": ["recommendation1"]
}"""

            else:  # scene_description
                prompt = "Describe what you see in this workspace image. Be specific about object locations and the overall scene."

            response = self.model.generate_content([prompt, pil_image])
            response_text = response.text.strip()

            # Try to parse JSON
            try:
                response_clean = response_text.replace('```json', '').replace('```', '').strip()
                data = json.loads(response_clean)

                return {
                    'success': True,
                    'analysis_type': analysis_type,
                    **data
                }
            except:
                # Return as text if not JSON
                return {
                    'success': True,
                    'analysis_type': analysis_type,
                    'description': response_text
                }

        except Exception as e:
            print(f"[VisionController] Workspace analysis error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def visualize_detection(
        self,
        rgb_frame: np.ndarray,
        detection_result: Dict,
        output_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Draw detection results on image for debugging.

        Args:
            rgb_frame: RGB image
            detection_result: Result from detect_object()
            output_path: Optional path to save image

        Returns:
            Image with visualization
        """
        img_vis = rgb_frame.copy()

        if detection_result.get('object_found') and 'bbox' in detection_result:
            x, y, w, h = detection_result['bbox']

            # Draw bounding box
            cv2.rectangle(img_vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw center point
            if 'center_pixel' in detection_result:
                cx, cy = detection_result['center_pixel']
                cv2.circle(img_vis, (cx, cy), 5, (0, 0, 255), -1)

            # Draw label
            label = detection_result.get('object_description', 'object')
            confidence = detection_result.get('confidence', 0)
            text = f"{label} ({confidence*100:.0f}%)"
            cv2.putText(img_vis, text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Draw 3D position if available
            if 'position_3d' in detection_result:
                pos_3d = detection_result['position_3d']
                pos_text = f"3D: [{pos_3d[0]:.2f}, {pos_3d[1]:.2f}, {pos_3d[2]:.2f}]"
                cv2.putText(img_vis, pos_text, (x, y + h + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)

        if output_path:
            cv2.imwrite(output_path, cv2.cvtColor(img_vis, cv2.COLOR_RGB2BGR))

        return img_vis

    def calibrate_camera(
        self,
        known_object_pixel: Tuple[int, int],
        known_object_position: Tuple[float, float, float],
        depth_frame: np.ndarray
    ):
        """
        Calibrate camera-to-robot transform using a known object.

        Args:
            known_object_pixel: (u, v) pixel coordinates of known object
            known_object_position: (x, y, z) actual position in robot frame
            depth_frame: Depth frame
        """
        # Calculate what the position would be with current calibration
        calculated_pos, _ = self._calculate_3d_position(
            known_object_pixel,
            depth_frame,
            'gripper_cam'
        )

        # Calculate offset error
        offset_error = np.array(known_object_position) - np.array(calculated_pos)

        print(f"[VisionController] Calibration:")
        print(f"  Expected: {known_object_position}")
        print(f"  Calculated: {calculated_pos}")
        print(f"  Offset error: {offset_error}")
        print(f"  Suggested camera_to_robot_offset: {self.camera_to_robot_offset + offset_error}")

        # Update offset
        self.camera_to_robot_offset += offset_error
        print(f"[VisionController] ✓ Calibration updated")


# Test script
if __name__ == "__main__":
    import sys

    print("Testing Vision Controller with Gemini API...")

    # Check for API key
    if not os.environ.get('GEMINI_API_KEY'):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("Export it with: export GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    try:
        controller = VisionController()
        print("✓ Vision controller initialized")

        # Test with a sample image (create a simple test image)
        test_image = np.ones((480, 640, 3), dtype=np.uint8) * 255

        # Draw a simple object (red circle) for testing
        cv2.circle(test_image, (320, 240), 50, (255, 0, 0), -1)

        print("\nTesting object detection on synthetic image...")
        result = controller.detect_object(
            test_image,
            None,
            "red circle"
        )

        print(f"\nResult: {json.dumps(result, indent=2)}")

    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
