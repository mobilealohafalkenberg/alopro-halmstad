import { useRef, Suspense, useState } from 'react';
import { useFrame, useLoader, ThreeEvent } from '@react-three/fiber';
import * as THREE from 'three';
import { STLLoader } from 'three-stdlib';
import { Html } from '@react-three/drei';
import { JointAngles, GripperState } from '../types/robot';

interface RobotArmProps {
  joints: JointAngles;
  gripperState: GripperState;
}

// Hoverable mesh component with label
function HoverableMesh({
  geometry,
  material,
  position,
  rotation,
  quaternion,
  label,
  castShadow = true,
}: {
  geometry: THREE.BufferGeometry;
  material: THREE.Material;
  position?: [number, number, number];
  rotation?: [number, number, number];
  quaternion?: THREE.Quaternion;
  label: string;
  castShadow?: boolean;
}) {
  const [hovered, setHovered] = useState(false);

  return (
    <mesh
      geometry={geometry}
      material={material}
      position={position}
      rotation={rotation}
      quaternion={quaternion}
      castShadow={castShadow}
      onPointerOver={(e: ThreeEvent<PointerEvent>) => {
        e.stopPropagation();
        setHovered(true);
      }}
      onPointerOut={() => setHovered(false)}
    >
      {hovered && (
        <Html distanceFactor={0.5}>
          <div
            style={{
              background: 'rgba(0, 0, 0, 0.8)',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              fontSize: '12px',
              whiteSpace: 'nowrap',
              pointerEvents: 'none',
            }}
          >
            {label}
          </div>
        </Html>
      )}
    </mesh>
  );
}

// Load all ALOHA arm meshes
function AlohaArmMeshes() {
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

  return {
    base,
    shoulder,
    upperArm,
    upperForearm,
    lowerForearm,
    wrist,
    gripperProp,
    gripperBar,
    gripperMount,
    fingerLeft,
    fingerRight,
    camera,
  };
}

// Component to load and display ALOHA gripper with hover labels
// Exact structure from ALOHA XML lines 141-180
function AlohaGripper({
  gripperState,
  meshes,
  material,
}: {
  gripperState: GripperState;
  meshes: ReturnType<typeof AlohaArmMeshes>;
  material: THREE.Material;
}) {
  const leftFingerRef = useRef<THREE.Group>(null);
  const rightFingerRef = useRef<THREE.Group>(null);

  // Animate gripper fingers based on joint state
  useFrame(() => {
    // ALOHA finger joints: range 0.015 to 0.037 meters
    const leftAngle = 0.015 + gripperState.position * (0.037 - 0.015);
    const rightAngle = 0.015 + gripperState.position * (0.037 - 0.015);

    if (leftFingerRef.current) {
      // Left finger moves in its local Y axis
      leftFingerRef.current.position.set(0.0191, leftAngle, 0.0211727);
    }
    if (rightFingerRef.current) {
      // Right finger moves in opposite direction
      rightFingerRef.current.position.set(-0.0191, -rightAngle, 0.0211727);
    }
  });

  return (
    <group>
      {/* gripper_base body: euler="0 1.57 -1.57" pos="0.035 0 0" */}
      <group position={[0.035, 0, 0]} rotation={[0, Math.PI / 2, -Math.PI / 2]}>
        {/* Main gripper components - all at origin of gripper_base */}
        <HoverableMesh geometry={meshes.gripperProp} material={material} label="gripper_prop" />
        <HoverableMesh geometry={meshes.gripperBar} material={material} label="gripper_bar" />

        {/* Wrist mount: pos="0 -0.03525 -0.0227" quat="0 -1 0 -1" */}
        <HoverableMesh
          geometry={meshes.gripperMount}
          material={material}
          position={[0, -0.03525, -0.0227]}
          quaternion={new THREE.Quaternion(0, -0.7071, 0, -0.7071)}
          label="wrist_mount"
        />

        {/* D405 Camera: pos="0 -0.0824748 -0.0095955" quat="0 0 -0.21644 -0.976296" */}
        <HoverableMesh
          geometry={meshes.camera}
          material={new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.5, roughness: 0.6 })}
          position={[0, -0.0824748, -0.0095955]}
          quaternion={new THREE.Quaternion(0, 0, -0.21644, -0.976296)}
          label="d405_camera"
        />

        {/* Left finger link: pos="0.0191 -0.0141637 0.0211727" quat="1 -1 -1 1" */}
        <group ref={leftFingerRef} quaternion={new THREE.Quaternion(0.5, -0.5, -0.5, 0.5)}>
          {/* Finger mesh: pos="0.0141637 0.0211727 0.06" quat="1 1 1 -1" */}
          <HoverableMesh
            geometry={meshes.fingerLeft}
            material={material}
            position={[0.0141637, 0.0211727, 0.06]}
            quaternion={new THREE.Quaternion(0.5, 0.5, 0.5, -0.5)}
            label="left_finger"
          />
        </group>

        {/* Right finger link: pos="-0.0191 -0.0141637 0.0211727" quat="1 1 1 1" */}
        <group ref={rightFingerRef} quaternion={new THREE.Quaternion(0.5, 0.5, 0.5, 0.5)}>
          {/* Finger mesh: pos="0.0141637 -0.0211727 0.0597067" quat="1 -1 -1 -1" */}
          <HoverableMesh
            geometry={meshes.fingerRight}
            material={material}
            position={[0.0141637, -0.0211727, 0.0597067]}
            quaternion={new THREE.Quaternion(0.5, -0.5, -0.5, -0.5)}
            label="right_finger"
          />
        </group>
      </group>
    </group>
  );
}

export function RobotArm({ joints, gripperState }: RobotArmProps) {
  // Joint references for animation
  const waistRef = useRef<THREE.Group>(null);
  const shoulderRef = useRef<THREE.Group>(null);
  const elbowRef = useRef<THREE.Group>(null);
  const forearmRollRef = useRef<THREE.Group>(null);
  const wristAngleRef = useRef<THREE.Group>(null);
  const wristRotateRef = useRef<THREE.Group>(null);

  // Update joint angles
  useFrame(() => {
    if (waistRef.current) waistRef.current.rotation.y = joints.waist;
    if (shoulderRef.current) shoulderRef.current.rotation.z = joints.shoulder;
    if (elbowRef.current) elbowRef.current.rotation.z = joints.elbow;
    if (forearmRollRef.current) forearmRollRef.current.rotation.x = joints.forearm_roll;
    if (wristAngleRef.current) wristAngleRef.current.rotation.z = joints.wrist_angle;
    if (wristRotateRef.current) wristRotateRef.current.rotation.x = joints.wrist_rotate;
  });

  // Interbotix material (anodized aluminum)
  const linkMaterial = new THREE.MeshStandardMaterial({
    color: 0x2c3e50,
    metalness: 0.6,
    roughness: 0.4,
  });

  return (
    <Suspense fallback={null}>
      <AlohaArmWithMeshes
        joints={joints}
        gripperState={gripperState}
        waistRef={waistRef}
        shoulderRef={shoulderRef}
        elbowRef={elbowRef}
        forearmRollRef={forearmRollRef}
        wristAngleRef={wristAngleRef}
        wristRotateRef={wristRotateRef}
        linkMaterial={linkMaterial}
      />
    </Suspense>
  );
}

// Component that loads meshes and renders the complete ALOHA arm
function AlohaArmWithMeshes({
  joints,
  gripperState,
  waistRef,
  shoulderRef,
  elbowRef,
  forearmRollRef,
  wristAngleRef,
  wristRotateRef,
  linkMaterial,
}: {
  joints: JointAngles;
  gripperState: GripperState;
  waistRef: React.RefObject<THREE.Group>;
  shoulderRef: React.RefObject<THREE.Group>;
  elbowRef: React.RefObject<THREE.Group>;
  forearmRollRef: React.RefObject<THREE.Group>;
  wristAngleRef: React.RefObject<THREE.Group>;
  wristRotateRef: React.RefObject<THREE.Group>;
  linkMaterial: THREE.Material;
}) {
  const meshes = AlohaArmMeshes();

  return (
    <group>
      {/* Base link - ALOHA XML: pos="0 0 0" */}
      <HoverableMesh
        geometry={meshes.base}
        material={linkMaterial}
        quaternion={new THREE.Quaternion(0, 0, 0, 1)}
        label="base_link"
      />

      {/* Waist/Shoulder link - ALOHA XML: pos="0 0 0.079" */}
      <group ref={waistRef} position={[0, 0, 0.079]}>
        <HoverableMesh
          geometry={meshes.shoulder}
          material={linkMaterial}
          position={[0, 0, -0.003]}
          quaternion={new THREE.Quaternion(0, 0, 0, 1)}
          label="shoulder_link"
        />

        {/* Upper arm link - ALOHA XML: pos="0 0 0.04805" */}
        <group ref={shoulderRef} position={[0, 0, 0.04805]}>
          <HoverableMesh
            geometry={meshes.upperArm}
            material={linkMaterial}
            quaternion={new THREE.Quaternion(0, 0, 0, 1)}
            label="upper_arm_link"
          />

          {/* Upper forearm link - ALOHA XML: pos="0.05955 0 0.3" */}
          <group ref={elbowRef} position={[0.05955, 0, 0.3]}>
            <HoverableMesh
              geometry={meshes.upperForearm}
              material={linkMaterial}
              label="upper_forearm_link"
            />

            {/* Lower forearm link - ALOHA XML: pos="0.2 0 0" */}
            <group ref={forearmRollRef} position={[0.2, 0, 0]}>
              <HoverableMesh
                geometry={meshes.lowerForearm}
                material={linkMaterial}
                quaternion={new THREE.Quaternion(0, 0, 1, 0)}
                label="lower_forearm_link"
              />

              {/* Wrist link - ALOHA XML: pos="0.1 0 0" */}
              <group ref={wristAngleRef} position={[0.1, 0, 0]}>
                <HoverableMesh
                  geometry={meshes.wrist}
                  material={linkMaterial}
                  quaternion={new THREE.Quaternion(0, 0, 0, 1)}
                  label="wrist_link"
                />

                {/* Gripper link - ALOHA XML: pos="0.069744 0 0" */}
                <group ref={wristRotateRef} position={[0.069744, 0, 0]}>
                  <AlohaGripper gripperState={gripperState} meshes={meshes} material={linkMaterial} />
                </group>
              </group>
            </group>
          </group>
        </group>
      </group>

      {/* Axes helper for debugging */}
      <axesHelper args={[0.2]} />
    </group>
  );
}
