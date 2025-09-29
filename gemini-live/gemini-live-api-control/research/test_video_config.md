# Video Detection Configuration Test

## Manual Configuration Steps

Since the automatic configuration isn't working properly, try this manual approach:

### 1. Before Connecting (in Settings Panel):

**System Instructions:**
```
You are analyzing a LIVE VIDEO STREAM from a webcam. You CAN SEE the video. You have visual capabilities. When you receive video frames, analyze them and call the person_wears_glasses function. You must call person_wears_glasses(wearing_glasses=true) if you see glasses on a person's face, or person_wears_glasses(wearing_glasses=false) if you don't. Do not respond with text saying you cannot see. You have video input and must use it.
```

**Function Declaration:**
Add this in the function declarations section:
```json
{
  "name": "person_wears_glasses",
  "description": "Report if person is wearing glasses",
  "parameters": {
    "type": "object",
    "properties": {
      "wearing_glasses": {
        "type": "boolean",
        "description": "True if wearing glasses"
      }
    },
    "required": ["wearing_glasses"]
  }
}
```

### 2. After Connecting:

1. Make sure webcam is enabled (you should see yourself in the video)
2. Check the console for `client.realtimeInput: video` messages
3. Type in the text box: "Look at the video and tell me if I'm wearing glasses"

## Debugging Checklist:

- [ ] Model is `gemini-2.0-flash-exp` (supports video)
- [ ] Webcam permission granted
- [ ] Video stream visible in UI
- [ ] `client.realtimeInput: video` messages in console
- [ ] System instructions explicitly mention video analysis
- [ ] Function declaration is present
- [ ] Response modality is set to TEXT

## Alternative Test:

If glasses detection doesn't work, try a simpler test:
1. Set system instructions to: "Describe what you see in the video"
2. Remove all function declarations
3. Connect and see if the model describes the video content

This will confirm if video processing is working at all.