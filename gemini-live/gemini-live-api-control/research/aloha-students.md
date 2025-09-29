# Mobile ALOHA + Gemini Live API: Student Project Brief

Overview Diagram (inspired by warp-aloha-live-api-v2.md)

```
┌─────────────────┐     WebSocket      ┌──────────────────┐
│  Gemini Live    │◄──────────────────►│  Live API        │
│  API (Cloud)    │  Video + Tool Calls │  Console (React) │
└─────────────────┘                     └──────────────────┘
                                                │
                                          HTTP  │ Tool Calls
                                                ▼
                                        ┌──────────────────┐
                                        │  Python Bridge   │
                                        │  (Port 8081)     │
                                        └──────────────────┘
                                                │
                                      ROS2/SDK  │ Commands + State
                                                ▼
                                        ┌──────────────────┐
                                        │  Mobile ALOHA    │
                                        │ (Interbotix)     │
                                        └──────────────────┘
```

Notes
- Live API streams video into the session and emits functionCalls in real time.
- The Console forwards functionCalls to the Bridge; the Bridge returns JSON results which the Console relays back via `functionResponses`.
- The Bridge converts high-level tool args (x,y,z, arm, action) into Interbotix/ROS2 commands (Cartesian helpers or IK → joints → servos) and reads state for feedback.

```
Legend: [Component]  -> data flow   => action/side-effect

┌────────────────────────────────────────────────────────────────────────────┐
│                           High‑Level Flow (Code)                           │
├────────────────────────────────────────────────────────────────────────────┤
│ 1) Web Console (React)                                                     │
│    - File: live-api-web-console/src/components/aloha-control/ALOHAControl.tsx│
│    - Creates Live session, attaches video track, declares tools            │
│    - On toolcall: POST /aloha-tool-call with {name,args,id}                │
│                                                                            │
│ 2) Gemini Live API                                                         │
│    - Sees video, language, tool schema                                     │
│    - Plans and emits functionCalls (e.g., move_to_position)                │
│                                                                            │
│ 3) Python Bridge (Robot PC)                                                │
│    - File: bridges/aloha_bridge.py                                         │
│    - Endpoint: POST /aloha-tool-call                                       │
│    - Dispatches tools -> Interbotix/ALOHA (RealEnv)                        │
│      • get_robot_status()  => read EE poses / grippers                     │
│      • move_to_position()  => Cartesian move (IK -> joints -> servos)      │
│      • control_gripper()   => open/close                                   │
│      • detect_objects()    => (stub or CV)                                 │
│    - Validates workspace, returns JSON {success,result,call_id}            │
│                                                                            │
│ 4) Interbotix / ALOHA                                                      │
│    - Drivers + kinematics compute joint targets, drive servos              │
│    - Publishes joint states; camera publishes /image_raw                   │
│                                                                            │
│ 5) Video Path                                                              │
│    - ROS camera -> web_video_server (MJPEG) -> <img> -> <canvas>           │
│    - canvas.captureStream() -> add track to Live session                   │
└────────────────────────────────────────────────────────────────────────────┘
```

This brief defines the exact scope, deliverables, and success criteria for building a working, voice-driven control pipeline for a Mobile ALOHA robot using the Gemini Live API. No model training is required. The focus is on systems integration, safety, and a clean developer experience.

## Project Goal

Enable a user to speak a task (e.g., “Grab the banana and put it in the bowl”) and have:
- The robot’s live camera feed and current arm states streamed to a Gemini Live API session.
- Gemini use its image + spatial understanding to plan and call tools in real time.
- A bridge translate those tool calls into Interbotix/ROS2 commands that move the Mobile ALOHA robot safely.

## High‑Level Architecture

```
User (voice) → Live API Web Console ↔ Gemini Live API (Cloud)
                                 ↘ tool calls (HTTP)
                         Python Bridge (Robot PC) → Interbotix/ROS2 → Mobile ALOHA
                                   ↑ status/poses
Robot camera → (ROS2) → web_video_server → Web Console video track → Gemini session
```

Key components you will create
- Live console component: declares tools, handles tool calls, attaches the video track.
- Python bridge (real): HTTP tool dispatcher with safety checks; calls Interbotix on robot PC.
- Python bridge (mock): local development server returning canned data.

## Step‑by‑Step Workspace Setup (Generic)

1) Create a working directory on your machine
```bash
mkdir -p ~/aloha-live-workspace && cd ~/aloha-live-workspace
```

2) Clone the Gemini Live API Web Console (TypeScript)
```bash
git clone https://github.com/google-gemini/live-api-web-console.git
```

3) Create a directory for Python bridges and docs
```bash
mkdir -p bridges docs
```

4) Add the ALOHA control component to the console
- Create a folder in the console app for the ALOHA UI and add a file:
  - `live-api-web-console/src/components/aloha-control/ALOHAControl.tsx`
- This component should:
  - Register function tools (get_robot_status, move_to_position, control_gripper, detect_objects).
  - Forward tool calls to `${process.env.REACT_APP_ROBOT_ENDPOINT}/aloha-tool-call`.
  - Send `client.sendToolResponse({ functionResponses })` with results.
  - Optionally render quick‑action buttons and show robot state.

5) Add Python bridges
- Create `bridges/mock_bridge.py` for local development (no robot): implements `/aloha-tool-call` and returns canned responses.
- Create `bridges/aloha_bridge.py` for the real robot PC: implements `/aloha-tool-call` and maps tools to Interbotix/ALOHA APIs with workspace safety.

6) Configure the console
- Create `live-api-web-console/.env` with:
```
REACT_APP_GEMINI_API_KEY=your_api_key_here
REACT_APP_ROBOT_ENDPOINT=http://localhost:8081   # mock during local dev
```

7) Install and run
```bash
# Terminal A – Mock bridge
python bridges/mock_bridge.py

# Terminal B – Console
cd live-api-web-console
npm install
npm start
```

8) Test (no robot)
- In the console UI, try:
  - “Show me the robot status.”
  - “Move the right arm to x 0.30, y 0.10, z 0.20 meters.”
  - “Pick up the red cup and place it in the blue bowl.”
- You should see tool‑call logs and structured responses from the mock bridge.

9) Transition to lab (with robot)
- On the Linux robot PC, run the real bridge: `python bridges/aloha_bridge.py`.
- In the console `.env`, set `REACT_APP_ROBOT_ENDPOINT=http://<ROBOT_PC_IP>:8081`.
- Stream ROS camera via `web_video_server` and attach to the session using a canvas track.

## Suggested Project Structure

```
~/aloha-live-workspace/
├─ live-api-web-console/                  # cloned from Google
│  ├─ src/components/aloha-control/
│  │  └─ ALOHAControl.tsx                 # your console component
│  └─ .env                                # Gemini key + ROBOT_ENDPOINT
├─ bridges/
│  ├─ mock_bridge.py                      # local dev (no robot)
│  └─ aloha_bridge.py                     # real bridge (robot PC)
├─ docs/
│  ├─ SYSTEM_INSTRUCTION.md               # system prompt for the session
│  └─ IMPLEMENTATION_GUIDE.md             # optional helper docs
└─ README.md
```

## Local Dev Setup (No Robot)

This gets you productive on your own machine before visiting the lab.

1) Prerequisites
- Node 18+, npm
- Python 3.10+, `pip`
- A Google AI Studio (Gemini) API key (get one at https://aistudio.google.com)

2) Clone the Live API Web Console (TypeScript)
- Option A (use the copy included in this repo): `live-api-web-console/`
- Option B (fresh clone upstream):
  ```bash
  git clone https://github.com/google-gemini/live-api-web-console.git
  cd live-api-web-console
  npm install
  ```

3) Configure the console
- Get a Gemini API key from https://aistudio.google.com (AI Studio). Keep it private.
- Create/edit `live-api-web-console/.env`:
  ```
  REACT_APP_GEMINI_API_KEY=your_api_key_here
  REACT_APP_ROBOT_ENDPOINT=http://localhost:8081  # mock bridge during local dev
  ```
- Ensure `.env` is in `.gitignore` so you don’t commit secrets. For Python scripts that may need API access later, you can also export:
  ```bash
  export GEMINI_API_KEY=your_api_key_here
  ```
- Ensure the ALOHA control is present at:
  - `live-api-web-console/src/components/aloha-control/ALOHAControl.tsx`. If you cloned upstream into a separate folder, create this file path and add the component.
- Start the console:
  ```bash
  cd live-api-web-console
  npm start
  ```

4) Run the mock bridge (no robot)
- From workspace root:
  ```bash
  python bridges/mock_bridge.py
  ```
- The console will now send tool calls to `http://localhost:8081/aloha-tool-call` and receive mocked responses.

5) Test
- In the console UI, try:
  - “Show me the robot status.”
  - “Move the right arm to x 0.30, y 0.10, z 0.20 meters.”
  - “Pick up the red cup and place it in the blue bowl.”

You should see tool-call logs and structured responses in the console and the mock server terminal.

## Requirements (What You Must Build)

1) Live API Console Integration (Frontend)
- Stream a video source into an active Live API session:
  - MVP: laptop webcam. Later: robot camera (via ROS MJPEG → canvas → captureStream).
- Define and register function tools that Gemini can call during the session:
  - `get_robot_status()` → returns EE pose and gripper states for both arms.
  - `move_to_position(arm: "left"|"right", x: number, y: number, z: number)` → absolute Cartesian move in base frame (meters).
  - `control_gripper(arm: "left"|"right", action: "open"|"close")`.
  - `detect_objects()` → optional/stub for MVP.
- Handle tool calls: forward JSON to the Python bridge, receive results, and send `functionResponses` back to Gemini.
- Provide a clear system instruction describing the coordinate frame, safety limits, and recommended flow (status → detect → move → grip).

Coordinate frames and units
- Tool inputs are in the robot base frame, meters: X forward, Y left, Z up.
- Gemini outputs will use this convention; the bridge enforces bounds and converts to robot calls.

2) Python Bridge (Backend on Robot PC)
- HTTP server (e.g., `aiohttp`) listening on `POST /aloha-tool-call`.
- Map tool names to implementations using Interbotix/ALOHA:
  - `get_robot_status`: read current EE poses; return JSON.
  - `move_to_position`: validate workspace limits; call Interbotix Cartesian move; return target + actual.
  - `control_gripper`: open/close; return state.
  - `detect_objects`: MVP can return stubbed detections or empty set.
- Enforce conservative workspace limits (e.g., X[0.15,0.55], Y[-0.35,0.35], Z[0.05,0.45]) and reject out‑of‑bounds.
- Return structured success/error payloads and useful error messages.

Command translation: XYZ → servos
- Interbotix provides Cartesian helpers (e.g., `set_ee_pose_components(x,y,z,roll,pitch,yaw,...)`).
- The bridge receives tool args `{arm,x,y,z}` and calls that helper with a safe orientation
  (e.g., roll=0, pitch≈0.5 rad, yaw=0). Interbotix performs IK to compute joint targets and drives servos.
- If Cartesian helper is unavailable, compute IK via the Interbotix kinematics API, then send joint goals.
- Always add pre‑grasp/post‑grasp Z offsets in the sequencing logic (e.g., approach at z+0.1, then lower).

3) Robot Camera to Console
- Linux robot PC publishes camera (ROS2 topic like `/image_raw`).
- Expose via `web_video_server` (MJPEG) at `http://<robot-ip>:8080/stream?topic=/image_raw`.
- In the console, draw MJPEG `<img>` to `<canvas>` at ~15 FPS and attach `canvas.captureStream()` to the Live API session as a video track.

State feedback and update cadence
- Gemini needs up‑to‑date state to plan safely. Use either:
  - Pull: The model calls `get_robot_status()` before/after moves.
  - Push‑on‑response: The bridge includes `actual` EE pose in each tool result.
- For long moves, consider breaking into smaller moves to let Gemini interleave checks.

4) Safety & Operations
- Rate‑limited moves with safe pre‑grasp patterns (lift before translate when needed).
- Clear E‑stop procedure and logs.
- All motion endpoints must validate bounds before executing.

## Non‑Goals (Out of Scope)
- Training custom policies (ACT/Diffusion). This project uses Gemini’s pre‑trained spatial reasoning.
- Full SLAM or mobile base autonomy. Only add base tools if time permits.

## Deliverables

- Working end‑to‑end demo:
  - Voice/text input in console → Gemini tool calls → robot moves and grips appropriately.
  - Video of the demo (screen recording + external view, if possible).
- Code & configs:
  - Frontend component(s) for tool declarations, tool‑call handling, and camera streaming.
  - Python bridge server with clear endpoints and safety checks.
  - `README.md` with run instructions for Mac (mock) and Linux (robot).
  - `.env` template for API key and robot endpoint.
- Logs demonstrating tool calls, bridge requests/responses, and robot state.
  - Include timing and any clamping of out‑of‑bounds requests.

## Success Criteria (Acceptance Tests)

- Console connects to Gemini and displays live video.
- Gemini can call `get_robot_status()` on request and receive plausible data.
- Command: “Move the right arm to x 0.30, y 0.10, z 0.20 meters.” results in exactly one `move_to_position` tool call and a successful bridge response (or a safe rejection if out of bounds).
- Command: “Open the left gripper.” results in a `control_gripper` tool call and confirmation.
- Scenario: “Pick up the red cup and place it in the blue bowl.” triggers a reasonable sequence: detect/status → approach above cup → lower → close → lift → move above bowl → open, with safety checks enforced.
  - Verify that move calls include a pre‑grasp z offset and that reported `actual` poses are within tolerance (e.g., ≤ 1 cm from target).

## Milestones & Timeline (Suggested)

- Week 1: Local console + mock bridge working on Mac; tools declared; `functionResponses` wired.
- Week 2: Python bridge on Linux controlling Interbotix arms; status and simple moves validated.
- Week 3: Camera streaming from ROS → web console → Gemini; safe pick‑and‑place demo.
- Week 4: Hardening (error paths, bounds, logging), documentation, and final demo.

## Technical Constraints & Interfaces

- Live API session: WebSocket handled by the provided console app; you will extend it.
- Tool calling: Must send responses via `client.sendToolResponse({ functionResponses: [...] })` after each tool call.
- HTTP bridge contract (request):
  ```json
  { "name": "move_to_position", "args": {"arm": "right", "x": 0.30, "y": 0.10, "z": 0.20}, "id": "uuid" }
  ```
- HTTP bridge contract (success response):
  ```json
  { "success": true, "result": {"target": {"x": 0.3, "y": 0.1, "z": 0.2}, "actual": {"x": 0.3, "y": 0.1, "z": 0.2}}, "call_id": "uuid" }
  ```
- On error, return `{ success: false, error: "..." }` with appropriate HTTP status.

Orientation handling
- If Gemini doesn’t specify orientation, default to a safe down‑facing wrist (roll=0, pitch≈0.5, yaw=0).
- Expose an optional `orientation` field later if needed: Euler or quaternion; convert to API format in the bridge.

## Dev & Test Environments

- Mac (no robot):
  - Use a mock bridge that implements the same API and returns canned data.
  - Use laptop webcam as video.
- Linux Robot PC:
  - Interbotix drivers running for both arms and grippers.
  - ALOHA/Interbotix `RealEnv` (or equivalent) accessible to the Python bridge.
  - ROS2 camera + `web_video_server` for MJPEG.
  - Verify ROS topics and services for arm control and joint states.

### Cloning Interbotix/ALOHA Repos (for reference and later lab work)

While not required for the no-robot MVP, you can review or prepare these:

```bash
# ACT++ (Mobile ALOHA imitation learning algorithms)
git clone https://github.com/Interbotix/act_plus_plus.git

# ALOHA hardware/env setup and scripts
git clone https://github.com/Interbotix/aloha.git
```

When on the lab Linux robot PC, you will use the real bridge:

```bash
python ~/aloha-live-workspace/bridges/aloha_bridge.py
# and set REACT_APP_ROBOT_ENDPOINT=http://<ROBOT_PC_IP>:8081 in the console .env
```

## Evaluation Rubric

- Correctness (40%): End‑to‑end flow works; tools and responses wired correctly; motions within bounds; clear error handling.
- Reliability (25%): Robust to disconnects, missing camera, or invalid inputs; informative logs.
- Safety (20%): Workspace enforcement, gentle motions, clear E‑stop procedure.
- Usability (10%): Clear UI affordances; easily configurable endpoints; readable console output.
- Documentation (5%): Setup/run docs for both Mac (mock) and Linux (robot).

## Stretch Goals (Optional)

- Add `move_trajectory` for multi‑waypoint motion.
- Expose mobile base tools (e.g., `move_base_to(x,y,theta)`) with strict safety checks.
- Enhance `detect_objects` with a lightweight CV module (e.g., ArUco tags) to provide approximate object frames.
- Record and display a timeline of tool calls and results.
 - Add periodic heartbeats from the bridge to the console to show robot health.

## References

- Gemini Live API docs (streaming): https://ai.google.dev/gemini-api/docs/live
- Gemini Live API docs (tools/function calls): https://ai.google.dev/gemini-api/docs/live-tools
- Live API Web Console (TypeScript sample app): https://github.com/google-gemini/live-api-web-console
- Interbotix ACT++ fork (Mobile ALOHA): https://github.com/Interbotix/act_plus_plus
- Interbotix ALOHA (hardware/env setup): https://github.com/Interbotix/aloha
- ROS web_video_server (MJPEG streaming): https://github.com/RobotWebTools/web_video_server
- See your workspace `bridges/` for bridge examples and `docs/` for system instruction and guides.

---

Point of contact: please include Slack/Email for questions; require PRs to pass a brief checklist (tool responses sent, bounds checks implemented, logs show sequence) before review.
