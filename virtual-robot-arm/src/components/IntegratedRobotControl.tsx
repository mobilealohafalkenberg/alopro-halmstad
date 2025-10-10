/**
 * Integrated Robot Control - Voice + 3D Visualization + Simulation Bridge
 *
 * Combines:
 * - Gemini Live voice control
 * - Three.js 3D robot visualization
 * - Connection to simulation bridge (port 8082)
 */

import { useState, useEffect, useRef } from 'react';
import { Scene } from './Scene';
import { VirtualRobotControl } from './VirtualRobotControl';
import { RobotController } from '../lib/robot-controller';
import { RobotState } from '../types/robot';

export function IntegratedRobotControl() {
  const [robotState, setRobotState] = useState<RobotState | null>(null);
  const lastTimeRef = useRef<number>(Date.now());

  // Create robot controller with state update callback
  const [robotController] = useState(() => {
    const controller = new RobotController(setRobotState);
    // Initialize state immediately
    if (!robotState) {
      setRobotState(controller.getState());
    }
    return controller;
  });

  // Animation loop - calls robotController.update() every frame
  useEffect(() => {
    let animationFrameId: number;

    const animate = () => {
      const now = Date.now();
      const deltaTime = (now - lastTimeRef.current) / 1000; // Convert to seconds
      lastTimeRef.current = now;

      // Update robot controller (handles joint interpolation and gripper animation)
      robotController.update(deltaTime);

      // Continue animation loop
      animationFrameId = requestAnimationFrame(animate);
    };

    // Start animation loop
    animationFrameId = requestAnimationFrame(animate);

    // Cleanup on unmount
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [robotController]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      {/* 3D Visualization - MJCF Parser with Three.js */}
      {robotState && <Scene robotState={robotState} />}

      {/* Voice Control Overlay */}
      <VirtualRobotControl
        robotController={robotController}
        onRobotStateChange={setRobotState}
      />
    </div>
  );
}
