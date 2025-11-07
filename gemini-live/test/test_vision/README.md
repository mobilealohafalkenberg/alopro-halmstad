# Vision System Tests

Tests for computer vision integration using Gemini API for object detection and workspace analysis.

## Prerequisites

1. **Set up Gemini API key:**
```bash
export GEMINI_API_KEY='your-gemini-api-key-here'
```

2. **Install dependencies:**
```bash
pip install google-generativeai pillow opencv-python pyrealsense2
```

3. **Hardware requirements:**
   - RealSense D405 cameras connected and powered
   - Robot doesn't need to be running for vision tests

## Running Tests

### Full Test Suite
```bash
cd gemini-live/test
python3 test_vision/test_vision_system.py
```

This runs all tests:
- Camera initialization
- Vision controller initialization
- Object detection with 3D positioning
- Workspace analysis
- Multiple object detection
- Optional calibration helper

### Quick Vision Test
```bash
# Test if vision controller works
cd gemini-live
python3 vision_controller.py
```

### Individual Component Tests

**Test camera only:**
```bash
cd gemini-live
python3 camera_controller.py
```

**Test object detection:**
```python
from camera_controller import CameraController
from vision_controller import VisionController

camera = CameraController()
camera.initialize()

vision = VisionController()

rgb, depth = camera.get_rgbd_frames('gripper_cam')
result = vision.detect_object(rgb, depth, "banana")

print(result)
```

## Expected Output

### Successful Detection
```json
{
  "success": true,
  "object_found": true,
  "object_description": "banana",
  "confidence": 0.95,
  "bbox": [150, 200, 100, 120],
  "center_pixel": [200, 260],
  "position_3d": [0.35, 0.05, 0.12],
  "depth_meters": 0.38,
  "detection_method": "gemini_api"
}
```

### Object Not Found
```json
{
  "success": true,
  "object_found": false,
  "object_description": "banana",
  "reason": "No banana visible in the image"
}
```

## Calibration

The camera-to-robot transform may need calibration for accurate 3D positioning.

**Interactive calibration:**
1. Run test suite: `python3 test_vision/test_vision_system.py`
2. Choose "y" for calibration test
3. Place a known object at a measured position
4. Enter object name and actual coordinates
5. System will calculate and apply offset

**Manual calibration:**
Edit `vision_controller.py` line 32:
```python
self.camera_to_robot_offset = np.array([0.15, 0.0, 0.05])  # Adjust these values
```

## Troubleshooting

### "GEMINI_API_KEY not set"
```bash
# Get API key from: https://aistudio.google.com/app/apikey
export GEMINI_API_KEY='your-key-here'

# Add to ~/.bashrc for persistence:
echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### "Camera controller not initialized"
- Check RealSense cameras are connected: `rs-enumerate-devices`
- Check USB connections and power
- Try unplugging and replugging cameras

### "Object not detected" (but it's visible)
- Improve lighting - avoid shadows and glare
- Move object closer to camera (20-60cm optimal)
- Use more descriptive object names: "yellow banana" instead of "banana"
- Try different camera angle

### "No depth data"
- Ensure RealSense depth stream is enabled
- Check object is within depth range (0.1m - 2.0m)
- Reflective or transparent objects may not have good depth

### Inaccurate 3D positions
- Run calibration test
- Check depth camera is clean (no smudges)
- Verify workspace is well-lit (not too bright, not too dark)
- Check camera mounting is secure (not vibrating)

## Architecture

```
vision_controller.py
├── Uses Gemini 2.0 Flash API for visual understanding
├── Receives RGB frames from camera_controller
├── Receives depth frames for 3D positioning
├── Transforms camera coordinates to robot coordinates
└── Returns bounding boxes, confidence, and 3D positions

camera_controller.py
├── Manages RealSense D405 cameras
├── Captures RGB frames (640x480)
├── Captures depth frames (16-bit, in meters)
├── Thread-safe frame access
└── Provides get_rgbd_frames() for synchronized capture

updated_bridge_aloha.py
├── Integrates vision_controller into tool calls
├── handle detect_and_target_object()
│   ├── Gets camera frame
│   ├── Detects object with Gemini
│   ├── Generates approach trajectory
│   └── Returns to Gemini with suggested path
└── handle analyze_workspace()
    ├── Gets workspace frame
    ├── Analyzes scene with Gemini
    └── Returns object list and safety info
```

## Performance

- **Camera capture:** 30 FPS (RGB + Depth)
- **Gemini API call:** 1-3 seconds
- **3D position calculation:** <10ms
- **Total detection time:** 1-3 seconds

## Next Steps

1. **Improve accuracy:** Run calibration with multiple known positions
2. **Add object tracking:** Use previous detections to predict motion
3. **Multi-camera fusion:** Combine gripper + top camera views
4. **Custom fine-tuning:** Train on specific objects in your workspace

## Related Files

- `vision_controller.py` - Main vision implementation
- `camera_controller.py` - Camera interface
- `updated_bridge_aloha.py` - Integration with robot bridge
- `test_vision_system.py` - This test suite

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review CLAUDE.md in project root
3. Check Gemini API status: https://status.cloud.google.com/
