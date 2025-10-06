// Forward and inverse kinematics for ViperX 300s robot arm
import * as THREE from 'three';
import { JointAngles, Position3D, ROBOT_SPECS } from '../types/robot';

/**
 * Convert joint angles to array format
 */
export function jointsToArray(joints: JointAngles): number[] {
  return [
    joints.waist,
    joints.shoulder,
    joints.elbow,
    joints.forearm_roll,
    joints.wrist_angle,
    joints.wrist_rotate,
  ];
}

/**
 * Convert array to joint angles object
 */
export function arrayToJoints(arr: number[]): JointAngles {
  return {
    waist: arr[0] || 0,
    shoulder: arr[1] || 0,
    elbow: arr[2] || 0,
    forearm_roll: arr[3] || 0,
    wrist_angle: arr[4] || 0,
    wrist_rotate: arr[5] || 0,
  };
}

/**
 * Auto-detect and convert angle units (degrees to radians)
 */
export function normalizeAngles(angles: number[]): number[] {
  // If any angle is > 2*PI (6.28), assume degrees
  const isDegrees = angles.some(a => Math.abs(a) > 6.28);

  if (isDegrees) {
    return angles.map(a => (a * Math.PI) / 180);
  }
  return angles;
}

/**
 * Forward kinematics: compute end effector position from joint angles
 * Uses simplified geometric approach for ViperX 300s
 */
export function forwardKinematics(joints: JointAngles): Position3D {
  const { links } = ROBOT_SPECS;

  // Extract angles
  const q1 = joints.waist;
  const q2 = joints.shoulder;
  const q3 = joints.elbow;
  const q4 = joints.wrist_angle;

  // Compute in horizontal plane first
  const L1 = links.shoulder_to_elbow;
  const L2 = links.elbow_to_forearm;
  const L3 = links.forearm_to_wrist + links.wrist_to_gripper;

  // Project onto 2D plane (r-z)
  const r1 = L1 * Math.cos(q2);
  const z1 = L1 * Math.sin(q2);

  const r2 = L2 * Math.cos(q2 + q3);
  const z2 = L2 * Math.sin(q2 + q3);

  const r3 = L3 * Math.cos(q2 + q3 + q4);
  const z3 = L3 * Math.sin(q2 + q3 + q4);

  // Total reach in horizontal plane
  const r_total = r1 + r2 + r3;

  // Convert to 3D coordinates
  const x = r_total * Math.cos(q1);
  const y = r_total * Math.sin(q1);
  const z = links.base_to_shoulder + z1 + z2 + z3;

  return { x, y, z };
}

/**
 * Simplified inverse kinematics for reaching target positions
 * Uses geometric approach suitable for real-time simulation
 */
export function inverseKinematics(
  target: Position3D,
  currentJoints?: JointAngles
): JointAngles | null {
  const { links, workspace } = ROBOT_SPECS;

  // Check workspace bounds
  if (
    target.x < workspace.x.min || target.x > workspace.x.max ||
    target.y < workspace.y.min || target.y > workspace.y.max ||
    target.z < workspace.z.min || target.z > workspace.z.max
  ) {
    console.warn('Target outside workspace bounds');
    return null;
  }

  // Waist angle (rotation around Z axis)
  const q1 = Math.atan2(target.y, target.x);

  // Distance in XY plane
  const r = Math.sqrt(target.x * target.x + target.y * target.y);

  // Height relative to base
  const h = target.z - links.base_to_shoulder;

  // Link lengths for 2D IK
  const L1 = links.shoulder_to_elbow;
  const L2 = links.elbow_to_forearm;
  const L3 = links.forearm_to_wrist + links.wrist_to_gripper;

  // Use wrist position (before last link)
  const wrist_r = r - L3 * 0.8; // Slight offset for natural pose
  const wrist_h = h;

  // Distance to wrist
  const d = Math.sqrt(wrist_r * wrist_r + wrist_h * wrist_h);

  // Check reachability
  if (d > L1 + L2 || d < Math.abs(L1 - L2)) {
    console.warn('Target unreachable');
    return null;
  }

  // Elbow angle using law of cosines
  const cos_q3 = (d * d - L1 * L1 - L2 * L2) / (2 * L1 * L2);
  const q3 = Math.acos(Math.max(-1, Math.min(1, cos_q3)));

  // Shoulder angle
  const alpha = Math.atan2(wrist_h, wrist_r);
  const beta = Math.acos(
    Math.max(-1, Math.min(1, (L1 * L1 + d * d - L2 * L2) / (2 * L1 * d)))
  );
  const q2 = alpha - beta;

  // Wrist angle (keep gripper pointing down)
  const q4 = -(q2 + q3);

  // Keep forearm roll and wrist rotate neutral or preserve current
  const q5 = currentJoints?.forearm_roll || 0;
  const q6 = currentJoints?.wrist_rotate || 0;

  return {
    waist: q1,
    shoulder: q2,
    elbow: q3,
    forearm_roll: q5,
    wrist_angle: q4,
    wrist_rotate: q6,
  };
}

/**
 * Interpolate between two joint configurations
 */
export function interpolateJoints(
  start: JointAngles,
  end: JointAngles,
  t: number
): JointAngles {
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

  return {
    waist: lerp(start.waist, end.waist, t),
    shoulder: lerp(start.shoulder, end.shoulder, t),
    elbow: lerp(start.elbow, end.elbow, t),
    forearm_roll: lerp(start.forearm_roll, end.forearm_roll, t),
    wrist_angle: lerp(start.wrist_angle, end.wrist_angle, t),
    wrist_rotate: lerp(start.wrist_rotate, end.wrist_rotate, t),
  };
}

/**
 * Clamp joint angles to valid limits
 */
export function clampJoints(joints: JointAngles): JointAngles {
  const { jointLimits } = ROBOT_SPECS;

  return {
    waist: Math.max(jointLimits.waist.min, Math.min(jointLimits.waist.max, joints.waist)),
    shoulder: Math.max(jointLimits.shoulder.min, Math.min(jointLimits.shoulder.max, joints.shoulder)),
    elbow: Math.max(jointLimits.elbow.min, Math.min(jointLimits.elbow.max, joints.elbow)),
    forearm_roll: Math.max(jointLimits.forearm_roll.min, Math.min(jointLimits.forearm_roll.max, joints.forearm_roll)),
    wrist_angle: Math.max(jointLimits.wrist_angle.min, Math.min(jointLimits.wrist_angle.max, joints.wrist_angle)),
    wrist_rotate: Math.max(jointLimits.wrist_rotate.min, Math.min(jointLimits.wrist_rotate.max, joints.wrist_rotate)),
  };
}

/**
 * Get named pose by name
 */
export function getNamedPose(name: 'home' | 'ready' | 'sleep'): JointAngles {
  const angles = ROBOT_SPECS.poses[name];
  return arrayToJoints([...angles]);
}
