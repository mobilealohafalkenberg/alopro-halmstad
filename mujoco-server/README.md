# MuJoCo Simulation Server

Server-side MuJoCo physics simulation with WebGL streaming for ALOHA robot.

## Overview

This server provides a WebSocket API for controlling the ALOHA robot in either:
- **Simulation mode**: Full MuJoCo physics with 30 FPS WebGL streaming
- **Real robot mode**: Direct control of physical Interbotix hardware

**Key Feature**: Uses the SAME API code for both modes - just change the `--mode` flag!

## Architecture

```
Browser (React)          Python Server             Real Robot
    │                         │                         │
    ├──► WebSocket ──────────►│                         │
    │    (Control commands)    │                         │
    │                          ├──► UnifiedBridge        │
    │                          │    (mode: sim|real)     │
    │◄──── WebGL stream ──────┤                         │
    │    (JPEG frames 30fps)   │    ├──► MuJoCo ───────►│
    │                          │    └──► Interbotix ────►│
```

## Installation

### Prerequisites

- Python 3.8+
- (Optional) ROS2 Humble + Interbotix SDK for real robot mode

### Setup

```bash
cd mujoco-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Simulation Mode (Recommended for Testing)

```bash
# Run with single-arm model
python simulation_server.py --mode simulation --model models/aloha/aloha_single_arm.xml

# Run with dual-arm model
python simulation_server.py --mode simulation --model models/aloha/aloha_simple.xml

# Custom port
python simulation_server.py --mode simulation --port 5001
```

### Real Robot Mode

```bash
# Make sure ROS2 and Interbotix SDK are sourced
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Run with real robot
python simulation_server.py --mode real --port 5000
```

### Testing the Bridge Directly

```bash
# Test simulation mode
python bridges/bridge_unified.py
```

## API Reference

### WebSocket Events

#### Client → Server

**`move_arm`**
```javascript
socket.emit('move_arm', {
  arm: 'left',  // or 'right'
  positions: [0, -0.96, 1.16, 0, -0.3, 0]  // 6 joint angles (radians)
});
```

**`control_gripper`**
```javascript
socket.emit('control_gripper', {
  arm: 'left',
  command: 'open'  // 'open', 'close', or number (0-1)
});
```

**`get_arm_status`**
```javascript
socket.emit('get_arm_status', {
  arm: 'left'
});
```

**`get_gripper_status`**
```javascript
socket.emit('get_gripper_status', {
  arm: 'left'
});
```

**`step_simulation`** (simulation mode only)
```javascript
socket.emit('step_simulation', {
  steps: 10  // Number of physics steps
});
```

**`reset_robot`**
```javascript
socket.emit('reset_robot', {});
```

**`get_initial_frame`** (simulation mode only)
```javascript
socket.emit('get_initial_frame', {});
```

#### Server → Client

**`frame_update`** (simulation mode only)
```javascript
socket.on('frame_update', (data) => {
  // data.frame: base64-encoded JPEG
  // data.state: robot state (optional)
  // data.timestamp: server timestamp
});
```

**`command_result`**
```javascript
socket.on('command_result', (data) => {
  // data.success: boolean
  // data.command: string
  // data.data: result data or error
});
```

**`connection_status`**
```javascript
socket.on('connection_status', (data) => {
  // data.status: 'connected' | 'disconnected'
  // data.mode: 'simulation' | 'real'
});
```

### HTTP Endpoints

**`GET /`**
- Returns server info and available endpoints

**`GET /status`**
- Returns current server status and mode

**`GET /health`**
- Health check endpoint

## Performance

### Simulation Mode (Local)
- Physics rate: 1000 Hz (MuJoCo native)
- Render rate: 30 FPS
- Frame encoding: ~5-10ms (JPEG quality 85)
- Network latency: <10ms (localhost)
- **Total latency: 15-20ms**

### Simulation Mode (LAN)
- Network latency: 20-50ms
- **Total latency: 30-65ms**

### Real Robot Mode
- Control loop: ~50-100ms (USB serial + ROS2)
- Similar to simulation latency

## Integration with Existing Bridge

The unified bridge can replace your existing `bridge_aloha_real.py`:

```python
# Before (separate implementations)
if using_simulation:
    # Simulation code
else:
    # Real robot code

# After (unified)
from bridges.bridge_unified import UnifiedRobotBridge

bridge = UnifiedRobotBridge(mode='simulation')  # or mode='real'
bridge.move_arm('left', positions)  # SAME CODE!
```

## Troubleshooting

### MuJoCo Model Won't Load

```bash
# Check model path is correct
ls models/aloha/aloha_single_arm.xml

# Try absolute path
python simulation_server.py --model /full/path/to/model.xml
```

### WebSocket Connection Refused

```bash
# Check server is running
curl http://localhost:5000/status

# Check firewall allows port 5000
sudo ufw allow 5000
```

### Import Error: mujoco

```bash
# Install MuJoCo
pip install mujoco==3.2.5

# Verify installation
python -c "import mujoco; print(mujoco.__version__)"
```

### Real Robot Mode Errors

```bash
# Source ROS2
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Check robots are powered on and connected
ls /dev/ttyUSB*  # Should show robot USB devices
```

## Development

### Project Structure

```
mujoco-server/
├── bridges/
│   └── bridge_unified.py       # Unified simulation + real robot bridge
├── models/
│   └── aloha/                  # Symlink to ALOHA models
├── static/                     # Future: Web UI files
├── simulation_server.py        # Main server
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Adding New Features

To add a new control command:

1. Add event handler in `simulation_server.py`:
```python
@socketio.on('my_command')
def handle_my_command(data):
    # Process command
    result = bridge.some_method(data)
    emit('command_result', {'success': True, 'data': result})
```

2. Add method to `bridge_unified.py`:
```python
def some_method(self, data):
    if self.mode == 'simulation':
        # Simulation implementation
    elif self.mode == 'real':
        # Real robot implementation
```

## Docker Deployment (Future)

```dockerfile
# Dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "simulation_server.py", "--mode", "simulation", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t mujoco-server .
docker run -p 5000:5000 mujoco-server
```

## License

Same as parent project (Apache 2.0)

## Credits

- MuJoCo physics engine: DeepMind
- ALOHA robot models: Google DeepMind / Stanford
- Interbotix SDK: Trossen Robotics
