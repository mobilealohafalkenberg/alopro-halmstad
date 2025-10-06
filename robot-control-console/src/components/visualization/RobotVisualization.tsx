import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { RobotMode } from '../mode-selector/ModeSelector';
import { CameraFeedView } from './CameraFeedView';
import './RobotVisualization.scss';

interface RobotVisualizationProps {
  mode: RobotMode;
  jointPositions?: number[];
  gripperState?: 'open' | 'close';
}

export function RobotVisualization({ mode, jointPositions, gripperState }: RobotVisualizationProps) {

  if (mode === 'real') {
    return <CameraFeedView endpoint="http://localhost:8081" />;
  }

  return (
    <div className="robot-visualization">
      <Canvas camera={{ position: [2, 2, 2], fov: 50 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} />
        <directionalLight position={[-5, 5, 5]} intensity={0.5} />

        <OrbitControls />
        <Grid args={[10, 10]} />

        {/* Placeholder robot arm - will be replaced with actual 3D model */}
        <mesh position={[0, 0.5, 0]}>
          <boxGeometry args={[0.1, 1, 0.1]} />
          <meshStandardMaterial color="#ff6b35" />
        </mesh>

        <mesh position={[0, 1, 0]}>
          <boxGeometry args={[0.8, 0.1, 0.1]} />
          <meshStandardMaterial color="#4a9eff" />
        </mesh>

        {/* Gripper indicator */}
        <mesh position={[0.4, 1, 0]}>
          <boxGeometry args={[0.1, 0.1, gripperState === 'open' ? 0.3 : 0.1]} />
          <meshStandardMaterial color={gripperState === 'open' ? '#4ade80' : '#f87171'} />
        </mesh>
      </Canvas>

      <div className="visualization-overlay">
        <div className="joint-display">
          <h4>Joint Positions</h4>
          {jointPositions?.map((pos, i) => (
            <div key={i} className="joint-value">
              <span className="joint-label">Joint {i}:</span>
              <span className="joint-number">{pos.toFixed(2)}°</span>
            </div>
          ))}
        </div>
        <div className="gripper-display">
          <span className="status-label">Gripper:</span>
          <span className={`status-value ${gripperState}`}>
            {gripperState || 'unknown'}
          </span>
        </div>
      </div>
    </div>
  );
}
