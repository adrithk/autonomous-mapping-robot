# Initial simulation implementation

**Date:** 2026-09-07 (recorded from builder-provided evidence)
**Operator:** Adrith
**Test level:** User-observed simulation smoke test; no physical robot test
**Source revision:** Expected my_bot main at `421c7fd` (WASD implementation);
exact PC checkout hash was not captured.
**Environment:** Windows PC, WSL, ROS 2 Jazzy, Gazebo Sim and RViz.
Exact Ubuntu release, GPU/driver and installed package versions were not captured.
**Physical hardware:** No Pi, ESP32 or physical LiDAR required/connected for this test.

## Goal and existing checks

Exercise initial simulation bringup, keyboard movement and simulated laser display,
as listed in SIMULATION.md's first-run checks. This record covers those observed
checks only; it does not establish every simulation or real-hardware acceptance criterion.

## Procedure

1. Builder cloned/built the my_bot package in `/home/adrith/ros_ws`.
2. Builder supplied an earlier terminal photo showing all three CTest entries
   passing and colcon reporting 12 tests, zero errors/failures/skips.
3. Sourced Jazzy and the workspace; launched `ros2 launch my_bot bringup.launch.py`.
4. Started `ros2 run my_bot teleop_wasd --ros-args -p use_sim_time:=true
   -r cmd_vel:=/diff_drive_controller/cmd_vel` in a separate terminal.
5. Builder reported successful movement using WASD, then reported `/scan` at 10 Hz.
6. Added the Views panel and selected TopDownOrtho to make the full scan visible.

## Observations and evidence

- Gazebo displays mapping_robot in the test room with walls and an obstacle.
- RViz displays red simulated laser returns outlining room boundaries.
- Visible RViz settings: Fixed Frame `odom`, LaserScan topic `/scan`, Status `Ok`,
  Best Effort reliability, Volatile durability, Flat Squares, size 0.04 m.
- The Views panel shows TopDownOrtho and Scale 100 in the attached photo.
- Builder confirmed WASD driving worked. Movement and 10 Hz frequency are reported
  observations; the still photo itself does not measure motion or scan frequency.
- These dots are laser returns, not a SLAM occupancy map. No saved map, SLAM Toolbox,
  Nav2 mission or autonomous exploration was demonstrated.

## Result

**Pass for initial simulation smoke-test scope:** launch, user-reported teleoperation,
user-reported scan publication and visible RViz laser display.
Real motor control, odometry accuracy and robust repeated startup remain unverified.

## Anomalies and recovery

- Initial package discovery failed because a shell command escaped the home-directory
  tilde. Sourcing the workspace with its full path resolved discovery.
- A later launch showed joint_state_broadcaster spawner exit 1, triggering coordinated
  shutdown. The originating error was not captured. A clean WSL restart was suggested;
  subsequent successful operation was reported, but exact recovery steps were not recorded.
- RViz camera manipulation was confusing; adding the Views panel and selecting
  TopDownOrtho resolved the builder's display problem.
- Prior failed command output remains visible behind the working applications in
  the photo; it is not evidence that every previous launch succeeded.

## Artifact

Original builder-supplied photo, preserved without modification:

![Initial Gazebo simulation with RViz laser returns](2026-09-07-initial-simulation/IMG_8215.JPG)

## Follow-up

Capture exact Ubuntu/package versions and checkout hash; verify repeatable startup,
controller activity, odometry signs and stop behavior. Save the preferred RViz layout.
Next integrate SLAM Toolbox with simulated /scan and odometry; physical Pi/ESP32/LiDAR
bringup remains a separate validation task.
