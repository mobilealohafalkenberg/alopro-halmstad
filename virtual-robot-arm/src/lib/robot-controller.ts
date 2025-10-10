/**
 * Virtual robot controller that simulates the ViperX 300s arm behavior
 */

import {
  JointAngles,
  Position3D,
  GripperState,
  RobotState,
  ROBOT_SPECS,
  TrajectoryWaypoint,
} from '../types/robot';
import {
  forwardKinematics,
  inverseKinematics,
  interpolateJoints,
  clampJoints,
  getNamedPose,
  normalizeAngles,
  arrayToJoints,
  jointsToArray,
} from './kinematics';

export class RobotController {
  private state: RobotState;
  private targetJoints: JointAngles | null = null;
  private animationProgress = 0;
  private animationDuration = 1.5; // seconds
  private isAnimating = false;

  // Gripper animation
  private targetGripperPosition: number | null = null;
  private gripperAnimationSpeed = 2.0; // units per second

  constructor(
    private onStateChange: (state: RobotState) => void
  ) {
    // Initialize to ready position (matching aloha_sim)
    this.state = {
      joints: getNamedPose('ready'),
      endEffectorPosition: { x: 0, y: 0, z: 0.5 },
      gripperState: {
        position: 0.0, // fully closed (matches MJCF base positions)
        state: 'closed',
      },
      status: 'idle',
      currentPose: 'ready',
    };

    this.updateEndEffectorPosition();
    this.onStateChange(this.state);
  }

  /**
   * Main update loop - call this every frame
   */
  update(deltaTime: number) {
    let stateChanged = false;

    // Animate arm movement
    if (this.isAnimating && this.targetJoints) {
      this.animationProgress += deltaTime / this.animationDuration;

      if (this.animationProgress >= 1.0) {
        // Animation complete
        this.state.joints = this.targetJoints;
        this.isAnimating = false;
        this.animationProgress = 0;
        this.state.status = 'idle';
        stateChanged = true;

        // Log final position
        this.updateEndEffectorPosition();
        console.log(`[RobotController] ✓ Movement complete - EE position: x=${this.state.endEffectorPosition.x.toFixed(3)}, y=${this.state.endEffectorPosition.y.toFixed(3)}, z=${this.state.endEffectorPosition.z.toFixed(3)}`);
      } else {
        // Interpolate
        const startJoints = this.state.joints;
        this.state.joints = interpolateJoints(
          startJoints,
          this.targetJoints,
          this.easeInOutCubic(this.animationProgress)
        );
        stateChanged = true;
      }

      this.updateEndEffectorPosition();
    }

    // Animate gripper
    if (this.targetGripperPosition !== null) {
      const diff = this.targetGripperPosition - this.state.gripperState.position;
      const step = Math.sign(diff) * this.gripperAnimationSpeed * deltaTime;

      if (Math.abs(diff) < Math.abs(step)) {
        // Create new gripperState object (don't mutate)
        this.state.gripperState = {
          position: this.targetGripperPosition,
          state: this.targetGripperPosition > 0.5 ? 'open' : 'closed',
        };
        this.targetGripperPosition = null;
        stateChanged = true;
        console.log(`[RobotController] ✓ Gripper action complete - state: ${this.state.gripperState.state}, position: ${(this.state.gripperState.position * 100).toFixed(0)}%`);
      } else {
        // Create new gripperState object (don't mutate)
        this.state.gripperState = {
          position: this.state.gripperState.position + step,
          state: step > 0 ? 'opening' : 'closing',
        };
        stateChanged = true;
      }
    }

    if (stateChanged) {
      this.onStateChange({ ...this.state });
    }
  }

  /**
   * Get current robot state
   */
  getState(): RobotState {
    return { ...this.state };
  }

  /**
   * Move arm to named pose
   */
  moveToNamedPose(name: 'home' | 'ready' | 'sleep', duration: number = 1.5): boolean {
    const joints = getNamedPose(name);
    this.startJointAnimation(joints, duration);
    this.state.currentPose = name;
    return true;
  }

  /**
   * Parse joint angles with automatic unit detection (matching real robot)
   */
  private parseJointAngles(angles: number[], unit: string = 'auto'): number[] {
    if (angles.length !== 6) {
      throw new Error(`Expected 6 joint angles, got ${angles.length}`);
    }

    // Auto-detect unit based on value ranges (same logic as real robot)
    if (unit === 'auto') {
      // If any absolute value > 2π (6.28), likely degrees
      if (angles.some(a => Math.abs(a) > 2 * Math.PI)) {
        console.log(`[RobotController] Auto-detected degrees (max value: ${Math.max(...angles.map(Math.abs)).toFixed(2)})`);
        return angles.map(a => (a * Math.PI) / 180); // Convert to radians
      } else {
        console.log(`[RobotController] Auto-detected radians (max value: ${Math.max(...angles.map(Math.abs)).toFixed(2)})`);
        return angles;
      }
    } else if (unit === 'degrees') {
      return angles.map(a => (a * Math.PI) / 180);
    } else {
      return angles; // Already in radians
    }
  }

  /**
   * Parse position coordinates with format detection (matching real robot)
   */
  private parsePosition(position: number[] | Position3D): Position3D {
    if (Array.isArray(position)) {
      if (position.length === 2) {
        // Assume [y, x] format (Gemini trajectory style)
        // Check if values are normalized (0-1000 range)
        if (position.some(v => Math.abs(v) > 10)) {
          // Likely normalized coordinates (0-1000)
          return {
            x: position[1] / 1000.0,
            y: position[0] / 1000.0,
            z: 0.2, // Default safe height
          };
        } else {
          // Already in meters
          return {
            x: position[1],
            y: position[0],
            z: 0.2, // Default safe height
          };
        }
      } else if (position.length === 3) {
        // Standard [x, y, z] format
        return { x: position[0], y: position[1], z: position[2] };
      } else {
        throw new Error(`Position must have 2 or 3 elements, got ${position.length}`);
      }
    } else {
      // Already a Position3D object
      return position;
    }
  }

  /**
   * Move arm to specific joint angles (with auto-detection)
   */
  moveToJointAngles(angles: number[], unit: string = 'auto', duration: number = 1.5): boolean {
    try {
      const anglesRad = this.parseJointAngles(angles, unit);
      const normalized = normalizeAngles(anglesRad);
      const joints = clampJoints(arrayToJoints(normalized));

      console.log(`[RobotController] → Moving to joint angles:`, angles);
      this.startJointAnimation(joints, duration);
      this.state.currentPose = undefined;
      return true;
    } catch (error) {
      console.error('[RobotController]', error);
      return false;
    }
  }

  /**
   * Move arm to cartesian position using IK (with format parsing)
   */
  moveToPosition(position: number[] | Position3D, duration: number = 1.5): boolean {
    try {
      const parsedPos = this.parsePosition(position);
      console.log(`[RobotController] → Moving to XYZ position: x=${parsedPos.x.toFixed(3)}, y=${parsedPos.y.toFixed(3)}, z=${parsedPos.z.toFixed(3)}`);

      const joints = inverseKinematics(parsedPos, this.state.joints);

      if (!joints) {
        console.error('[RobotController] ❌ Cannot reach target position:', parsedPos);
        return false;
      }

      this.startJointAnimation(joints, duration);
      this.state.currentPose = undefined;
      return true;
    } catch (error) {
      console.error('[RobotController]', error);
      return false;
    }
  }

  /**
   * Unified move_arm function matching real robot API
   */
  moveArm(args: {
    pose?: 'home' | 'ready' | 'sleep';
    joints?: number[];
    position?: number[] | Position3D;
    unit?: string;
    moving_time?: number;
  }): { success: boolean; error?: string } {
    const duration = args.moving_time || 1.5;

    try {
      // Priority: pose > joints > position
      if (args.pose) {
        this.moveToNamedPose(args.pose, duration);
        return { success: true };
      } else if (args.joints) {
        const success = this.moveToJointAngles(args.joints, args.unit || 'auto', duration);
        return { success };
      } else if (args.position) {
        const success = this.moveToPosition(args.position, duration);
        return { success };
      } else {
        return { success: false, error: 'Must provide pose, joints, or position' };
      }
    } catch (error) {
      return { success: false, error: String(error) };
    }
  }

  /**
   * Execute trajectory with multiple waypoints (matching real robot behavior)
   */
  async executeTrajectory(
    waypoints: TrajectoryWaypoint[],
    speed: 'slow' | 'medium' | 'fast' = 'medium'
  ): Promise<boolean> {
    const durations = { slow: 2.5, medium: 1.5, fast: 0.8 };
    const duration = durations[speed];

    console.log(`[RobotController] Executing trajectory with ${waypoints.length} waypoints at ${speed} speed`);

    for (let i = 0; i < waypoints.length; i++) {
      const waypoint = waypoints[i];
      const label = waypoint.label || `waypoint ${i + 1}`;

      console.log(`[RobotController] Moving to ${label}:`, waypoint.point);

      // Handle gripper action first (before movement)
      if (waypoint.gripper_action === 'open') {
        console.log(`[RobotController] Opening gripper at ${label}`);
        this.openGripper();
      } else if (waypoint.gripper_action === 'close') {
        console.log(`[RobotController] Closing gripper at ${label}`);
        this.closeGripper();
      }

      // Move to position using parsePosition for format compatibility
      const success = this.moveToPosition(waypoint.point, duration);

      if (!success) {
        console.error(`[RobotController] ❌ Failed to reach ${label}`);
        return false;
      }

      // Wait for movement to complete
      await this.waitForMovementComplete();
      console.log(`[RobotController] ✓ Reached ${label}`);
    }

    console.log(`[RobotController] ✓ Trajectory completed successfully`);
    return true;
  }

  /**
   * Open gripper
   */
  openGripper(): boolean {
    console.log(`[RobotController] openGripper() called - current: ${this.state.gripperState.position.toFixed(2)}, target: 1.0`);
    this.targetGripperPosition = 1.0;
    return true;
  }

  /**
   * Close gripper
   */
  closeGripper(): boolean {
    console.log(`[RobotController] closeGripper() called - current: ${this.state.gripperState.position.toFixed(2)}, target: 0.0`);
    this.targetGripperPosition = 0.0;
    return true;
  }

  /**
   * Get arm status
   */
  getArmStatus() {
    const jointsDegrees = jointsToArray(this.state.joints).map(rad => (rad * 180) / Math.PI);

    return {
      state: this.state.status,
      joints: jointsToArray(this.state.joints),
      joints_degrees: jointsDegrees,
      ee_position: this.state.endEffectorPosition,
      pose: this.state.currentPose || null,
      success: true,
    };
  }

  /**
   * Get gripper status
   */
  getGripperStatus() {
    return {
      state: this.state.gripperState.state,
      position_normalized: this.state.gripperState.position,
      position_percent: this.state.gripperState.position * 100,
      success: true,
    };
  }

  // Private helper methods

  private startJointAnimation(joints: JointAngles, duration: number) {
    this.targetJoints = joints;
    this.animationDuration = duration;
    this.animationProgress = 0;
    this.isAnimating = true;
    this.state.status = 'moving';
    this.onStateChange({ ...this.state });
  }

  private updateEndEffectorPosition() {
    this.state.endEffectorPosition = forwardKinematics(this.state.joints);
  }

  private easeInOutCubic(t: number): number {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  private async waitForMovementComplete(): Promise<void> {
    return new Promise((resolve) => {
      const checkInterval = setInterval(() => {
        if (!this.isAnimating && this.targetGripperPosition === null) {
          clearInterval(checkInterval);
          resolve();
        }
      }, 100);
    });
  }
}
