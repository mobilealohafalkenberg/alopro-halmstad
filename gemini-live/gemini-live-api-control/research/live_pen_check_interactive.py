#!/usr/bin/env python3
import os
import cv2
import time
import argparse
import asyncio
from typing import Any, Dict
from datetime import datetime

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Store last detection state to track changes
last_pen_state = None
last_detection_time = time.time()

# ---- Tool: holding_pen(bool) -> string ----
HOLDING_PEN_DECL = types.FunctionDeclaration(
    name="holding_pen",
    description="Report whether a pen is currently visible in the video feed.",
    parameters=types.Schema(
        type="object",
        properties={
            "is_holding": types.Schema(type="boolean", description="True if pen is visible.")
        },
        required=["is_holding"],
    ),
)
TOOLS = [types.Tool(function_declarations=[HOLDING_PEN_DECL])]

SYSTEM_INSTRUCTION = (
    "You are a pen detection system. Your ONLY job is to call holding_pen() function. "
    "Call it immediately when asked, and call it again whenever the pen status changes. "
    "Do not wait. React instantly to changes. Keep watching actively."
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
            await asyncio.sleep(delay)
    finally:
        cap.release()

async def prompt_sender(session):
    """Periodically send prompts to keep the model actively checking"""
    await asyncio.sleep(2)  # Initial delay
    
    prompts = [
        "Check for pen now",
        "Is there a pen?",
        "Update pen status",
        "Check again",
        "Report current pen status",
    ]
    
    prompt_idx = 0
    while True:
        global last_detection_time
        # Send a prompt every 3 seconds if no recent detection
        if time.time() - last_detection_time > 3:
            prompt = prompts[prompt_idx % len(prompts)]
            content = types.Content(role="user", parts=[types.Part(text=prompt)])
            await session.send_client_content(turns=[content], turn_complete=True)
            print(f"📝 Sending prompt: {prompt}")
            prompt_idx += 1
        await asyncio.sleep(3)

async def handle_tool_call(session, tool_call_msg):
    global last_pen_state, last_detection_time
    responses = []
    for fn in getattr(tool_call_msg, "function_calls", []) or []:
        name = fn.name
        call_id = fn.id
        args: Dict[str, Any] = dict(fn.args or {})
        if name == "holding_pen":
            is_holding = bool(args.get("is_holding", False))
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            
            # Check if state changed
            state_changed = last_pen_state != is_holding
            if state_changed:
                emoji = "✅" if is_holding else "❌"
                change_text = "CHANGED" if last_pen_state is not None else "INITIAL"
                print(f"\n{emoji} [{timestamp}] Pen {change_text}: {'DETECTED' if is_holding else 'NOT DETECTED'}")
            else:
                print(f"  [{timestamp}] Same state: {'pen visible' if is_holding else 'no pen'}")
            
            last_pen_state = is_holding
            last_detection_time = time.time()
            
            result = f"Pen {'detected' if is_holding else 'not detected'}"
            responses.append(types.FunctionResponse(name=name, id=call_id, response={"result": result}))
    if responses:
        await session.send_tool_response(function_responses=responses)

async def receiver(session):
    async for message in session.receive():
        # Tool call from server?
        if getattr(message, "tool_call", None):
            await handle_tool_call(session, message.tool_call)
            continue
        # Model text output - suppress most of it
        if message.server_content and message.server_content.model_turn:
            for p in (message.server_content.model_turn.parts or []):
                if p.text and len(p.text.strip()) > 50:  # Only show longer responses
                    print(f"Model: {p.text[:100]}...", flush=True)

async def main():
    parser = argparse.ArgumentParser(description="Interactive Gemini Live pen detection")
    parser.add_argument("--model", default="models/gemini-live-2.5-flash-preview")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--fps", type=float, default=5.0)
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
        temperature=0.1,  # Lower temperature for more consistent detection
    )
    
    print(f"🎥 Starting Interactive Pen Detection")
    print(f"📹 Camera: {args.camera}, FPS: {args.fps}")
    print("="*50)
    print("Instructions:")
    print("  1. Show and hide a pen to see detections")
    print("  2. The system will check every few seconds")
    print("  3. Look for ✅ (pen detected) and ❌ (no pen)")
    print("  4. Press Ctrl+C to stop")
    print("="*50)

    async with client.aio.live.connect(model=args.model, config=config) as session:
        # Send initial prompt
        initial = types.Content(role="user", parts=[types.Part(text="Start detecting pen now. Call holding_pen immediately.")])
        await session.send_client_content(turns=[initial], turn_complete=True)
        
        tasks = [
            asyncio.create_task(receiver(session)),
            asyncio.create_task(prompt_sender(session))
        ]
        if not args.text_only:
            tasks.append(asyncio.create_task(webcam_streamer(session, args.camera, args.fps)))
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")