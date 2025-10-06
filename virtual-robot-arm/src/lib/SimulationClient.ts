/**
 * MuJoCo Simulation WebSocket Client
 *
 * Connects to the MuJoCo simulation server and provides an API
 * for controlling the dual-arm ALOHA robot.
 */

import { io, Socket } from 'socket.io-client';

export type ArmSide = 'left' | 'right';
export type GripperCommand = 'open' | 'close' | number;

export interface ArmStatus {
  positions: number[];
  velocities: number[];
  mode: string;
}

export interface GripperStatus {
  position: number;
  is_open: boolean;
  mode: string;
}

export interface FrameUpdate {
  frame: string;  // Base64-encoded JPEG
  state?: ArmStatus;
  gripper_state?: GripperStatus;
  timestamp: number;
  initial?: boolean;
}

export interface CommandResult {
  success: boolean;
  command?: string;
  data?: any;
  error?: string;
}

export interface ConnectionStatus {
  status: string;
  mode: string;
  message: string;
}

/**
 * WebSocket client for MuJoCo simulation server
 */
export class SimulationClient {
  private socket: Socket | null = null;
  private serverUrl: string;
  private connected: boolean = false;

  // Event callbacks
  private onConnectCallback?: () => void;
  private onDisconnectCallback?: () => void;
  private onFrameUpdateCallback?: (data: FrameUpdate) => void;
  private onArmStatusCallback?: (arm: ArmSide, status: ArmStatus) => void;
  private onGripperStatusCallback?: (arm: ArmSide, status: GripperStatus) => void;
  private onCommandResultCallback?: (result: CommandResult) => void;
  private onErrorCallback?: (error: string) => void;

  constructor(serverUrl: string = 'http://localhost:5000') {
    this.serverUrl = serverUrl;
  }

  /**
   * Connect to the simulation server
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.serverUrl, {
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionDelay: 1000,
          reconnectionAttempts: 5
        });

        // Connection event
        this.socket.on('connect', () => {
          console.log('[SimulationClient] Connected to server');
          this.connected = true;
          if (this.onConnectCallback) this.onConnectCallback();
          resolve();
        });

        // Disconnection event
        this.socket.on('disconnect', () => {
          console.log('[SimulationClient] Disconnected from server');
          this.connected = false;
          if (this.onDisconnectCallback) this.onDisconnectCallback();
        });

        // Connection status
        this.socket.on('connection_status', (data: ConnectionStatus) => {
          console.log('[SimulationClient] Connection status:', data);
        });

        // Frame updates
        this.socket.on('frame_update', (data: FrameUpdate) => {
          if (this.onFrameUpdateCallback) this.onFrameUpdateCallback(data);
        });

        // Arm status
        this.socket.on('arm_status', (data: { arm: ArmSide; status: ArmStatus; timestamp: number }) => {
          if (this.onArmStatusCallback) this.onArmStatusCallback(data.arm, data.status);
        });

        // Gripper status
        this.socket.on('gripper_status', (data: { arm: ArmSide; status: GripperStatus; timestamp: number }) => {
          if (this.onGripperStatusCallback) this.onGripperStatusCallback(data.arm, data.status);
        });

        // Command results
        this.socket.on('command_result', (result: CommandResult) => {
          if (this.onCommandResultCallback) this.onCommandResultCallback(result);
          if (!result.success && this.onErrorCallback) {
            this.onErrorCallback(result.error || 'Command failed');
          }
        });

        // Connection errors
        this.socket.on('connect_error', (error) => {
          console.error('[SimulationClient] Connection error:', error);
          if (this.onErrorCallback) this.onErrorCallback(error.message);
          reject(error);
        });

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the server
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Check if connected
   */
  isConnected(): boolean {
    return this.connected && this.socket !== null;
  }

  /**
   * Move arm to specified joint positions
   */
  moveArm(arm: ArmSide, positions: number[]): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('move_arm', { arm, positions });
  }

  /**
   * Control gripper
   */
  controlGripper(arm: ArmSide, command: GripperCommand): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('control_gripper', { arm, command });
  }

  /**
   * Get arm status
   */
  getArmStatus(arm: ArmSide): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('get_arm_status', { arm });
  }

  /**
   * Get gripper status
   */
  getGripperStatus(arm: ArmSide): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('get_gripper_status', { arm });
  }

  /**
   * Step simulation (simulation mode only)
   */
  stepSimulation(steps: number = 1): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('step_simulation', { steps });
  }

  /**
   * Reset robot to home position
   */
  resetRobot(): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('reset_robot');
  }

  /**
   * Request initial frame (simulation mode only)
   */
  getInitialFrame(): void {
    if (!this.socket) {
      throw new Error('Not connected to server');
    }
    this.socket.emit('get_initial_frame');
  }

  // Event handlers
  onConnect(callback: () => void): void {
    this.onConnectCallback = callback;
  }

  onDisconnect(callback: () => void): void {
    this.onDisconnectCallback = callback;
  }

  onFrameUpdate(callback: (data: FrameUpdate) => void): void {
    this.onFrameUpdateCallback = callback;
  }

  onArmStatus(callback: (arm: ArmSide, status: ArmStatus) => void): void {
    this.onArmStatusCallback = callback;
  }

  onGripperStatus(callback: (arm: ArmSide, status: GripperStatus) => void): void {
    this.onGripperStatusCallback = callback;
  }

  onCommandResult(callback: (result: CommandResult) => void): void {
    this.onCommandResultCallback = callback;
  }

  onError(callback: (error: string) => void): void {
    this.onErrorCallback = callback;
  }
}
