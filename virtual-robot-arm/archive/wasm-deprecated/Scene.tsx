import { useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { RobotArm } from './RobotArm';
import { RobotState } from '../types/robot';

interface SceneProps {
  robotState: RobotState;
}

// Table removed to focus on arm - will be re-added when using MuJoCo WASM

function BlueCube({ position }: { position: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);

  return (
    <mesh ref={meshRef} position={position} castShadow>
      <boxGeometry args={[0.05, 0.05, 0.05]} />
      <meshStandardMaterial
        color="#2196F3"
        roughness={0.2}
        metalness={0.6}
      />
    </mesh>
  );
}

function Lighting() {
  return (
    <>
      {/* Main directional light (sun) */}
      <directionalLight
        position={[5, 5, 5]}
        intensity={1}
        castShadow
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
        shadow-camera-far={20}
        shadow-camera-left={-2}
        shadow-camera-right={2}
        shadow-camera-top={2}
        shadow-camera-bottom={-2}
      />

      {/* Fill light */}
      <directionalLight position={[-5, 3, -5]} intensity={0.3} />

      {/* Ambient light */}
      <ambientLight intensity={0.4} />

      {/* Hemisphere light for natural sky/ground bounce */}
      <hemisphereLight args={['#87CEEB', '#654321', 0.3]} />
    </>
  );
}

function WorkspaceGrid() {
  return (
    <>
      {/* Floor grid */}
      <Grid
        position={[0, 0, -0.8]}
        args={[10, 10]}
        cellSize={0.1}
        cellThickness={0.5}
        cellColor="#6e6e6e"
        sectionSize={0.5}
        sectionThickness={1}
        sectionColor="#9d4b4b"
        fadeDistance={5}
        fadeStrength={1}
        infiniteGrid={false}
      />

      {/* Workspace boundary visualization */}
      <lineSegments>
        <edgesGeometry
          args={[new THREE.BoxGeometry(1.0, 1.0, 0.5)]}
        />
        <lineBasicMaterial color="#ff6b6b" transparent opacity={0.3} />
      </lineSegments>
    </>
  );
}

export function Scene({ robotState }: SceneProps) {
  return (
    <div style={{ width: '100%', height: '100vh', background: '#1a1a1a' }}>
      <Canvas
        shadows
        camera={{
          position: [1.2, -1.2, 0.8],
          fov: 50,
        }}
        gl={{ antialias: true }}
      >
        {/* Lighting */}
        <Lighting />

        {/* Environment map for reflections */}
        <Environment preset="city" />

        {/* Objects in scene - table removed to focus on arm */}
        <BlueCube position={[-0.4, -0.15, -0.1]} />

        {/* Robot arm positioned like ALOHA left arm: pos="-0.469 -0.019 0.02" */}
        <group position={[-0.469, 0.02, -0.019]}>
          <RobotArm joints={robotState.joints} gripperState={robotState.gripperState} />
        </group>

        {/* Workspace grid */}
        <WorkspaceGrid />

        {/* Camera controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          target={[0.2, 0, 0.2]}
          minDistance={0.5}
          maxDistance={3}
          maxPolarAngle={Math.PI / 2}
        />

        {/* Axes helper for debugging */}
        <axesHelper args={[0.2]} />
      </Canvas>
    </div>
  );
}
