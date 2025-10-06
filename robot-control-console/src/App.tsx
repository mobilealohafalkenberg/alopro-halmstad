import { useState } from 'react';
import { LiveAPIProvider } from './contexts/LiveAPIContext';
import { ModeSelector, RobotMode } from './components/mode-selector/ModeSelector';
import { RobotControl } from './components/robot-control/RobotControl';
import { RobotVisualization } from './components/visualization/RobotVisualization';
import './App.css';

const API_KEY = process.env.REACT_APP_GEMINI_API_KEY as string;
if (!API_KEY) {
  throw new Error('Set REACT_APP_GEMINI_API_KEY in .env');
}

function App() {
  const [mode, setMode] = useState<RobotMode>('simulation');
  const [jointPositions, setJointPositions] = useState<number[]>([0, 0, 0, 0, 0, 0]);
  const [gripperState, setGripperState] = useState<'open' | 'close'>('close');

  return (
    <div className="App">
      <LiveAPIProvider options={{ apiKey: API_KEY }}>
        <div className="app-header">
          <h1>🤖 ALOHA Robot Control Console</h1>
          <ModeSelector mode={mode} onModeChange={setMode} />
        </div>

        <RobotControl
          mode={mode}
          onJointUpdate={setJointPositions}
          onGripperUpdate={setGripperState}
        />

        <RobotVisualization
          mode={mode}
          jointPositions={jointPositions}
          gripperState={gripperState}
        />

        <div className="instructions">
          <h3>🎤 Voice Commands</h3>
          <p>Click the microphone button in the control panel and try:</p>
          <ul>
            <li>"Open the gripper"</li>
            <li>"Move to home position"</li>
            <li>"Close the gripper"</li>
            <li>"Move the arm to ready position"</li>
          </ul>
        </div>
      </LiveAPIProvider>
    </div>
  );
}

export default App;
