/**
 * MuJoCo WASM Loader
 * Loads the MuJoCo WASM module with browser compatibility patches
 */

export async function loadMuJoCo(): Promise<any> {
  try {
    // Fetch the MuJoCo WASM JavaScript file
    const response = await fetch('/mujoco/mujoco_wasm.js');
    let code = await response.text();

    // Patch out Node.js-specific code that doesn't work in browsers
    // The zalo/mujoco_wasm file contains: const{createRequire:createRequire}=await import("module")
    // This is used for Node.js compatibility but breaks in browser
    code = code.replace(/const\{createRequire:createRequire\}=await import\("module"\);?/g, '');
    code = code.replace(/createRequire\(import\.meta\.url\)/g, '() => {}');

    // Create a blob URL from the patched code
    const blob = new Blob([code], { type: 'application/javascript' });
    const blobUrl = URL.createObjectURL(blob);

    // Dynamically import the patched module
    const module = await import(/* webpackIgnore: true */ blobUrl);

    // Clean up the blob URL
    URL.revokeObjectURL(blobUrl);

    // The default export is a factory function that returns a Promise
    // Call it to get the initialized MuJoCo module
    const load_mujoco_fn = module.default;
    if (typeof load_mujoco_fn !== 'function') {
      throw new Error('MuJoCo WASM module does not export a factory function');
    }

    console.log('[MuJoCo Loader] Loaded factory function, initializing MuJoCo...');

    // Capture MuJoCo stdout/stderr for error messages
    const capturedOutput: string[] = [];
    const capturedErrors: string[] = [];

    // Initialize and return the MuJoCo module instance
    const mujocoModule = await load_mujoco_fn({
      locateFile: (path: string) => {
        // Tell MuJoCo where to find the .wasm file
        if (path.endsWith('.wasm')) {
          return '/mujoco/' + path;
        }
        return path;
      },
      print: (text: string) => {
        capturedOutput.push(text);
        console.log('[MuJoCo stdout]', text);
      },
      printErr: (text: string) => {
        capturedErrors.push(text);
        console.error('[MuJoCo stderr]', text);
      }
    });

    // Store captured output on the module for access
    (mujocoModule as any).getCapturedOutput = () => capturedOutput;
    (mujocoModule as any).getCapturedErrors = () => capturedErrors;

    console.log('[MuJoCo Loader] MuJoCo module initialized successfully');
    return mujocoModule;
  } catch (error) {
    console.error('[MuJoCo Loader] Failed to load MuJoCo WASM:', error);
    throw error;
  }
}
