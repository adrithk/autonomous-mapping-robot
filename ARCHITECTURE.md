# Architecture

## Status and scope

This document describes the repository at commit `67ddc21` plus the engineering-harness documentation added on 2026-09-01. It separates **implemented**, **intended**, and **unscoped** behavior. The intended product is autonomous fresh-zone mapping: place the robot in a bounded indoor zone, turn it on, and save the map it creates. Saved-map localization and user-directed navigation are out of scope. Hardware presence is not assumed merely because firmware targets it.

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
BTS7960 driver inputs -> motors   [driver, wiring, and motion unverified]
```

The firmware maps five characters to two open-loop motor commands at a fixed PWM duty, explicitly disables output on an unknown byte, and stops after a 1000 ms command timeout. It counts encoder A transitions using the corresponding B signal for direction, but does not calculate wheel speed or perform PID. It contains no ROS communication, IMU input, transport framing, or hardware fault input.

## Major hardware and computers

| Component | Repository evidence | State |
|---|---|---|
| ESP32 development module | `platformio.ini`, `src/main.cpp`, and builder report in `hardware/parts-list.md` | Reported on hand; exact physical board/variant not recorded; firmware builds |
| Two 12 V, 131:1 geared motors with encoders | Builder report in `hardware/parts-list.md` | Two are expected for the differential drive; exact manufacturer/model and electrical details remain unconfirmed; hardware unverified |
| Two HiLetgo BTS7960 motor-driver modules | Builder report in `hardware/parts-list.md` | Reported purchased; one module is intended per motor. Arrival, wiring, logic levels, limits, and behavior are unverified |
| Cytron MDD10A motor driver | Builder report in `hardware/parts-list.md` | Reported damaged; retired from the intended drivetrain pending separate diagnosis/repair |
| Four-channel logic-level shifter | Builder photograph and `hardware/parts-list.md` | Reported on hand; intended for 5 V encoder signals to 3.3 V ESP32 inputs; unverified |
| Tattu LiPo battery | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, cell count, capacity, connector, and suitability unknown |
| Pololu wheels | Builder report in `hardware/parts-list.md` | Reported on hand; exact model, quantity, diameter, and hub fit unknown |
| 3D-printed differential-drive chassis | Builder report in `hardware/parts-list.md` | Reported built; CAD revision, material, dimensions, and physical test evidence absent |
| Wheel encoders | Included with the reported motors | Electrical interface and counts per revolution are unknown; not implemented or verified |
| IMU | None | Intentionally omitted from the current project plan |
| LiDAR | None | Planned |
| Onboard ROS computer | README design intent and builder report | Planned; a Raspberry Pi has not been acquired or selected |
| Dock/charger | None | Possible future feature, not designed |
| Vacuum subsystem | None | Not scoped |

## Component ownership

| Capability | Intended owner | Current state |
|---|---|---|
| Encoder sampling | ESP32 firmware | Preliminary raw counting code exists; unbuilt and hardware unverified |
| Motor PWM/direction | ESP32 firmware | Open-loop output implemented; hardware unverified |
| Wheel velocity control/PID | ESP32 firmware | Not implemented |
| Immediate command watchdog and actuator-safe state | ESP32 firmware/hardware | Preliminary boot-stop, unknown-input stop, and 1000 ms timeout code exists; unbuilt and hardware unverified |
| System emergency stop/power isolation | Dedicated hardware plus coordinated software reporting | Not designed or verified |
| Serial/transport bridge | ROS computer with matching ESP32 endpoint | Only single-character ESP32 input exists |
| Wheel odometry calculation/publication | TBD design: encoder acquisition on ESP32; ROS-facing ownership must be decided | Not implemented |
| LiDAR driver | ROS computer | Not implemented |
| Robot description and TF coordination | ROS computer | Not implemented |
| SLAM and autonomous exploration | ROS computer using SLAM Toolbox, a frontier-exploration component, and a minimal Nav2 configuration as the exploration motion executor | Not implemented |
| Map saving and run recording | ROS computer | Not implemented |
| Docking orchestration | ROS computer; local dock hardware safety at device layer | Not implemented |
| Vacuum control | TBD; no requirements | Not scoped |

## Firmware responsibilities

Today, `src/main.cpp` owns serial input decoding and direct motor output. The intended microcontroller boundary includes deterministic actuator control, encoder sampling, local velocity loops, and loss-of-command handling. It must remain able to reach an actuator-safe state without depending on ROS scheduling or connectivity.

The current firmware contains preliminary stop-at-boot, unknown-input stop, and command-timeout behavior, but it has not been built or physically validated. It therefore cannot yet be treated as meeting the intended safety boundary.

## ROS 2 system

There are no ROS 2 packages, nodes, launch files, configuration files, message definitions, or bag files in the repository. Ubuntu 24.04, ROS 2 Jazzy, SLAM Toolbox, a frontier-exploration component, a minimal Nav2 configuration, and RViz are intended technologies, not installed or integrated project capabilities.

When introduced, prefer existing packages for hardware control, transforms, filtering, SLAM, and navigation. Repository-specific nodes should bridge genuinely custom hardware or implement robot-specific behavior.

## Data pipelines

- **Command flow now:** terminal character → ESP32 command branch → fixed left/right PWM and direction.
- **Wheel odometry:** planned; encoder resolution, wheel radius, track width, sampling rate, computation owner, covariance, and publication rate are unknown.
- **State estimation:** planned without an IMU; wheel odometry and LiDAR scan matching will provide the available motion information.
- **LiDAR:** planned; device, transport, driver, mounting transform, and scan rate are unknown.
- **SLAM and exploration:** planned; no sensor or odometry inputs exist. SLAM creates the map; an exploration component will choose unknown-area goals, while a minimal Nav2 configuration will execute those goals.
- **Map output:** planned; each autonomous mapping run will save its map and associated run artifacts. Loading old maps for navigation is not a project requirement.

## TF tree

No TF frames are currently published. A future ROS design will likely need `map`, `odom`, `base_link`, sensor frames, and wheel frames, but names and publishers must be specified in an execution plan before implementation. Do not treat that likely structure as a current interface.

## Configuration ownership

- `platformio.ini` owns the ESP32 build target, framework, and serial/upload rates.
- `src/main.cpp` currently owns pin assignments, PWM settings, fixed duty, direction polarity, and command characters.
- No calibrated robot geometry or sensor configuration exists.
- Future hardware constants should be centralized and documented with units; ROS parameters should live in the package that consumes them, with a single authoritative robot description for frames and geometry.

## Safety, logging, and testing

The repository has no independent emergency stop, watchdog, current/thermal monitoring, fault reporting, structured telemetry, automated test cases, or recorded physical results. Serial character echo is the only runtime diagnostic. The test strategy and evidence format are defined in [docs/testing.md](docs/testing.md) and [`results/README.md`](results/README.md).
