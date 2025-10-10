/**
 * Virtual Camera System - Simulates robot cameras in Three.js
 *
 * Creates virtual cameras matching the real robot's camera setup:
 * - Gripper Camera: Attached to gripper, looks forward
 * - Top Camera: Overhead view of workspace
 *
 * Renders to textures that can be sent to Gemini for visual understanding
 */

import { useRef, useEffect, useState } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { RobotState } from '../types/robot';

export interface CameraViewData {
  name: string;
  imageData: string; // base64 JPEG
  timestamp: number;
}

interface VirtualCameraSystemProps {
  robotState: RobotState;
  onFrameCapture?: (views: CameraViewData[]) => void;
  captureRate?: number; // Frames per second (default: 1 FPS to match real robot)
  resolution?: { width: number; height: number };
}

export function VirtualCameraSystem({
  robotState,
  onFrameCapture,
  captureRate = 1,
  resolution = { width: 640, height: 480 }
}: VirtualCameraSystemProps) {
  const { scene, gl } = useThree();

  // Camera refs
  const gripperCameraRef = useRef<THREE.PerspectiveCamera>();
  const topCameraRef = useRef<THREE.PerspectiveCamera>();

  // Render targets for each camera
  const gripperTargetRef = useRef<THREE.WebGLRenderTarget>();
  const topTargetRef = useRef<THREE.WebGLRenderTarget>();

  // Timing for capture rate
  const lastCaptureTimeRef = useRef<number>(0);
  const captureIntervalMs = 1000 / captureRate;

  // Initialize cameras and render targets
  useEffect(() => {
    // Create gripper camera (FOV ~70° to match RealSense D405)
    const gripperCamera = new THREE.PerspectiveCamera(
      70, // FOV
      resolution.width / resolution.height,
      0.01, // near
      5.0   // far
    );
    gripperCameraRef.current = gripperCamera;

    // Create top camera (overhead view)
    const topCamera = new THREE.PerspectiveCamera(
      60,
      resolution.width / resolution.height,
      0.1,
      5.0
    );
    topCameraRef.current = topCamera;

    // Create render targets
    gripperTargetRef.current = new THREE.WebGLRenderTarget(
      resolution.width,
      resolution.height,
      {
        minFilter: THREE.LinearFilter,
        magFilter: THREE.LinearFilter,
        format: THREE.RGBAFormat,
      }
    );

    topTargetRef.current = new THREE.WebGLRenderTarget(
      resolution.width,
      resolution.height,
      {
        minFilter: THREE.LinearFilter,
        magFilter: THREE.LinearFilter,
        format: THREE.RGBAFormat,
      }
    );

    return () => {
      // Cleanup
      gripperTargetRef.current?.dispose();
      topTargetRef.current?.dispose();
    };
  }, [resolution]);

  // Render from virtual cameras and capture frames
  useFrame(() => {
    if (!onFrameCapture) return;
    if (!gripperCameraRef.current || !topCameraRef.current) return;
    if (!gripperTargetRef.current || !topTargetRef.current) return;

    const now = Date.now();
    if (now - lastCaptureTimeRef.current < captureIntervalMs) return;
    lastCaptureTimeRef.current = now;

    // Find the gripper_base group in the scene hierarchy to track its transform
    let gripperBaseGroup: THREE.Object3D | undefined;
    scene.traverse((obj) => {
      if (obj.name === 'left/gripper_base') {
        gripperBaseGroup = obj;
      }
    });

    if (gripperBaseGroup) {
      // Get world position and quaternion of gripper_base
      const worldPosition = new THREE.Vector3();
      const worldQuaternion = new THREE.Quaternion();
      gripperBaseGroup.getWorldPosition(worldPosition);
      gripperBaseGroup.getWorldQuaternion(worldQuaternion);

      // Camera offset from MJCF: pos="0 -0.0824748 -0.0095955"
      const localCameraOffset = new THREE.Vector3(0, -0.0824748, -0.0095955);

      // Transform local offset to world space
      const worldCameraOffset = localCameraOffset.clone().applyQuaternion(worldQuaternion);

      // Set camera position
      gripperCameraRef.current.position.copy(worldPosition).add(worldCameraOffset);

      // Set camera orientation: euler="2.70525955359 0 0" from MJCF (radians, XYZ order)
      const localEuler = new THREE.Euler(2.70525955359, 0, 0, 'XYZ');
      const localCameraRotation = new THREE.Quaternion().setFromEuler(localEuler);

      // Combine gripper rotation with camera's local rotation
      gripperCameraRef.current.quaternion.copy(worldQuaternion).multiply(localCameraRotation);

      // Set up vector for Z-up coordinate system
      gripperCameraRef.current.up.set(0, 0, 1);
    }

    // Top camera: Overhead looking down at workspace
    topCameraRef.current.position.set(0, -0.3, 1.0);
    topCameraRef.current.up.set(0, 1, 0); // Y-forward for overhead view
    topCameraRef.current.lookAt(0, 0, 0); // Look down at table center

    // Render from gripper camera
    const originalRenderTarget = gl.getRenderTarget();
    gl.setRenderTarget(gripperTargetRef.current);
    gl.render(scene, gripperCameraRef.current);

    // Render from top camera
    gl.setRenderTarget(topTargetRef.current);
    gl.render(scene, topCameraRef.current);

    // Restore original render target
    gl.setRenderTarget(originalRenderTarget);

    // Capture frames as base64 JPEG
    const gripperImageData = renderTargetToBase64(gl, gripperTargetRef.current);
    const topImageData = renderTargetToBase64(gl, topTargetRef.current);

    if (gripperImageData && topImageData) {
      onFrameCapture([
        { name: 'gripper_cam', imageData: gripperImageData, timestamp: now },
        { name: 'top_cam', imageData: topImageData, timestamp: now },
      ]);
    }
  });

  return null; // This component doesn't render anything visible
}

/**
 * Convert WebGL render target to base64 JPEG
 */
function renderTargetToBase64(
  renderer: THREE.WebGLRenderer,
  renderTarget: THREE.WebGLRenderTarget
): string | null {
  try {
    // Read pixels from render target
    const width = renderTarget.width;
    const height = renderTarget.height;
    const pixels = new Uint8Array(width * height * 4);

    renderer.readRenderTargetPixels(
      renderTarget,
      0, 0,
      width, height,
      pixels
    );

    // Create canvas and draw pixels
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');

    if (!ctx) return null;

    // Create ImageData and flip Y axis (WebGL coordinates are bottom-up)
    const imageData = ctx.createImageData(width, height);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const srcIdx = ((height - 1 - y) * width + x) * 4; // Flip Y
        const dstIdx = (y * width + x) * 4;
        imageData.data[dstIdx] = pixels[srcIdx];     // R
        imageData.data[dstIdx + 1] = pixels[srcIdx + 1]; // G
        imageData.data[dstIdx + 2] = pixels[srcIdx + 2]; // B
        imageData.data[dstIdx + 3] = pixels[srcIdx + 3]; // A
      }
    }

    ctx.putImageData(imageData, 0, 0);

    // Convert to base64 JPEG
    const base64 = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];
    return base64;
  } catch (error) {
    console.error('[VirtualCameraSystem] Error capturing frame:', error);
    return null;
  }
}
