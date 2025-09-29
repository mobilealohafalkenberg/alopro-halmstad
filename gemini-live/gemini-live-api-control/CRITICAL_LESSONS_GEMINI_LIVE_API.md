# 🚨 CRITICAL LESSONS: Gemini Live API with Vision & Function Calling

## ⚠️ MUST READ - These issues cost hours of debugging!

### 🆕 NEW CRITICAL DISCOVERY: Python Code Execution vs Tool Calls
**Date: Sep 8, 2025**
**Issue: "Load failed" errors when Gemini tries to execute Python alongside tool calls**

#### The Problem We Discovered
Gemini Live models can generate BOTH Python code execution AND tool calls simultaneously. When this happens in a browser context, you'll see:
- `executableCode: PYTHON` with `print(default_api.function_name())`
- `toolCall` with the actual function call
- Error response: `{"error": "Load failed"}`

This happens because the browser can't execute Python code, and the model gets confused waiting for both responses.

#### The Solution: Fire-and-Forget Pattern
```javascript
// ❌ WRONG - Returning bridge response directly causes "Load failed"
const res = await fetch(`${BRIDGE_URL}/endpoint`, {...});
const data = await res.json();
responses.push({ 
  name: call.name, 
  id: call.id, 
  response: data.result  // BAD: Python execution fails on this
});

// ✅ CORRECT - Always return simple success, handle bridge async
responses.push({ 
  name: call.name, 
  id: call.id, 
  response: { success: true, status: 'executed' }  // GOOD: Simple response
});

// Then update UI with bridge data (fire-and-forget)
try {
  const res = await fetch(`${BRIDGE_URL}/endpoint`, {...});
  const data = await res.json();
  // Update your UI state here, but don't send to Gemini
  setLocalState(data.result);
} catch (e) {
  console.error('Bridge error:', e);  // Non-fatal
}
```

**Key Insight:** The tool response to Gemini should be minimal and immediate. The actual bridge communication is secondary and shouldn't affect the Gemini response.

### 1. 🔴 **ALWAYS SEND TOOL RESPONSES BACK**
**THE MOST CRITICAL ISSUE:** When Gemini calls a function, you MUST send a response back, or the model will hang forever waiting.

```javascript
// ❌ WRONG - Model will hang after calling the function
client.on('toolcall', (toolCall) => {
  console.log('Function called:', toolCall);
  // Process the call but forget to respond...
});

// ✅ CORRECT - Always send response back
client.on('toolcall', (toolCall) => {
  const responses = [];
  for (const call of toolCall.functionCalls) {
    // Process the function call
    responses.push({
      name: call.name,
      id: call.id,  // CRITICAL: Must match the call ID
      response: { result: 'ok' }
    });
  }
  // CRITICAL: Send response back to complete the cycle
  client.sendToolResponse({ functionResponses: responses });
});
```

**Why this happens:** The Live API implements a request-response pattern for function calls. The model pauses execution after making a tool call and waits for your response before continuing. Without a response, it's stuck in limbo.

### 2. 🔴 **DON'T INTERRUPT THE MODEL**
Sending prompts too frequently will interrupt the model mid-response, causing chaos.

```javascript
// ❌ WRONG - Interrupts every 2 seconds
setInterval(() => {
  client.send({ text: 'Check now' });
}, 2000);

// ✅ CORRECT - Give model time to process
setInterval(() => {
  client.send({ text: 'Check now' });
}, 10000); // 10+ seconds between prompts
```

**What we saw:** The model would start processing, then get interrupted by the next prompt, never completing its task.

### 3. 🔴 **CONFIGURATION TIMING MATTERS**
Setting configuration AFTER connection often fails. Configure BEFORE connecting.

```javascript
// ❌ WRONG - Config after connection might not apply
await client.connect();
client.setConfig({ tools: [...] }); // Too late!

// ✅ CORRECT - Config before connection
client.setConfig({ tools: [...] });
await client.connect();
```

### 4. 🔴 **TELL THE MODEL IT HAS EYES**
The model needs explicit instructions that it can see video, or it will say "I have no visual capabilities."

```javascript
// ❌ WRONG - Model thinks it's text-only
systemInstruction: "Detect if person has glasses"

// ✅ CORRECT - Explicitly mention video capabilities
systemInstruction: "You are analyzing a LIVE VIDEO STREAM from a webcam. You CAN SEE the video. You have visual input. Analyze what you see and call functions based on the visual content."
```

### 5. 🔴 **VIDEO REQUIRES REALTIME INPUT**
Video must be sent via `sendRealtimeInput`, not regular messages.

```javascript
// ✅ CORRECT - Video as realtime input
await session.sendRealtimeInput({
  video: types.Blob(data=videoData, mime_type="image/jpeg")
});
```

### 6. 🔴 **DEFAULT CONFIGS OVERRIDE YOURS**
Watch out for components that set their own configs (like Altair in our case).

```javascript
// If multiple components set config, last one wins!
// Solution: Disable competing components or ensure your config loads last
```

## 📋 Complete Working Pattern

```javascript
// 1. Configure BEFORE connecting
const config = {
  tools: [{ functionDeclarations: [yourTool] }],
  systemInstruction: 'You have video input. Analyze it and call functions.',
  response_modalities: ["TEXT"]
};

// 2. Connect
await client.connect(model, config);

// 3. Handle tool calls WITH RESPONSES
client.on('toolcall', async (toolCall) => {
  const responses = [];
  
  for (const call of toolCall.functionCalls) {
    // Process the call
    handleYourFunction(call.args);
    
    // ALWAYS add response
    responses.push({
      name: call.name,
      id: call.id,
      response: { result: 'processed' }
    });
  }
  
  // ALWAYS send responses back
  client.sendToolResponse({ functionResponses: responses });
});

// 4. Send prompts sparingly
setInterval(() => {
  client.send({ text: 'Analyze the video' });
}, 10000); // 10+ second intervals
```

## 🎯 Debugging Checklist

When Gemini Live API with vision isn't working:

- [ ] Are you sending tool responses back? (Check for `client.toolResponse` in logs)
- [ ] Are you interrupting the model? (Check prompt frequency)
- [ ] Is config applied before connection?
- [ ] Does system instruction explicitly mention video/visual capabilities?
- [ ] Is video being sent? (Look for `client.realtimeInput: video` in logs)
- [ ] Are other components overriding your config?
- [ ] Is the model correct? (`gemini-live-2.5-flash-preview` for Live API)
- [ ] Are tool call IDs matching in responses?

## 💡 Signs It's Working

✅ You see `server.toolCall` in logs
✅ Followed by `client.toolResponse` 
✅ No "I cannot see" messages from model
✅ Regular pattern of call → response → call → response

## 🚫 Signs It's Broken

❌ Model says "I have no eyes" or "I cannot see"
❌ Tool calls but no responses
❌ Rapid interruptions in logs
❌ Model stops responding after first tool call
❌ Empty system instructions in settings panel

## 🔧 Our Specific Fix Sequence

1. **Removed competing Altair component** that was overriding config
2. **Added tool response handling** - THE KEY FIX
3. **Reduced prompt frequency** from 2s to 10s
4. **Explicit video instructions** in system prompt
5. **Config before connection** pattern
6. **Switched to optimized model** `gemini-live-2.5-flash-preview`
7. **Fixed "Load failed" errors** by using fire-and-forget pattern for bridge responses

## 🌉 Bridge Architecture Pattern

### The Problem
When building external control systems (robots, hardware, system control), you need a bridge between the browser and the actual system. But Gemini can get confused if responses are complex.

### The Solution: Python Bridge + Simple Responses
```
Browser (React) → Gemini API → Tool Call
    ↓
Tool Response (immediate, simple: {success: true})
    ↓
Async fetch to Python Bridge (fire-and-forget)
    ↓
Python Bridge → Actual System Control
```

### Example: Working Mac Control Bridge
```python
# Python Bridge (runs on separate port)
async def handle_tool_call(request):
    data = await request.json()
    name = data.get('name')
    
    # Execute actual system command
    if name == 'play_sound':
        subprocess.run(["afplay", f"/System/Library/Sounds/Glass.aiff"])
        
    # Return result (browser may or may not use this)
    return web.json_response({'result': {...}, 'call_id': data.get('id')})

# Enable CORS for browser access
cors = setup(app, defaults={
    '*': ResourceOptions(
        allow_credentials=True,
        expose_headers='*',
        allow_headers='*',
        allow_methods='*'
    )
})
```

```javascript
// React Component
const handleToolCall = async (toolCall) => {
  const responses = [];
  
  for (const call of toolCall.functionCalls) {
    // IMMEDIATELY respond to Gemini (prevents hang)
    responses.push({ 
      name: call.name, 
      id: call.id, 
      response: { success: true, status: 'executed' } 
    });
    
    // THEN call bridge (async, non-blocking)
    fetch(`http://localhost:8082/mac-control`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: call.name, args: call.args })
    }).catch(e => console.error('Bridge error:', e));
  }
  
  // Send simple responses back to Gemini
  client.sendToolResponse({ functionResponses: responses });
};
```

### Key Lessons from Our Success
1. **Two separate ports**: React (3000), Mock Bridge (8081), Mac Control (8082)
2. **CORS must be enabled** on Python bridges for browser access
3. **Tool responses must be simple** - complex data confuses Gemini when it's also trying to execute Python
4. **Bridge calls are optional** - if bridge is down, Gemini still works
5. **Real system effects** - We successfully controlled Mac (sounds, notifications, volume, screenshots, apps, TTS)

## 📚 References

- Live API only supports ONE response modality (text OR audio, not both)
- Session limits: 15 min audio, 2 min video (without compression)
- Tool responses are MANDATORY for function calling to work
- Native audio models have limited tool support

## 🎉 Success Story: Mac Control Demo
We successfully built a system that lets you control your Mac computer through voice/text commands using Gemini Live API:

### What We Built
- **Voice-controlled Mac**: Say "play a sound" → Mac plays sound
- **System notifications**: Visual feedback through macOS notifications  
- **Volume control**: Actually changes system volume
- **Screenshots**: Takes and saves screenshots to Desktop
- **App launcher**: Opens real applications
- **Text-to-speech**: Mac speaks back to you
- **System beeps**: Audio feedback

### The Magic Moment
After fixing the "Load failed" errors by implementing the fire-and-forget pattern, everything clicked:
1. User speaks to Gemini: "Play the glass sound"
2. Gemini calls tool: `play_sound({sound: "glass"})`
3. React immediately responds: `{success: true}`
4. Python bridge plays actual sound on Mac
5. User hears the sound! 🎉

### Proven Architecture
```
User Voice → Gemini Live API → Tool Call → React App
                                              ↓
                                    Simple Response Back
                                              ↓
                                    Python Bridge (8082)
                                              ↓
                                    Mac System Commands
                                              ↓
                                    Real World Effects!
```

This proves the pattern works for controlling ANY external system - robots, IoT devices, computers, etc.

---

**Remember:** The #1 cause of Gemini Live API function calling failures is not sending tool responses back. If your model makes a tool call and hangs, CHECK YOUR RESPONSE HANDLING FIRST!

**NEW #2 Issue:** "Load failed" errors mean Gemini is trying to execute Python code in the browser. Use the fire-and-forget pattern: respond immediately with simple success, then call your bridge asynchronously.