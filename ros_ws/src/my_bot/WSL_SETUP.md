# Start simulation on your Windows PC

Use **WSL2, Ubuntu 24.04, ROS 2 Jazzy and Gazebo Harmonic**. ESP32 and Pi are not
needed. This source bundle includes a real hardware plugin, but default simulation
never opens a serial device. Initial WSL driving and scans are documented in [the simulation result](docs/results/2026-09-07-initial-simulation.md); repeatable startup and SLAM acceptance remain pending.

## 1. Windows preparation

In administrator PowerShell, if Ubuntu 24.04 is not installed:

```powershell
wsl --install -d Ubuntu-24.04
wsl --update
```

Restart if Windows requests it, open Ubuntu 24.04 and create your Linux user.
Use `wsl -l -v` in PowerShell to confirm version 2. WSLg requires a supported
Windows version and working GPU driver; see Microsoft's reference below.

## 2. ROS installation (Ubuntu terminal)

If `/opt/ros/jazzy/setup.bash` does not exist, first follow the official
[ROS 2 Jazzy Ubuntu installation](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)
through repository setup and installation of `ros-jazzy-desktop` and `ros-dev-tools`.
Then:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-dev-tools unzip ros-jazzy-ros-gz ros-jazzy-gz-ros2-control \
  ros-jazzy-ros2-controllers
```

## 3. Clone the project, build and test

Keep the workspace in Linux's home filesystem. In Ubuntu:

```bash
source /opt/ros/jazzy/setup.bash
cd ~
git clone https://github.com/adrithk/autonomous-mapping-robot.git
cd ~/autonomous-mapping-robot/ros_ws
# First rosdep use only; skip init if already initialized:
[ -f /etc/ros/rosdep/sources.list.d/20-default.list ] || sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
colcon test --packages-select my_bot --event-handlers console_direct+
colcon test-result --verbose
```

For an existing checkout, stop launches and run `git pull --ff-only` from
`~/autonomous-mapping-robot`, then repeat the workspace dependency/build steps.
The package name stays `my_bot`; do not build a second copy in the same workspace.

## 4. Launch simulation

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot bringup.launch.py
```

This opens Gazebo and RViz, spawns the robot, activates the wheel controllers and
bridges simulated laser scans and clock. For no RViz use `rviz:=false`.

In a second Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args \
  -p use_sim_time:=true -p frame_id:=base_link \
  -p speed:=0.1 -p turn:=0.5 -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Hold `w` forward, `s` reverse, `a` left, `d` right; space or `x` stops.
The keyboard command expires after 0.2 s without a key repeat. Initial keyboard repeat delay may
cause a brief pause. Simulation timestamps are required: keep `use_sim_time:=true`.

In a third Ubuntu terminal after sourcing both setup files:

```bash
ros2 control list_controllers
ros2 control list_hardware_interfaces
ros2 topic hz /scan
ros2 topic echo /diff_drive_controller/odom --once
```

Expect both controllers active, wheel velocity interfaces claimed, scan around
10 Hz, and changing odometry while driving. RViz should show robot/scan in odom.
A source build passing is not proof of those runtime checks: verify each on the PC.
If Gazebo cannot render, first check WSLg/GPU support. GPU LiDAR needs a rendering
context even without RViz. Do not install Gazebo Classic from older Foxy tutorials.

## 5. Pi later

Stop simulation. Follow [HARDWARE.md](HARDWARE.md), upload ESP32 ros_serial v2,
and explicitly select `mode:=hardware` with its USB device path. Hardware teleop
uses `use_sim_time:=false`. Confirm odometry and the real A1M8 scan before adding
SLAM Toolbox; SLAM/Nav2 are not started by these launches.

Sources: [Microsoft WSL GUI support](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gui-apps),
[Jazzy Gazebo Harmonic integration](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html).

## Next: map the obstacle room

Follow [SLAM.md](SLAM.md) to update, install SLAM Toolbox, launch simulation mapping
and save the resulting occupancy map.

## Nav2 click-to-go navigation

For navigation while SLAM maps, use [NAVIGATION.md](NAVIGATION.md) and the
[updated copy/paste workflow](../../../docs/WSL_COPY_PASTE.md). Stop manual teleop
and the old launch first; run only `nav_sim.launch.py`. Runtime validation of
this new navigation mode is pending.
