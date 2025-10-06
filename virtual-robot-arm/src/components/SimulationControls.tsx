/**
 * Simulation Controls Component
 *
 * Provides UI controls for the MuJoCo simulation server.
 * Allows users to control both arms and grippers via WebSocket.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { SimulationClient, ArmSide, ArmStatus } from '../lib/SimulationClient';

const HOME_POSITIONS = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0];
const READY_POSITIONS = [0.0, -0.5, 0.8, 0.0, -0.5, 0.0];

export const SimulationControls: React.FC = () => {
  const [client] = useState(() => new SimulationClient('http://localhost:5000'));
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [leftArmStatus, setLeftArmStatus] = useState<ArmStatus | null>(null);
  const [rightArmStatus, setRightArmStatus] = useState<ArmStatus | null>(null);
  const [log, setLog] = useState<string[]>([]);

  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLog(prev => [`[${timestamp}] ${message}`, ...prev.slice(0, 9)]);
  }, []);

  useEffect(() => {
    // Set up event handlers
    client.onConnect(() => {
      setConnected(true);
      setConnecting(false);
      addLog('✓ Connected to simulation server');
    });

    client.onDisconnect(() => {
      setConnected(false);
      addLog('✗ Disconnected from server');
    });

    client.onArmStatus((arm: ArmSide, status: ArmStatus) => {
      if (arm === 'left') {
        setLeftArmStatus(status);
      } else {
        setRightArmStatus(status);
      }
    });

    client.onCommandResult((result) => {
      if (result.success) {
        addLog(`✓ Command succeeded: ${result.command || 'unknown'}`);
      } else {
        addLog(`✗ Command failed: ${result.error}`);
      }
    });

    client.onError((error) => {
      addLog(`✗ Error: ${error}`);
    });

    // Cleanup on unmount
    return () => {
      if (connected) {
        client.disconnect();
      }
    };
  }, [client, addLog, connected]);

  const handleConnect = async () => {
    setConnecting(true);
    addLog('Connecting to server...');
    try {
      await client.connect();
    } catch (error) {
      addLog(`Failed to connect: ${error}`);
      setConnecting(false);
    }
  };

  const handleDisconnect = () => {
    client.disconnect();
    addLog('Disconnected');
  };

  const handleMoveArm = (arm: ArmSide, positions: number[]) => {
    try {
      client.moveArm(arm, positions);
      addLog(`Moving ${arm} arm`);
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  const handleGripper = (arm: ArmSide, command: 'open' | 'close') => {
    try {
      client.controlGripper(arm, command);
      addLog(`${command === 'open' ? 'Opening' : 'Closing'} ${arm} gripper`);
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  const handleReset = () => {
    try {
      client.resetRobot();
      addLog('Resetting robot to home position');
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  const handleGetStatus = () => {
    try {
      client.getArmStatus('left');
      client.getArmStatus('right');
      addLog('Querying arm status...');
    } catch (error) {
      addLog(`Error: ${error}`);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>MuJoCo Simulation Controls</h2>
        <div style={styles.connectionStatus}>
          {connected ? (
            <span style={{ ...styles.statusBadge, ...styles.statusConnected }}>● Connected</span>
          ) : (
            <span style={{ ...styles.statusBadge, ...styles.statusDisconnected }}>○ Disconnected</span>
          )}
        </div>
      </div>

      {/* Connection Controls */}
      <div style={styles.section}>
        {!connected ? (
          <button
            onClick={handleConnect}
            disabled={connecting}
            style={{ ...styles.button, ...styles.buttonPrimary }}
          >
            {connecting ? 'Connecting...' : 'Connect to Server'}
          </button>
        ) : (
          <button
            onClick={handleDisconnect}
            style={{ ...styles.button, ...styles.buttonDanger }}
          >
            Disconnect
          </button>
        )}
      </div>

      {connected && (
        <>
          {/* General Controls */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>General</h3>
            <div style={styles.buttonGroup}>
              <button onClick={handleReset} style={styles.button}>
                Reset to Home
              </button>
              <button onClick={handleGetStatus} style={styles.button}>
                Get Status
              </button>
            </div>
          </div>

          {/* Left Arm Controls */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Left Arm</h3>
            <div style={styles.buttonGroup}>
              <button
                onClick={() => handleMoveArm('left', HOME_POSITIONS)}
                style={styles.button}
              >
                Move to Home
              </button>
              <button
                onClick={() => handleMoveArm('left', READY_POSITIONS)}
                style={styles.button}
              >
                Move to Ready
              </button>
            </div>
            <div style={styles.buttonGroup}>
              <button
                onClick={() => handleGripper('left', 'open')}
                style={styles.button}
              >
                Open Gripper
              </button>
              <button
                onClick={() => handleGripper('left', 'close')}
                style={styles.button}
              >
                Close Gripper
              </button>
            </div>
            {leftArmStatus && (
              <div style={styles.status}>
                <small>
                  Positions: [{leftArmStatus.positions.map(p => p.toFixed(2)).join(', ')}]
                </small>
              </div>
            )}
          </div>

          {/* Right Arm Controls */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Right Arm</h3>
            <div style={styles.buttonGroup}>
              <button
                onClick={() => handleMoveArm('right', HOME_POSITIONS)}
                style={styles.button}
              >
                Move to Home
              </button>
              <button
                onClick={() => handleMoveArm('right', READY_POSITIONS)}
                style={styles.button}
              >
                Move to Ready
              </button>
            </div>
            <div style={styles.buttonGroup}>
              <button
                onClick={() => handleGripper('right', 'open')}
                style={styles.button}
              >
                Open Gripper
              </button>
              <button
                onClick={() => handleGripper('right', 'close')}
                style={styles.button}
              >
                Close Gripper
              </button>
            </div>
            {rightArmStatus && (
              <div style={styles.status}>
                <small>
                  Positions: [{rightArmStatus.positions.map(p => p.toFixed(2)).join(', ')}]
                </small>
              </div>
            )}
          </div>

          {/* Activity Log */}
          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Activity Log</h3>
            <div style={styles.log}>
              {log.map((entry, index) => (
                <div key={index} style={styles.logEntry}>
                  {entry}
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    position: 'fixed',
    top: '20px',
    right: '20px',
    width: '350px',
    maxHeight: '90vh',
    overflowY: 'auto',
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    color: 'white',
    padding: '20px',
    borderRadius: '10px',
    fontFamily: 'monospace',
    zIndex: 1000,
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.5)',
  },
  header: {
    marginBottom: '20px',
    borderBottom: '2px solid #333',
    paddingBottom: '10px',
  },
  title: {
    margin: '0 0 10px 0',
    fontSize: '18px',
    fontWeight: 'bold',
  },
  connectionStatus: {
    display: 'flex',
    justifyContent: 'flex-start',
  },
  statusBadge: {
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 'bold',
  },
  statusConnected: {
    backgroundColor: '#22c55e',
    color: 'white',
  },
  statusDisconnected: {
    backgroundColor: '#64748b',
    color: 'white',
  },
  section: {
    marginBottom: '20px',
  },
  sectionTitle: {
    margin: '0 0 10px 0',
    fontSize: '14px',
    color: '#60a5fa',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
  },
  buttonGroup: {
    display: 'flex',
    gap: '8px',
    marginBottom: '8px',
    flexWrap: 'wrap',
  },
  button: {
    flex: '1',
    padding: '8px 12px',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 'bold',
    transition: 'all 0.2s',
  },
  buttonPrimary: {
    backgroundColor: '#22c55e',
  },
  buttonDanger: {
    backgroundColor: '#ef4444',
  },
  status: {
    padding: '8px',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: '4px',
    marginTop: '8px',
  },
  log: {
    maxHeight: '200px',
    overflowY: 'auto',
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '11px',
  },
  logEntry: {
    marginBottom: '4px',
    fontFamily: 'monospace',
  },
};
