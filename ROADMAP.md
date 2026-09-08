# Capability status and remaining work

Updated September 7, 2026. This is the current status summary; dated execution
history and acceptance criteria remain in [docs/plans/](docs/plans/).
The mission is autonomous fresh-zone indoor mapping without an IMU.

| Capability | Source / observed result | Remaining acceptance |
|---|---|---|
| ESP32 motor and encoder control | Implemented; motor/encoder motion observed | Repeated boot, stop, timeout and power-isolation measurements |
| Wheel-speed PI control | Implemented; earlier raised-wheel ±3000 counts/s tracking recorded | Current ramps, final payload, measured ground trials |
| Serial v2 transport | Firmware and host implemented; native tests recorded | Live USB, disconnect/watchdog/reconnect trials |
| ROS model and hardware plugin | Included in `ros_ws/src/my_bot` | Jazzy build/test record, plugin loading and physical integration |
| Gazebo driving and simulated LiDAR | Initial WSL demonstration recorded | Revision-pinned repeatable startup and measured odometry |
| SLAM and manual map export | Simulation launch/configuration implemented | Runtime map creation, loop consistency and saved YAML/image |
| Real LiDAR and TF | Provisional model and hardware identified | Driver, final mount, scans and clock/frame checks |
| Autonomous exploration | Planned | Frontier selection, Nav2 execution, completion and automatic map saving |
| Project showcase | README, documentation and upload slots prepared | Finished robot photo, video, three room maps and measured results |

## Finish in this order

1. Reproduce the simulation SLAM run and save its map: [plan 005](docs/plans/active/005-simulation-slam.md).
2. Complete Pi setup, calibrated geometry, raised-wheel serial and watchdog trials:
   [plan 003](docs/plans/active/003-ros-ready-esp32-transport.md) and [plan 004](docs/plans/active/004-pi-hardware-interface.md).
3. Finish physical drivetrain acceptance: [plan 001](docs/plans/active/001-safe-motor-command-interface.md)
   and [plan 002](docs/plans/active/002-wheel-speed-pid.md).
4. Integrate the physical LiDAR, odometry/TF and manually driven mapping.
5. Implement and validate autonomous exploration and automatic map saving through
   bounded plans following the [ROS platform sequence](docs/ros-platform-roadmap.md).
6. Record three representative room trials and fill the [showcase checklist](docs/project-completion.md).

Completion requires dated evidence of the autonomous mission ending with the
robot stopped and a saved map, including repeated runs of the same environment.
Documentation preparation does not close these engineering acceptance gates.
