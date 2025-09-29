# GPT‑5 ALOHA Live — Complete Implementation Guide

End‑to‑end instructions to control a Trossen/Interbotix Mobile ALOHA robot using Gemini Live API in real time, without training custom models. You will:
- Stream the robot’s camera into a Live API session.
- Expose a few robot actions as “tools”.
- Let Gemini plan and call your tools to execute tasks like “Grab the banana and put it in the bowl.”

This guide assumes a dual‑arm ALOHA (Interbotix) setup with ROS2 on a robot PC and a separate development machine for the web console.

## Architecture

```
┌──────────────┐   WebSocket (audio/video + tool calls)   ┌────────────────────┐
│ Gemini 2.5   │◄────────────────────────────────────────►│ Live API Web Console│
│ (Cloud)      │                                         │ (React)             │
└──────────────┘                                         └─────────┬──────────┘
                                                      HTTP POST     │ tool calls
+ video track                                                   ▼
+ system instruction                                  ┌──────────────────┐
                                                      │ Python Bridge    │
                                                      │ (aiohttp, 8081)  │
                                                      └─────────┬────────┘
                                             ROS2 cmds         │
                                                               ▼
                                                      ┌──────────────────┐
                                                      │ Mobile ALOHA     │
                                                      │ (Interbotix)     │
                                                      └──────────────────┘
```

## Prerequisites

- Robot PC (Ubuntu): ROS2 (e.g., Humble), Interbotix drivers (e.g., `vx300s` arms), ALOHA/Interbotix environment providing `RealEnv` or equivalent API; Python 3.10+.
- Dev machine (Mac/Windows/Linux): Node 18+, npm; Google AI Studio/Vertex AI access to Gemini Live API.
- Network: Dev machine must reach the robot PC on HTTP port 8081.

Install on robot PC:

```bash
sudo apt-get install python3-pip
pip install aiohttp aiohttp-cors numpy
# Your ALOHA/Interbotix environment should already be installed and working.
```

## Step 1 — Live API Web Console

Start from Google’s Live API Web Console example. Confirm you can:
- Enter your Gemini API key.
- Start a session.
- Send text/voice and receive responses.

Tip: Use your laptop webcam first to verify video streaming before switching to robot camera.

Environment variables (console):

```
# live-api-console/.env
REACT_APP_GEMINI_API_KEY=your_api_key
# During Mac development with the mock bridge:
REACT_APP_ROBOT_ENDPOINT=http://localhost:8081
# When switching to Linux robot PC:
# REACT_APP_ROBOT_ENDPOINT=http://<LINUX_IP>:8081
```

## Step 2 — Define Robot Tools in the Console

You will add a UI component that:
- Declares function tools for Gemini to call.
- Forwards tool calls to the robot PC HTTP bridge.
- Sends `functionResponses` back to Gemini.

Use the sample in `examples/ALOHAControl.tsx` as a template. Tools to start with:
- `detect_objects()` — optional stub for MVP.
- `move_to_position(arm, x, y, z)` — absolute XYZ in robot base frame.
- `control_gripper(arm, action)` — open/close.
- `get_robot_status()` — end‑effector poses, basic info.

Recommended system instruction: see `SYSTEM_INSTRUCTION.md`.

## Step 3 — Stream Camera Into the Session

Start simple, then upgrade.

- Option A: Laptop webcam via `navigator.mediaDevices.getUserMedia` (works out of the box in the web console).
- Option B: Robot camera via ROS2 + web_video_server, then into a `<canvas>`:
  1) On robot PC, publish your camera (e.g., `/image_raw`).
  2) Run `web_video_server` to expose MJPEG at `http://ROBOT_PC_IP:8080/stream?topic=/image_raw`.
  3) In the browser, draw that `<img>` to a `<canvas>` at ~15 FPS and call `canvas.captureStream(15)` to get a `MediaStream`.
  4) Attach the stream’s video track to the Live API session (the console example shows attaching tracks). Example snippet:

```ts
const canvas = document.getElementById('rosCanvas') as HTMLCanvasElement;
const stream = canvas.captureStream(15);
const [videoTrack] = stream.getVideoTracks();
client.attachVideoTrack(videoTrack); // or the equivalent API in the console
```

This keeps everything browser‑native and avoids custom RTP pipelines.

## Step 4 — Python Bridge on Robot PC

Use `examples/aloha_bridge.py` as your starting point. It:
- Listens on `POST /aloha-tool-call`.
- Validates workspace bounds before motion.
- Calls Interbotix/ALOHA APIs to move arms and control grippers.
- Returns JSON results to the console.

Run it:

```bash
python gpt5-aloha-live/examples/aloha_bridge.py
```

Mac-only local dev (no robot):

```bash
python gpt5-aloha-live/examples/mock_bridge.py
# ensure REACT_APP_ROBOT_ENDPOINT=http://localhost:8081 in live-api-console/.env
```

## Step 5 — Bring‑Up Sequence

1) Start Interbotix drivers (adjust models/names):

```bash
ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
  robot_model:=vx300s robot_name:=puppet_left  use_gripper:=true
ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
  robot_model:=vx300s robot_name:=puppet_right use_gripper:=true
```

2) Start cameras (or use laptop webcam for MVP). If using ROS cameras, run `web_video_server` and verify MJPEG stream in a browser.

3) Start the Python bridge (see above).

4) Launch the Live API Web Console, connect to Gemini, and ensure the tool endpoint points to `http://ROBOT_PC_IP:8081/aloha-tool-call`.

5) Test prompts:
- “Show me the robot status.” → calls `get_robot_status`.
- “Move the right arm to x 0.30, y 0.10, z 0.20 meters.” → calls `move_to_position`.
- “Open the left gripper.” → calls `control_gripper`.
- “Pick up the red cup and place it in the blue bowl.” → sequence of calls.

## Safety

- Enforce workspace limits in the bridge: X[0.15,0.55], Y[-0.35,0.35], Z[0.05,0.45] (tune for your setup).
- Move slowly and keep a pre‑grasp Z offset; avoid sudden changes.
- Keep an E‑stop within reach and maintain line of sight.
- Encourage grounding: Ask Gemini to call `get_robot_status` before moving.

## Troubleshooting

- ROS topics: `ros2 topic list | grep puppet`, `ros2 topic echo /puppet_left/joint_states`.
- Bridge health:

```bash
curl -X POST http://ROBOT_PC_IP:8081/aloha-tool-call \
  -H 'Content-Type: application/json' \
  -d '{"name":"get_robot_status","args":{},"id":"t"}'
```

- Video: Load the MJPEG URL directly in a browser; if it renders, the canvas method should work. Ensure HTTPS/camera permissions if your console runs on HTTPS.

## Next Steps

- Replace `detect_objects` stub with a lightweight CV module (ArUco, color thresholding) or rely on Gemini’s visual grounding and spatial reasoning.
- Add a `move_trajectory` tool for multi‑waypoint motions.
- Expose mobile base commands as tools when you are ready.

## File Map in This Folder

- `SYSTEM_INSTRUCTION.md` — Suggested system prompt for the session.
- `examples/ALOHAControl.tsx` — Console component template for tools + toolcall handling.
- `examples/aloha_bridge.py` — Minimal Python bridge for Interbotix/ALOHA.

---

With this setup, you can control Mobile ALOHA by voice via Gemini Live API, no training required. Start with the MVP path above, then iterate on perception and safety.
