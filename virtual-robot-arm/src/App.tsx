/**
 * Virtual Robot Arm Application
 *
 * Server-side MuJoCo simulation with React control interface.
 * The MuJoCo physics server runs on localhost:5000 (Python/Flask-SocketIO).
 * This React app provides a web UI to control the dual-arm ALOHA robot.
 */

import { SimulationControls } from './components/SimulationControls';
import './App.css';

function App() {
  return (
    <div className="App">
      <SimulationControls />
    </div>
  );
}

export default App;
