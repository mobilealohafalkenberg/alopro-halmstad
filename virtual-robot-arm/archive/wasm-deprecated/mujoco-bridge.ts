/**
 * Bridge between RobotController API and MuJoCo simulation
 * Translates robot control commands to MuJoCo joint positions
 */

import { JointAngles, GripperState, Position3D } from '../types/robot';

export class MuJoCoBridge {
  private mujoco: any;
  private simulation: any;

  constructor(mujoco: any, simulation: any) {
    this.mujoco = mujoco;
    this.simulation = simulation;
  }

  /**
   * Set joint angles in MuJoCo simulation
   */
  setJointAngles(joints: JointAngles): void {
    if (!this.simulation || !this.simulation.qpos) {
      console.warn('[MuJoCoBridge] Simulation not ready');
      return;
    }

    // Map joint angles to qpos array
    // ALOHA left arm joint order: waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate
    this.simulation.qpos[0] = joints.waist;
    this.simulation.qpos[1] = joints.shoulder;
    this.simulation.qpos[2] = joints.elbow;
    this.simulation.qpos[3] = joints.forearm_roll;
    this.simulation.qpos[4] = joints.wrist_angle;
    this.simulation.qpos[5] = joints.wrist_rotate;

    // Step simulation to update
    this.simulation.step();
  }

  /**
   * Set gripper state in MuJoCo simulation
   */
  setGripperState(gripperState: GripperState): void {
    if (!this.simulation || !this.simulation.qpos) {
      console.warn('[MuJoCoBridge] Simulation not ready');
      return;
    }

    // ALOHA gripper joints: left_finger, right_finger
    // Gripper position: 0 (closed) to 1 (open)
    // ALOHA finger range: 0.015 to 0.037 meters
    const gripperAngle = 0.015 + gripperState.position * (0.037 - 0.015);

    // Assuming gripper joints are indices 6 and 7 (after the 6 arm joints)
    if (this.simulation.qpos.length > 6) {
      this.simulation.qpos[6] = gripperAngle;  // left finger
    }
    if (this.simulation.qpos.length > 7) {
      this.simulation.qpos[7] = gripperAngle;  // right finger
    }

    this.simulation.step();
  }

  /**
   * Get current joint angles from MuJoCo simulation
   */
  getJointAngles(): JointAngles {
    if (!this.simulation || !this.simulation.qpos) {
      return {
        waist: 0,
        shoulder: 0,
        elbow: 0,
        forearm_roll: 0,
        wrist_angle: 0,
        wrist_rotate: 0,
      };
    }

    return {
      waist: this.simulation.qpos[0] || 0,
      shoulder: this.simulation.qpos[1] || 0,
      elbow: this.simulation.qpos[2] || 0,
      forearm_roll: this.simulation.qpos[3] || 0,
      wrist_angle: this.simulation.qpos[4] || 0,
      wrist_rotate: this.simulation.qpos[5] || 0,
    };
  }

  /**
   * Get end-effector position from MuJoCo simulation
   * Uses forward kinematics from MuJoCo's computed xpos
   */
  getEndEffectorPosition(): Position3D {
    if (!this.simulation || !this.simulation.xpos) {
      return { x: 0, y: 0, z: 0 };
    }

    // End-effector is typically the last body in the kinematic chain
    // ALOHA has gripper_link as the end-effector
    // xpos is a flat array: [body0_x, body0_y, body0_z, body1_x, body1_y, body1_z, ...]

    // Find the end-effector body index (gripper_link or last body)
    const numBodies = this.simulation.xpos.length / 3;
    const endEffectorIndex = Math.max(0, numBodies - 1);

    const baseIndex = endEffectorIndex * 3;

    return {
      x: this.simulation.xpos[baseIndex] || 0,
      y: this.simulation.xpos[baseIndex + 1] || 0,
      z: this.simulation.xpos[baseIndex + 2] || 0,
    };
  }

  /**
   * Step the MuJoCo simulation
   */
  step(): void {
    if (this.simulation) {
      this.simulation.step();
    }
  }

  /**
   * Reset simulation to initial state
   */
  reset(): void {
    if (this.simulation && this.simulation.qpos) {
      // Reset to home position
      for (let i = 0; i < this.simulation.qpos.length; i++) {
        this.simulation.qpos[i] = 0;
      }
      this.simulation.step();
    }
  }

  /**
   * Get MuJoCo simulation instance (for advanced usage)
   */
  getSimulation(): any {
    return this.simulation;
  }

  /**
   * Get MuJoCo module instance (for advanced usage)
   */
  getMuJoCo(): any {
    return this.mujoco;
  }
}
