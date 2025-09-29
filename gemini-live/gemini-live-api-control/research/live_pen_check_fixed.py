#!/usr/bin/env python3
import os
import cv2
import time
import argparse
import asyncio
from typing import Any, Dict, Optional

from google import genai
from google.genai import types
from dotenv import load_dotenv

# ----------------------------
# Env / API key
# ----------------------------
load_dotenv()
API_KEY = (
    os.getenv("GEMINI_API_KEY")
    or os.getenv("GOOGLE_API_KEY")
    or os.getenv("GOOGLE_GENAI_KEY")
)

# ----------------------------
# Tool: holding_pen(bool) -> str
# ----------------------------
HOLDING_PEN_DECL = types.FunctionDeclaration(
    name="holding_pen",
    description="Report whether the person is holding a pen.",
    parameters=types.Schema(
        type="object",
        properties={
            "is_holding": types.Schema(
                type="boolean", description="True if the user is holding a pen."
            )
        },
        required=["is_holding"],
    ),
)
TOOLS = [types.Tool(function_declarations=[HOLDING_PEN_DECL])]

# The model should ONLY call the function each turn; no text.
SYSTEM_INSTRUCTION = (
    "You see a live video stream of the user. On every turn, call only the function "
    "`holding_pen` with your best current guess: is_holding=true or false. "
    "Do not send text; only the function call."
)

# ----------------------------
# Globals (simple dedupe)
# ----------------------------
last_holding: Optional[bool] = None

# ----------------------------
# Video helpers
# ----------------------------
def jpeg_bytes_from_bgr(frame) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()

async def webcam_streamer(session, camera_index: int, fps: float):
    """
    Capture frames and stream them to the Live API as per-frame JPEG blobs.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open webcam index {camera_index}. "
            "On macOS, grant Camera permission to your terminal/VS Code in "
            "System Settings → Privacy & Security → Camera."
        )

    delay = 1.0 / max(fps, 0.1)
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.05)
                continue

            # Light downscale to reduce bandwidth
            h, w = frame.shape[:2]
            if max(h, w) > 640:
                scale = 640.0 / max(h, w)
                frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

            data = jpeg_bytes_from_bgr(frame)
            await session.send_realtime_input(
                video=types.Blob(data=data, mime_type="image/jpeg")
            )
            await asyncio.sleep(delay)
    finally:
        cap.release()

# ----------------------------
# Turn pinger: starts a new "turn" periodically
# ----------------------------
async def turn_pinger(session, period_sec: float = 1.0):
    """
    The model only reasons & can call tools during a 'turn'.
    This pings a new turn periodically so it re-evaluates latest frames.
    """
    # Small initial delay to let video frames start flowing
    await asyncio.sleep(0.5)
    
    while True:
        # Send minimal content to trigger a new turn
        content = types.Content(role="user", parts=[types.Part(text="Check")])
        await session.send_client_content(turns=[content], turn_complete=True)
        await asyncio.sleep(period_sec)

# ----------------------------
# Initial prompt (optional)
# ----------------------------
async def send_initial_prompt(session, prompt_text: str):
    content = types.Content(role="user", parts=[types.Part(text=prompt_text)])
    await session.send_client_content(turns=[content], turn_complete=True)

# ----------------------------
# Tool call handler
# ----------------------------
async def handle_tool_call(session, tool_call_msg):
    global last_holding
    responses = []
    for fn in getattr(tool_call_msg, "function_calls", []) or []:
        name = getattr(fn, "name", "")
        call_id = getattr(fn, "id", None)
        args: Dict[str, Any] = dict(getattr(fn, "args", {}) or {})

        if name == "holding_pen":
            is_holding = bool(args.get("is_holding", False))
            # Dedupe: only print when the state changes
            if is_holding != last_holding:
                last_holding = is_holding
                ts = time.strftime("%H:%M:%S")
                emoji = "✅" if is_holding else "❌"
                msg = f"[{ts}] Pen {'DETECTED' if is_holding else 'NOT DETECTED'}"
                print(f"\n{emoji} State changed: {msg}", flush=True)

            # Always send a function response to complete the tool call.
            responses.append(
                types.FunctionResponse(
                    name=name,
                    id=call_id,
                    response={"result": "ok"},
                )
            )
        else:
            responses.append(
                types.FunctionResponse(
                    name=name,
                    id=call_id,
                    response={"error": f"unsupported tool: {name}"},
                )
            )

    if responses:
        await session.send_tool_response(function_responses=responses)

# ----------------------------
# Receiver: handles tool calls and any model text
# ----------------------------
async def receiver(session):
    async for message in session.receive():
        # Tool call?
        if getattr(message, "tool_call", None):
            await handle_tool_call(session, message.tool_call)
            continue

        # Model text (we asked for function-calls only, but just in case)
        if message.server_content and message.server_content.model_turn:
            for p in (message.server_content.model_turn.parts or []):
                if p.text and p.text.strip():
                    # Suppress most text output since we want function calls only
                    pass

# ----------------------------
# Main
# ----------------------------
async def main():
    parser = argparse.ArgumentParser(description="Gemini Live webcam pen detection (continuous loop)")
    parser.add_argument(
        "--model",
        default="models/gemini-live-2.5-flash-preview",
        help="Live-capable model"
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera index (default 0)")
    parser.add_argument("--fps", type=float, default=3.0, help="Frame rate to send (default 3 FPS)")
    parser.add_argument("--text-only", action="store_true", help="Run without webcam (debug)")
    parser.add_argument("--turn-period", type=float, default=1.0, help="Seconds between turns (default 1.0)")
    args = parser.parse_args()

    if not API_KEY:
        raise SystemExit("Set GEMINI_API_KEY (or GOOGLE_API_KEY / GOOGLE_GENAI_KEY)")

    client = genai.Client(api_key=API_KEY)

    # Use top-level fields on LiveConnectConfig (non-deprecated)
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        tools=TOOLS,
        system_instruction=SYSTEM_INSTRUCTION,
        temperature=0.2,
    )

    print(f"🎥 Starting Gemini Live Pen Detection (Continuous)")
    print(f"📹 Camera: {args.camera}, FPS: {args.fps}")
    print(f"🔄 Turn interval: {args.turn_period} seconds")
    print("="*50)
    print("The model will check for pen every second.")
    print("You'll see output only when state changes:")
    print("  ✅ = Pen detected")
    print("  ❌ = No pen detected")
    print("Press Ctrl+C to stop")
    print("="*50)

    if args.text_only:
        print("⚠️  Running in --text-only mode (no webcam)\n")

    async with client.aio.live.connect(model=args.model, config=config) as session:
        tasks = [
            asyncio.create_task(receiver(session)),
            asyncio.create_task(turn_pinger(session, period_sec=args.turn_period)),
        ]
        if not args.text_only:
            tasks.append(asyncio.create_task(webcam_streamer(session, args.camera, args.fps)))

        # Optional initial prompt to get the first turn flowing immediately.
        await send_initial_prompt(session, "Start detecting")

        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting…")