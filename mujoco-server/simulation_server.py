"""
MuJoCo Simulation Server with WebGL Streaming

This server provides a WebSocket API for controlling the ALOHA robot simulation.
It uses the unified bridge to support both simulation and real robot modes.

Usage:
    python simulation_server.py --mode simulation --port 5000
    python simulation_server.py --mode real --port 5000
"""

import argparse
import base64
import cv2
import numpy as np
import time
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import sys
import os

# Add bridges directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bridges'))

from bridge_unified import UnifiedRobotBridge

# Initialize Flask app
app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25, async_mode='threading')

# Global bridge instance
bridge = None
physics_running = False
HEADLESS_MODE = False  # Set via --headless flag


def encode_frame_jpeg(frame: np.ndarray, quality: int = 85) -> str:
    """
    Encode frame as base64 JPEG.

    Args:
        frame: RGB image array
        quality: JPEG quality (1-100)

    Returns:
        Base64-encoded JPEG string
    """
    # Convert RGB to BGR for OpenCV
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])

    # Convert to base64
    frame_b64 = base64.b64encode(buffer).decode('utf-8')

    return frame_b64


# ================================================================================
# WebSocket Event Handlers - SAME API as real robot bridge!
# ================================================================================

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print(f"[Server] Client connected: {bridge.mode} mode")
    emit('connection_status', {
        'status': 'connected',
        'mode': bridge.mode,
        'message': f'Connected to {bridge.mode} robot'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print("[Server] Client disconnected")


@socketio.on('move_arm')
def handle_move_arm(data):
    """
    Move arm to specified positions.

    Args:
        data: {
            'arm': 'left' | 'right',
            'positions': [float, float, ...]  // radians
        }
    """
    try:
        arm = data.get('arm', 'left')
        positions = data.get('positions', [])

        print(f"[Server] Moving {arm} arm to: {positions}")

        # Move arm using bridge
        result = bridge.move_arm(arm, positions)

        # For simulation, send updated frame (if not headless)
        if bridge.mode == 'simulation' and not HEADLESS_MODE:
            frame = bridge.render()
            frame_b64 = encode_frame_jpeg(frame)

            state = bridge.get_arm_status(arm)

            emit('frame_update', {
                'frame': frame_b64,
                'state': state,
                'timestamp': time.time()
            })

        emit('command_result', {
            'success': True,
            'command': 'move_arm',
            'data': result
        })

    except Exception as e:
        print(f"[Server] Error in move_arm: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('control_gripper')
def handle_control_gripper(data):
    """
    Control gripper.

    Args:
        data: {
            'arm': 'left' | 'right',
            'command': 'open' | 'close' | float
        }
    """
    try:
        arm = data.get('arm', 'left')
        command = data.get('command', 'open')

        print(f"[Server] Gripper {arm}: {command}")

        # Control gripper using bridge
        result = bridge.control_gripper(arm, command)

        # For simulation, send updated frame (if not headless)
        if bridge.mode == 'simulation' and not HEADLESS_MODE:
            frame = bridge.render()
            frame_b64 = encode_frame_jpeg(frame)

            gripper_state = bridge.get_gripper_status(arm)

            emit('frame_update', {
                'frame': frame_b64,
                'gripper_state': gripper_state,
                'timestamp': time.time()
            })

        emit('command_result', {
            'success': True,
            'command': 'control_gripper',
            'data': result
        })

    except Exception as e:
        print(f"[Server] Error in control_gripper: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('get_arm_status')
def handle_get_arm_status(data):
    """Get current arm status"""
    try:
        arm = data.get('arm', 'left')
        status = bridge.get_arm_status(arm)

        emit('arm_status', {
            'arm': arm,
            'status': status,
            'timestamp': time.time()
        })

    except Exception as e:
        print(f"[Server] Error in get_arm_status: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('get_gripper_status')
def handle_get_gripper_status(data):
    """Get current gripper status"""
    try:
        arm = data.get('arm', 'left')
        status = bridge.get_gripper_status(arm)

        emit('gripper_status', {
            'arm': arm,
            'status': status,
            'timestamp': time.time()
        })

    except Exception as e:
        print(f"[Server] Error in get_gripper_status: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('step_simulation')
def handle_step_simulation(data):
    """Advance simulation by N steps (simulation mode only)"""
    if bridge.mode != 'simulation':
        emit('command_result', {
            'success': False,
            'error': 'step_simulation only available in simulation mode'
        })
        return

    try:
        steps = data.get('steps', 1)
        bridge.step_simulation(steps)

        # Send updated frame (if not headless)
        if not HEADLESS_MODE:
            frame = bridge.render()
            frame_b64 = encode_frame_jpeg(frame)

            emit('frame_update', {
                'frame': frame_b64,
                'timestamp': time.time()
            })

    except Exception as e:
        print(f"[Server] Error in step_simulation: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('reset_robot')
def handle_reset():
    """Reset robot to home position"""
    try:
        print("[Server] Resetting robot to home position")
        bridge.reset()

        # For simulation, send updated frame (if not headless)
        if bridge.mode == 'simulation' and not HEADLESS_MODE:
            frame = bridge.render()
            frame_b64 = encode_frame_jpeg(frame)

            emit('frame_update', {
                'frame': frame_b64,
                'timestamp': time.time()
            })

        emit('command_result', {
            'success': True,
            'command': 'reset'
        })

    except Exception as e:
        print(f"[Server] Error in reset: {e}")
        emit('command_result', {
            'success': False,
            'error': str(e)
        })


@socketio.on('get_initial_frame')
def handle_get_initial_frame():
    """Get initial rendered frame (simulation mode only)"""
    if bridge.mode != 'simulation' or HEADLESS_MODE:
        return

    try:
        frame = bridge.render()
        frame_b64 = encode_frame_jpeg(frame)

        emit('frame_update', {
            'frame': frame_b64,
            'timestamp': time.time(),
            'initial': True
        })

    except Exception as e:
        print(f"[Server] Error rendering initial frame: {e}")


# ================================================================================
# HTTP Endpoints
# ================================================================================

@app.route('/')
def index():
    """Serve main page"""
    return jsonify({
        'status': 'running',
        'mode': bridge.mode if bridge else 'not initialized',
        'endpoints': {
            'websocket': 'ws://localhost:5000',
            'status': '/status',
            'health': '/health'
        }
    })


@app.route('/status')
def status():
    """Get server status"""
    return jsonify({
        'mode': bridge.mode if bridge else 'not initialized',
        'ready': bridge is not None,
        'physics_running': physics_running
    })


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})


# ================================================================================
# Main
# ================================================================================

def main():
    parser = argparse.ArgumentParser(description='MuJoCo Simulation Server')
    parser.add_argument('--mode', type=str, default='simulation',
                       choices=['simulation', 'real'],
                       help='Robot mode: simulation or real')
    parser.add_argument('--model', type=str, default='models/aloha/aloha_single_arm.xml',
                       help='Path to MuJoCo XML model (simulation mode only)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Server port')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Server host')
    parser.add_argument('--headless', action='store_true',
                       help='Run in headless mode (no rendering/OpenGL)')

    args = parser.parse_args()

    # Set headless mode globally
    global HEADLESS_MODE
    HEADLESS_MODE = args.headless

    # Initialize bridge
    global bridge
    print("="*60)
    print(f"Starting MuJoCo Simulation Server")
    print(f"  Mode: {args.mode}")
    print(f"  Model: {args.model}")
    print(f"  Port: {args.port}")
    print("="*60)

    try:
        bridge = UnifiedRobotBridge(mode=args.mode, model_path=args.model)
        print(f"\n✓ Bridge initialized in {args.mode} mode")

        # Reset to home position
        print("✓ Resetting to home position...")
        bridge.reset()

        print(f"\n✓ Server ready at http://{args.host}:{args.port}")
        print(f"✓ WebSocket endpoint: ws://{args.host}:{args.port}")
        print("\nPress Ctrl+C to stop\n")

        # Run server (allow_unsafe_werkzeug for development)
        socketio.run(app, host=args.host, port=args.port, debug=False, allow_unsafe_werkzeug=True)

    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n✗ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if bridge:
            bridge.close()


if __name__ == '__main__':
    main()
