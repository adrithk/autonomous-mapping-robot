# WSL: Nav2 navigation while SLAM maps

For Ubuntu 24.04 in WSL2 with ROS 2 Jazzy already installed. No physical robot or
LiDAR needed. Use this consolidated repository, not the older ~/ros_ws checkout.

New capability: **click a destination and Nav2 drives there while SLAM maps**.
Automatic destination selection/exploration is not implemented yet. This Nav2
addition passed offline checks, but its first Linux runtime test is still pending.
Your previously working SLAM-only mode remains available below.

## 1. Stop the old simulation and WASD

Press Ctrl+C in every old launch/teleop terminal and close them. Open a fresh Ubuntu
terminal. Do not run WASD concurrently with Nav2; both would command the drivetrain.
Paste blocks intact (underscores need no backslashes). Stop if a build/test fails.

## 2. Update, install Nav2, build and test

Paste the entire block below into Ubuntu. It stops on errors. sudo asks for your
Ubuntu password; typing the password shows no characters. Keep local Git changes;
if Git reports conflicts, stop and share the error instead of resetting files.

```bash
bash <<'BASH'
set -e
. /etc/os-release
if [ "$VERSION_ID" != "24.04" ]; then
  echo "Use Ubuntu 24.04. Detected: $PRETTY_NAME"
  exit 1
fi
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y git ros-dev-tools ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-ros2-controllers ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server ros-jazzy-navigation2 ros-jazzy-nav2-rviz-plugins
cd "$HOME"
if [ ! -d autonomous-mapping-robot ]; then
  git clone https://github.com/adrithk/autonomous-mapping-robot.git
fi
cd "$HOME/autonomous-mapping-robot"
git pull --ff-only
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update
cd ros_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
colcon test --packages-select my_bot --event-handlers console_direct+
colcon test-result --verbose
ros2 pkg prefix my_bot
BASH
```

Expect zero test failures and a package path under
~/autonomous-mapping-robot/ros_ws/install. A successful build is not a navigation test.
The new ROS launch check should run on Jazzy rather than be skipped.

## Quick start: already installed and built

Stop previous launches and RViz first. Use this instead of the installation block
for normal repeat sessions. It pulls Git, rebuilds only when the revision changes,
and starts the navigation simulation. No apt update/install or rosdep update runs.
The parentheses keep error handling and setup isolated to this launch session.

```bash
(
  set -e
  cd ~/autonomous-mapping-robot
  previous_revision=$(git rev-parse HEAD)
  git pull --ff-only
  source /opt/ros/jazzy/setup.bash
  cd ros_ws
  if [ "$previous_revision" != "$(git rev-parse HEAD)" ]; then
    colcon build --packages-select my_bot --symlink-install
  fi
  source install/setup.bash
  ros2 launch my_bot nav_sim.launch.py
)
```

With no Git changes, this skips the build. New revisions trigger a build because
new files, compiled code or install rules can require it. If an update adds new
dependencies, use section 2 once. If you already pulled separately, edited files
locally, or a previous build failed, rebuild explicitly before using this shortcut:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/autonomous-mapping-robot/ros_ws
colcon build --packages-select my_bot --symlink-install
```

## 3. Terminal 1: launch everything

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot nav_sim.launch.py
```

Leave it running. This starts Gazebo, the robot/controllers, simulated LiDAR, SLAM,
Nav2 and one RViz window. Do not also start bringup.launch.py or slam_sim.launch.py.
RViz should open automatically with **Nav2 Goal** in the toolbar and the
**Navigation 2** panel. A child-launch argument leak that previously prevented
this has been fixed; pull and rebuild before retrying. RViz process logs now
appear in Terminal 1. Wait for the map and navigation activation. “Registering sensor” is normal and does
not indicate a stalled progress bar. No separate /scan echo is needed to publish data.

## 4. Click a destination

1. In RViz, wait for the live map and robot to appear.
2. Choose **Nav2 Goal** in the toolbar.
3. Click a nearby clear, mapped area; drag the arrow for the final heading, then release.
4. The green path should appear, and the robot should drive to the goal while the map updates.
5. Once that succeeds, try a clear goal requiring a route around a box.

Use known free space, not unknown cells or a box/wall. Keep initial goals away from
obstacles. Conservative collision bounds can reject narrow gaps. No AMCL initial
pose is needed. Nav2 chooses a route; it does not yet choose destinations itself.

## 5. Terminal 2: verify status and cancel

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 control list_controllers
for node in controller_server planner_server behavior_server bt_navigator velocity_smoother collision_monitor; do
  timeout 10s ros2 lifecycle get /$node
done
timeout 15s ros2 topic echo /map --once --field info
ros2 topic info /diff_drive_controller/cmd_vel --verbose
```

Expect both wheel controllers and all six Nav2 nodes active, nonzero map dimensions,
and geometry_msgs/msg/TwistStamped on the drivetrain input. In Nav2 mode its only
command publisher should be collision_monitor. An echo timeout is not a pass.

Use **Cancel** in RViz's Navigation 2 panel while moving and confirm it stops.
Alternative: cancel all click-to-go requests from Terminal 2:

```bash
ros2 service call /navigate_to_pose/_action/cancel_goal action_msgs/srv/CancelGoal '{}'
```

Cancellation may allow brief deceleration. If cancellation does not respond, stop
the entire launch with Ctrl+C in Terminal 1; the wheel command timeout stops stale
motion. Ctrl+C on a goal-client terminal alone is not a reliable goal cancellation.

## 6. Save the map

Keep Terminal 1 running, cancel navigation, then use the sourced Terminal 2:

```bash
mkdir -p ~/autonomous-mapping-robot/ros_ws/maps
map_file="$HOME/autonomous-mapping-robot/ros_ws/maps/nav_sim_$(date +%Y%m%d_%H%M%S)"
ros2 run nav2_map_server map_saver_cli -f "$map_file" --ros-args -p use_sim_time:=true -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0
ls -lh "${map_file}".*
explorer.exe "$(wslpath -w "$HOME/autonomous-mapping-robot/ros_ws/maps")"
```

Expect YAML and an image, normally PGM. Keep both files. Each launch starts a fresh
map. Saving does not establish full coverage or accuracy.

## 7. If something fails, collect text

Leave the failing launch running. In a fresh Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
{
  cat /etc/os-release
  git -C ~/autonomous-mapping-robot rev-parse HEAD
  ros2 pkg prefix my_bot
  colcon test-result --test-result-base ~/autonomous-mapping-robot/ros_ws/build --verbose
  timeout 10s ros2 control list_controllers
  for node in slam_toolbox controller_server planner_server behavior_server bt_navigator velocity_smoother collision_monitor; do
    timeout 5s ros2 lifecycle get /$node
    timeout 5s ros2 param get /$node use_sim_time
  done
  timeout 10s ros2 topic echo /clock --once
  timeout 10s ros2 topic echo /scan --once --field header
  timeout 10s ros2 topic echo /map --once --field info
  timeout 5s ros2 topic info /clock --verbose
  timeout 5s ros2 topic echo /diff_drive_controller/odom --once --field header
  timeout 5s ros2 run tf2_ros tf2_echo map odom --ros-args -p use_sim_time:=true
  timeout 5s ros2 run tf2_ros tf2_echo odom base_link --ros-args -p use_sim_time:=true
  timeout 5s ros2 run tf2_ros tf2_echo map laser --ros-args -p use_sim_time:=true
  timeout 5s ros2 param get /controller_server FollowPath.transform_tolerance
  timeout 5s ros2 param get /slam_toolbox transform_timeout
  timeout 10s ros2 topic info /cmd_vel_nav --verbose
  timeout 10s ros2 topic info /cmd_vel_smoothed --verbose
  timeout 10s ros2 topic info /diff_drive_controller/cmd_vel --verbose
} > ~/ros-diagnostics.txt 2>&1
explorer.exe "$(wslpath -w "$HOME")"
```

Send ros-diagnostics.txt and the launch/RViz error text. The timeouts prevent
indefinite monitoring; collecting all diagnostics can take a few minutes.

If only RViz fails, stop Terminal 1 and restart with:

```bash
ros2 launch my_bot nav_sim.launch.py rviz:=false
```

To reopen just RViz in a second terminal (only when no RViz window is running):

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot rviz_navigation.launch.py
```

This standalone launch loads **navigation.rviz**, including the **Nav2 Goal** toolbar
tool and **Navigation 2** panel with cancellation controls. Do not use the old
`slam.rviz` command: that view has no Nav2 controls.

This separates the GUI from the running stack; it is not a graphics fix. Gazebo's
simulated LiDAR still requires a working rendering context.

## 8. Optional: return to manual WASD mapping

Stop Nav2's entire launch first. In Terminal 1:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot slam_sim.launch.py
```

Then in Terminal 2:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args -p use_sim_time:=true -p speed:=0.1 -p turn:=0.5 -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Hold lowercase w/s forward/back, a/d turn; x/space stops. Stop both terminals before
switching back to Nav2. Next session, section 3 is enough if code has not changed.

## How it works

SLAM supplies the growing map and pose. NavFn plans through known free space. DWB
follows that path using current LiDAR obstacles. The velocity smoother limits
acceleration; the collision monitor checks the scans before commands reach the
existing differential-drive controller. It turns body commands into wheel speeds.
The navigation manager activates these servers; RViz sends a NavigateToPose goal.

File-by-file details and test criteria: [NAVIGATION.md](../ros_ws/src/my_bot/NAVIGATION.md).
Frontier exploration, automatic mission completion/save and physical Nav2 testing
are future steps, not enabled by this launch.

## Transform-related goal aborts

“Unable to transform robot pose into global plan's frame” means the controller
cannot relate its odometry pose to the map path at the required time. It does not
establish an obstacle or planning failure. Nav2 aborts TF errors immediately;
`failure_tolerance` applies to a different error (no valid control), so removing
that timeout does not fix this error.

The configuration now gives SLAM's map TF and the map-consuming navigation
components a bounded 1.5-second margin (increased from 0.5 after continued failures) (the navigator's
previous implicit default was not set here). This mitigates brief timing delays;
it cannot fix missing TF, duplicate simulations, mixed clocks, or sustained lag.
Local odometry/collision-monitor tolerances and motor watchdogs remain unchanged.
This change needs a PC runtime retest; the reported root cause is not confirmed.

Stop the previous launch with Ctrl+C before pulling and rebuilding. Use this
instead of the normal launch line to retain the complete error and preceding
transform timestamps:

```bash
ros2 launch my_bot nav_sim.launch.py 2>&1 | tee ~/nav2-launch.log
```

Keep the same sourced terminal setup from above. If the goal aborts again, collect
section 7 diagnostics while it is still running and send `nav2-launch.log` too.
Do not run WASD while Nav2 controls the robot.

## Small performance update

Planner fallback tolerance is now 15 cm; simulation navigation tops out at
0.20 m/s. Costmaps publish changed regions, and unconfigured native builds default
to RelWithDebInfo (optimization plus debugging symbols). No new packages needed.
Use the normal pull/build workflow. Existing explicit build-type choices are
preserved; to explicitly enable the optimized build, replace the build line with:

```bash
colcon build --packages-select my_bot --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo
colcon test --packages-select my_bot
colcon test-result --verbose
```

After relaunch, test an open-space goal and a goal around a box, cancellation,
and a blocked goal. Enable Local obstacle clearance in RViz and confirm it
updates as the robot moves. Reduced traffic is workload-dependent; no Pi/WSL
performance gain has been measured yet. Slowing near obstacles is still expected.
