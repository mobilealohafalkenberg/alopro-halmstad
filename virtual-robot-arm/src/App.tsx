/**
 * Virtual Robot Arm Application
 *
 * Integrated voice control + 3D visualization + MuJoCo simulation.
 * - Voice control via Gemini Live API
 * - 3D robot arm visualization with Three.js
 * - Simulation bridge on port 8082
 * - MuJoCo physics server on port 5000
 */

import { IntegratedRobotControl } from './components/IntegratedRobotControl';
import './App.css';

function App() {
  return (
    <div className="App">
      <IntegratedRobotControl />
    </div>
  );
}

export default App;
