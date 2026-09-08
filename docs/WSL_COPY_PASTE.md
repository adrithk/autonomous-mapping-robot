# WSL simulation and SLAM: copy/paste guide

Use Ubuntu 24.04 in WSL2, with ROS 2 Jazzy already installed. No Pi, ESP32 or
physical LiDAR is needed for this simulation. These instructions use the consolidated
repository, not the older ~/ros_ws copy. Do not run both workspaces at once.
The RViz rendering issue remains unresolved; these commands do not claim to fix it.

## 1. Stop old runs

Press Ctrl+C in each old simulation, SLAM, RViz and teleop terminal. Close those
Ubuntu terminals, then open a fresh Ubuntu terminal. Keep the code blocks intact;
underscores need no backslashes. Run blocks in order and stop if a build/test fails.

## 2. Download/update, install dependencies, build and test

Paste this entire block into Ubuntu. It stops on an error. Your sudo password is
your Ubuntu password; typing it does not show characters. Download/build time varies.

```bash
bash <<'BASH'
set -e
. /etc/os-release
if [ "$VERSION_ID" != "24.04" ]; then
  echo "Use Ubuntu 24.04 for these Jazzy instructions. Detected: $PRETTY_NAME"
  exit 1
fi
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y git ros-dev-tools ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-ros2-controllers ros-jazzy-slam-toolbox ros-jazzy-nav2-map-server
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

Expect zero test failures. The package path should be under
~/autonomous-mapping-robot/ros_ws/install. The new hardware_plugin_test checks real
plugin loading without connecting motors; it has not yet been validated on Linux.
If Git reports local changes/conflicts, stop and share the error; do not reset them.

## 3. Terminal 1: start simulation AND SLAM

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot slam_sim.launch.py
```

Leave this terminal running. It launches Gazebo, controllers, simulated LiDAR,
SLAM Toolbox and RViz. Do not also launch bringup.launch.py. The last message
“Registering sensor” does not mean it is stuck; this process keeps running.

If RViz fails, stop this launch with Ctrl+C and use this instead to run without RViz:

```bash
ros2 launch my_bot slam_sim.launch.py rviz:=false
```

Gazebo still needs working graphics for simulated LiDAR. This option only excludes
RViz; it does not fix a Gazebo rendering failure.

## 4. Terminal 2: drive

Open a second Ubuntu terminal and paste:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args -p use_sim_time:=true -p speed:=0.1 -p turn:=0.5 -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Keep this terminal focused. Hold lowercase w/s to move forward/back, a/d to turn;
space or x stops, Ctrl+C quits. Drive slowly around boxes and back toward the start.
There is no autonomous obstacle avoidance yet. Brief pauses before keyboard repeat
starts are expected. No third terminal is required to make /scan publish.

## 5. Terminal 3: check that mapping works

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 control list_controllers
ros2 lifecycle get /slam_toolbox
timeout 15s ros2 topic echo /map --once --field info
```

Expect both controllers active, SLAM active, and nonzero map width/height. An echo
that times out with no data is not a pass. These checks work without an RViz window.

To open RViz separately ONLY if you launched with rviz:=false:

```bash
rviz2 -d ~/autonomous-mapping-robot/ros_ws/install/my_bot/share/my_bot/config/slam.rviz --ros-args -p use_sim_time:=true
```

## 6. Save the map (keep Terminal 1 running)

Use Terminal 3, or another sourced Ubuntu terminal. This creates a unique filename:

```bash
mkdir -p ~/autonomous-mapping-robot/ros_ws/maps
map_file="$HOME/autonomous-mapping-robot/ros_ws/maps/sim_$(date +%Y%m%d_%H%M%S)"
ros2 run nav2_map_server map_saver_cli -f "$map_file" --ros-args -p use_sim_time:=true -p map_subscribe_transient_local:=true -p save_map_timeout:=10.0
ls -lh "${map_file}".*
explorer.exe "$(wslpath -w "$HOME/autonomous-mapping-robot/ros_ws/maps")"
```

Expect a YAML file and image, normally PGM. Windows Explorer opens the folder so
you can copy/email both files. Saving does not validate map accuracy.

## 7. If it fails: collect text instead of photos

Leave the failing simulation running. In a fresh Ubuntu terminal paste:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
{
  cat /etc/os-release
  git -C ~/autonomous-mapping-robot rev-parse HEAD
  ros2 pkg prefix my_bot
  colcon test-result --test-result-base ~/autonomous-mapping-robot/ros_ws/build --verbose
  timeout 10s ros2 control list_controllers
  timeout 10s ros2 lifecycle get /slam_toolbox
  timeout 10s ros2 topic info /clock --verbose
  timeout 10s ros2 topic echo /clock --once
  timeout 10s ros2 topic echo /scan --once --field header
  timeout 10s ros2 topic echo /map --once --field info
  timeout 5s ros2 run tf2_ros tf2_echo map laser
} > ~/ros-diagnostics.txt 2>&1
explorer.exe "$(wslpath -w "$HOME")"
```

Send ros-diagnostics.txt plus the error text from the launch/RViz terminal.
Timeouts here deliberately keep diagnostics from running forever. None of the
read-only topic checks starts the sensor publisher.

## Shut down / next session

Stop teleop with Ctrl+C, then stop the launch in Terminal 1 with Ctrl+C. Stop any
separately opened RViz too. Next session, repeat sections 3 and 4; rebuild only after
code updates. Real robot bringup and physical SLAM are separate pending steps.
