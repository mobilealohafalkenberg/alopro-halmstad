#!/bin/bash
# Test Runner Script
echo "=================================="
echo "GEMINI-LIVE TEST SUITE"
echo "=================================="
echo ""

# Source ROS environment
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

cd test

echo "Available tests:"
echo "1. test_dry_run/test_dry_run_mode.py"
echo "2. test_async_trajectory/test_async_trajectory.py"
echo "3. test_emergency_stop/test_emergency_stop.py"
echo "4. test_safety_validator/test_safety_integration.py"
echo "5. test_arm_controller/test_arm_controller.py (requires real robot)"
echo "6. test_gripper/example_gemini_integration.py (requires real robot)"
echo ""
