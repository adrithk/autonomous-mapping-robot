# Architecture

## Status and scope

This document describes the repository at commit `67ddc21` plus the engineering-harness documentation added on 2026-09-01. It separates **implemented**, **intended**, and **unscoped** behavior. Hardware presence is not assumed merely because firmware targets it.

## Current implemented path

```text
Human serial terminal
  | one ASCII character at 115200 baud
  v
ESP32 Arduino firmware (src/main.cpp)
  |-- left:  GPIO 25 PWM + GPIO 26 direction
  `-- right: GPIO 33 PWM + GPIO 32 direction
          |
          v
Motor driver inputs -> motors     [driver, wiring, and motion unverified]
```

The firmware maps five characters to two open-loop motor commands at a fixed PWM duty. It contains no ROS communication, feedback controller, encoder input, IMU input, transport framing, command timeout, or hardware fault input.

## Major hardware and computers

| Component | Repository evidence | State |
|---|---|---|
| ESP32 development module | `platformio.ini`, `src/main.cpp`, and builder report in `hardware/parts-list.md` | Reported on hand; exact physical board/variant not recorded; firmware builds |
| Two 12 V, 131:1 geared motors with encoders | Builder report in `hardware/parts-list.md` | Two are expected for the differential drive; exact manufacturer/model and electrical details remain unconfirmed; hardware unverified |
| Cytron MDD10A motor driver | Builder report in `hardware/parts-list.md` | Reported on hand; revision, wiring, limits, and behavior unverified |
| Tattu LiPo battery | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, cell count, capacity, connector, and suitability unknown |
| Pololu wheels | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, quantity, diameter, and hub fit unknown |
| 3D-printed differential-drive chassis | Builder report in `hardware/parts-list.md` | Reported built; CAD revision, material, dimensions, and physical test evidence absent |
| Wheel encoders | Included with the reported motors | Electrical interface and counts per revolution are unknown; not implemented or verified |
| IMU | None | Planned |
| LiDAR | None | Planned |
| Onboard ROS computer | README design intent and builder report | Planned; a Raspberry Pi has not been acquired or selected |
| Dock/charger | None | Possible future feature, not designed |
| Vacuum subsystem | None | Not scoped |

## Component ownership

| Capability | Intended owner | Current state |
|---|---|---|
| Encoder sampling | ESP32 firmware | Not implemented |
| Motor PWM/direction | ESP32 firmware | Open-loop output implemented; hardware unverified |
| Wheel velocity control/PID | ESP32 firmware | Not implemented |
| Immediate command watchdog and actuator-safe state | ESP32 firmware/hardware | Not implemented; `x` is only a normal serial stop command |
| System emergency stop/power isolation | Dedicated hardware plus coordinated software reporting | Not designed or verified |
| Serial/transport bridge | ROS computer with matching ESP32 endpoint | Only single-character ESP32 input exists |
| Wheel odometry calculation/publication | TBD design: encoder acquisition on ESP32; ROS-facing ownership must be decided | Not implemented |
| IMU acquisition | ESP32 is current intent; exact device/driver TBD | Not implemented |
| IMU processing and sensor fusion | ROS computer, likely standard ROS 2 tooling | Not implemented |
| LiDAR driver | ROS computer | Not implemented |
| Robot description and TF coordination | ROS computer | Not implemented |
| SLAM/localization/Nav2 | ROS computer using established ROS 2 packages | Not implemented |
| Mission behavior/exploration/coverage | ROS computer | Not implemented |
| Docking orchestration | ROS computer; local dock hardware safety at device layer | Not implemented |
| Vacuum control | TBD; no requirements | Not scoped |

## Firmware responsibilities

Today, `src/main.cpp` owns serial input decoding and direct motor output. The intended microcontroller boundary includes deterministic actuator control, encoder sampling, local velocity loops, and loss-of-command handling. It must remain able to reach an actuator-safe state without depending on ROS scheduling or connectivity.

The current firmware does not meet that intended safety boundary: commands remain active until another recognized command changes them, invalid bytes do not stop motion, and no timeout exists.

## ROS 2 system

There are no ROS 2 packages, nodes, launch files, configuration files, message definitions, or bag files in the repository. Ubuntu 24.04, ROS 2 Jazzy, SLAM Toolbox, Nav2, and RViz are intended technologies, not installed or integrated project capabilities.

When introduced, prefer existing packages for hardware control, transforms, filtering, SLAM, and navigation. Repository-specific nodes should bridge genuinely custom hardware or implement robot-specific behavior.

## Data pipelines

- **Command flow now:** terminal character → ESP32 command branch → fixed left/right PWM and direction.
- **Wheel odometry:** planned; encoder resolution, wheel radius, track width, sampling rate, computation owner, covariance, and publication rate are unknown.
- **IMU/state estimation:** planned; device, mounting transform, calibration, filter, and fusion configuration are unknown.
- **LiDAR:** planned; device, transport, driver, mounting transform, and scan rate are unknown.
- **SLAM/localization:** planned; no sensor or odometry inputs exist.
- **Navigation:** planned; no robot model, costmaps, controller, planner, or behavior-tree configuration exists.

## TF tree

No TF frames are currently published. A future ROS design will likely need `map`, `odom`, `base_link`, sensor frames, and wheel frames, but names and publishers must be specified in an execution plan before implementation. Do not treat that likely structure as a current interface.

## Configuration ownership

- `platformio.ini` owns the ESP32 build target, framework, and serial/upload rates.
- `src/main.cpp` currently owns pin assignments, PWM settings, fixed duty, direction polarity, and command characters.
- No calibrated robot geometry or sensor configuration exists.
- Future hardware constants should be centralized and documented with units; ROS parameters should live in the package that consumes them, with a single authoritative robot description for frames and geometry.

## Safety, logging, and testing

The repository has no independent emergency stop, watchdog, current/thermal monitoring, fault reporting, structured telemetry, automated test cases, or recorded physical results. Serial character echo is the only runtime diagnostic. The test strategy and evidence format are defined in [docs/testing.md](docs/testing.md) and [`results/README.md`](results/README.md).
