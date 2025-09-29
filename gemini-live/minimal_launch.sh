#!/bin/bash

# Minimal launch for JUST follower_left arm
# No cameras, no base, no other arms

echo "=========================================="
echo "MINIMAL Launch - follower_left arm ONLY"
echo "=========================================="

# Set environment
source /opt/ros/humble/setup.bash
source ~/interbotix_ws/install/setup.bash

# Launch ONLY the follower_left arm driver
ros2 launch interbotix_xsarm_control xsarm_control.launch.py \
    robot_model:=vx300s \
    robot_name:=follower_left \
    #mode_configs:=$HOME/interbotix_ws/src/aloha/config/follower_modes_left.yaml \
    use_rviz:=false \
    use_sim:=false