import { useEffect, useState } from 'react';
import { useLiveAPIContext } from '../../contexts/LiveAPIContext';
import { RobotMode } from '../mode-selector/ModeSelector';
import { ROBOT_TOOLS } from './tools';
import './RobotControl.scss';

interface RobotControlProps {
  mode: RobotMode;
  onJointUpdate?: (positions: number[]) => void;
  onGripperUpdate?: (state: 'open' | 'close') => void;
}

export function RobotControl({ mode, onJointUpdate, onGripperUpdate }: RobotControlProps) {
  const { client, connected } = useLiveAPIContext();
  const [taskStatus, setTaskStatus] = useState('Ready');

  const ROBOT_ENDPOINT = mode === 'simulation'
    ? 'http://localhost:8082'
    : 'http://localhost:8081';

  useEffect(() => {
    if (!connected) return;

    const config = {
      model: 'models/gemini-2.0-flash-exp',
      systemInstruction: {
        parts: [{
          text: `You are controlling an ALOHA robot. Current mode: ${mode}.
Available commands: open/close gripper, move arm to positions (home, ready, sleep), get status, reset robot.
Respond naturally and confirm actions. Be concise.`
        }]
      },
      tools: [{ functionDeclarations: ROBOT_TOOLS }],
      generationConfig: {
        responseModalities: 'audio',
        speechConfig: {
          voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Puck' }}
        }
      }
    };

    client.connect(config);
  }, [connected, mode, client]);

  useEffect(() => {
    const handleToolCall = async (toolCall: any) => {
      const calls = toolCall.toolCall?.functionCalls || [];
      const responses: any[] = [];

      setTaskStatus('Executing...');

      for (const call of calls) {
        console.log(`[${mode}] Tool call:`, call.name, call.args);

        try {
          const response = await fetch(`${ROBOT_ENDPOINT}/aloha-tool-call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: call.name, args: call.args })
          });

          const result = await response.json();
          console.log(`[${mode}] Result:`, result);

          if (mode === 'simulation') {
            if (result.joint_positions && onJointUpdate) {
              onJointUpdate(result.joint_positions);
            }
            if (result.state && onGripperUpdate) {
              onGripperUpdate(result.state);
            }
          }

          responses.push({
            functionResponses: [{
              response: { name: call.name, content: result },
              id: call.id
            }]
          });

        } catch (error) {
          console.error(`[${mode}] Tool call error:`, error);
          responses.push({
            functionResponses: [{
              response: {
                name: call.name,
                content: { success: false, error: String(error) }
              },
              id: call.id
            }]
          });
        }
      }

      if (responses.length > 0) {
        client.sendToolResponse(responses);
      }
      setTaskStatus('Ready');
    };

    client.on('toolcall' as any, handleToolCall);
    return () => {
      client.off('toolcall' as any, handleToolCall);
    };
  }, [client, mode, ROBOT_ENDPOINT, onJointUpdate, onGripperUpdate]);

  return (
    <div className="robot-control">
      <div className="status-bar">
        <span className="mode-badge">{mode === 'simulation' ? '🖥️ Virtual' : '🤖 Real'}</span>
        <span className="task-status">{taskStatus}</span>
        <span className="endpoint">{ROBOT_ENDPOINT}</span>
      </div>
    </div>
  );
}
