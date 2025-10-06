import { useEffect, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment } from '@react-three/drei';
import { RobotState } from '../types/robot';
  import { loadMuJoCo } from '../lib/mujoco-loader';

interface MuJoCoSceneProps{
  robotState: RobotState;
  onMuJoCoReady?: (mujoco: any, simulation: any) => void;
}

export function MuJoCoScene({ robotState, onMuJoCoReady }: MuJoCoSceneProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mujocoRef = useRef<any>(null);
  const simulationRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    let cleanupModel: any = null;
    let cleanupState: any = null;
    let cleanupSimulation: any = null;

    const initMuJoCo = async () => {
      try {
        console.log('%c[MuJoCo Init] Step 1: Loading WASM module...', 'color: #00ff00; font-weight: bold');

        // Load MuJoCo using our custom loader (no double-await - loader handles initialization)
        const mujoco = await loadMuJoCo();
        mujocoRef.current = mujoco;

        // Log API verification (helpful for debugging)
        console.log('%c[MuJoCo Init] ✓ Module loaded successfully', 'color: #00ff00');
        console.log('[MuJoCo Init] API Check:', {
          hasModel: typeof mujoco.Model === 'function',
          hasState: typeof mujoco.State === 'function',
          hasSimulation: typeof mujoco.Simulation === 'function',
          hasFS: typeof mujoco.FS === 'object',
        });

        console.log('%c[MuJoCo Init] Step 2: Setting up virtual filesystem...', 'color: #00ff00; font-weight: bold');

        // Set up Emscripten virtual filesystem
        // IMPORTANT: Pattern that works - mkdir first, then mount
        mujoco.FS.mkdir('/working');
        mujoco.FS.mount(mujoco.MEMFS, { root: '.' }, '/working');
        mujoco.FS.mkdir('/working/assets');
        console.log('%c[MuJoCo Init] ✓ Virtual filesystem ready', 'color: #00ff00');

        console.log('%c[MuJoCo Init] Step 3: Loading ALOHA XML files...', 'color: #00ff00; font-weight: bold');

        // Load ALOHA XML files (scene includes aloha, aloha includes actuators)
        // IMPORTANT: scene.xml is the main entry point, includes aloha.xml
        const xmlFiles = [
          'scene.xml',          // Main scene (includes aloha.xml)
          'aloha.xml',          // Robot definition (includes actuators and keyframes)
          'joint_position_actuators.xml',
          'keyframe_ctrl.xml'
        ];

        let xmlLoadCount = 0;
        for (const xmlFile of xmlFiles) {
          try {
            const xmlResponse = await fetch(`/models/aloha/${xmlFile}`);
            if (!xmlResponse.ok) {
              console.warn(`[MuJoCo Init] ⚠ HTTP ${xmlResponse.status} for ${xmlFile}`);
              continue;
            }
            const xmlContent = await xmlResponse.text();
            mujoco.FS.writeFile(`/working/${xmlFile}`, xmlContent);
            xmlLoadCount++;
            console.log(`[MuJoCo Init] ✓ Loaded ${xmlFile}`);
          } catch (err) {
            console.warn(`[MuJoCo Init] ✗ Could not load ${xmlFile}:`, err);
          }
        }
        console.log(`[MuJoCo Init] Loaded ${xmlLoadCount}/${xmlFiles.length} XML files`);

        console.log('%c[MuJoCo Init] Step 4: Loading mesh and texture files...', 'color: #00ff00; font-weight: bold');

        // Load all mesh and texture files
        const assetFiles = [
          // Robot arm meshes
          'vx300s_1_base.stl',
          'vx300s_2_shoulder.stl',
          'vx300s_3_upper_arm.stl',
          'vx300s_4_upper_forearm.stl',
          'vx300s_5_lower_forearm.stl',
          'vx300s_6_wrist.stl',
          'vx300s_7_gripper_prop.stl',
          'vx300s_7_gripper_bar.stl',
          'vx300s_7_gripper_wrist_mount.stl',
          'vx300s_8_custom_finger_left.stl',
          'vx300s_8_custom_finger_right.stl',
          'd405_solid.stl',
          // Table and frame meshes (required by scene.xml)
          'tablelegs.obj',
          'tabletop.obj',
          'extrusion_2040_880.stl',
          'extrusion_150.stl',
          'corner_bracket.stl',
          'extrusion_1220.stl',
          'extrusion_1000.stl',
          'angled_extrusion.stl',
          'extrusion_600.stl',
          'overhead_mount.stl',
          'extrusion_2040_1000.stl',
          'wormseye_mount.stl',
          // Textures
          'small_meta_table_diffuse.png',
          'interbotix_black.png'
        ];

        let loadedCount = 0;
        for (const assetFile of assetFiles) {
          try {
            const assetResponse = await fetch(`/models/aloha/assets/${assetFile}`);
            if (!assetResponse.ok) {
              console.warn(`[MuJoCo Init] ⚠ HTTP ${assetResponse.status} for ${assetFile}`);
              continue;
            }
            const assetBuffer = await assetResponse.arrayBuffer();
            mujoco.FS.writeFile(`/working/assets/${assetFile}`, new Uint8Array(assetBuffer));
            loadedCount++;
          } catch (err) {
            console.warn(`[MuJoCo Init] ✗ Could not load ${assetFile}:`, err);
          }
        }
        console.log(`%c[MuJoCo Init] ✓ Loaded ${loadedCount}/${assetFiles.length} asset files`, 'color: #00ff00');

        // Debug: List what's in the virtual filesystem
        try {
          const workingFiles = mujoco.FS.readdir('/working');
          const assetsFiles = mujoco.FS.readdir('/working/assets');
          console.log('[MuJoCo Init] VFS Check:', {
            working: workingFiles,
            assets: assetsFiles.length + ' files'
          });

          // Verify key files exist
          const keyFiles = ['scene.xml', 'aloha.xml', 'joint_position_actuators.xml', 'keyframe_ctrl.xml'];
          keyFiles.forEach(file => {
            try {
              const stat = mujoco.FS.stat('/working/' + file);
              console.log(`[MuJoCo Init] ✓ ${file} exists (${stat.size} bytes)`);
            } catch (e) {
              console.error(`[MuJoCo Init] ✗ ${file} NOT FOUND`);
            }
          });
        } catch (err) {
          console.warn('[MuJoCo Init] ⚠ Could not list filesystem:', err);
        }

        console.log('%c[MuJoCo Init] Step 5: Creating MuJoCo model...', 'color: #00ff00; font-weight: bold');

        // Check current working directory
        try {
          const cwd = mujoco.FS.cwd();
          console.log('[MuJoCo Init] Current working directory:', cwd);

          // Change to /working directory so relative paths work
          mujoco.FS.chdir('/working');
          console.log('[MuJoCo Init] Changed CWD to:', mujoco.FS.cwd());
        } catch (cwdErr) {
          console.warn('[MuJoCo Init] Could not change directory:', cwdErr);
        }

        // Create MuJoCo model and simulation
        // Check if constructors are available
        let model, state, simulation;
        try {
          // Verify that MuJoCo exports the required constructors
          if (!mujoco.Model || !mujoco.State || !mujoco.Simulation) {
            console.error('[MuJoCoScene] MuJoCo API inspection:', {
              hasModel: !!mujoco.Model,
              hasState: !!mujoco.State,
              hasSimulation: !!mujoco.Simulation,
              availableKeys: Object.keys(mujoco).filter(k => typeof mujoco[k] === 'function').slice(0, 20)
            });
            throw new Error('MuJoCo WASM build does not expose Model, State, or Simulation constructors. Available functions: ' + Object.keys(mujoco).filter(k => typeof mujoco[k] === 'function').slice(0, 10).join(', '));
          }

          // Try to create model, state, and simulation
          // First try with just the filename (now that CWD is /working)
          console.log('[MuJoCo Init] Attempting to load model from scene.xml...');
          model = new mujoco.Model('scene.xml');
          console.log('%c[MuJoCo Init] ✓ Model created', 'color: #00ff00');

          state = new mujoco.State(model);
          console.log('%c[MuJoCo Init] ✓ State created', 'color: #00ff00');

          simulation = new mujoco.Simulation(model, state);
          simulationRef.current = simulation;
          console.log('%c[MuJoCo Init] ✓ Simulation created', 'color: #00ff00');
          console.log('[MuJoCo Init] Simulation Info:', {
            qpos_length: simulation.qpos?.length || 0,
            qvel_length: simulation.qvel?.length || 0,
            has_step: typeof simulation.step === 'function'
          });

          // Store references for cleanup
          cleanupModel = model;
          cleanupState = state;
          cleanupSimulation = simulation;
        } catch (modelError: any) {
          console.error('%c[MuJoCo Init] ✗ Failed to create model', 'color: #ff0000; font-weight: bold');
          console.error('[MuJoCo Init] Error details:', {
            message: modelError.message,
            toString: modelError.toString(),
            stack: modelError.stack,
            type: typeof modelError,
            errorObject: modelError
          });

          // Try to get more info from MuJoCo
          console.log('[MuJoCo Init] Checking for error info in mujoco object...');
          const mujocoKeys = Object.keys(mujoco).filter(k => k.toLowerCase().includes('error') || k.toLowerCase().includes('warn'));
          console.log('[MuJoCo Init] MuJoCo error-related keys:', mujocoKeys);

          // Try reading the XML file to see if it's valid
          console.log('[MuJoCo Init] Attempting to read scene.xml from VFS...');
          try {
            const sceneContent = mujoco.FS.readFile('/working/scene.xml', { encoding: 'utf8' });
            console.log('[MuJoCo Init] scene.xml first 500 chars:', sceneContent.substring(0, 500));
          } catch (readErr) {
            console.error('[MuJoCo Init] Could not read scene.xml:', readErr);
          }

          throw modelError;
        }

        console.log('%c[MuJoCo Init] Step 6: Setting initial joint positions...', 'color: #00ff00; font-weight: bold');

        // Set initial joint positions to ready pose
        const readyPose = [0.0, -0.96, 1.16, 0.0, -0.3, 0.0];
        // MuJoCo uses qpos for joint positions
        if (simulation && simulation.qpos) {
          for (let i = 0; i < readyPose.length; i++) {
            simulation.qpos[i] = readyPose[i];
          }
          console.log('%c[MuJoCo Init] ✓ Ready pose set', 'color: #00ff00');
        }

        setIsLoading(false);
        console.log('%c[MuJoCo Init] ✅ Initialization complete!', 'color: #00ff00; font-weight: bold; font-size: 14px');

        // Notify parent component
        if (onMuJoCoReady) {
          onMuJoCoReady(mujoco, simulation);
        }
      } catch (err: any) {
        console.error('%c[MuJoCo Init] ❌ Initialization failed', 'color: #ff0000; font-weight: bold; font-size: 14px');
        console.error('[MuJoCo Init] Error:', err);
        setError(err.message || 'Failed to load MuJoCo');
        setIsLoading(false);
      }
    };

    initMuJoCo();

    // Cleanup function to free MuJoCo memory
    return () => {
      console.log('%c[MuJoCo Cleanup] Freeing resources...', 'color: #ffaa00');

      // Free MuJoCo objects in reverse order of creation
      if (cleanupSimulation && typeof cleanupSimulation.free === 'function') {
        cleanupSimulation.free();
        console.log('[MuJoCo Cleanup] ✓ Simulation freed');
      }
      if (cleanupState && typeof cleanupState.free === 'function') {
        cleanupState.free();
        console.log('[MuJoCo Cleanup] ✓ State freed');
      }
      if (cleanupModel && typeof cleanupModel.free === 'function') {
        cleanupModel.free();
        console.log('[MuJoCo Cleanup] ✓ Model freed');
      }

      // Clear refs
      simulationRef.current = null;
      mujocoRef.current = null;
      console.log('%c[MuJoCo Cleanup] ✓ Complete', 'color: #ffaa00');
    };
  }, [onMuJoCoReady]);

  // Update simulation based on robot state
  useEffect(() => {
    if (simulationRef.current && !isLoading) {
      const sim = simulationRef.current;
      const joints = robotState.joints;

      // Update joint positions
      if (sim.qpos) {
        sim.qpos[0] = joints.waist;
        sim.qpos[1] = joints.shoulder;
        sim.qpos[2] = joints.elbow;
        sim.qpos[3] = joints.forearm_roll;
        sim.qpos[4] = joints.wrist_angle;
        sim.qpos[5] = joints.wrist_rotate;

        // Update gripper (if MuJoCo model has gripper joints)
        // Gripper position: 0 (closed) to 1 (open)
        const gripperAngle = robotState.gripperState.position;
        if (sim.qpos.length > 6) {
          sim.qpos[6] = gripperAngle * 0.037; // Scale to ALOHA gripper range
        }
      }

      // Step simulation
      sim.step();
    }
  }, [robotState, isLoading]);

  if (isLoading) {
    return (
      <div
        style={{
          width: '100%',
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#1a1a1a',
          color: 'white',
          fontSize: 24,
        }}
      >
        Loading MuJoCo ALOHA Model...
      </div>
    );
  }

  if (error) {
    return (
      <div
        style={{
          width: '100%',
          height: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#1a1a1a',
          color: '#ff6b6b',
          fontSize: 18,
          flexDirection: 'column',
          gap: '20px',
        }}
      >
        <div>Error Loading MuJoCo:</div>
        <div style={{ fontSize: 14, color: '#aaa' }}>{error}</div>
        <div style={{ fontSize: 12, color: '#666', maxWidth: '600px', textAlign: 'center' }}>
          Try refreshing the page. If the error persists, check the browser console for details.
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100vh', background: '#1a1a1a' }}>
      <Canvas
        ref={canvasRef}
        shadows
        camera={{
          position: [1.2, -1.2, 0.8],
          fov: 50,
        }}
        gl={{ antialias: true }}
      >
        {/* Lighting */}
        <directionalLight
          position={[5, 5, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <directionalLight position={[-5, 3, -5]} intensity={0.3} />
        <ambientLight intensity={0.4} />

        {/* Environment map */}
        <Environment preset="city" />

        {/* MuJoCo renders its own scene - placeholder for now */}
        {/* We'll integrate MuJoCo's rendering in the next iteration */}
        <axesHelper args={[0.5]} />

        {/* Camera controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          target={[0.2, 0, 0.2]}
          minDistance={0.5}
          maxDistance={3}
          maxPolarAngle={Math.PI / 2}
        />
      </Canvas>

      <div
        style={{
          position: 'absolute',
          top: 20,
          left: 20,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '10px 15px',
          borderRadius: '5px',
          fontSize: '14px',
        }}
      >
        🎮 MuJoCo Simulation Active
      </div>
    </div>
  );
}
