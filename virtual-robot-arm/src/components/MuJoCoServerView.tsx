import { useEffect, useRef, useState } from 'react';
import io, { Socket } from 'socket.io-client';
import { RobotState } from '../types/robot';

interface MuJoCoServerViewProps {
  robotState: RobotState;
  serverUrl?: string;
}

export function MuJoCoServerView({ robotState, serverUrl = 'http://localhost:5001' }: MuJoCoServerViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[MuJoCoServerView] Connecting to server:', serverUrl);

    // Connect to MuJoCo server
    const socket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[MuJoCoServerView] Connected to server');
      setConnected(true);
      setError(null);
    });

    socket.on('disconnect', () => {
      console.log('[MuJoCoServerView] Disconnected from server');
      setConnected(false);
    });

    socket.on('connection_status', (data) => {
      console.log('[MuJoCoServerView] Connection status:', data);
    });

    socket.on('frame_update', (data) => {
      // Receive JPEG frame from server and display it
      if (canvasRef.current && data.frame) {
        const img = new Image();
        img.onload = () => {
          const canvas = canvasRef.current;
          if (canvas) {
            const ctx = canvas.getContext('2d');
            if (ctx) {
              // Set canvas size to match image
              canvas.width = img.width;
              canvas.height = img.height;
              ctx.drawImage(img, 0, 0);
            }
          }
        };
        img.src = `data:image/jpeg;base64,${data.frame}`;
      }
    });

    socket.on('connect_error', (err) => {
      console.error('[MuJoCoServerView] Connection error:', err.message);
      setError(`Connection error: ${err.message}`);
    });

    return () => {
      console.log('[MuJoCoServerView] Disconnecting...');
      socket.disconnect();
    };
  }, [serverUrl]);

  // Send robot state updates to server
  useEffect(() => {
    if (!socketRef.current || !connected) return;

    console.log('[MuJoCoServerView] Sending robot state update');

    // Send arm positions
    socketRef.current.emit('move_arm', {
      arm: 'left',
      positions: [
        robotState.joints.waist,
        robotState.joints.shoulder,
        robotState.joints.elbow,
        robotState.joints.forearm_roll,
        robotState.joints.wrist_angle,
        robotState.joints.wrist_rotate,
      ],
    });

    // Send gripper state
    socketRef.current.emit('control_gripper', {
      arm: 'left',
      command: robotState.gripperState.position > 0.5 ? 'open' : 'close',
    });
  }, [robotState, connected]);

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', background: '#1a1a1a' }}>
      {/* Status bar */}
      <div
        style={{
          padding: '10px',
          background: connected ? '#1e4620' : '#4a1f1f',
          color: 'white',
          fontFamily: 'monospace',
          fontSize: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: connected ? '#4ade80' : '#ef4444',
            }}
          />
          <span>{connected ? '🎮 MuJoCo Server Connected' : '⚠️ Disconnected from MuJoCo Server'}</span>
          <span style={{ marginLeft: 'auto', opacity: 0.7 }}>{serverUrl}</span>
        </div>
        {error && (
          <div style={{ marginTop: '5px', color: '#fca5a5' }}>
            Error: {error}
          </div>
        )}
      </div>

      {/* Video stream canvas */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
        <canvas
          ref={canvasRef}
          style={{
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            imageRendering: 'auto',
          }}
        />
        {!connected && (
          <div style={{ position: 'absolute', color: 'white', textAlign: 'center' }}>
            <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔌</div>
            <div style={{ fontSize: '18px', marginBottom: '10px' }}>Connecting to MuJoCo Server...</div>
            <div style={{ fontSize: '14px', opacity: 0.7 }}>{serverUrl}</div>
            {error && (
              <div style={{ marginTop: '20px', padding: '10px', background: '#4a1f1f', borderRadius: '5px' }}>
                {error}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Info overlay */}
      <div
        style={{
          position: 'absolute',
          bottom: '20px',
          left: '20px',
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontFamily: 'monospace',
          fontSize: '11px',
        }}
      >
        <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>🤖 Full Physics Simulation</div>
        <div>MuJoCo 3.2.5 | Dual-Arm ALOHA</div>
        <div style={{ marginTop: '5px', opacity: 0.7 }}>
          Joints: [{Object.values(robotState.joints).map(v => v.toFixed(2)).join(', ')}]
        </div>
      </div>
    </div>
  );
}
