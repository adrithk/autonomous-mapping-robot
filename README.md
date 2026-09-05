# Autonomous Indoor Mapping Robot

This repository develops a custom differential-drive robot whose final job is to autonomously map previously unknown indoor zones with ROS 2. The complete product behavior is simple: place the robot in a clear, bounded indoor zone, turn it on, let it explore and create a fresh map, then save that map. It does not need to reload maps, localize in old maps, accept user navigation goals, or reroute through prior maps.

## Project status

The project is in **wheel-control validation and ROS-transport bench testing**. The ESP32 has separate keyboard and ROS-serial firmware builds that share the same BTS7960 motor output, quadrature encoder acquisition, ramps, and feed-forward/PI wheel-speed controllers. Both builds compile and the controller/protocol tests pass. A raised-wheel forward/reverse test showed stable tracking at +/-3000 encoder counts/s using the preceding 400 ms ramp configuration. A qualitative ground observation reported only very slight rightward drift, but no measured ground acceptance test has been completed.

The current 300 ms straight ramps, 100 ms turn ramps, and new ROS-serial watchdog still need physical validation. Encoder counts per wheel revolution, final loaded PID behavior, formal stop tests, and exact electrical specifications remain unresolved. No Raspberry Pi ROS 2 workspace, Pi-side hardware plugin, LiDAR integration, odometry, SLAM, Nav2, autonomous exploration, or automatic map saving exists yet. An IMU is intentionally outside the project plan.

## Current firmware behavior

- Target: ESP32 development module using Arduino and PlatformIO
- Serial: 115200 baud
- Commands: `w` forward, `s` reverse, `a` turn left, `d` turn right, `x` stop
- Motor outputs: left BTS7960 `RPWM` GPIO 25 and `LPWM` GPIO 26; right `RPWM` GPIO 32 and `LPWM` GPIO 33; all driver enables on GPIO 27
- Encoders: left A/B on GPIO 34/35; right A/B on GPIO 36 (`VP`)/39 (`VN`)
- PWM configuration: 20 kHz, 8-bit, closed-loop output limited to 200/255
- Initial wheel-speed targets: 3000 counts/s straight, 1800 counts/s turning
- Control: nominal 50 Hz with encoder-speed feedback, bounded integral, and feed-forward/PI output
- Motion leases: five seconds for straight commands and one second for turns
- Ramps: 300 ms for straight motion and 100 ms for turns

The firmware stops on explicit `x`, unknown input, and command timeout, but those software paths are not a verified hardware emergency stop. Follow [docs/testing.md](docs/testing.md), keep motor-power removal accessible, and do not infer safety from compilation or one successful drive observation.

## Intended architecture

The accepted design separates time-sensitive motor and encoder work on the ESP32 from higher-level sensing, mapping, exploration, and map saving on a Raspberry Pi. ROS 2 Jazzy and `ros2_control` will run on the Pi. A custom `ros2_control` hardware plugin will exchange versioned USB-serial wheel commands and feedback with the ESP32; the ESP32 will not run micro-ROS or directly subscribe to ROS topics in the first version. See [ARCHITECTURE.md](ARCHITECTURE.md) and the [ROS platform roadmap](docs/ros-platform-roadmap.md).

The ROS-ready ESP32 work is tracked in [plan 003](docs/plans/active/003-ros-ready-esp32-transport.md). `src/main.cpp` remains the default keyboard build; `src/main_ros.cpp` is selected explicitly and accepts versioned, checksummed serial commands with a 250 ms watchdog. It has automated build/parser evidence but still needs raised-wheel testing before Pi integration.

## Intended mapping run

1. The operator places the robot in a clear, bounded indoor zone and turns on motor power.
2. The robot performs startup checks, waits for valid wheel-odometry, LiDAR, and transform data, then begins a new SLAM map.
3. An exploration component selects reachable unexplored areas; an internal motion controller drives to them while the ESP32 maintains safe wheel control.
4. When no useful unexplored area remains, the robot stops and saves the map and run artifacts.

The map is an output of the run. Loading an old map and navigating it is deliberately outside this project's scope.

## Build

Install PlatformIO, then run from the repository root:

```sh
pio run
pio run -e keyboard
pio run -e ros_serial
```

Upload and monitor only when the target board and wiring have been checked:

```sh
pio run -e keyboard --target upload
pio run -e ros_serial --target upload
pio device monitor
```

No ROS 2 workspace exists yet, so there are currently no `colcon` build or run commands.

## Repository guide

- [START_HERE.md](START_HERE.md) — shortest onboarding and current work
- [AGENTS.md](AGENTS.md) — persistent instructions for AI-assisted work
- [ARCHITECTURE.md](ARCHITECTURE.md) — ownership and system/data flows
- [ROADMAP.md](ROADMAP.md) — evidence-based capability milestones
- [hardware/parts-list.md](hardware/parts-list.md) — reported hardware, missing components, and unresolved specifications
- [docs/interfaces.md](docs/interfaces.md) — current and planned interfaces
- [docs/testing.md](docs/testing.md) — automated and physical verification
- [docs/ros-platform-roadmap.md](docs/ros-platform-roadmap.md) — staged Raspberry Pi, ROS 2, LiDAR, SLAM, Nav2, exploration, and map-saving plan
- [`docs/plans/`](docs/plans/) — active and completed execution plans
- [`docs/decisions/`](docs/decisions/) — architecture decision records
- [`results/`](results/) — measured test evidence
- `src/main.cpp` — current ESP32 firmware
- `src/main_ros.cpp` — separately selected ROS-serial ESP32 firmware
- `src/robot_drive.cpp` — shared encoder, PID, ramp, PWM, and watchdog runtime

The standard engineering loop is: define, specify, plan, implement, automatically verify, review, hardware-test, record results, update documentation and plan, commit, then choose the next bounded task.
