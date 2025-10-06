import { FunctionDeclaration, Type } from '@google/genai';

export const toolControlGripper: FunctionDeclaration = {
  name: 'control_gripper',
  description: 'Open or close the robot gripper',
  parameters: {
    type: Type.OBJECT,
    properties: {
      action: { type: Type.STRING, description: 'open or close' },
      arm: { type: Type.STRING, description: 'left or right arm' },
    },
    required: ['action'],
  },
};

export const toolGetGripperStatus: FunctionDeclaration = {
  name: 'get_gripper_status',
  description: 'Get current gripper state and position',
  parameters: {
    type: Type.OBJECT,
    properties: {
      arm: { type: Type.STRING, description: 'left or right arm' },
    },
    required: [],
  },
};

export const toolMoveArm: FunctionDeclaration = {
  name: 'move_arm',
  description: 'Move the robot arm to a target position or pose',
  parameters: {
    type: Type.OBJECT,
    properties: {
      pose: {
        type: Type.STRING,
        description: 'Named pose: home, sleep, or ready',
        enum: ['home', 'sleep', 'ready']
      },
      arm: { type: Type.STRING, description: 'left or right arm' },
    },
    required: [],
  },
};

export const toolGetArmStatus: FunctionDeclaration = {
  name: 'get_arm_status',
  description: 'Get current arm state and joint positions',
  parameters: {
    type: Type.OBJECT,
    properties: {
      arm: { type: Type.STRING, description: 'left or right arm' },
    },
    required: [],
  },
};

export const toolResetRobot: FunctionDeclaration = {
  name: 'reset_robot',
  description: 'Reset the robot to home position',
  parameters: {
    type: Type.OBJECT,
    properties: {},
    required: [],
  },
};

export const ROBOT_TOOLS = [
  toolControlGripper,
  toolGetGripperStatus,
  toolMoveArm,
  toolGetArmStatus,
  toolResetRobot,
];
