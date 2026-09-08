# Simulation SLAM Toolbox and obstacle room

Date: 2026-09-07. Status: implemented; WSL runtime validation pending.

Scope: extend the sibling my_bot test room to six interior boxes; add a separate
slam_sim.launch.py using the standard Jazzy online_async_launch.py, /scan,
base_link/odom/map frames, simulation time and 5 cm map resolution. Add RViz
occupancy-map display with an overhead view and manual map-saving instructions.
Keep physical hardware, Nav2 navigation and autonomous exploration out of this step.

Verification: eight offline model/configuration/world tests and three WASD tests
passed. Tests check scan ranges, frames/clock, map QoS, obstacle count/nonoverlap,
spawn clearance and Python/XML/YAML syntax. ROS/Gazebo is unavailable on this Mac;
the previous builder-observed simulation result does not validate this new SLAM launch.

Acceptance remaining on WSL: update/build/test, start only slam_sim.launch.py,
confirm SLAM active and /map plus map->odom, drive a loop around obstacles, inspect
map consistency, save a YAML/image and record the result. Commands are in my_bot/SLAM.md.
No firmware changes in this step. Physical watchdog and Pi integration remain pending.

## Repository consolidation — 2026-09-07

The full ROS package is now in `ros_ws/src/my_bot` in this repository. Earlier
sibling-package references are historical. Source behavior and pending physical
acceptance are unchanged. See [current status](../../../ROADMAP.md).
