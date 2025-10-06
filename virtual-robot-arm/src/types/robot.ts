// Robot arm state and types matching ViperX 300s specifications

export interface JointAngles {
  waist: number;
  shoulder: number;
  elbow: number;
  forearm_roll: number;
  wrist_angle: number;
  wrist_rotate: number;
}

export interface Position3D {
  x: number;
  y: number;
  z: number;
}

export interface Orientation {
  roll: number;
  pitch: number;
  yaw: number;
}

export interface GripperState {
  position: number; // 0 (closed) to 1 (open)
  state: 'open' | 'closed' | 'opening' | 'closing';
}

export interface RobotState {
  joints: JointAngles;
  endEffectorPosition: Position3D;
  gripperState: GripperState;
  status: 'idle' | 'moving' | 'error';
  currentPose?: 'home' | 'ready' | 'sleep';
}

export interface TrajectoryWaypoint {
  point: number[]; // [x, y, z]
  label?: string;
  gripper_action?: 'open' | 'close' | 'maintain';
}

export interface Trajectory {
  waypoints: TrajectoryWaypoint[];
  speed: 'slow' | 'medium' | 'fast';
}

// ViperX 300s specifications
export const ROBOT_SPECS = {
  // Joint limits in radians (matching ALOHA VX300s from MuJoCo Menagerie)
  jointLimits: {
    waist: { min: -3.14158, max: 3.14158 },
    shoulder: { min: -1.85005, max: 1.25664 },
    elbow: { min: -1.76278, max: 1.6057 },
    forearm_roll: { min: -3.14158, max: 3.14158 },
    wrist_angle: { min: -1.8675, max: 2.23402 },
    wrist_rotate: { min: -3.14158, max: 3.14158 },
  },

  // DH parameters (link lengths in meters)
  links: {
    base_to_shoulder: 0.10065,
    shoulder_to_elbow: 0.3,
    elbow_to_forearm: 0.3,
    forearm_to_wrist: 0.065,
    wrist_to_gripper: 0.10,
  },

  // Workspace limits in meters
  workspace: {
    x: { min: -0.5, max: 0.5 },
    y: { min: -0.5, max: 0.5 },
    z: { min: 0.1, max: 0.6 },
  },

  // Named poses (in radians) - matching real ViperX 300s
  poses: {
    home: [0.0, -0.3, 0.6, 0.0, -0.3, 0.0] as const,
    ready: [0.0, -0.96, 1.16, 0.0, -0.3, 0.0] as const,
    sleep: [0.0, -1.85, 1.55, 0.0, -1.57, 0.0] as const,
  },
};
