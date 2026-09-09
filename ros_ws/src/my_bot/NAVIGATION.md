# Nav2 while building a fresh map

Implementation added September 8, 2026. Offline checks pass; Jazzy launch/runtime,
goal completion and obstacle avoidance still need the PC acceptance run. No physical
navigation or automatic exploration is claimed.

## Files and command flow

- `launch/nav_sim.launch.py` starts the existing simulation SLAM launch without its
  RViz, then navigation and a single navigation RViz window. Simulation-only.
- `launch/navigation.launch.py` starts standard Nav2 servers and their lifecycle
  manager. It deliberately selects the six servers we need rather than launching
  unrelated docking, route and waypoint servers from the upstream all-purpose
  bringup. No AMCL, saved-map server, duplicate odometry or custom planner.
- `config/nav2.yaml` configures NavFn known-space planning, DWB path tracking,
  recovery behaviors, velocity smoothing, collision monitoring and costmaps.
- `config/navigation.rviz` supplies Nav2 Goal, navigation status/cancel controls,
  live map, scans, green planned path and optional local costmap display.
- `test/test_navigation.py` checks integration contracts and, on ROS, generates
  launch descriptions, checks server installation and verifies clock rewriting.
  This is not an end-to-end navigation test.

`NavigateToPose` goal -> NavFn path -> DWB body velocity -> velocity smoother ->
collision monitor -> `/diff_drive_controller/cmd_vel` -> existing wheel controller.
Behaviors (spin/back up/wait) use the same velocity pipeline during recovery.
`/cmd_vel_nav`, `/cmd_vel_smoothed` and the drivetrain input all use TwistStamped;
Jazzy requires explicit `enable_stamped_cmd_vel: true`. No conversion node needed.

SLAM owns `/map` and map->odom, wheel odometry owns odom->base_link, and robot state
publisher owns the laser transform. Every simulated node uses `/clock`. The lower
navigation launch can rewrite all clock settings, but physical integration remains
outside this change; use only nav_sim.launch.py for this acceptance run.

## Conservative first settings

Nav2 is limited to 0.12 m/s and 0.6 rad/s, within the existing drivetrain limits.
NavFn and DWB use a 0.215 m collision radius plus 0.005 m padding: this encloses the
robot's offset 0.18 m front extent and 0.1075 m half-width (corner radius ~0.210 m).
It may reject narrow passages that a more precisely modeled robot could traverse.
The inflation layer adds a graded clearance cost to 0.35 m. Unknown space is not
traversable in this first step; choose goals in observed free space. Frontier goal
selection will come later, on the known side of those boundaries.

The collision monitor uses scans and the costmap footprint to reduce motion before
predicted collision and stop on stale scan input (0.5 s source timeout). This is a
software safeguard needing runtime validation, not a certified emergency stop.
Drivetrain command timeout remains 0.25 s. Do not run teleop while Nav2 is running:
teleop's direct drivetrain output would bypass the navigation pipeline. Switching
control modes currently means stopping one launch and starting the other.

## Copy/paste setup

Use the consolidated repository instructions:
[WSL build, launch, goals, cancellation and map export](../../../docs/WSL_COPY_PASTE.md).
After dependencies/build/tests, the launch command is:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot nav_sim.launch.py
```

Wait for the map and Nav2 activation. Select **Nav2 Goal**, click a nearby clear
mapped area, drag to choose heading and release. Use **Cancel** in Navigation 2 to
cancel. Do not set an AMCL initial pose: SLAM is already estimating the pose.

## Runtime acceptance still required

Record commit, Ubuntu/ROS versions and results, not just a successful build:
1. All six Nav2 servers active; map, scan, TF and stamped command types consistent.
2. Reach a nearby clear goal, then a farther goal around a box without collision.
3. Cancel a moving goal and confirm it stops; SLAM continues updating.
4. A goal in occupied/unknown/unreachable space must not cause contact. A reported
   failure is acceptable; false success is not.
5. Stop and restart from a fresh map, repeat; save YAML/image using the guide.

Sources checked against Jazzy:
- https://docs.nav2.org/jazzy/tutorials/general_tutorials/navigation2_with_slam/navigation2_with_slam/
- https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/launch/navigation_launch.py
- https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_bringup/params/nav2_params.yaml
- https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/core_servers/configuring_velocity_smoother/

## RViz startup correction — September 8

The included SLAM/simulation launch was passed rviz=false without a scoped group.
ROS launch arguments modify LaunchContext, so that value also disabled the parent
RViz action. Both nav_sim and slam_sim now isolate the child override with
GroupAction(scoped=True). Default launch requests one RViz window; rviz=false
still requests none. RViz output is visible in the launch terminal.

For an already running stack with no RViz window, open only the correct UI:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot rviz_navigation.launch.py
```

This loads navigation.rviz with Nav2 Goal and Navigation 2, not the older slam.rviz
view. Do not launch a second simulation just to open RViz. Offline regression
checks reject the previous unscoped launch. A ROS-only regression checks parent
true/false decisions using LaunchContext without starting processes; it remains
unrun on this Mac. WSL window/rendering behavior still needs user confirmation.
