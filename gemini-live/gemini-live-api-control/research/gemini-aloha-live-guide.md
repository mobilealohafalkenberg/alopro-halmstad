# 🤖 Gemini + Mobile ALOHA: A Simplified Integration Guide

**Our Goal**: Control the Mobile ALOHA robot using natural language. We will use the Gemini Live API as the "brain" to understand commands and a live video feed, and a simple Python script as the "hands" to execute precise robot movements.

---

## ⚙️ Core Principles

This guide follows a simple philosophy:

1.  **Gemini is the Brain**: Gemini's built-in spatial understanding will analyze the live camera feed to locate objects. We will not write any custom computer vision models.
2.  **Python is the Hands**: Our Python script will expose a few simple, precise functions for Gemini to use (like "move arm" or "close gripper"). It does not need to know *what* it is picking up, only *where* to move.
3.  **Simplicity**: We will only build what is necessary to achieve the core goal, starting with the safest, read-only functions first.

---

## 🏗️ System Architecture

The system has three parts that talk to each other:

```
┌─────────────────┐      WebSocket       ┌──────────────────┐
│  Gemini Live    │◄───────────────────► │  Live API Console  │
│  API (The Brain)│ (Video In, Tools Out)│  (React Frontend)  │
└─────────────────┘                      └──────────────────┘
                                                 │
                                           HTTP  │ (Tool Calls)
                                                 ▼
                                         ┌──────────────────┐
                                         │  aloha_bridge.py │
                                         │ (The Hands)      │
                                         └──────────────────┘
                                                 │
                                            ROS2 │ (Motor Commands)
                                                 ▼
                                         ┌──────────────────┐
                                         │  Mobile ALOHA HW │
                                         └──────────────────┘
```

---

## 🛠️ The Plan: A Phased Approach

We will build this system in three safe, logical phases.

### Phase 1: Build the "Hands" (Read-Only)

First, we'll create the Python bridge and implement a single, safe, read-only function. This lets us test the robot connection without any movement.

**1. Create `aloha_bridge.py`:**
This script will run an HTTP server and listen for commands from our frontend.

**2. Implement `get_robot_status()`:**
This function will connect to the robot via ROS, read the current positions of the arms and grippers, and return them as JSON.

**3. Test with `curl`:**
We will verify the bridge is working by calling it directly from the command line:
```bash
curl -X POST http://localhost:8081/aloha-tool-call \
  -H "Content-Type: application/json" \
  -d '{"name": "get_robot_status", "args": {}, "id": "test01"}'
```
A successful test means the bridge can communicate with the robot.

### Phase 2: Connect the "Brain" to the "Eyes"

Next, we'll update the React frontend to define the tools for Gemini and connect it to the bridge we just built.

**1. Define the Toolset:**
In a new `ALOHAControl.tsx` component, we will define the *only* three tools Gemini needs:
   - `get_robot_status()`: Gets the current state of the robot's arms and grippers.
   - `move_to_position(arm, x, y, z)`: Moves a specified arm to an absolute coordinate.
   - `control_gripper(arm, action)`: Opens or closes a specified gripper.

**2. Refine the System Instruction:**
We will give Gemini a clear prompt that tells it how to use these tools:
```
You are controlling a Mobile ALOHA robot with dual arms. Your goal is to complete tasks given by the user.

1. Analyze the live video feed to identify objects and their locations.
2. Use `get_robot_status` to understand the current positions of the robot's arms.
3. Formulate a plan to move the arms and grippers to complete the user's instruction.
4. Execute the plan by calling `move_to_position` and `control_gripper`.
5. Always specify which arm ("left" or "right") to use.

Coordinate system: X=forward, Y=left, Z=up from the robot's base (0,0,0).
```

**3. Test the Connection:**
We will run the frontend and ask Gemini, "What is the robot's status?". Gemini should call our `get_robot_status` tool, which will be sent to the Python bridge. The result from the robot should then be displayed in the UI.

### Phase 3: Enable Movement

With the read-only connection verified, we will now implement the functions that physically move the robot.

**1. Implement `move_to_position()` and `control_gripper()` in `aloha_bridge.py`:**
We will add the code that makes the robot's arms and grippers move based on the arguments provided by Gemini.

**2. Include Safety Checks:**
We will add workspace limits inside the bridge to prevent Gemini from sending the robot arms to positions that are out of bounds or unsafe.

**3. Full End-to-End Test:**
This is the final test. We will start all systems and give the command: **"Pick up the banana and put it in the bowl."**

We will watch as Gemini performs the task:
1.  Gemini sees the banana and bowl in the video.
2.  It calls `get_robot_status()` to know where the arms are.
3.  It calls `move_to_position()` to move the arm above the banana.
4.  It calls `move_to_position()` again to lower the arm.
5.  It calls `control_gripper(action="close")` to grasp the banana.
6.  It continues with more `move_to_position` and `control_gripper` calls to complete the task.

---

## 🚀 Next Steps

This guide provides the roadmap. The immediate next step is to begin **Phase 1**: creating the `aloha_bridge.py` file and implementing the `get_robot_status` function.

```