# Simulation, mapping and navigation

Use Ubuntu 24.04, ROS 2 Jazzy and Gazebo Harmonic with a working graphics environment.
Complete the [build steps](README.md#build), then source ROS and the workspace in
each terminal. The Pi and ESP32 are not needed for simulation.

## Choose a mode

Run one of these launches at a time; each starts Gazebo, controllers and RViz.
Stop the previous launch and teleop before switching modes.

| Mode | Command |
|---|---|
| Drive with laser visualization | `ros2 launch my_bot bringup.launch.py` |
| Build a map while driving | `ros2 launch my_bot slam_sim.launch.py` |
| Navigate while SLAM builds the map | `ros2 launch my_bot nav_sim.launch.py` |

The local world contains four boundary walls and six interior box obstacles.
Gazebo supplies wheel feedback and simulated LiDAR; `diff_drive_controller`
publishes odometry. `/clock` and `/scan` are bridged to ROS. All simulated nodes
use `use_sim_time:=true`.

## Drive and map

With the driving or mapping launch running, use a second sourced terminal:

```bash
ros2 run my_bot teleop_wasd --ros-args \
  -p use_sim_time:=true -p frame_id:=base_link -p speed:=0.1 -p turn:=0.5 \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Hold W/S to drive forward/reverse and A/D to turn. Space or X stops; Ctrl+C exits.
The default teleop expires after 0.2 s without a key repeat. Keep the terminal focused.
Drive slowly around obstacles, then return near the starting position to inspect
map consistency. RViz shows free, occupied and unknown space with red laser returns.

Useful checks in another sourced terminal:

```bash
ros2 control list_controllers
ros2 topic hz /scan
ros2 topic echo /diff_drive_controller/odom --once
```

Both controllers should be active, scans should use frame `laser` at the configured
15 Hz, and odometry should change while driving. During mapping, also check:

```bash
ros2 lifecycle get /slam_toolbox
ros2 topic echo /map --once --field info
ros2 run tf2_ros tf2_echo map odom
```

SLAM should be active with a nonempty map and a `map → odom` transform.
`diff_drive_controller` owns `odom → base_link`; `robot_state_publisher` owns the
robot link transforms. Persistent missing-map or TF errors need investigation.

## Save a map

While SLAM is running, choose a new basename for each run:

```bash
mkdir -p ~/robot_maps
ros2 run nav2_map_server map_saver_cli -f ~/robot_maps/room_01 --ros-args \
  -p use_sim_time:=true -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0
```

Keep the YAML and its referenced occupancy image together. Reusing the basename
replaces the saved files. This exports an occupancy map; it does not save SLAM
Toolbox's resumable pose graph. Record selected runs under [results](../../../results/README.md).

## Nav2 goals

Stop teleop and the old launch, then start `nav_sim.launch.py`. Wait for the map
and Nav2 activation. Select **Nav2 Goal** in RViz, click in known free space, and
drag to choose the final heading. Use **Cancel** in Navigation 2 to cancel a goal.
Live SLAM estimates the pose in this mode, so no AMCL initial pose is needed.

NavFn plans a path, DWB tracks it, and velocity smoothing and collision monitoring
feed stamped commands to `/diff_drive_controller/cmd_vel`. Teleop publishes directly
to that controller; do not run it concurrently with Nav2.

| Setting | Configured value |
|---|---|
| Navigation speed limits | 0.20 m/s, 0.6 rad/s |
| Collision radius / padding | 0.215 m / 0.005 m |
| Wheel command timeout | 0.25 s |
| Collision-monitor scan timeout | 0.5 s |

These are simulation settings, not measured physical stopping guarantees.
Goals must lie in observed free space. The physical demonstration uses a saved
map with AMCL instead; see the [hardware guide](HARDWARE.md#mapping-and-navigation).

If only RViz is missing, open the UI without starting another simulation:

```bash
ros2 launch my_bot rviz_navigation.launch.py
```

## Model assumptions and verification

[simulation_parameters.xacro](description/simulation_parameters.xacro) centralizes
estimated mass (1.6 kg), inertias, friction and scanner properties. The scanner uses
360 samples at 15 Hz over 0.15–6 m with 0.01 m simulated range noise. Velocity control
does not reproduce the ESP32 PI loop or USB timing. GPU LiDAR needs a rendering
context even when RViz is disabled.

Initial driving and [interactive SLAM](../../../results/2026-09-08-simulated-lidar-slam.md)
are recorded. Repeatable Nav2 acceptance should cover a nearby goal, a path around
an obstacle, cancellation, an unreachable goal and a fresh restart. Record source
revision, configuration and outcomes; offline checks do not establish obstacle avoidance.

Detailed contracts and provisional TF timing settings are in
[interfaces](../../../docs/interfaces.md); earlier tuning history is retained in
[plan 008](../../../docs/plans/active/008-nav2-simulation.md).
