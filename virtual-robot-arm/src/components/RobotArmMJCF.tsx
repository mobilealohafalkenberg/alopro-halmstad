/**
 * RobotArmMJCF - MJCF-based Robot Arm Visualization
 *
 * This component reads the MJCF XML file to get exact joint positions and hierarchy,
 * ensuring perfect alignment with the MuJoCo simulation.
 */

import { useEffect, useState, useRef, useMemo } from 'react';
import { useFrame, useLoader } from '@react-three/fiber';
import * as THREE from 'three';
import { STLLoader } from 'three-stdlib';
import { JointAngles, GripperState } from '../types/robot';
import { parseMJCF, MJCFBody, MJCFModel, printBodyHierarchy, countBodies } from '../lib/mjcf-parser';

interface RobotArmMJCFProps {
  joints: JointAngles;
  gripperState: GripperState;
}

/**
 * Load and cache STL meshes with correct scaling
 * Note: All hooks must be called unconditionally, so we load all meshes upfront
 */
function useALOHAMeshes() {
  // Load all STL files (hooks must be called unconditionally)
  const base = useLoader(STLLoader, '/models/aloha/assets/vx300s_1_base.stl');
  const shoulder = useLoader(STLLoader, '/models/aloha/assets/vx300s_2_shoulder.stl');
  const upperArm = useLoader(STLLoader, '/models/aloha/assets/vx300s_3_upper_arm.stl');
  const upperForearm = useLoader(STLLoader, '/models/aloha/assets/vx300s_4_upper_forearm.stl');
  const lowerForearm = useLoader(STLLoader, '/models/aloha/assets/vx300s_5_lower_forearm.stl');
  const wrist = useLoader(STLLoader, '/models/aloha/assets/vx300s_6_wrist.stl');
  const gripperProp = useLoader(STLLoader, '/models/aloha/assets/vx300s_7_gripper_prop.stl');
  const gripperBar = useLoader(STLLoader, '/models/aloha/assets/vx300s_7_gripper_bar.stl');
  const gripperMount = useLoader(STLLoader, '/models/aloha/assets/vx300s_7_gripper_wrist_mount.stl');
  const fingerLeft = useLoader(STLLoader, '/models/aloha/assets/vx300s_8_custom_finger_left.stl');
  const fingerRight = useLoader(STLLoader, '/models/aloha/assets/vx300s_8_custom_finger_right.stl');
  const camera = useLoader(STLLoader, '/models/aloha/assets/d405_solid.stl');

  // Build mesh map with scaled geometries using MJCF scale values
  const meshMap = useMemo(() => {
    const map = new Map<string, THREE.BufferGeometry>();

    // Helper to scale and prepare geometry
    const prepareGeometry = (geom: THREE.BufferGeometry, scale: number) => {
      const scaled = geom.clone();
      scaled.scale(scale, scale, scale);
      scaled.computeVertexNormals();
      return scaled;
    };

    // Arm parts: 0.001 scale (millimeters to meters)
    const ARM_SCALE = 0.001;
    map.set('vx300s_1_base', prepareGeometry(base, ARM_SCALE));
    map.set('vx300s_2_shoulder', prepareGeometry(shoulder, ARM_SCALE));
    map.set('vx300s_3_upper_arm', prepareGeometry(upperArm, ARM_SCALE));
    map.set('vx300s_4_upper_forearm', prepareGeometry(upperForearm, ARM_SCALE));
    map.set('vx300s_5_lower_forearm', prepareGeometry(lowerForearm, ARM_SCALE));
    map.set('vx300s_6_wrist', prepareGeometry(wrist, ARM_SCALE));

    // Gripper parts: 1.0 scale (already in meters)
    const GRIPPER_SCALE = 1.0;
    map.set('vx300s_7_gripper_prop', prepareGeometry(gripperProp, GRIPPER_SCALE));
    map.set('vx300s_7_gripper_bar', prepareGeometry(gripperBar, GRIPPER_SCALE));
    map.set('vx300s_7_gripper_wrist_mount', prepareGeometry(gripperMount, GRIPPER_SCALE));
    map.set('vx300s_8_custom_finger_left', prepareGeometry(fingerLeft, GRIPPER_SCALE));
    map.set('vx300s_8_custom_finger_right', prepareGeometry(fingerRight, GRIPPER_SCALE));
    map.set('d405_solid', prepareGeometry(camera, GRIPPER_SCALE));

    return map;
  }, [base, shoulder, upperArm, upperForearm, lowerForearm, wrist, gripperProp, gripperBar, gripperMount, fingerLeft, fingerRight, camera]);

  return meshMap;
}

/**
 * Recursive component to render MJCF body hierarchy
 */
function MJCFBodyRenderer({
  body,
  meshMap,
  jointAngles,
  material,
}: {
  body: MJCFBody;
  meshMap: Map<string, THREE.BufferGeometry>;
  jointAngles: Map<string, number>;
  material: THREE.Material;
}) {
  const groupRef = useRef<THREE.Group>(null);

  // Apply joint transformations
  useFrame(() => {
    if (!groupRef.current || !body.jointName) return;

    const angle = jointAngles.get(body.jointName) || 0;

    // Finger slide joints: only left_finger and right_finger (not gripper_base or other parts)
    const isFingerJoint = body.jointName === 'left/left_finger' ||
                          body.jointName === 'left/right_finger' ||
                          body.jointName === 'right/left_finger' ||
                          body.jointName === 'right/right_finger';

    if (isFingerJoint) {
      // Fingers slide along their local Z-axis (axis="0 0 -1" in MJCF)
      // Transform the displacement from local to world coordinates using the body quaternion
      const localDisplacement = new THREE.Vector3(0, 0, -angle); // Negative Z as per MJCF
      const worldDisplacement = localDisplacement.applyQuaternion(bodyQuaternion);
      groupRef.current.position.copy(body.position).add(worldDisplacement);
    } else if (body.jointAxis) {
      // Hinge joints: rotate around axis
      const jointRot = new THREE.Quaternion().setFromAxisAngle(body.jointAxis, angle);
      groupRef.current.quaternion.copy(bodyQuaternion).multiply(jointRot);

      // Log waist joint specifically
      if (body.jointName === 'left/waist' && Math.abs(angle) > 0.01) {
        console.log(`[RobotArmMJCF] Rendering waist rotation: ${angle.toFixed(3)}rad (${(angle * 180 / Math.PI).toFixed(1)}°)`);
      }
    }
  });

  // Use body quaternion directly (no correction needed)
  const bodyQuaternion = body.quaternion;

  return (
    <group ref={groupRef} name={body.name} position={body.position} quaternion={bodyQuaternion}>
      {/* Render all geometries in this body */}
      {body.geometries.map((geom, index) => (
        meshMap.has(geom.meshName) && (
          <mesh
            key={`${body.name}-geom-${index}`}
            geometry={meshMap.get(geom.meshName)!}
            material={material}
            position={geom.position}
            quaternion={geom.quaternion}
            castShadow
            receiveShadow
          />
        )
      ))}

      {/* Recursively render children */}
      {body.children.map((child, index) => (
        <MJCFBodyRenderer
          key={`${child.name}-${index}`}
          body={child}
          meshMap={meshMap}
          jointAngles={jointAngles}
          material={material}
        />
      ))}
    </group>
  );
}

export function RobotArmMJCF({ joints, gripperState }: RobotArmMJCFProps) {
  const [mjcfModel, setMJCFModel] = useState<MJCFModel | null>(null);

  // Load and parse MJCF XML
  useEffect(() => {
    fetch('/models/aloha/aloha.xml')
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return response.text();
      })
      .then((xmlText) => {
        const model = parseMJCF(xmlText);
        setMJCFModel(model);
        console.log(`[RobotArmMJCF] Loaded MJCF model: ${countBodies(model.bodies)} bodies`);
      })
      .catch((error) => {
        console.error('[RobotArmMJCF] Failed to load MJCF:', error);
      });
  }, []);

  // Load meshes
  const meshMap = useALOHAMeshes();

  // Create material
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: 0x2a2a2a,
        metalness: 0.6,
        roughness: 0.4,
      }),
    []
  );

  // Build joint angles map
  const jointAngles = useMemo(() => {
    const gripperValue = gripperState.position * 0.041; // Convert 0-1 to 0-0.041m

    console.log(`[RobotArmMJCF] Joint update - waist: ${joints.waist.toFixed(3)}rad (${(joints.waist * 180 / Math.PI).toFixed(1)}°)`);

    return new Map<string, number>([
      ['left/waist', joints.waist],
      ['left/shoulder', joints.shoulder],
      ['left/elbow', joints.elbow],
      ['left/forearm_roll', joints.forearm_roll],
      ['left/wrist_angle', joints.wrist_angle],
      ['left/wrist_rotate', joints.wrist_rotate],
      // Gripper fingers (slide joints in local Z-axis)
      ['left/left_finger', gripperValue],
      ['left/right_finger', gripperValue],
    ]);
  }, [joints, gripperState]);

  // Show loading state
  if (!mjcfModel) {
    return (
      <group>
        <mesh>
          <boxGeometry args={[0.1, 0.1, 0.1]} />
          <meshStandardMaterial color="orange" />
        </mesh>
      </group>
    );
  }

  return (
    <group>
      {/* Render all bodies from MJCF */}
      {mjcfModel.bodies.map((body, index) => (
        <MJCFBodyRenderer
          key={`${body.name}-${index}`}
          body={body}
          meshMap={meshMap}
          jointAngles={jointAngles}
          material={material}
        />
      ))}

      {/* Coordinate axes for debugging */}
      <axesHelper args={[0.2]} />
    </group>
  );
}
