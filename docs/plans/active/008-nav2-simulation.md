# Nav2 click-to-go simulation

2026-09-08. Implement a separate simulation launch combining existing SLAM/Gazebo
with standard Nav2 planner, controller, behaviors, navigator, velocity smoother
and collision monitor. Configure conservative circular collision bounds enclosing
the offset robot footprint, known-space planning, stamped commands and sim time.
Do not implement frontier exploration, AMCL, physical navigation or new firmware.
Existing WASD-only and SLAM-only launches remain available.

Acceptance: offline configuration/launch checks; Jazzy build/test and runtime
startup; goal reached around an obstacle; canceled goal stops motion; blocked goal
fails without collision; SLAM updates while moving; repeat on a fresh launch.
Mac offline checks cannot establish Linux/Gazebo/physical acceptance.
Update the copy/paste WSL guide with dependencies, goals, cancellation and logs;
commit and push the implementation and explicitly report runtime limits.

## Implementation and offline verification

Added navigation.launch.py, nav_sim.launch.py, nav2.yaml and navigation.rviz;
registered dependencies, installation and navigation tests. Updated WSL workflow
and NAVIGATION.md with goals, cancellation, diagnostics and manual-mode switching.
Fourteen offline checks passed (3 navigation, 8 model, 3 teleop); one ROS-dependent
launch/install/clock test skipped on macOS. Bash documentation syntax and diff
whitespace checks passed. No firmware change. ROS/colcon/Gazebo is unavailable on
this Mac, so target build, new hardware-plugin test and runtime acceptance remain
pending on the PC. Do not mark this plan complete until the runtime criteria pass.
