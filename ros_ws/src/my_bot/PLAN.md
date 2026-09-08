# Preliminary robot description

Date: 2026-09-06. Scope: a simple Jazzy-targeted kinematic description and preview.

- Implement measured wheel layout and builder-approved 26 cm envelope.
- Keep the chassis/caster simple and record assumptions explicitly.
- Use the builder-authorized provisional centered LiDAR mount, scan plane 0.10 m
  above floor (0.06 m above wheel axles); confirm before real mapping.
- Provide a real-description launch and a separate GUI-only preview launch.
- Expand Xacro, check geometry/frame connectivity, and inspect Python/YAML syntax.
- On the Pi: colcon build/test, inspect RViz, verify forward/left axes and wheel
  motion, then compare geometry with the assembled robot.

This preliminary description is not acceptance evidence for motion, odometry,
collision avoidance or SLAM. Encoder calibration, hardware plugin, final mounting
measurements and integrated tests remain separate tasks.

Status: local validation passed with Xacro 2.1.1: expansion with/without LiDAR, connected frame trees, wheel spacing/radius/width and footprint extents, Python launch syntax, package XML, RViz YAML, and git diff --check. Generated robot.urdf saved. Jazzy colcon build/test and RViz runtime remain pending; ROS is not installed in this macOS environment.

LiDAR revision: enabled provisional laser frame and visual cylinder; mount assumptions
are documented. Local expansion and transform checks passed; ROS runtime pending.

## Estimated simulation extension

Builder requested estimated masses/inertias, contact settings, gz_ros2_control,
and a simulated LiDAR. Added a conditional Gazebo model, controller configuration,
clock/scan bridge, local test room and separate simulation launch. Estimates and
real-hardware limitations are in SIMULATION.md. Four local automated checks passed: all four simulation/LiDAR combinations,
connected frame trees, positive inertias and 1.6 kg mass totals, controller/geometry
consistency, sensor and bridge wiring, and XML/Python/YAML syntax. The generated
URDF was refreshed and git diff --check passed. colcon/Gazebo/WSL runtime checks
remain pending because ROS and Gazebo
are not installed here. The real ESP32 SystemInterface is still not implemented.

## ESP32 hardware and selectable bringup — 2026-09-07

Implemented `my_bot/Esp32System`, serial v2 transport, pluginlib export/build rules,
opt-in hardware Xacro and launch, and default-simulation bringup switch. Added
separate real/sim clocks, common conservative limits and WSL/Pi instructions.
Offline verification: pseudo-terminal transport/fault tests, model/configuration
checks and Python/XML syntax. Jazzy compile/plugin loading and Gazebo/WSL runtime
remain pending on Ubuntu; physical acceptance remains pending on the Pi.
This supersedes earlier statements that the hardware plugin does not exist.

## WASD teleoperation — 2026-09-07

Added a shared stamped-command terminal executable for simulation and hardware.
W/S select forward/reverse; A/D turn; space/X/unknown keys stop. Monotonic 0.2 s
key expiry prevents stale input from persisting when simulation time pauses.
Mapping, repeat/expiry and invalid-speed tests pass offline. ROS/terminal integration
still requires Ubuntu. Updated dependencies, install rules and operation commands.

## User-observed simulation result — 2026-09-07

Recorded [initial simulation implementation](docs/results/2026-09-07-initial-simulation.md) with the builder's original photo. Gazebo launch, WASD driving,
10 Hz simulated scans and RViz display were reported working. The screenshot
confirms visible scan returns with RViz status Ok. This supersedes earlier pending
statements for the initial simulation smoke test only; physical validation,
repeatable startup, odometry accuracy and SLAM remain pending.

## Simulation SLAM and obstacle room — 2026-09-07

Bounded scope: add five static obstacles, a simulation-only async SLAM Toolbox
launch, matching frame/clock/range parameters, an overhead RViz map display,
and manual map-saving instructions. Keep hardware and default teleop behavior.
Verify offline model/configuration/world checks; builder must validate /map,
map->odom, slow driving/loop closure and saved YAML/image in WSL.

SLAM step offline verification: eight model/configuration/world tests and three
WASD tests passed; git diff --check passed. WSL SLAM/map-export testing is pending.
