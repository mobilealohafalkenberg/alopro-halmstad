import React, { useEffect, useState } from 'react';

// Replace with your app's Live API context/hooks
// import { useLiveAPIContext } from '../path/to/LiveAPIContext';

// Tool declarations
const ROBOT_TOOLS = [
  {
    name: 'detect_objects',
    description: 'Identify items from the current scene',
    parameters: { type: 'object', properties: {}, required: [] },
  },
  {
    name: 'move_to_position',
    description: 'Move an arm to XYZ (meters in robot base frame)',
    parameters: {
      type: 'object',
      properties: {
        arm: { type: 'string', enum: ['left', 'right'] },
        x: { type: 'number' },
        y: { type: 'number' },
        z: { type: 'number' },
      },
      required: ['arm', 'x', 'y', 'z'],
    },
  },
  {
    name: 'control_gripper',
    description: 'Open or close gripper',
    parameters: {
      type: 'object',
      properties: {
        arm: { type: 'string', enum: ['left', 'right'] },
        action: { type: 'string', enum: ['open', 'close'] },
      },
      required: ['arm', 'action'],
    },
  },
  {
    name: 'get_robot_status',
    description: 'Get EE pose and gripper states',
    parameters: { type: 'object', properties: {}, required: [] },
  },
];

const SYSTEM_INSTRUCTION = `
You control a Mobile ALOHA robot. Use tools responsibly.
Coordinate frame: X forward, Y left, Z up (meters). 
Stay within X[0.15,0.55], Y[-0.35,0.35], Z[0.05,0.45].
`;

export function ALOHAControl({ client, setConfig, connected, robotEndpoint }: any) {
  const [status, setStatus] = useState('Ready');
  const [robotState, setRobotState] = useState<any>(null);

  // Configure tools and system instruction before connecting
  useEffect(() => {
    if (!setConfig) return;
    setConfig({
      tools: [{ functionDeclarations: ROBOT_TOOLS }],
      systemInstruction: SYSTEM_INSTRUCTION,
    });
  }, [setConfig]);

  // Handle tool calls from Gemini
  useEffect(() => {
    if (!client) return;
    const handle = async (toolCall: any) => {
      const responses: any[] = [];
      for (const call of toolCall.functionCalls) {
        setStatus(`Executing: ${call.name}`);
        try {
          const res = await fetch(`${robotEndpoint}/aloha-tool-call`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: call.name, args: call.args, id: call.id }),
          });
          const data = await res.json();
          if (call.name === 'get_robot_status') setRobotState(data.result);
          responses.push({ name: call.name, id: call.id, response: data.result ?? data });
        } catch (e: any) {
          responses.push({ name: call.name, id: call.id, response: { error: e?.message || 'error' } });
        }
      }
      if (responses.length) client.sendToolResponse({ functionResponses: responses });
      setStatus('Ready');
    };
    client.on('toolcall', handle);
    return () => client.off('toolcall', handle);
  }, [client, robotEndpoint]);

  const sendPrompt = (text: string) => connected && client?.send?.({ text });

  return (
    <div>
      <h3>ALOHA Robot Control</h3>
      <div><strong>Status:</strong> {status}</div>
      <div><strong>Connected:</strong> {connected ? '✅' : '❌'}</div>
      {robotState && <pre>{JSON.stringify(robotState, null, 2)}</pre>}
      <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
        <button onClick={() => sendPrompt('Show me the robot status')}>Get Status</button>
        <button onClick={() => sendPrompt('Move the right arm to x 0.30, y 0.10, z 0.20 meters')}>Move Right Arm</button>
        <button onClick={() => sendPrompt('Open the left gripper')}>Open Left Gripper</button>
        <button onClick={() => sendPrompt('Pick up the red cup with the right arm and place it in the blue bowl')}>Pick & Place</button>
      </div>
    </div>
  );
}

// Example camera pipeline (robot MJPEG -> canvas -> session track)
// 
// <img id="rosImg" src={`http://ROBOT_PC_IP:8080/stream?topic=/image_raw`} />
// <canvas id="rosCanvas" width={640} height={480} />
// setInterval(() => {
//   const img = document.getElementById('rosImg') as HTMLImageElement;
//   const canvas = document.getElementById('rosCanvas') as HTMLCanvasElement;
//   const ctx = canvas.getContext('2d');
//   if (img && ctx) ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
// }, 66); // ~15 fps
// const stream = (document.getElementById('rosCanvas') as HTMLCanvasElement).captureStream(15);
// const [track] = stream.getVideoTracks();
// client.attachVideoTrack(track);
