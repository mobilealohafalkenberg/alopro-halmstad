"use client"
import { useEffect, useState, useRef } from 'react';
import { GenAILiveClient } from '../lib/genai-live-client';
import { AudioRecorder } from '../lib/audio-recorder';
import { RobotController } from '../lib/robot-controller';
import { RobotState, ROBOT_SPECS } from '../types/robot';
import { FunctionDeclaration, Type } from '@google/genai';

interface VirtualRobotControlProps {
  robotController: RobotController;
  onRobotStateChange: (state: RobotState) => void;
}

// Tool function declarations for Gemini
const toolControlGripper: FunctionDeclaration = {
  name: 'control_gripper',
  description: 'Open or close the robot gripper',
  parameters: {
    type: Type.OBJECT,
    properties: {
      action: { type: Type.STRING, description: 'open or close' },
    },
    required: ['action'],
  },
};

const toolGetGripperStatus: FunctionDeclaration = {
  name: 'get_gripper_status',
  description: 'Get current gripper state and position',
  parameters: { type: Type.OBJECT, properties: {}, required: [] },
};

const toolMoveArm: FunctionDeclaration = {
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
      joints: {
        type: Type.ARRAY,
        description: 'List of 6 joint angles (auto-detects radians or degrees)',
        items: { type: Type.NUMBER }
      },
      position: {
        type: Type.ARRAY,
        description: 'Cartesian position [x,y,z] in meters',
        items: { type: Type.NUMBER }
      },
      moving_time: {
        type: Type.NUMBER,
        description: 'Time to complete movement in seconds'
      }
    },
    required: [],
  },
};

const toolGetArmStatus: FunctionDeclaration = {
  name: 'get_arm_status',
  description: 'Get current arm state, joint positions, and end effector pose',
  parameters: { type: Type.OBJECT, properties: {}, required: [] },
};

const toolMoveArmTrajectory: FunctionDeclaration = {
  name: 'move_arm_trajectory',
  description: 'Execute a multi-point trajectory for complex movements with optional gripper actions',
  parameters: {
    type: Type.OBJECT,
    properties: {
      trajectory: {
        type: Type.ARRAY,
        description: 'Array of waypoints forming the trajectory',
        items: {
          type: Type.OBJECT,
          properties: {
            point: {
              type: Type.ARRAY,
              description: 'Position [x,y,z] in meters',
              items: { type: Type.NUMBER }
            },
            label: {
              type: Type.STRING,
              description: 'Descriptive label for this waypoint'
            },
            gripper_action: {
              type: Type.STRING,
              description: 'Optional gripper action at this waypoint',
              enum: ['open', 'close', 'maintain']
            }
          },
          required: ['point']
        }
      },
      speed: {
        type: Type.STRING,
        description: 'Overall trajectory execution speed',
        enum: ['slow', 'medium', 'fast']
      }
    },
    required: ['trajectory']
  }
};

const SYSTEM_INSTRUCTION = `
You are an advanced spatial reasoning AI controlling a virtual Mobile ALOHA robot with a 6-DOF arm and gripper.

CONTROL CAPABILITIES:
- move_arm(): Single-point movements (pose/joints/position)
- control_gripper(): Open or close gripper
- get_arm_status() / get_gripper_status(): Query current state
- move_arm_trajectory(): Execute multi-waypoint paths with labeled steps and gripper coordination

WORKSPACE CONSTRAINTS:
- x, y: [-0.5, 0.5] meters
- z: [0.1, 0.6] meters (NEVER go below z=0.1m - table level)

OBJECTS IN SCENE:
- Green apple at approximately [0.25, 0.15, 0.04]
- Blue cube at approximately [0.3, -0.1, 0.025]

TRAJECTORY FORMAT:
When using move_arm_trajectory, structure waypoints as:
[
  {"point": [x, y, z], "label": "approach", "gripper_action": "open"},
  {"point": [x, y, z], "label": "grasp_position", "gripper_action": "close"},
  {"point": [x, y, z], "label": "lift", "gripper_action": "maintain"}
]

EXAMPLE BEHAVIORS:
- "Pick up the apple": Generate trajectory to approach, grasp, and lift
- "Move to home": Use move_arm with pose="home"
- "Open gripper": Use control_gripper with action="open"

Be precise with coordinates and ensure all z values stay above 0.1m for safety.
`;

export function VirtualRobotControl({ robotController, onRobotStateChange }: VirtualRobotControlProps) {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [taskStatus, setTaskStatus] = useState('Ready');
  const [transcript, setTranscript] = useState<string[]>([]);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [textInput, setTextInput] = useState('');

  const clientRef = useRef<GenAILiveClient | null>(null);
  const audioRecorderRef = useRef<AudioRecorder | null>(null);

  // Initialize Gemini client
  useEffect(() => {
    console.log('[VirtualRobotControl] Initializing...');
    const apiKey = process.env.REACT_APP_GEMINI_API_KEY;

    if (!apiKey) {
      const error = 'REACT_APP_GEMINI_API_KEY not set in .env file';
      console.error('[VirtualRobotControl]', error);
      setConnectionError(error);
      return;
    }

    console.log('[VirtualRobotControl] API key found, creating client');
    const client = new GenAILiveClient({ apiKey });
    clientRef.current = client;

    // Setup event listeners with detailed logging
    client.on('open', () => {
      console.log('[Gemini] ✅ WebSocket connection opened');
      setConnected(true);
      setConnecting(false);
      setConnectionError(null);
    });

    client.on('setupcomplete', () => {
      console.log('[Gemini] ✅ Setup complete - ready to receive audio/text');
    });

    client.on('close', (event) => {
      console.log('[Gemini] ❌ Connection closed:', {
        code: event.code,
        reason: event.reason || 'No reason provided',
        wasClean: event.wasClean
      });
      setConnected(false);
      setConnecting(false);
      if (!event.wasClean) {
        setConnectionError(`Connection closed unexpectedly: ${event.reason || 'Unknown error'}`);
      }
    });

    client.on('error', (error) => {
      console.error('[Gemini] ❌ Error:', error);
      setConnectionError(error.message || 'Unknown error');
      setConnecting(false);
    });

    client.on('content', (content) => {
      console.log('[Gemini] 📥 Content received:', content);
      if ('modelTurn' in content && content.modelTurn && content.modelTurn.parts) {
        content.modelTurn.parts.forEach((part) => {
          if ('text' in part && part.text) {
            console.log('[Gemini] 💬 Text response:', part.text);
            setTranscript(prev => [...prev, `Gemini: ${part.text}`]);
          }
        });
      }
    });

    client.on('interrupted', () => {
      console.log('[Gemini] ⚠️ Response interrupted');
    });

    client.on('turncomplete', () => {
      console.log('[Gemini] ✅ Turn complete');
    });

    client.on('toolcall', async (toolCall) => {
      console.log('[Gemini] 🔧 Tool call received:', toolCall);
      const responses: any[] = [];

      for (const call of toolCall.functionCalls || []) {
        console.log(`[Gemini] Executing tool: ${call.name}`, call.args);
        setTaskStatus(`Executing: ${call.name || 'unknown'}`);
        const result = await handleToolCall(call.name || '', call.args);
        console.log(`[Gemini] Tool result for ${call.name}:`, result);

        responses.push({
          name: call.name,
          id: call.id,
          response: result,
        });
      }

      // Send responses back to Gemini
      if (responses.length > 0) {
        console.log('[Gemini] 📤 Sending tool responses:', responses);
        client.sendToolResponse({ functionResponses: responses });
      }

      setTaskStatus('Ready');
    });

    console.log('[VirtualRobotControl] Event listeners configured');

    return () => {
      console.log('[VirtualRobotControl] Cleanup: disconnecting client');
      if (client.status === 'connected') {
        client.disconnect();
      }
    };
  }, []);

  // Handle tool calls from Gemini (matching real robot API)
  const handleToolCall = async (name: string, args: any): Promise<any> => {
    try {
      console.log(`[VirtualRobotControl] Executing tool: ${name}`, args);

      switch (name) {
        case 'move_arm': {
          // Use unified moveArm function that matches real robot API
          const result = robotController.moveArm({
            pose: args.pose,
            joints: args.joints,
            position: args.position,
            unit: args.unit,
            moving_time: args.moving_time,
          });

          if (result.success) {
            const method = args.pose ? `pose: ${args.pose}` :
                         args.joints ? `joints` :
                         `position: ${JSON.stringify(args.position)}`;
            return { success: true, message: `Moving arm (${method})` };
          }
          return { success: false, error: result.error };
        }

        case 'control_gripper': {
          if (args.action === 'open') {
            robotController.openGripper();
            return { success: true, state: 'opening', message: 'Opening gripper' };
          } else if (args.action === 'close') {
            robotController.closeGripper();
            return { success: true, state: 'closing', message: 'Closing gripper' };
          }
          return { success: false, error: 'Invalid gripper action (must be "open" or "close")' };
        }

        case 'get_arm_status':
          return robotController.getArmStatus();

        case 'get_gripper_status':
          return robotController.getGripperStatus();

        case 'move_arm_trajectory': {
          if (args.trajectory && Array.isArray(args.trajectory)) {
            const success = await robotController.executeTrajectory(
              args.trajectory,
              args.speed || 'medium'
            );
            return {
              success,
              message: `Trajectory with ${args.trajectory.length} waypoints ${success ? 'completed' : 'failed'}`
            };
          }
          return { success: false, error: 'Invalid trajectory (must be array of waypoints)' };
        }

        default:
          return { success: false, error: `Unknown tool: ${name}` };
      }
    } catch (error) {
      console.error(`[VirtualRobotControl] Error executing ${name}:`, error);
      return { success: false, error: String(error) };
    }
  };

  // Toggle connection to Gemini
  const toggleConnection = async () => {
    if (!clientRef.current) {
      console.error('[VirtualRobotControl] No client available');
      return;
    }

    // If already connected, disconnect
    if (connected) {
      console.log('[VirtualRobotControl] User requested disconnect');
      clientRef.current.disconnect();
      setConnected(false);
      setConnecting(false);
      return;
    }

    // If connecting, ignore (prevent double-click issues)
    if (connecting) {
      console.log('[VirtualRobotControl] Already connecting, please wait...');
      return;
    }

    // Attempt to connect
    console.log('[VirtualRobotControl] Attempting to connect to Gemini Live API...');
    setConnecting(true);
    setConnectionError(null);

    try {
      const success = await clientRef.current.connect('models/gemini-live-2.5-flash-preview', {
        tools: [{
          functionDeclarations: [
            toolMoveArmTrajectory,
            toolControlGripper,
            toolGetGripperStatus,
            toolMoveArm,
            toolGetArmStatus,
          ]
        }],
        systemInstruction: SYSTEM_INSTRUCTION,
      });

      if (success) {
        console.log('[VirtualRobotControl] ✅ Connection initiated successfully');
        // Note: setConnected(true) will be called by the 'open' event listener
      } else {
        console.error('[VirtualRobotControl] ❌ Failed to initiate connection');
        setConnecting(false);
        setConnectionError('Failed to initiate connection');
      }
    } catch (error: any) {
      console.error('[VirtualRobotControl] ❌ Connection error:', error);
      setConnecting(false);
      setConnectionError(error.message || 'Connection failed');
    }
  };

  // Start/stop voice recording
  const toggleRecording = async () => {
    if (isRecording) {
      if (audioRecorderRef.current) {
        audioRecorderRef.current.stop();
        audioRecorderRef.current = null;
      }
      setIsRecording(false);
    } else {
      const recorder = new AudioRecorder(16000);

      // Set up event listener for audio data
      recorder.on('data', (base64Data: string) => {
        // Send audio to Gemini
        clientRef.current?.sendRealtimeInput([{
          mimeType: 'audio/pcm;rate=16000',
          data: base64Data,
        }]);
      });

      audioRecorderRef.current = recorder;
      await recorder.start();
      setIsRecording(true);
    }
  };

  // Send text command
  const sendTextCommand = (text: string) => {
    if (!connected) return;
    setTranscript(prev => [...prev, `You: ${text}`]);
    clientRef.current?.send([{ text }]);
  };

  // Handle text input submission
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      sendTextCommand(textInput.trim());
      setTextInput('');
    }
  };

  return (
    <div style={{
      position: 'absolute',
      top: 20,
      right: 20,
      background: 'rgba(0, 0, 0, 0.8)',
      color: 'white',
      padding: 20,
      borderRadius: 8,
      maxWidth: 350,
      maxHeight: 'calc(100vh - 40px)',
      overflow: 'auto',
    }}>
      <h2 style={{ margin: '0 0 16px 0' }}>Virtual Robot Control</h2>

      {/* Connection status */}
      <div style={{ marginBottom: 16 }}>
        <div><strong>Status:</strong> {
          connected ? '✅ Connected' :
          connecting ? '🔄 Connecting...' :
          '❌ Disconnected'
        }</div>
        <div><strong>Task:</strong> {taskStatus}</div>

        {/* Connection error display */}
        {connectionError && (
          <div style={{
            marginTop: 8,
            padding: 8,
            background: '#ff5252',
            borderRadius: 4,
            fontSize: 12,
          }}>
            ⚠️ {connectionError}
          </div>
        )}

        {/* Connect/Disconnect button */}
        <button
          onClick={toggleConnection}
          disabled={connecting}
          style={{
            marginTop: 8,
            padding: '8px 16px',
            background: connected ? '#ff5252' : connecting ? '#666' : '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: 4,
            cursor: connecting ? 'not-allowed' : 'pointer',
            width: '100%',
            opacity: connecting ? 0.7 : 1,
          }}
        >
          {connecting ? 'Connecting...' : connected ? 'Disconnect' : 'Connect to Gemini'}
        </button>
      </div>

      {/* Voice control */}
      {connected && (
        <div style={{ marginBottom: 16 }}>
          <button
            onClick={toggleRecording}
            style={{
              padding: '12px 24px',
              background: isRecording ? '#f44336' : '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: 4,
              cursor: 'pointer',
              width: '100%',
              fontSize: 16,
            }}
          >
            {isRecording ? '🎤 Stop Recording' : '🎤 Start Voice Control'}
          </button>
        </div>
      )}

      {/* Text input */}
      {connected && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px 0' }}>Text Command</h4>
          <form onSubmit={handleTextSubmit} style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type a command..."
              style={{
                flex: 1,
                padding: '8px 12px',
                border: '1px solid #555',
                borderRadius: 4,
                background: 'rgba(255, 255, 255, 0.1)',
                color: 'white',
                fontSize: 14,
              }}
            />
            <button
              type="submit"
              disabled={!textInput.trim()}
              style={{
                padding: '8px 16px',
                background: textInput.trim() ? '#4CAF50' : '#666',
                color: 'white',
                border: 'none',
                borderRadius: 4,
                cursor: textInput.trim() ? 'pointer' : 'not-allowed',
                fontSize: 14,
              }}
            >
              Send
            </button>
          </form>
        </div>
      )}

      {/* Quick commands */}
      {connected && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ margin: '0 0 8px 0' }}>Quick Commands</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <button onClick={() => sendTextCommand('Move to home position')}>🏠 Home</button>
            <button onClick={() => sendTextCommand('Move to ready position')}>✅ Ready</button>
            <button onClick={() => sendTextCommand('Open the gripper')}>🤚 Open Gripper</button>
            <button onClick={() => sendTextCommand('Close the gripper')}>✊ Close Gripper</button>
            <button onClick={() => sendTextCommand('Pick up the green apple')}>🍏 Pick Apple</button>
            <button onClick={() => sendTextCommand('Pick up the blue cube')}>🔵 Pick Cube</button>
          </div>
        </div>
      )}

      {/* Transcript */}
      <div style={{ marginTop: 16 }}>
        <h4 style={{ margin: '0 0 8px 0' }}>Conversation</h4>
        <div style={{
          maxHeight: 200,
          overflow: 'auto',
          fontSize: 12,
          background: 'rgba(255, 255, 255, 0.1)',
          padding: 8,
          borderRadius: 4,
        }}>
          {transcript.map((line, i) => (
            <div key={i} style={{ marginBottom: 4 }}>{line}</div>
          ))}
          {transcript.length === 0 && (
            <div style={{ opacity: 0.5 }}>No messages yet...</div>
          )}
        </div>
      </div>

      {/* Instructions */}
      <div style={{ marginTop: 16, fontSize: 12, opacity: 0.7 }}>
        <strong>Try saying:</strong>
        <div>• "Move to home position"</div>
        <div>• "Pick up the green apple"</div>
        <div>• "Move to x=0.3, y=0, z=0.2"</div>
      </div>
    </div>
  );
}
