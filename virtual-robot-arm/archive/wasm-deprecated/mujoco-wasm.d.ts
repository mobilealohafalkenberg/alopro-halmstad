declare module 'mujoco-wasm' {
  function load_mujoco(config?: { locateFile?: (path: string) => string }): Promise<MuJoCoModule>;
  export default load_mujoco;

  export interface MuJoCoModule {
    // Emscripten filesystem
    FS: {
      mkdir(path: string): void;
      mount(type: any, opts: any, mountpoint: string): void;
      readdir(path: string): string[];
      writeFile(path: string, data: string | Uint8Array): void;
      readFile(path: string): Uint8Array;
    };
    MEMFS: any;

    // MuJoCo constructors (may not be available depending on WASM build)
    Model?: {
      new(xmlPath: string): MuJoCoModel;
    };
    State?: {
      new(model: MuJoCoModel): MuJoCoState;
    };
    Simulation?: {
      new(model: MuJoCoModel, state: MuJoCoState): MuJoCoSimulation;
    };

    // Memory management
    _malloc?(size: number): number;
    _free?(ptr: number): void;
  }

  export interface MuJoCoModel {
    free?(): void;
  }

  export interface MuJoCoState {
    free?(): void;
  }

  export interface MuJoCoSimulation {
    qpos: Float64Array;
    qvel: Float64Array;
    ctrl: Float64Array;
    xpos: Float64Array;
    step(): void;
    free?(): void;
  }
}
