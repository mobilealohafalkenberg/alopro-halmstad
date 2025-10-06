import { useState } from 'react';
import './ModeSelector.scss';

export type RobotMode = 'simulation' | 'real';

interface ModeSelectorProps {
  mode: RobotMode;
  onModeChange: (mode: RobotMode) => void;
  disabled?: boolean;
}

export function ModeSelector({ mode, onModeChange, disabled }: ModeSelectorProps) {
  return (
    <div className="mode-selector">
      <label>Robot Mode:</label>
      <div className="mode-buttons">
        <button
          className={mode === 'simulation' ? 'active' : ''}
          onClick={() => onModeChange('simulation')}
          disabled={disabled}
        >
          🖥️ Virtual Robot
        </button>
        <button
          className={mode === 'real' ? 'active' : ''}
          onClick={() => onModeChange('real')}
          disabled={disabled}
        >
          🤖 Real Robot
        </button>
      </div>
      <div className="mode-info">
        {mode === 'simulation' ? (
          <span className="info">Connected to simulation (port 8082)</span>
        ) : (
          <span className="info">Connected to real robot (port 8081)</span>
        )}
      </div>
    </div>
  );
}
