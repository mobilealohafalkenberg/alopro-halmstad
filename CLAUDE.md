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
# All tests are organized in gemini-live/test/ directory
cd gemini-live/test

# Test arm controller
python3 test_arm_controller/test_arm_controller.py

# Test trajectory bridge
python3 test_trajectory_bridge/test_trajectory_bridge.py

# Test gripper directly
python3 test_gripper/example_gemini_integration.py

# Launch robot driver only (from gemini-live-api-control/)
cd ../gemini-live-api-control
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

### Test Directory Structure

All tests are organized under `gemini-live/test/` with subdirectories named after the component being tested:

```
gemini-live/test/
├── test_arm_controller/
│   └── test_arm_controller.py
├── test_trajectory_bridge/
│   └── test_trajectory_bridge.py
├── test_gripper/
│   └── example_gemini_integration.py
└── test_camera/
    └── test_camera_controller.py
```

**Creating New Tests:**
- Create a subdirectory under `gemini-live/test/` named `test_<component>`
- Place test files within that subdirectory
- Example: Testing safety_validator → `gemini-live/test/test_safety_validator/test_safety_validator.py`

**Running Tests:**
```bash
# Navigate to test directory
cd gemini-live/test

# Run specific component test
python3 test_arm_controller/test_arm_controller.py
python3 test_gripper/example_gemini_integration.py
python3 test_trajectory_bridge/test_trajectory_bridge.py
```

### Validation Checklist

When making changes:
1. Test individual controllers with their respective test files in `gemini-live/test/`
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
- [ ] All tests pass (run relevant tests from `gemini-live/test/`)
- [ ] New tests created in appropriate `gemini-live/test/test_<component>/` directory if needed
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
---

## Task Workflow and Branch Management

### Development Phases

The project is organized into 5 development phases. Each phase focuses on a specific subsystem and can be worked on independently where possible.

#### Phase 1: Arm Controller ✅ COMPLETE
**Tasks:** 1.1 - 1.14
**Focus:** Core arm movement, safety, trajectories
**Status:** Testing complete, all features validated

#### Phase 2: Gripper Controller ⏳ IN PROGRESS
**Tasks:** 2.1 - 2.x
**Focus:** Gripper control, state monitoring, arm coordination
**Status:** Basic implementation exists, needs comprehensive testing

#### Phase 3: Camera Controller 📋 PLANNED
**Tasks:** 3.1 - 3.x
**Focus:** Camera initialization, frame capture, visual integration
**Status:** Basic implementation exists, needs testing

#### Phase 4: Bridge Integration 📋 PLANNED
**Tasks:** 4.1 - 4.x
**Focus:** Gemini API integration, tool routing
**Status:** Basic implementation exists, needs comprehensive testing

#### Phase 5: System Integration 📋 PLANNED
**Tasks:** 5.1 - 5.x
**Focus:** End-to-end testing, optimization, deployment
**Status:** Not started

### Task Selection Guidelines

**Independent Tasks (Work in Any Order):**
- Most tasks within a phase can be done independently
- Tasks with "Infrastructure" or "Testing" in the name
- Documentation and refactoring tasks

**Dependent Tasks (Must Be Done First):**
- Tasks marked with "⚠️ PREREQUISITE" in CHANGELOG
- Core initialization tasks (X.1 tasks)
- Integration tasks that span multiple phases

**Priority Tasks:**
1. Phase 2 tests (gripper functionality)
2. Phase 3 tests (camera integration)  
3. Phase 4 tests (bridge tool calls)
4. Phase 5 integration tests

### Branch Naming Convention

**Format:** `<type>/<phase>-<task-id>-<brief-description>`

**Types:**
- `feature/` - New functionality
- `fix/` - Bug fixes
- `test/` - Adding or updating tests
- `refactor/` - Code refactoring
- `docs/` - Documentation updates

**Examples:**
```bash
# Phase 1 examples
git checkout -b fix/1.11-workspace-bounds
git checkout -b test/1.6-parameter-validation
git checkout -b refactor/1.10-test-infrastructure

# Phase 2 examples
git checkout -b feature/2.1-gripper-initialization
git checkout -b test/2.2-gripper-position-control
git checkout -b fix/2.3-state-monitoring

# Phase 3 examples
git checkout -b feature/3.1-camera-init
git checkout -b test/3.2-frame-capture
```

### Starting a New Task

**1. Check Dependencies:**
```bash
# Review CHANGELOG.md for task prerequisites
cat CHANGELOG.md | grep -A 10 "Task <task-id>"

# Check TEST_RESULTS.md for test requirements
cat test/TEST_RESULTS.md | grep -A 5 "Test <task-id>"
```

**2. Create Feature Branch:**
```bash
# From dev branch
git checkout dev
git pull origin dev

# Create task branch
git checkout -b <type>/<phase>-<task-id>-<description>
```

**3. Review Task Requirements:**
- Read task entry in CHANGELOG.md
- Check if test file exists in `test/` directory
- Review related code in the component directory

**4. Development Workflow:**

**TDD (Test-Driven Development) - Recommended:**
```bash
# 1. Write test first (if not exists)
cd test/test_<component>
cp template_test.py test_<feature>.py
# Edit test file with expected behavior

# 2. Run test (should fail)
python3 test_<feature>.py

# 3. Implement feature
cd ../..
# Edit component file

# 4. Run test again (should pass)
cd test/test_<component>
python3 test_<feature>.py

# 5. Refactor if needed
```

**Implementation-First Approach:**
```bash
# 1. Implement feature
# Edit component file

# 2. Create test
cd test/test_<component>
# Create test file

# 3. Validate
python3 test_<feature>.py
```

**5. Testing Your Changes:**

```bash
# Source ROS environment
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Run specific test
cd test
python3 test_<component>/test_<feature>.py

# Run all Phase tests (when available)
./run_phase<N>_tests.sh
```

**6. Document Changes:**

Update CHANGELOG.md:
```markdown
### Task <phase>.<number>: <Task Name>

**Date**: YYYY-MM-DD
**Phase**: <phase> (<Phase Name>)
**Task ID**: <phase>.<number>
**Task Name**: <Brief Name>
**Test File**: test_<component>/test_<feature>.py
**Author**: <your-name>
**Branch**: `<branch-name>`

#### Summary
<What was changed and why>

#### Changes Made
1. <Change 1>
2. <Change 2>

#### Impact
- <Impact 1>
- <Impact 2>

#### Files Modified
- `path/to/file.py` (lines X-Y)

#### Testing
Run test: `python3 test/<component>/test_<feature>.py`
```

Update TEST_RESULTS.md:
```markdown
### Test <phase>.<number>: <Feature Name>
**Test File:** `test/<component>/test_<feature>.py`
**Task:** <phase>.<number>
**Date:** YYYY-MM-DD
**Status:** ✅ PASS / ❌ FAIL / ⏳ PENDING

**What Was Tested:**
- <Test case 1>
- <Test case 2>

**Result:** <Summary>
```

**7. Commit and Push:**

```bash
# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "Task <phase>.<number>: <Brief description>

<Detailed explanation>
- Change 1
- Change 2

Test: test/<component>/test_<feature>.py
Status: <PASS/FAIL>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: <your-name> <your-email>"

# Push to remote
git push -u origin <branch-name>
```

**8. Create Pull Request:**

```bash
# Using GitHub CLI
gh pr create --title "Task <phase>.<number>: <Title>" --body "$(cat <<'EOF'
## Summary
<What this PR does>

## Changes
- Change 1
- Change 2

## Testing
- [x] Test file created: test/<component>/test_<feature>.py
- [x] All tests pass
- [x] CHANGELOG.md updated
- [x] TEST_RESULTS.md updated

## Related Tasks
- Task <phase>.<number> in CHANGELOG.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"

# Or via GitHub web UI
# Navigate to repository and click "New Pull Request"
```

### Quick Reference

**Check Current Task Status:**
```bash
# View task in CHANGELOG
grep -A 20 "Task <phase>.<number>" CHANGELOG.md

# View test results
grep -A 10 "Test <phase>.<number>" test/TEST_RESULTS.md

# Check git status
git status
git branch
```

**Common Commands:**
```bash
# Create new task branch
git checkout dev && git pull
git checkout -b <type>/<phase>-<task>-<description>

# Run tests
cd test && python3 test_<component>/test_<feature>.py

# Update documentation
# 1. Edit CHANGELOG.md - add/update task entry
# 2. Edit test/TEST_RESULTS.md - add/update test results

# Commit changes
git add <files>
git commit -m "Task <phase>.<number>: <description>

<details>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: <name> <email>"

# Push and create PR
git push -u origin <branch>
gh pr create --title "Task <phase>.<number>: <title>"
```

---
