# GPT‑5 ALOHA Live Guide

End‑to‑end guide to control a Trossen/Interbotix Mobile ALOHA robot using Gemini Live API with voice and video, no training required. You will stream the robot’s camera, expose a few robot actions as tools, and let Gemini plan and call those tools in real time.

## Scope & Outcomes

- Voice commands like “Grab the banana and put it in the bowl” execute via Gemini Live API tool calls.
- Live video from the robot’s camera grounds Gemini’s spatial reasoning.
- A minimal Python bridge sends tool calls to the Interbotix/ALOHA stack.
- Safety: workspace limits and conservative motions baked in.

## Prerequisites

- Hardware: Mobile ALOHA (dual arms), grippers, at least one RGB camera; an Ubuntu robot PC (ROS2), and your Mac/PC for the web console.
- Accounts: Access to Gemini API and Live API (Google AI Studio / Vertex AI).
- Software (robot PC):
  - ROS2 (e.g., Humble) + Interbotix drivers for your arms (e.g., `vx300s`).
  - ALOHA/Interbotix environment providing `RealEnv` (or equivalent arm/gripper API).
  - Python 3.10+, `pip install aiohttp aiohttp-cors numpy`.
- Software (console machine): Node 18+, npm, the Live API Web Console sample app.

## Architecture

```
┌──────────────┐   WebSocket (audio/video + tool calls)   ┌────────────────────┐
│ Gemini 2.5   │◄────────────────────────────────────────►│ Live API Web Console│
│ (Cloud)      │                                         │ (React)             │
└──────────────┘                                         └─────────┬──────────┘
                                                      HTTP POST     │ tool calls
                                                                     ▼
                                                            ┌──────────────────┐
                                                            │ Python Bridge    │
                                                            │ (aiohttp, 8081)  │
                                                            └─────────┬────────┘
                                                       ROS2 cmds      │
                                                                     ▼
                                                            ┌──────────────────┐
                                                            │ Mobile ALOHA     │
                                                            │ (Interbotix)     │
                                                            └──────────────────┘
```

## Step 1 — Live API Web Console

1) Clone and run the Live API Web Console (Google’s sample app).

- Install deps, configure your Gemini API key per that repo’s README, then `npm start`.
- Confirm you can start/stop a Live API session and send simple text/voice prompts.

Tip: For a quick dry run, use your laptop webcam first. You can switch to robot camera later.

## Step 2 — Define Robot Tools in the Console

Add a panel/component that:
- Declares tools for Gemini to call.
- Routes tool calls to the Python bridge.
- Sends back `functionResponses` to complete the tool cycle.

Tool declarations (names/args) to start with:

```ts
const ROBOT_TOOLS = [
  {
    name: "detect_objects",
    description: "Identify items and rough 3D positions from the current scene",
    parameters: { type: "object", properties: {}, required: [] }
  },
  {
    name: "move_to_position",
    description: "Move an arm to absolute XYZ (meters, robot base frame)",
    parameters: {
      type: "object",
      properties: {
        arm: { type: "string", enum: ["left", "right"] },
        x: { type: "number" },
        y: { type: "number" },
        z: { type: "number" }
      },
      required: ["arm", "x", "y", "z"]
    }
  },
  {
    name: "control_gripper",
    description: "Open or close gripper",
    parameters: {
      type: "object",
      properties: {
        arm: { type: "string", enum: ["left", "right"] },
        action: { type: "string", enum: ["open", "close"] }
      },
      required: ["arm", "action"]
    }
  },
  {
    name: "get_robot_status",
    description: "Return joint states, EE pose, gripper state",
    parameters: { type: "object", properties: {}, required: [] }
  }
];
```

Minimal React integration sketch:

```tsx
// inside a component mounted while the session is active
useEffect(() => {
  setConfig({
    tools: [{ functionDeclarations: ROBOT_TOOLS }],
    systemInstruction: `You control a Mobile ALOHA robot.\n` +
      `Coordinate frame: X forward, Y left, Z up from base.\n` +
      `Use detect_objects first if needed; then move_to_position and control_gripper.\n` +
      `Respect safety; stay within X[0.15,0.55], Y[-0.35,0.35], Z[0.05,0.45].`
  });
}, [setConfig]);

useEffect(() => {
  const onToolCall = async (evt) => {
    const responses = [];
    for (const call of evt.functionCalls) {
      const res = await fetch('http://ROBOT_PC_IP:8081/aloha-tool-call', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: call.name, args: call.args, id: call.id })
      });
      const data = await res.json();
      responses.push({ name: call.name, id: call.id, response: data.result ?? data });
    }
    if (responses.length) client.sendToolResponse({ functionResponses: responses });
  };
  client.on('toolcall', onToolCall); return () => client.off('toolcall', onToolCall);
}, [client]);
```

## Step 3 — Stream Robot Camera to the Session

Start with a simple source, then upgrade:

- Option A (Quick): Use your laptop webcam via `getUserMedia`. Confirm Gemini can reason about the scene and call tools.
- Option B (Robot): Publish camera via ROS and view in browser, then stream to the session.

ROS2 path in browser:

1) Run `web_video_server` on the robot PC to expose an MJPEG stream of your camera topic (e.g., `/image_raw`).
2) In the React app, set an `<img src="http://ROBOT_PC_IP:8080/stream?topic=/image_raw" />`, draw it to a `<canvas>`, and call `canvas.captureStream()`.
3) Add the resulting `MediaStreamTrack` to the Live API session (the web console sample shows how to attach video tracks).

This keeps the pipeline browser‑native and avoids custom video bridges.

## Step 4 — Python Bridge (Robot PC)

Create `aloha_bridge.py` to receive tool calls and command the robot via Interbotix/ALOHA. Minimal, safe defaults shown below.

```py
#!/usr/bin/env python3
import asyncio, time, traceback
from aiohttp import web
from aiohttp_cors import setup, ResourceOptions

# Import your robot env (adjust paths per your setup)
from aloha.real_env import RealEnv

WORKSPACE = { 'x': (0.15, 0.55), 'y': (-0.35, 0.35), 'z': (0.05, 0.45) }

class Bridge:
  def __init__(self):
    self.env = RealEnv(init_node=True, setup_robots=True, setup_base=False)

  def _validate(self, x,y,z):
    if not (WORKSPACE['x'][0] <= x <= WORKSPACE['x'][1] and
            WORKSPACE['y'][0] <= y <= WORKSPACE['y'][1] and
            WORKSPACE['z'][0] <= z <= WORKSPACE['z'][1]):
      raise ValueError(f"XYZ outside workspace: {(x,y,z)} {WORKSPACE}")

  async def detect_objects(self, args):
    # MVP stub; rely on Gemini’s visual grounding first
    return { 'objects': {}, 'note': 'stubbed; use visual reasoning' }

  async def move_to_position(self, args):
    arm = args.get('arm'); x=float(args['x']); y=float(args['y']); z=float(args['z'])
    self._validate(x,y,z)
    bot = self.env.puppet_bot_left if arm=='left' else self.env.puppet_bot_right
    ok = bot.arm.set_ee_pose_components(x=x,y=y,z=z, roll=0.0,pitch=0.5,yaw=0.0,
                                        execute=True, moving_time=2.0, accel_time=0.5)
    pose = bot.arm.get_ee_pose()
    return { 'success': bool(ok), 'target': {'x':x,'y':y,'z':z},
             'actual': {'x':float(pose[0,3]),'y':float(pose[1,3]),'z':float(pose[2,3])} }

  async def control_gripper(self, args):
    arm = args.get('arm'); action = args.get('action')
    grip = (self.env.puppet_bot_left if arm=='left' else self.env.puppet_bot_right).gripper
    if action=='open': grip.open()
    elif action=='close': grip.close()
    else: raise ValueError('action must be open|close')
    await asyncio.sleep(1.0)
    return { 'success': True, 'arm': arm, 'action': action }

  async def get_robot_status(self, args):
    status = {}
    for name, bot in [('left', self.env.puppet_bot_left), ('right', self.env.puppet_bot_right)]:
      pose = bot.arm.get_ee_pose()
      status[name] = {
        'end_effector': {'x':float(pose[0,3]),'y':float(pose[1,3]),'z':float(pose[2,3])}
      }
    return { 'arms': status, 'workspace': WORKSPACE, 'ts': time.time() }

bridge = Bridge()

async def handle(request):
  try:
    data = await request.json(); name = data.get('name'); args = data.get('args', {})
    if   name=='detect_objects':   res = await bridge.detect_objects(args)
    elif name=='move_to_position': res = await bridge.move_to_position(args)
    elif name=='control_gripper':  res = await bridge.control_gripper(args)
    elif name=='get_robot_status': res = await bridge.get_robot_status(args)
    else: raise ValueError(f'unknown tool {name}')
    return web.json_response({ 'success': True, 'result': res, 'call_id': data.get('id') })
  except Exception as e:
    traceback.print_exc()
    return web.json_response({ 'success': False, 'error': str(e) }, status=500)

app = web.Application()
setup(app, defaults={"*": ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods="*")})
app.router.add_post('/aloha-tool-call', handle)

if __name__ == '__main__':
  web.run_app(app, host='0.0.0.0', port=8081)
```

Install and run on the robot PC:

```bash
pip install aiohttp aiohttp-cors numpy
python aloha_bridge.py
```

## Step 5 — Bring‑Up & Test

1) Start Interbotix drivers (examples; adjust for your models):

```bash
ros2 launch interbotix_xsarm_control xsarm_control.launch.py robot_model:=vx300s robot_name:=puppet_left  use_gripper:=true
ros2 launch interbotix_xsarm_control xsarm_control.launch.py robot_model:=vx300s robot_name:=puppet_right use_gripper:=true
```

2) Start camera nodes (or use laptop webcam for MVP). If using ROS camera, also run `web_video_server`.

3) Run the Python bridge on the robot PC:

```bash
python aloha_bridge.py
```

4) Launch the Live API Web Console on your Mac/PC, set tool endpoint to `http://ROBOT_PC_IP:8081/aloha-tool-call`, connect to Gemini.

5) Test prompts:
- “Show me the robot status.” → Should call `get_robot_status`.
- “Move the right arm to x 0.30, y 0.10, z 0.20 meters.” → Should call `move_to_position`.
- “Open the left gripper.” → Should call `control_gripper`.
- “Pick up the red cup and place it in the blue bowl.” → Expect a sequence of tool calls.

## Safety & Ops

- Start with slow speeds and high Z pre‑poses.
- Keep workspace limits strict in the bridge; reject out‑of‑bounds.
- Provide a physical E‑stop and a clear line of sight.
- Let Gemini ground itself: have it call `get_robot_status` first in your prompt (“get your bearings, then…”).

## Upgrades (Optional)

- Real detection: Replace `detect_objects` stub with CV (ArUco tags; simple color thresholding; or a local detector). You can also rely on Gemini’s pointing/region reasoning with live frames to minimize custom CV.
- Trajectories: Add a `move_trajectory` tool for multi‑waypoint motions.
- Mobile base: Expose `move_base_to(x,y,theta)` as a tool and add safety layers.
- Learning: If desired later, integrate ACT++ to generate actions from demos; keep Gemini as planner/referee.

## Troubleshooting

- ROS topics: `ros2 topic list | grep puppet` and `ros2 topic echo /puppet_left/joint_states`.
- Bridge health: `curl -X POST http://ROBOT_PC_IP:8081/aloha-tool-call -H 'Content-Type: application/json' -d '{"name":"get_robot_status","args":{},"id":"t"}'`.
- Video: If the session can’t see video, test the MJPEG URL in a browser, then the canvas stream.

## FAQ

- Do I need to train a model? No. Gemini 2.5’s spatial reasoning + tool use is enough for MVP.
- How does Gemini know where objects are? From the live video; optionally from your `detect_objects` tool if you provide one.
- What frame are XYZ in? Robot base frame (define it clearly in the system instruction and enforce in code).

---

With this setup, you get real‑time, voice‑driven manipulation on Mobile ALOHA powered by Gemini Live API—no training required. Start with the MVP flow, then iterate on perception and safety as you gain confidence.

