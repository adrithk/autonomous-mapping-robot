# Architecture

## Status and scope

This document describes the working tree after commit `504b7f9`. It separates **implemented**, **intended**, and **unscoped** behavior. The intended product is autonomous fresh-zone mapping: place the robot in a bounded indoor zone, turn it on, and save the map it creates. Saved-map localization and user-directed navigation are out of scope. Hardware presence is not assumed merely because firmware targets it.

## Current implemented path

```text
Human serial terminal
  | one ASCII character at 115200 baud
  v
ESP32 Arduino firmware (src/main.cpp)
  |-- shared BTS7960 enable: GPIO 27
  |-- left BTS7960:  GPIO 25 RPWM + GPIO 26 LPWM
  |-- right BTS7960: GPIO 32 RPWM + GPIO 33 LPWM
  |-- left encoder: GPIO 34 A + GPIO 35 B
  `-- right encoder: GPIO 36/VP A + GPIO 39/VN B
          |
          v
BTS7960 driver inputs -> motors   [motion observed; formal safety validation pending]
```

The default keyboard firmware maps characters to signed wheel-speed targets, measures encoder speed at 50 Hz, and runs one preliminary feed-forward/PI controller per wheel. Straight commands target 3000 counts/s for up to 5000 ms with 300 ms ramps; turns target 1800 counts/s for up to 1000 ms with 100 ms ramps. A second, separately built `main_ros.cpp` accepts checksummed wheel commands, enforces a 250 ms watchdog, and returns state telemetry. Both builds share `src/robot_drive.cpp`. Both firmware environments build and protocol/controller unit tests pass. The ROS-serial build has not been uploaded or physically tested, and no ROS workspace exists.

## Major hardware and computers

| Component | Repository evidence | State |
|---|---|---|
| ESP32 development module | `platformio.ini`, `src/main.cpp`, and builder report in `hardware/parts-list.md` | Reported on hand; exact physical board/variant not recorded; firmware builds |
| Two 12 V, 131:1 geared motors with encoders | Builder report and dated results | Both motors and encoder signs have operated; exact manufacturer/model, current ratings, and counts/revolution remain unconfirmed |
| Two HiLetgo BTS7960 motor-driver modules | Builder report and dated results | Both channels have operated with PID; exact revision, limits, thermal behavior, and safe-state behavior remain unverified |
| Cytron MDD10A motor driver | Builder report in `hardware/parts-list.md` | Reported damaged; retired from the intended drivetrain pending separate diagnosis/repair |
| Four-channel logic-level shifter | Builder photograph, wiring report, and encoder observations | Used for encoder signals; electrical levels and edge quality remain unmeasured |
| Tattu LiPo battery | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, cell count, capacity, connector, and suitability unknown |
| Pololu wheels | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, quantity, diameter, and hub fit unknown |
| 3D-printed differential-drive chassis | Builder report in `hardware/parts-list.md` | Reported built; CAD revision, material, dimensions, and physical test evidence absent |
| Wheel encoders | Included with the reported motors and dated results | Counting and direction are implemented and observed; voltage, edge quality, missed counts, and counts/revolution remain unverified |
| IMU | None | Intentionally omitted from the current project plan |
| LiDAR | None | Planned |
| Onboard ROS computer | README design intent and builder report | Planned; a Raspberry Pi has not been acquired or selected |
| Dock/charger | None | Possible future feature, not designed |
| Vacuum subsystem | None | Not scoped |

## Component ownership

| Capability | Intended owner | Current state |
|---|---|---|
| Encoder sampling | ESP32 firmware | Implemented at 50 Hz; forward/reverse count signs observed; resolution uncalibrated |
| Motor PWM/direction | ESP32 firmware | Shared BTS7960 output implemented; physical motion observed |
| Wheel velocity control/PID | ESP32 firmware | Feed-forward/PI builds; raised-wheel convergence passed on the preceding ramp revision; final-payload validation pending |
| Immediate command watchdog and actuator-safe state | ESP32 firmware/hardware | Keyboard timeouts and ROS-serial 250 ms watchdog implemented; formal repeated physical stop validation pending |
| System emergency stop/power isolation | Dedicated hardware plus coordinated software reporting | Not designed or verified |
| Serial/transport bridge | ROS computer with matching ESP32 endpoint | ESP32 endpoint builds/tests; Pi `ros2_control` plugin not implemented |
| Wheel odometry calculation/publication | Standard `diff_drive_controller` using state from the Pi hardware plugin | Not implemented |
| LiDAR driver | ROS computer | Not implemented |
| Robot description and TF coordination | ROS computer | Not implemented |
| SLAM and autonomous exploration | ROS computer using SLAM Toolbox, a frontier-exploration component, and a minimal Nav2 configuration as the exploration motion executor | Not implemented |
| Map saving and run recording | ROS computer | Not implemented |
| Docking orchestration | ROS computer; local dock hardware safety at device layer | Not implemented |
| Vacuum control | TBD; no requirements | Not scoped |

## Firmware responsibilities

`src/main.cpp` and `src/main_ros.cpp` are mutually exclusive entry points. Shared code owns deterministic actuator control, encoder sampling, local velocity loops, ramps, and loss-of-command handling. The ROS-serial endpoint uses a fixed-buffer parser and remains able to stop without depending on ROS scheduling or connectivity.

Both builds compile, but only the keyboard/PID path has physical motion evidence. The new serial parser, watchdog, and reconnect behavior require raised-wheel validation before they can be treated as meeting the intended safety boundary.

## ROS 2 system

There are no ROS 2 packages, nodes, launch files, configuration files, message definitions, or bag files in the repository. The accepted target is Ubuntu 24.04 and ROS 2 Jazzy on a Raspberry Pi, using a custom `ros2_control` serial `SystemInterface`, standard `diff_drive_controller`, the exact LiDAR's supported driver, SLAM Toolbox, Nav2, and a validated frontier explorer. See `docs/ros-platform-roadmap.md`.

When introduced, prefer existing packages for hardware control, transforms, filtering, SLAM, and navigation. Repository-specific nodes should bridge genuinely custom hardware or implement robot-specific behavior.

## Data pipelines

- **Command flow now:** keyboard build uses terminal characters; ROS-serial build accepts version-2 left/right rad/s frames, converted by the ROS-only `include/ros_wheel_units.h` to counts/s using preliminary per-wheel calibration. Both feed the same local wheel controllers.
- **Wheel odometry:** planned in `diff_drive_controller`; encoder resolution, wheel radius, wheel separation, covariance, and publication rate remain unmeasured/unconfigured.
- **State estimation:** planned without an IMU; wheel odometry and LiDAR scan matching will provide the available motion information.
- **LiDAR:** planned; device, transport, driver, mounting transform, and scan rate are unknown.
- **SLAM and exploration:** planned; no sensor or odometry inputs exist. SLAM creates the map; an exploration component will choose unknown-area goals, while a minimal Nav2 configuration will execute those goals.
- **Map output:** planned; each autonomous mapping run will save its map and associated run artifacts. Loading old maps for navigation is not a project requirement.

## TF tree

No TF frames are currently published. The planned primary chain is `map -> odom -> base_link -> laser`: SLAM Toolbox owns `map -> odom`, `diff_drive_controller` initially owns `odom -> base_link`, and robot state publisher owns the fixed LiDAR transform.

## Configuration ownership

- `platformio.ini` owns the mutually exclusive `keyboard` and `ros_serial` builds and makes `keyboard` the default.
- `src/robot_drive.cpp` owns shared pins, PWM settings, controller gains/limits, encoder sampling, and polarity. Each entry point owns its command interface and lease/ramp values.
- No calibrated robot geometry or sensor configuration exists.
- Future hardware constants should be centralized and documented with units; ROS parameters should live in the package that consumes them, with a single authoritative robot description for frames and geometry.

## Safety, logging, and testing

The repository has software command timeouts, ROS-serial status telemetry, controller/protocol tests, and dated preliminary physical results. It still has no verified independent emergency stop, driver-fault input, or current/thermal monitoring. The test strategy and evidence format are defined in [docs/testing.md](docs/testing.md) and [`results/README.md`](results/README.md).

## Pi-side hardware implementation update — 2026-09-07

The sibling `/Users/adrithk/Developer/my_bot` package now implements a C++
`my_bot/Esp32System` ros2_control SystemInterface and version-2 POSIX USB transport.
It exports wheel rad/s commands and radians/rad/s state, with preliminary 4185
counts/revolution feedback calibration. Default bringup selects Gazebo; real control
requires `mode:=hardware` and an explicit serial_device. The two models cannot be
selected together. Hardware uses wall time; simulation and its teleop use /clock.

Startup requires fresh v2 telemetry and an acknowledged explicit stop. Runtime
telemetry/ACK stalls over 200 ms, new firmware status faults, reboot/time regression
or I/O failure fault control and attempt a stop. No automatic reconnection/replay.
The independent ESP32 250 ms watchdog remains required. Previously latched firmware
status bits are logged; repeated occurrences of the same bit are not observable.
See sibling HARDWARE.md and WSL_SETUP.md for operation and limitations.

Offline model/configuration and pseudo-terminal transport tests passed, including
compatibility with this repository's actual firmware parser/state formatter.
ROS plugin compilation/loading, Gazebo/WSL launch and physical validation remain
pending. This source implementation supersedes earlier statements that the Pi-side
plugin is absent; it does not advance hardware/integrated acceptance milestones.
