# Camera Permissions for macOS

The script requires camera access on macOS. If you see errors like:
- "OpenCV: not authorized to capture video"
- "OpenCV: camera failed to properly initialize!"

## Solution:

1. **Grant Terminal/IDE camera permission:**
   - Go to System Settings > Privacy & Security > Camera
   - Enable camera access for Terminal, iTerm2, VS Code, or whichever terminal/IDE you're using

2. **Test without camera first:**
   ```bash
   uv run live_pen_check.py --text-only --model models/gemini-live-2.5-flash-preview
   ```

3. **Once permissions are granted, run with camera:**
   ```bash
   uv run live_pen_check.py --model models/gemini-live-2.5-flash-preview
   ```

## Additional Options:
- `--camera 1` to use a different camera index if you have multiple cameras
- `--fps 5` to increase frame rate (default is 3 fps)
- `--prompt "custom prompt"` to use a different initial prompt