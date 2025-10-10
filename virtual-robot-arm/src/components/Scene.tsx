import { useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid, Environment } from '@react-three/drei';
import * as THREE from 'three';
import { RobotArmMJCF } from './RobotArmMJCF';
import { RobotState } from '../types/robot';
import { VirtualCameraSystem, CameraViewData } from './VirtualCameraSystem';
import { VirtualCameraFeed } from './VirtualCameraFeed';

interface SceneProps {
  robotState: RobotState;
}

/**
 * Scene setup matching ALOHA_sim official configuration
 * Reference: https://github.com/google-deepmind/aloha_sim
 *
 * COORDINATE SYSTEM:
 * Using MuJoCo coordinates directly: X-right, Y-forward, Z-up
 * Three.js will render this with Z-up by rotating the camera appropriately
 *
 * Key coordinates from aloha_pbr.xml and scene_pbr.xml:
 * - Table position: (0, 0, -0.732)
 * - Table top collision: +0.6509 Z offset
 * - Left arm base: (-0.469, -0.019, 0.02)
 * - Right arm base: (0.469, -0.019, 0.02)
 * - Table dimensions: 1.22m x 0.762m x 0.2m
 */

// Simple table matching ALOHA dimensions using MuJoCo coordinates
function AlohaTable() {
  return (
    <group position={[0, 0, -0.732]}>
      {/* Table top collision box at +0.6509 Z offset (matching ALOHA XML) */}
      <mesh position={[0, 0, 0.6509]} receiveShadow castShadow>
        <boxGeometry args={[1.22, 0.762, 0.2]} /> {/* X-width, Y-depth, Z-height */}
        <meshStandardMaterial
          color="#8B7355"
          roughness={0.7}
          metalness={0.1}
        />
      </mesh>

      {/* Table legs (simplified) - positioned at corners */}
      {[
        [-0.5, -0.3, 0.3],
        [0.5, -0.3, 0.3],
        [-0.5, 0.3, 0.3],
        [0.5, 0.3, 0.3],
      ].map((pos, i) => (
        <mesh key={i} position={pos as [number, number, number]} castShadow receiveShadow>
          <boxGeometry args={[0.05, 0.05, 0.6]} /> {/* X, Y, Z-height */}
          <meshStandardMaterial color="#654321" roughness={0.8} />
        </mesh>
      ))}
    </group>
  );
}

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

// Lighting matching ALOHA_sim: headlight diffuse="0.6 0.6 0.6" ambient="0.6 0.6 0.6"
function Lighting() {
  return (
    <>
      {/* Main light positioned above workspace */}
      <pointLight position={[0, 0.1, 2.5]} intensity={1.2} castShadow />

      {/* Ambient light matching ALOHA headlight */}
      <ambientLight intensity={0.6} color="#ffffff" />

      {/* Hemisphere for natural lighting */}
      <hemisphereLight args={['#ffffff', '#444444', 0.6]} />
    </>
  );
}

// Floor plane at Z=-0.75 (MuJoCo coordinates)
function WorkspaceFloor() {
  return (
    <>
      {/* Floor plane - needs to be in XY plane for Z-up coordinate system */}
      <mesh position={[0, 0, -0.75]} rotation={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[4, 4]} />
        <meshStandardMaterial
          color="#2a2a2a"
          roughness={0.8}
          metalness={0.2}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Grid on floor for reference */}
      <Grid
        position={[0, 0, -0.749]}
        args={[4, 4]}
        cellSize={0.1}
        cellThickness={0.5}
        cellColor="#4a4a4a"
        sectionSize={0.5}
        sectionThickness={1}
        sectionColor="#6a6a6a"
        fadeDistance={3}
        fadeStrength={1}
        infiniteGrid={false}
      />
    </>
  );
}

export function Scene({ robotState }: SceneProps) {
  const [cameraViews, setCameraViews] = useState<CameraViewData[]>([]);

  const handleFrameCapture = (views: CameraViewData[]) => {
    setCameraViews(views);
  };

  return (
    <div style={{ width: '100%', height: '100vh', background: '#1a1a1a' }}>
      {/* Camera feed overlay */}
      <VirtualCameraFeed cameraViews={cameraViews} />

      <Canvas
        shadows
        camera={{
          // Camera positioned for Z-up view (MuJoCo coordinates)
          // Overhead angled view from ALOHA: (0, -0.303794, 1.02524)
          position: [0, -1.2, 1.2],
          up: [0, 0, 1], // Z is up in MuJoCo
          fov: 50,
        }}
        gl={{ antialias: true }}
      >
        {/* Lighting */}
        <Lighting />

        {/* Environment map for reflections */}
        <Environment preset="warehouse" />

        {/* Floor */}
        <WorkspaceFloor />

        {/* ALOHA Table */}
        <AlohaTable />

        {/* Test cube on table surface */}
        <BlueCube position={[0, 0, -0.05]} />

        {/* Robot arms - positions defined in MJCF */}
        <RobotArmMJCF joints={robotState.joints} gripperState={robotState.gripperState} />

        {/* Virtual camera system */}
        <VirtualCameraSystem
          robotState={robotState}
          onFrameCapture={handleFrameCapture}
          captureRate={1}
          resolution={{ width: 640, height: 480 }}
        />

        {/* Camera controls - target workspace center (0, -0.1, 0.2) */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          target={[0, -0.1, 0.2]}
          minDistance={0.5}
          maxDistance={3}
          minPolarAngle={0}
          maxPolarAngle={Math.PI}
        />

        {/* Axes helper at world origin for debugging
            Red = X (right), Green = Y (forward), Blue = Z (up) */}
        <axesHelper args={[0.3]} />
      </Canvas>
    </div>
  );
}
