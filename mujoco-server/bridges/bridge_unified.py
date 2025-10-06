"""
Unified Robot Bridge - Works with BOTH simulation and real robot

This bridge provides the SAME API for controlling either:
- MuJoCo simulation (mode='simulation')
- Real Interbotix robot (mode='real')

Usage:
    bridge = UnifiedRobotBridge(mode='simulation')
    bridge.move_arm('left', [0, -0.96, 1.16, 0, -0.3, 0])
    bridge.control_gripper('left', 'open')
"""

import numpy as np
from typing import Dict, List, Literal, Optional, Tuple

# Mode type
RobotMode = Literal['simulation', 'real']
ArmSide = Literal['left', 'right']


class UnifiedRobotBridge:
    """
    Unified interface for both simulated and real ALOHA robot.

    The SAME code works for both modes - just change the mode parameter!
    """

    def __init__(self, mode: RobotMode = 'simulation', model_path: str = 'models/aloha/scene.xml'):
        """
        Initialize robot bridge.

        Args:
            mode: 'simulation' for MuJoCo, 'real' for physical robot
            model_path: Path to MuJoCo XML model (simulation mode only)
        """
        self.mode = mode
        self.model_path = model_path

        if mode == 'simulation':
            self._init_simulation()
        elif mode == 'real':
            self._init_real_robot()
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'simulation' or 'real'")

    def _init_simulation(self):
        """Initialize MuJoCo simulation"""
        try:
            import mujoco
        except ImportError:
            raise ImportError("mujoco package required for simulation mode. Install: pip install mujoco")

        print(f"[UnifiedBridge] Loading MuJoCo model: {self.model_path}")
        self.model = mujoco.MjModel.from_xml_path(self.model_path)
        self.data = mujoco.MjData(self.model)

        # Create renderer lazily (only when render() is called)
        # This allows headless operation without OpenGL
        self.renderer = None

        # Detect available joints
        # ALOHA has 7 joints per arm (6 DOF + gripper) for dual-arm
        # or 6 joints for single-arm (no gripper in simplified model)
        total_dof = self.model.nv

        # Single arm: 6 DOF
        # Dual arm: 12-16 DOF (depending on gripper implementation)
        if total_dof <= 7:
            # Single arm model
            self.left_arm_joints = list(range(0, min(6, total_dof)))
            self.right_arm_joints = []
            self.has_right_arm = False
        else:
            # Dual arm model
            joints_per_arm = total_dof // 2
            self.left_arm_joints = list(range(0, joints_per_arm))
            self.right_arm_joints = list(range(joints_per_arm, total_dof))
            self.has_right_arm = True

        print(f"[UnifiedBridge] MuJoCo simulation initialized")
        print(f"  - Model DOF: {self.model.nv}")
        print(f"  - Left arm joints: {self.left_arm_joints}")
        if self.has_right_arm:
            print(f"  - Right arm joints: {self.right_arm_joints}")
        else:
            print(f"  - Single arm model (no right arm)")

    def _init_real_robot(self):
        """Initialize real Interbotix robot"""
        try:
            from interbotix_xs_modules.xs_robot.arm import InterbotixManipulatorXS
        except ImportError:
            raise ImportError(
                "interbotix_xs_modules required for real mode. "
                "Install from: https://github.com/Interbotix/interbotix_ros_manipulators"
            )

        print("[UnifiedBridge] Initializing real Interbotix robots...")

        # Initialize left arm
        self.robot_left = InterbotixManipulatorXS(
            robot_model="vx300s",
            robot_name="follower_left",
            group_name="arm"
        )

        # Initialize right arm
        self.robot_right = InterbotixManipulatorXS(
            robot_model="vx300s",
            robot_name="follower_right",
            group_name="arm"
        )

        print("[UnifiedBridge] Real robots initialized")

    # ================================================================================
    # Core API - SAME for both simulation and real!
    # ================================================================================

    def move_arm(
        self,
        arm: ArmSide,
        positions: List[float],
        blocking: bool = False
    ) -> Dict:
        """
        Move arm to specified joint positions.

        Args:
            arm: 'left' or 'right'
            positions: List of 6 joint angles (radians)
            blocking: Wait for movement to complete (real robot only)

        Returns:
            Dictionary with success status
        """
        if self.mode == 'simulation':
            # Check if arm exists
            if arm == 'right' and not self.has_right_arm:
                return {'success': False, 'error': 'Right arm not available in single-arm model'}

            # Update MuJoCo simulation
            joint_indices = self.left_arm_joints if arm == 'left' else self.right_arm_joints

            # Set joint positions
            num_joints = min(len(joint_indices), len(positions))
            for i in range(num_joints):
                if i < len(joint_indices):
                    self.data.qpos[joint_indices[i]] = positions[i]

            # Forward kinematics to update state
            import mujoco
            mujoco.mj_forward(self.model, self.data)

            return {'success': True, 'mode': 'simulation'}

        elif self.mode == 'real':
            # Send to real robot
            robot = self.robot_left if arm == 'left' else self.robot_right
            robot.arm.set_joint_positions(positions, blocking=blocking)

            return {'success': True, 'mode': 'real'}

    def control_gripper(
        self,
        arm: ArmSide,
        command: Literal['open', 'close'] | float,
        delay: float = 1.0
    ) -> Dict:
        """
        Control gripper state.

        Args:
            arm: 'left' or 'right'
            command: 'open', 'close', or position value (0-1)
            delay: Time to wait for gripper movement (real robot only)

        Returns:
            Dictionary with success status
        """
        # Convert command to position
        if command == 'open':
            position = 0.037  # Open position in meters
        elif command == 'close':
            position = -0.01  # Close position in meters
        else:
            position = float(command)

        if self.mode == 'simulation':
            # Update gripper joint in MuJoCo
            joint_indices = self.left_arm_joints if arm == 'left' else self.right_arm_joints
            gripper_index = joint_indices[6]  # 7th joint is gripper

            self.data.qpos[gripper_index] = position

            import mujoco
            mujoco.mj_forward(self.model, self.data)

            return {'success': True, 'mode': 'simulation', 'position': position}

        elif self.mode == 'real':
            robot = self.robot_left if arm == 'left' else self.robot_right
            robot.gripper.set_pressure(1.0)  # Set gripper pressure

            # Open or close gripper
            if command == 'open':
                robot.gripper.open(delay=delay)
            elif command == 'close':
                robot.gripper.close(delay=delay)
            else:
                robot.gripper.set_position(position)

            return {'success': True, 'mode': 'real', 'command': command}

    def get_arm_status(self, arm: ArmSide) -> Dict:
        """
        Get current arm joint positions.

        Args:
            arm: 'left' or 'right'

        Returns:
            Dictionary with joint positions and velocities
        """
        if self.mode == 'simulation':
            joint_indices = self.left_arm_joints if arm == 'left' else self.right_arm_joints

            positions = [self.data.qpos[i] for i in joint_indices[:6]]
            velocities = [self.data.qvel[i] for i in joint_indices[:6]]

            return {
                'positions': positions,
                'velocities': velocities,
                'mode': 'simulation'
            }

        elif self.mode == 'real':
            robot = self.robot_left if arm == 'left' else self.robot_right

            positions = robot.arm.get_joint_positions().tolist()

            return {
                'positions': positions,
                'velocities': [0.0] * 6,  # Real robot doesn't expose velocities easily
                'mode': 'real'
            }

    def get_gripper_status(self, arm: ArmSide) -> Dict:
        """
        Get current gripper state.

        Args:
            arm: 'left' or 'right'

        Returns:
            Dictionary with gripper position
        """
        if self.mode == 'simulation':
            joint_indices = self.left_arm_joints if arm == 'left' else self.right_arm_joints
            gripper_index = joint_indices[6]

            position = self.data.qpos[gripper_index]

            return {
                'position': position,
                'is_open': position > 0,
                'mode': 'simulation'
            }

        elif self.mode == 'real':
            robot = self.robot_left if arm == 'left' else self.robot_right

            # Real robot gripper status
            position = robot.gripper.get_position()

            return {
                'position': position,
                'is_open': position > 0.02,
                'mode': 'real'
            }

    def step_simulation(self, steps: int = 1):
        """
        Advance physics simulation (simulation mode only).

        Args:
            steps: Number of simulation steps
        """
        if self.mode != 'simulation':
            raise RuntimeError("step_simulation() only available in simulation mode")

        import mujoco
        for _ in range(steps):
            mujoco.mj_step(self.model, self.data)

    def render(self) -> np.ndarray:
        """
        Render current scene (simulation mode only).

        Returns:
            RGB image array (H x W x 3)
        """
        if self.mode != 'simulation':
            raise RuntimeError("render() only available in simulation mode")

        # Lazy initialization of renderer (requires OpenGL)
        if self.renderer is None:
            try:
                import mujoco
                print("[UnifiedBridge] Initializing renderer (requires OpenGL/X11)...")
                self.renderer = mujoco.Renderer(self.model, height=480, width=640)
            except Exception as e:
                print(f"[UnifiedBridge] WARNING: Could not create renderer: {e}")
                print("[UnifiedBridge] Running in headless mode - rendering disabled")
                # Return a blank frame
                return np.zeros((480, 640, 3), dtype=np.uint8)

        self.renderer.update_scene(self.data)
        return self.renderer.render()

    def reset(self):
        """
        Reset robot to home position.
        """
        home_positions = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0]

        self.move_arm('left', home_positions)

        # Only reset right arm if it exists
        if self.mode == 'simulation':
            if self.has_right_arm:
                self.move_arm('right', home_positions)

            import mujoco
            mujoco.mj_forward(self.model, self.data)
        elif self.mode == 'real':
            self.move_arm('right', home_positions)

    def close(self):
        """
        Clean up resources.
        """
        if self.mode == 'real':
            print("[UnifiedBridge] Closing real robot connections...")
            self.robot_left.core.robot_shutdown()
            self.robot_right.core.robot_shutdown()

        print("[UnifiedBridge] Bridge closed")


# Example usage
if __name__ == '__main__':
    import time

    # Test simulation mode
    print("="*60)
    print("Testing SIMULATION mode")
    print("="*60)

    bridge = UnifiedRobotBridge(mode='simulation')

    # Move left arm
    print("\nMoving left arm to ready position...")
    bridge.move_arm('left', [0, -0.96, 1.16, 0, -0.3, 0])

    # Get status
    status = bridge.get_arm_status('left')
    print(f"Left arm status: {status}")

    # Render frame
    frame = bridge.render()
    print(f"Rendered frame shape: {frame.shape}")

    # Close gripper
    print("\nClosing left gripper...")
    bridge.control_gripper('left', 'close')

    gripper_status = bridge.get_gripper_status('left')
    print(f"Gripper status: {gripper_status}")

    print("\n" + "="*60)
    print("Simulation test complete!")
    print("="*60)

    # Uncomment to test with real robot:
    # bridge_real = UnifiedRobotBridge(mode='real')
    # bridge_real.move_arm('left', [0, -0.96, 1.16, 0, -0.3, 0])
