# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This repository contains three separate projects for controlling a Mobile ALOHA robot system:

1. **gemini-live/** - Voice-controlled robot system using Gemini 2.5 Live API
2. **live-api-web-console/** - React-based starter app for Gemini Live API websocket
3. **python_scripts/** - Python utilities using google-genai library

## Key Commands

### Robot Control System (gemini-live/)

**Starting the full system:**
```bash
# Terminal 1: Start Robot Bridge
cd gemini-live/gemini-live-api-control
./run_bridge.sh

# Terminal 2: Start Web Interface  
cd gemini-live/gemini-live-api-control/live-api-console
npm start
```

**Testing Python components:**
```bash
# Test arm controller
python3 test_arm_controller.py

# Test trajectory bridge
python3 test_trajectory_bridge.py  

# Test gripper directly
python3 example_gemini_integration.py

# Launch robot driver only
./minimal_launch.sh
```

**React development (in live-api-console/):**
```bash
npm install       # Install dependencies
npm start         # Start dev server on port 3000
npm run build     # Build for production
npm test          # Run tests
```

### Live API Web Console (live-api-web-console/)

```bash
npm install       # Install dependencies
npm start         # Start dev server
npm run build     # Build for production
```

### Python Scripts (python_scripts/)

```bash
# Uses uv for dependency management
uv sync           # Install dependencies
uv run main.py    # Run main script
```

## Architecture

### Gemini Live Robot Control Flow
```
Voice → Gemini Live API → Tool Calls → Python Bridge (8081) → ROS2 → ALOHA Hardware
         ↑                                    ↓
         └── Visual Feedback ← Camera Feed ──┘
```

### Key Components

**Frontend (React/TypeScript):**
- `live-api-console/src/lib/genai-live-client.ts` - Gemini Live WebSocket client
- `live-api-console/src/components/aloha-control/` - Robot control UI components
- Audio processing: Captures at 48kHz, resamples to 16kHz PCM16 for Gemini

**Bridge Layer (Python):**
- `bridges/bridge_aloha_real.py` - HTTP server on port 8081, translates Gemini calls
- Fire-and-forget pattern to avoid "Load failed" timeouts
- Auto-launches robot driver subprocess

**Robot Controllers (Python/ROS2):**
- `arm_controller.py` - 6-DOF arm control with auto-detection of radians/degrees
- `gripper_controller.py` - Thread-safe gripper with current-based position control (300mA)
- `camera_controller.py` - Dual RealSense D405 camera capture
- `trajectory_bridge.py` - Multi-waypoint trajectory execution with gripper coordination
- `safety_validator.py` - Workspace limits and collision prevention

### Critical Configuration

**Environment Setup:**
```bash
# Required for any robot operations
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash
```

**API Keys:**
- Gemini API key in `live-api-console/.env`: `REACT_APP_GEMINI_API_KEY=your-key`

**Port Usage:**
- 3000: React development server
- 8081: Python bridge HTTP server

**Camera Configuration:**
- LEFT gripper cam: `130322273632`
- TOP overhead cam: `130322273629`
- Merged view: 1280x480 labeled frame at 1 FPS

## Robot Specifications

- Model: ViperX 300s (vx300s), control group: follower_left
- 6 DOF joints: waist, shoulder, elbow, forearm_roll, wrist_angle, wrist_rotate
- Workspace: x,y: ±0.5m, z: 0.1-0.6m (min 0.1m for table safety)
- Gripper: current_based_position mode, 300mA limit
- Named poses: home (all zeros), ready (working position), sleep (wrist up)

## Tool Functions for Gemini

Primary trajectory tools:
- `move_arm_trajectory` - Multi-waypoint paths with gripper actions
- `detect_and_target_object` - Visual object detection (placeholder)
- `analyze_workspace` - Scene analysis (placeholder)

Standard control:
- `move_arm` - Single-point movement
- `control_gripper` - Open/close commands
- `get_arm_status` / `get_gripper_status` - State queries

## Testing and Validation

When making changes:
1. Test individual controllers with their test_*.py files
2. Verify bridge connectivity: `curl http://localhost:8081/status`
3. Check voice capture via UI volume indicators
4. Monitor browser console for tool call events
5. Watch bridge terminal for action logs

## Common Issues

- **No voice pickup**: Check browser mic permissions and volume indicators
- **Gripper not moving**: Verify robot power, USB connection, and bridge on 8081
- **"Load failed" errors**: Normal with fire-and-forget pattern
- **IK solution errors**: Check target within workspace limits (z ≥ 0.1m)

## Development Workflow

### Git Configuration

**Initial Setup:**
```bash
# Configure git identity
git config --global user.name "your-username"
git config --global user.email "your-email@example.com"

# Set up SSH key for GitHub
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub  # Copy this to GitHub Settings > SSH Keys

# Test SSH connection
ssh -T git@github.com

# Add SSH key to agent (to avoid repeated passphrase entry)
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

**Repository Setup:**
```bash
# Clone repository
git clone git@github.com:mobilealohafalkenberg/alopro-halmstad.git

# Or set remote URL to SSH
git remote set-url origin git@github.com:mobilealohafalkenberg/alopro-halmstad.git
```

### Branching and Committing Changes

**Creating a Feature Branch:**
```bash
# Create and switch to new branch
git checkout -b fix/descriptive-name

# Or branch from specific commit/branch
git checkout -b feature/new-feature dev
```

**Making Changes:**
```bash
# Check status
git status

# View changes
git diff

# Stage specific files
git add path/to/file.py

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "Brief description

Detailed explanation of changes:
- Change 1
- Change 2
- Change 3

Impact: Description of impact

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

**Pushing Changes:**
```bash
# Push new branch to remote
git push -u origin fix/descriptive-name

# Push updates to existing branch
git push
```

**Merging to Main Branch:**
```bash
# Switch to dev branch
git checkout dev

# Merge feature branch
git merge fix/descriptive-name

# Push merged changes
git push origin dev

# Delete local branch (optional)
git branch -d fix/descriptive-name

# Delete remote branch (optional)
git push origin --delete fix/descriptive-name
```

### Documentation Requirements

**CHANGELOG.md:**
- **MUST** update `CHANGELOG.md` for every bug fix, feature, or significant change
- Use the template provided in the file
- Include: Date, Task ID, Summary, Impact, Files Modified, Testing Recommendations
- Follow task ID numbering: Major (1.0), Sub-tasks (1.1, 1.2), Hotfixes (1.1.1)

**Example Entry:**
```markdown
### Task 1.1: Fix Race Condition in Position Monitoring

**Date**: 2025-10-06
**Task ID**: 1.1
**Author**: username
**Branch**: `fix/race-condition-position-monitoring`

#### Summary
Fixed critical thread safety issue...

#### Changes Made
1. Modified _start_position_monitor() method
2. Added lock protection around shared state updates

#### Impact
- Critical Safety Fix: Prevents incorrect safety validations
- Thread Safety: Eliminates race condition
```

### Code Review Checklist

Before committing:
- [ ] Code follows existing style and conventions
- [ ] All tests pass (run relevant test_*.py files)
- [ ] CHANGELOG.md updated with detailed entry
- [ ] No sensitive data (API keys, passwords) in commits
- [ ] Thread safety considered for concurrent operations
- [ ] Safety constraints validated for robot movements
- [ ] Error handling added for edge cases
- [ ] Comments added for complex logic

### SSH Troubleshooting

**Permission denied (publickey):**
```bash
# Verify SSH key is added to GitHub
ssh -T git@github.com

# If fails, add key to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Verify correct remote URL
git remote -v
# Should show: git@github.com:mobilealohafalkenberg/alopro-halmstad.git
```

**Wrong remote URL:**
```bash
# Fix HTTPS to SSH
git remote set-url origin git@github.com:mobilealohafalkenberg/alopro-halmstad.git

# Fix incorrect username in SSH URL
git remote set-url origin git@github.com:mobilealohafalkenberg/alopro-halmstad.git
```