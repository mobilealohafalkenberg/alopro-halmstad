#!/usr/bin/env python3
import os
import cv2
import time
import argparse
import asyncio
from typing import Any, Dict

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")


# ---- Tool: holding_pen(bool) -> string ----
HOLDING_PEN_DECL = types.FunctionDeclaration(
    name="holding_pen",
    description="Return a fixed string indicating whether the person is holding a pen.",
    parameters=types.Schema(
        type="object",
        properties={
            "is_holding": types.Schema(type="boolean", description="True if holding a pen.")
        },
        required=["is_holding"],
    ),
)
TOOLS = [types.Tool(function_declarations=[HOLDING_PEN_DECL])]

SYSTEM_INSTRUCTION = (
    "You are a real-time pen detection assistant. Continuously monitor the video feed. "
    "IMMEDIATELY call holding_pen() whenever the pen status changes (appears or disappears). "
    "Call the function every time you detect a change. Be responsive and active."
)

DEFAULT_PROMPT = (
    "Start monitoring now. Call holding_pen() right away with current status, "
    "then call it again every time the pen appears or disappears. React to every change immediately."
)

def jpeg_bytes_from_bgr(frame) -> bytes:
    ok, buf = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok:
        raise RuntimeError("JPEG encode failed")
    return buf.tobytes()

async def webcam_streamer(session, camera_index: int, fps: float):
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam index {camera_index}")
    try:
        delay = 1.0 / max(fps, 0.1)
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            h, w = frame.shape[:2]
            if max(h, w) > 640:
                scale = 640.0 / max(h, w)
                frame = cv2.resize(frame, (int(w*scale), int(h*scale)))
            data = jpeg_bytes_from_bgr(frame)
            await session.send_realtime_input(
                video=types.Blob(data=data, mime_type="image/jpeg")
            )
            frame_count += 1
            if frame_count % 30 == 0:  # Every ~10 seconds at 3 fps
                # Send a reminder prompt to keep the model active
                reminder = types.Content(role="user", parts=[types.Part(text="Continue monitoring for pen changes.")])
                await session.send_client_content(turns=[reminder], turn_complete=True)
            await asyncio.sleep(delay)
    finally:
        cap.release()

async def send_initial_prompt(session, prompt_text: str):
    content = types.Content(role="user", parts=[types.Part(text=prompt_text)])
    await session.send_client_content(turns=[content], turn_complete=True)

async def handle_tool_call(session, tool_call_msg):
    """
    tool_call_msg.function_calls is a list of function call objects.
    We reply with types.FunctionResponse for each, matched by id.
    """
    responses = []
    for fn in getattr(tool_call_msg, "function_calls", []) or []:
        name = fn.name
        call_id = fn.id
        args: Dict[str, Any] = dict(fn.args or {})
        if name == "holding_pen":
            is_holding = bool(args.get("is_holding", False))
            timestamp = time.strftime("%H:%M:%S")
            result = f"[{timestamp}] Pen detected: {'YES' if is_holding else 'NO'}"
            print(f"\n🔧 Function called: holding_pen(is_holding={is_holding})")
            print(f"   Response: {result}")
            responses.append(types.FunctionResponse(name=name, id=call_id, response={"result": result}))
        else:
            responses.append(types.FunctionResponse(name=name, id=call_id, response={"error": f"unsupported tool: {name}"}))
    if responses:
        await session.send_tool_response(function_responses=responses)

async def receiver(session):
    async for message in session.receive():
        # Tool call from server?
        if getattr(message, "tool_call", None):
            await handle_tool_call(session, message.tool_call)
            continue
        # Model text output
        if message.server_content and message.server_content.model_turn:
            for p in (message.server_content.model_turn.parts or []):
                if p.text:
                    print(f"Model: {p.text}", flush=True)
        # Binary audio chunks (if you request AUDIO) would come in message.data

async def main():
    parser = argparse.ArgumentParser(description="Gemini Live webcam + holding_pen tool")
    parser.add_argument("--model", default="gemini-live-2.5-flash-preview",
                        help="Live-capable model, e.g., gemini-live-2.5-flash-preview "
                             "or gemini-2.5-flash-preview-native-audio-dialog")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--fps", type=float, default=3.0)
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT)
    parser.add_argument("--text-only", action="store_true")
    args = parser.parse_args()

    api_key = (os.getenv("GEMINI_API_KEY")
               or os.getenv("GOOGLE_API_KEY")
               or os.getenv("GOOGLE_GENAI_KEY"))
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY")

    client = genai.Client(api_key=api_key)
    config = types.LiveConnectConfig(
        response_modalities=["TEXT"],
        system_instruction=SYSTEM_INSTRUCTION,
        tools=TOOLS,
        temperature=0.2,
    )
    
    print(f"🎥 Starting Gemini Live session with model: {args.model}")
    print(f"📹 Camera index: {args.camera}, FPS: {args.fps}")
    print("🔍 Monitoring for pen detection...")
    print("   Hold up a pen and put it down to test detection")
    print("   Press Ctrl+C to stop\n")

    async with client.aio.live.connect(model=args.model, config=config) as session:
        tasks = [asyncio.create_task(receiver(session))]
        if not args.text_only:
            tasks.append(asyncio.create_task(webcam_streamer(session, args.camera, args.fps)))
        await send_initial_prompt(session, args.prompt)
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting…")
