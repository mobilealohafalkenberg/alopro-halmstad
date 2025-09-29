# Gemini Live API Pen Detection with Python Bridge

## Overview
This setup uses the Google Gemini Live API Web Console (React/TypeScript) to handle the WebSocket connection and video streaming, while Python processes the function calls.

## Architecture
```
┌─────────────────┐     WebSocket      ┌────────────────┐
│                 │◄──────────────────►│  Gemini Live   │
│  React App      │                    │      API       │
│  (localhost:    │     Video Stream   │                │
│    3000)        │───────────────────►│  Processes     │
│                 │                    │  video & calls │
│                 │◄───────────────────│  holding_pen() │
└────────┬────────┘     Tool Calls    └────────────────┘
         │
         │ HTTP POST
         │ (tool calls)
         ▼
┌─────────────────┐
│  Python Server  │
│  (localhost:    │
│    8081)        │
│                 │
│  - Process      │
│    detections   │
│  - Trigger      │
│    actions      │
└─────────────────┘
```

## Setup Instructions

### 1. Start the React Web Console
```bash
cd live-api-console
npm start
# Opens at http://localhost:3000
```

### 2. Start the Python Bridge Server
```bash
uv run pen_detection_bridge.py --server
# Runs at http://localhost:8081
```

### 3. Configure the React App
In the React app at http://localhost:3000:
1. Click "Connect" to establish WebSocket connection to Gemini Live API
2. Allow camera access when prompted
3. The app will automatically send video frames to Gemini

### 4. Add Pen Detection Component (Optional)
To add the visual pen detection component to the React app:

Edit `live-api-console/src/App.tsx` and add:
```tsx
import { PenDetection } from './components/pen-detection/PenDetection';

// In the JSX, add:
<PenDetection />
```

## How It Works

1. **Video Capture**: React app captures webcam frames
2. **Streaming**: Frames are sent to Gemini Live API via WebSocket
3. **AI Processing**: Gemini analyzes frames and calls `holding_pen(true/false)`
4. **Tool Calls**: React app receives tool calls and forwards to Python
5. **Python Actions**: Python server processes detections and triggers actions

## Python Actions

Edit `pen_detection_bridge.py` to customize what happens when a pen is detected:

```python
def pen_detected_action():
    """Called when pen is detected"""
    # Your custom code here:
    # - Save screenshot
    # - Start recording
    # - Send notification
    # - Control IoT devices
    # - Log to database
    # etc.

def pen_removed_action():
    """Called when pen is removed"""
    # Your custom code here
```

## API Endpoints

Python server provides:
- `GET http://localhost:8081/status` - Check server status
- `POST http://localhost:8081/tool-call` - Receive tool calls from React

## Troubleshooting

1. **Port already in use**: Change port in `pen_detection_bridge.py` and `use-pen-detection.ts`
2. **Camera not working**: Check browser permissions for localhost:3000
3. **No detections**: Ensure good lighting and pen is clearly visible
4. **Python not receiving calls**: Check CORS and that both servers are running

## Features

- ✅ Real-time pen detection
- ✅ Python function triggers
- ✅ Visual feedback in browser
- ✅ Detection counter
- ✅ Connection status monitoring
- ✅ Customizable Python actions

## Limitations

- 2-minute session limit for video (unless using compression)
- Requires manual turn triggering (React app should send periodic messages)
- WebSocket connection may timeout after ~10 minutes