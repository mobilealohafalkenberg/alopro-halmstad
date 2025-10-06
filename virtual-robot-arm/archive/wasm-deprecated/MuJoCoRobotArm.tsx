import { useRef, useEffect, useState } from 'react';
import { MuJoCoModel } from '@vuer-ai/mujoco-ts';

interface MuJoCoRobotArmProps {
  onReady?: () => void;
  onError?: (error: Error) => void;
}

/**
 * MuJoCo WASM-based robot arm simulation
 * Loads the official ALOHA model from Google DeepMind's mujoco_menagerie
 */
export function MuJoCoRobotArm({ onReady, onError }: MuJoCoRobotArmProps) {
  const modelRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // List all assets needed by the ALOHA model
  const alohaAssets = [
    'models/aloha/aloha.xml',
    // VX300s robot meshes
    'models/aloha/assets/vx300s_1_base.stl',
    'models/aloha/assets/vx300s_2_shoulder.stl',
    'models/aloha/assets/vx300s_3_upper_arm.stl',
    'models/aloha/assets/vx300s_4_upper_forearm.stl',
    'models/aloha/assets/vx300s_5_lower_forearm.stl',
    'models/aloha/assets/vx300s_6_wrist.stl',
    'models/aloha/assets/vx300s_7_gripper.stl',
    'models/aloha/assets/vx300s_7_gripper_bar.stl',
    'models/aloha/assets/vx300s_7_gripper_camera.stl',
    'models/aloha/assets/vx300s_7_gripper_prop.stl',
    'models/aloha/assets/vx300s_7_gripper_prop_bar.stl',
    'models/aloha/assets/vx300s_7_gripper_wrist_mount.stl',
    'models/aloha/assets/vx300s_8_custom_finger_left.stl',
    'models/aloha/assets/vx300s_8_custom_finger_right.stl',
    // Camera meshes
    'models/aloha/assets/d405_solid.stl',
    // Table and frame meshes
    'models/aloha/assets/tablelegs.obj',
    'models/aloha/assets/tabletop.obj',
    'models/aloha/assets/extrusion_2040_880.stl',
    'models/aloha/assets/extrusion_2040_1000.stl',
    'models/aloha/assets/extrusion_1220.stl',
    'models/aloha/assets/extrusion_1000.stl',
    'models/aloha/assets/extrusion_600.stl',
    'models/aloha/assets/extrusion_150.stl',
    'models/aloha/assets/corner_bracket.stl',
    'models/aloha/assets/angled_extrusion.stl',
    'models/aloha/assets/overhead_mount.stl',
    'models/aloha/assets/wormseye_mount.stl',
    // Textures
    'models/aloha/assets/small_meta_table_diffuse.png',
    'models/aloha/assets/interbotix_black.png',
  ];

  useEffect(() => {
    const handleLoad = () => {
      console.log('[MuJoCoRobotArm] Model loaded successfully');
      setIsLoading(false);
      if (onReady) onReady();
    };

    const handleError = (err: Error) => {
      console.error('[MuJoCoRobotArm] Error loading model:', err);
      setError(err.message);
      setIsLoading(false);
      if (onError) onError(err);
    };

    // Set up event listeners if model ref is available
    if (modelRef.current) {
      modelRef.current.addEventListener('load', handleLoad);
      modelRef.current.addEventListener('error', handleError);

      return () => {
        if (modelRef.current) {
          modelRef.current.removeEventListener('load', handleLoad);
          modelRef.current.removeEventListener('error', handleError);
        }
      };
    }
  }, [onReady, onError]);

  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative' }}>
      {isLoading && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0, 0, 0, 0.8)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px',
            zIndex: 1000,
          }}
        >
          Loading ALOHA Model...
        </div>
      )}

      {error && (
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(220, 53, 69, 0.9)',
            color: 'white',
            padding: '20px',
            borderRadius: '8px',
            zIndex: 1000,
            maxWidth: '500px',
          }}
        >
          <h3>Error Loading Model</h3>
          <p>{error}</p>
        </div>
      )}

      <MuJoCoModel
        ref={modelRef}
        {...{
          src: 'models/aloha/scene.xml',
          assets: alohaAssets,
          speed: 1.0,
        } as any}
      />
    </div>
  );
}
