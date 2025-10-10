/**
 * Virtual Camera Feed Display
 * Shows camera views from the virtual robot's cameras
 */

import { useState } from 'react';
import { CameraViewData } from './VirtualCameraSystem';

interface VirtualCameraFeedProps {
  cameraViews: CameraViewData[];
}

export function VirtualCameraFeed({ cameraViews }: VirtualCameraFeedProps) {
  const [expanded, setExpanded] = useState(true);

  const getCameraTitle = (name: string): string => {
    switch (name) {
      case 'gripper_cam':
        return 'Gripper Camera';
      case 'top_cam':
        return 'Top Camera';
      default:
        return name;
    }
  };

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 20,
        left: 20,
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: 16,
        borderRadius: 8,
        maxWidth: 700,
        zIndex: 100,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 12,
          cursor: 'pointer',
        }}
        onClick={() => setExpanded(!expanded)}
      >
        <h3 style={{ margin: 0, fontSize: 14 }}>
          🎥 Virtual Camera Feeds
        </h3>
        <button
          style={{
            background: 'none',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            fontSize: 16,
          }}
        >
          {expanded ? '▼' : '▲'}
        </button>
      </div>

      {expanded && (
        <div
          style={{
            display: 'flex',
            gap: 12,
            flexWrap: 'wrap',
          }}
        >
          {cameraViews.map((view) => (
            <div
              key={view.name}
              style={{
                display: 'inline-block',
                background: '#1f2937',
                borderRadius: 8,
                padding: 8,
              }}
            >
              <h4 style={{ margin: '0 0 8px 0', fontSize: 12, color: '#9ca3af' }}>
                {getCameraTitle(view.name)}
              </h4>

              {view.imageData ? (
                <img
                  src={`data:image/jpeg;base64,${view.imageData}`}
                  alt={view.name}
                  style={{
                    width: 320,
                    height: 240,
                    borderRadius: 4,
                    display: 'block',
                    objectFit: 'cover',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: 320,
                    height: 240,
                    background: '#374151',
                    borderRadius: 4,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#9ca3af',
                    fontSize: 12,
                  }}
                >
                  Initializing camera...
                </div>
              )}

              <div
                style={{
                  marginTop: 4,
                  fontSize: 10,
                  color: '#6b7280',
                  textAlign: 'center',
                }}
              >
                {view.name} • {new Date(view.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ))}

          {cameraViews.length === 0 && (
            <div
              style={{
                padding: 20,
                color: '#9ca3af',
                fontSize: 12,
                textAlign: 'center',
              }}
            >
              No camera feeds available
            </div>
          )}
        </div>
      )}

      <div
        style={{
          marginTop: 8,
          fontSize: 10,
          color: '#6b7280',
          textAlign: 'center',
        }}
      >
        Virtual cameras render at 1 FPS • 640x480 resolution
      </div>
    </div>
  );
}
