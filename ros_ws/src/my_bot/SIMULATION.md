# Gazebo Harmonic + ROS 2 Jazzy

This is an estimated simulation setup, not a calibrated digital model. It uses
the same standard diff_drive_controller intended for the Pi; Gazebo supplies the
wheel interface here. The implemented opt-in Pi SystemInterface speaks our ESP32 serial v2 protocol.
See HARDWARE.md; physical plugin validation remains pending. Initial simulation
driving/scans have been observed; repeatable runtime checks remain below.

## Estimated physics

`description/simulation_parameters.xacro` owns these assumptions:

| Parameter | Starting value |
|---|---:|
| Total mass | 1.60 kg |
| Each drive wheel | 0.08 kg |
| Caster | 0.04 kg |
| LiDAR | 0.17 kg |
| Remaining chassis/electronics | 1.23 kg |
| Body inertia envelope height | 0.08 m |
| Body COM above plate center | 0.03 m |
| Wheel friction coefficient | 0.8 |
| Caster sphere friction coefficient | 0.001 |
| Wheel torque / velocity limits | 0.3 N m / 12.5 rad/s |
| LiDAR rate / samples per scan | 10 Hz / 360 |
| LiDAR range / Gaussian range noise stddev | 0.15–6 m / 0.01 m |

Box, cylinder and sphere inertia formulas produce positive inertias for these
assumptions. With LiDAR disabled its allocated mass returns to the chassis.
The caster is a low-friction sphere, not a simulated swivel assembly. LiDAR
scan properties are convenient test settings, not verified A1M8 specifications.
The visual LiDAR housing sits just below the scan plane to avoid self-obstruction.
Velocity control does not reproduce the ESP32 PI loop, serial timing, or verified
motor torque. Do not use these simulation values to tune real motor gains.

`config/controllers.yaml` uses the preliminary builder-reported wheel geometry and conservative
simulation limits: 0.15 m/s translation, 0.75 rad/s rotation and a 0.25 s command
timeout. These are not calibrated real-robot limits. Geometry consistency is
checked against Xacro by the tests; update both when geometry changes.

## Run on Ubuntu 24.04 with Jazzy (including WSL2 with working WSLg graphics)

Gazebo runs on the PC; the Pi is not required for simulation. Follow [WSL_SETUP.md](WSL_SETUP.md) to clone the consolidated repository first. In the Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install ros-jazzy-ros-gz ros-jazzy-gz-ros2-control ros-jazzy-ros2-controllers
cd ~/autonomous-mapping-robot/ros_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot
colcon test --packages-select my_bot
colcon test-result --verbose
source install/setup.bash
ros2 launch my_bot bringup.launch.py
```

The world is a local 4 m room with six interior box obstacles and requires no remote model
downloads. The launch starts Gazebo running, publishes the description, spawns
the model, starts the joint-state broadcaster and then the drive controller.
It bridges only `/clock` and `/scan`. ros2_control owns joint states and odometry;
there is no second Gazebo DiffDrive plugin or fake joint-state publisher.

In a second Ubuntu terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args \
  -p use_sim_time:=true -p frame_id:=base_link -p speed:=0.1 -p turn:=0.5 \
  -r cmd_vel:=/diff_drive_controller/cmd_vel
```

Keep the keyboard terminal focused. Hold w/a/s/d to drive; space or x stops.
The teleop sends zero after 0.2 s without key repeats; controller timeout is 0.25 s. RViz uses odom as its fixed frame.

## Repeatable runtime acceptance checks

1. Robot settles upright without sinking, bouncing or drifting.
2. `ros2 control list_controllers` shows both controllers active.
3. Forward commands move toward the caster; positive angular.z turns left.
4. `ros2 topic hz /scan` is about 10 Hz and scan frame is `laser`; room walls
   appear at plausible distances in RViz.
5. Joint states and `/diff_drive_controller/odom` update; exactly one publisher
   owns odom -> base_link. Ending command publication stops requested wheel motion.
6. Drive a slow loop and check scan/odometry consistency before adding SLAM.

GPU LiDAR needs working rendering even without the Gazebo GUI. If WSL graphics
fails, first resolve WSLg/GPU support; do not interpret a missing scan as a real
LiDAR failure. `rviz:=false` disables RViz only, not Gazebo's rendering requirements.

## Real robot later

Stop simulation, then choose `mode:=hardware` and explicitly supply the ESP32
serial device. See [HARDWARE.md](HARDWARE.md) for exact commands and bench checks.
`rsp.launch.py` alone remains a description-only launch. Hardware and simulation
must not run simultaneously in the same ROS domain.

References: [Jazzy gz_ros2_control](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html),
[Jazzy diff_drive_controller](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html),
[Harmonic sensors](https://gazebosim.org/docs/harmonic/sensors/).

## User-observed simulation result — 2026-09-07

Recorded [initial simulation implementation](docs/results/2026-09-07-initial-simulation.md) with the builder's original photo. Gazebo launch, WASD driving,
10 Hz simulated scans and RViz display were reported working. The screenshot
confirms visible scan returns with RViz status Ok. This supersedes earlier pending
statements for the initial simulation smoke test only; physical validation,
repeatable startup, odometry accuracy and SLAM remain pending.
