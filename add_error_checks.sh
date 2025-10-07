#!/bin/bash

# Add ERROR check to move_to_position (after line 496)
sed -i '496a\
\        # Check if system is in ERROR state (e.g., after emergency stop)\
        with self.state_lock:\
            if self.current_state == ArmState.ERROR:\
                return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}\
' gemini-live/arm_controller.py

# Add initialization and ERROR check to move_to_pose (after line 614 - after the pose_name check)
sed -i '618a\
\        if not self.initialized:\
            return {"success": False, "error": "Not initialized", "state": "unknown"}\
\
        # Check if system is in ERROR state (e.g., after emergency stop)\
        with self.state_lock:\
            if self.current_state == ArmState.ERROR:\
                return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}\
' gemini-live/arm_controller.py

# Add initialization and ERROR check to execute_trajectory (after line 672 - after the docstring)
sed -i '677a\
        if not self.initialized:\
            return {"success": False, "error": "Not initialized", "state": "unknown"}\
\
        # Check if system is in ERROR state (e.g., after emergency stop)\
        with self.state_lock:\
            if self.current_state == ArmState.ERROR:\
                return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}\
' gemini-live/arm_controller.py

# Add initialization and ERROR check to set_speed (after line 1117 - after the docstring)
sed -i '1126a\
        if not self.initialized:\
            return {"success": False, "error": "Not initialized", "state": "unknown"}\
\
        # Check if system is in ERROR state (e.g., after emergency stop)\
        with self.state_lock:\
            if self.current_state == ArmState.ERROR:\
                return {"success": False, "error": "System in ERROR state. Call resume_after_stop() to recover.", "state": "error"}\
' gemini-live/arm_controller.py

echo "All ERROR state checks added successfully"
