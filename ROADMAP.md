# Capability status and remaining work

Updated September 10, 2026. This is the current status summary; dated execution
history and acceptance criteria remain in [docs/plans/](docs/plans/).
The mission is autonomous fresh-zone indoor mapping without an IMU.

| Capability | Source / observed result | Remaining acceptance |
|---|---|---|
| ESP32 motor and encoder control | Implemented; motor/encoder motion observed | Repeated boot, stop, timeout and power-isolation measurements |
| Wheel-speed PI control | Implemented; earlier raised-wheel ±3000 counts/s tracking recorded | Current ramps, final payload, measured ground trials |
| Serial v2 transport | Firmware and host implemented; native tests recorded | Live USB, disconnect/watchdog/reconnect trials |
| ROS model and hardware plugin | Included; initial physical driving demonstrated | Revision-pinned Jazzy build/test and repeated physical integration |
| Gazebo driving and simulated LiDAR | Initial WSL demonstration recorded | Revision-pinned repeatable startup and measured odometry |
| SLAM and manual map export | Implemented; [initial simulated SLAM screenshot](results/2026-09-08-simulated-lidar-slam.md) records visualization; physical mapping/save also reported in September 10 evidence | Repeatability, loop consistency and archived YAML/image |
| Real LiDAR and TF | A1M8 scan publication and physical mapping demonstrated | Measured final mount, clock/frame and calibration checks |
| Nav2 click-to-go navigation | Simulation code plus initial physical saved-map demonstration | Repeated goals around obstacles, cancellation and failure tests with logs |
| Autonomous exploration | Frontier manager, simulation launch and automatic saving implemented; offline tests | Jazzy/Gazebo repeated missions, collision-free execution, map reload and physical acceptance |
| Project showcase | Real-room photo/map pair and two Nav2 recordings published | Original map files, end-to-end autonomous exploration recording and measured results |

The [September 10 demonstration record](results/2026-09-10-real-room-mapping-navigation.md)
adds initial physical teleoperation, mapping/export and saved-map navigation evidence.
It does not close measured hardware or autonomous exploration acceptance.

## Finish in this order

1. Reproduce the simulation SLAM run and save its map: [plan 005](docs/plans/active/005-simulation-slam.md).
2. Complete Pi setup, calibrated geometry, raised-wheel serial and watchdog trials:
   [plan 003](docs/plans/active/003-ros-ready-esp32-transport.md) and [plan 004](docs/plans/active/004-pi-hardware-interface.md).
3. Finish physical drivetrain acceptance: [plan 001](docs/plans/active/001-safe-motor-command-interface.md)
   and [plan 002](docs/plans/active/002-wheel-speed-pid.md).
4. Repeat and measure the demonstrated physical LiDAR, odometry/TF and manually driven mapping.
5. Validate the implemented autonomous exploration and automatic map saving through
   bounded plans following the [ROS platform sequence](docs/ros-platform-roadmap.md).
6. Record representative trials in one or two rooms and fill the [showcase checklist](docs/project-completion.md).

Completion requires dated evidence of the autonomous mission ending with the
robot stopped and a saved map, including repeated runs of the same environment.
Documentation preparation does not close these engineering acceptance gates.

The [ROS audit record](ros_ws/src/my_bot/docs/results/2026-09-07-code-audit.md)
reports an initial 79 × 79 map received by RViz and an earlier rendering error.
The user confirmed successful RViz/SLAM operation on September 8; the earlier
error’s root cause remains undetermined.
This is additional initial map-output evidence; map accuracy/export and autonomous
mission acceptance remain pending.
