import { useEffect, useState } from 'react';
import './CameraFeedView.scss';

interface CameraFeedViewProps {
  endpoint: string;
}

export function CameraFeedView({ endpoint }: CameraFeedViewProps) {
  const [cameraFrame, setCameraFrame] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${endpoint}/camera/merged`);
        if (!response.ok) throw new Error('Camera feed unavailable');

        const data = await response.json();
        if (data.frame) {
          setCameraFrame(`data:image/jpeg;base64,${data.frame}`);
          setError(null);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Camera error');
        console.error('Camera feed error:', err);
      }
    }, 1000); // 1 FPS

    return () => clearInterval(interval);
  }, [endpoint]);

  return (
    <div className="camera-feed-view">
      <h3>🎥 Robot Camera Feeds</h3>
      {error && <div className="error-message">⚠️ {error}</div>}
      {cameraFrame ? (
        <img src={cameraFrame} alt="Robot camera" className="camera-frame" />
      ) : (
        <div className="no-feed">
          <div className="loading-spinner"></div>
          <p>Waiting for camera feed...</p>
        </div>
      )}
    </div>
  );
}
