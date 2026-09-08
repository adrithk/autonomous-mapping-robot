# Simulation mapping with SLAM Toolbox

The world now contains six interior box obstacles (five added), four boundary walls
and a clear spawn area. Drive manually around obstacles to reveal surfaces hidden
from the initial scan. No autonomous obstacle avoidance or navigation is enabled.

## Update on WSL

Stop existing launches/teleop with Ctrl-C first. Run in Ubuntu:

```bash
cd ~/autonomous-mapping-robot/ros_ws/src/my_bot
git pull --ff-only
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server
cd ~/autonomous-mapping-robot/ros_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
colcon test --packages-select my_bot --event-handlers console_direct+
colcon test-result --verbose
ros2 launch my_bot slam_sim.launch.py
```

This single launch starts Gazebo, controllers, SLAM Toolbox and one RViz window.
Do not also run bringup.launch.py. The ordinary bringup launch remains available
for teleoperation without SLAM. Both now default to an overhead RViz view.

## Drive and check the map

Second Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args -p use_sim_time:=true -p speed:=0.1 -p turn:=0.5 -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Hold w/s for forward/reverse, a/d to turn; space/x stops. Drive slowly around each
box, then return near your start. RViz displays /map (free/occupied/unknown cells)
plus red /scan returns. The first map may take a few scans; transient missing-map
or transform status during startup is expected, persistent errors need diagnosis.

In a third sourced Ubuntu terminal:

```bash
ros2 lifecycle get /slam_toolbox
ros2 topic echo /map --once --field info
ros2 run tf2_ros tf2_echo map odom
```

Expected: SLAM active, map width/height nonzero, map->odom available. Ctrl-C exits
TF monitoring. SLAM owns map->odom; diff_drive_controller owns odom->base_link;
robot_state_publisher owns base_link->laser. No duplicate odometry/TF publisher.

## Save while the simulation and SLAM are still running

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
mkdir -p ~/autonomous-mapping-robot/ros_ws/maps
ros2 run nav2_map_server map_saver_cli -f ~/autonomous-mapping-robot/ros_ws/maps/initial_sim_map --ros-args -p use_sim_time:=true -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0
ls -lh ~/autonomous-mapping-robot/ros_ws/maps/initial_sim_map.*
```

Expect YAML and an image (normally PGM). Reusing the same filename replaces that
saved map; choose another basename for another run. Copy a selected run’s YAML and referenced image into the repository’s `maps/room-01/`
(or another room slot), then fill that slot’s README and link a dated result.

This saves an occupancy map,
not SLAM Toolbox's resumable pose graph. Each launch starts fresh mapping.
Installing nav2_map_server does not start Nav2 navigation. Real LiDAR/SLAM,
frontier exploration and automatic completion/map saving remain future work.

## Validation

Offline checks cover frame/clock/range configuration, occupancy-map display and
world geometry including spawn clearance. Existing simulation was demonstrated
by the builder; this new SLAM integration needs WSL runtime validation: map creation,
map->odom, exploration around boxes, loop consistency and successful map export.

References: [SLAM Toolbox Jazzy launch](https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/launch/online_async_launch.py),
[Jazzy mapping parameters](https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/config/mapper_params_online_async.yaml).
