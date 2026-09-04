# Autonomous Indoor Mapping Robot

This repository contains the earliest firmware for a custom differential-drive robot that autonomously maps previously unknown indoor zones with ROS 2. The complete product behavior is simple: place the robot in a clear, bounded indoor zone, turn it on, let it explore and create a fresh map, then save that map. It does not need to reload maps, localize in old maps, accept user navigation goals, or reroute through prior maps.

## Project status

The project is in the **motor-control bring-up** stage. The current ESP32 firmware accepts single-character commands over USB serial and drives left and right PWM/direction outputs. The firmware builds successfully, but the repository contains no recorded physical test results, so motor motion, wiring, direction, and stopping behavior are **not yet verified**.

Encoder-based wheel-speed control, LiDAR, an onboard ROS computer, ROS 2 packages, odometry, SLAM, autonomous exploration, map saving, docking, and a vacuum subsystem are not implemented in this repository. An IMU is intentionally outside the current project plan.

## Current firmware behavior

- Target: ESP32 development module using Arduino and PlatformIO
- Serial: 115200 baud
- Commands: `w` forward, `s` reverse, `a` turn left, `d` turn right, `x` stop
- Motor outputs: PWM on GPIO 25/33 and direction on GPIO 26/32
- PWM configuration: 20 kHz, 8-bit, fixed duty value 100/255

This is open-loop bring-up code. It has no command timeout, encoder feedback, velocity controller, or verified emergency-stop mechanism. Do not operate it around people or with the wheels loaded until the safety checks in [docs/testing.md](docs/testing.md) are followed.

## Intended architecture

The intended design separates time-sensitive motor and encoder work on the ESP32 from higher-level sensing, state estimation, mapping, exploration, and map saving on a future ROS 2 computer. See [ARCHITECTURE.md](ARCHITECTURE.md) for implemented and planned component ownership.

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
```

Upload and monitor only when the target board and wiring have been checked:

```sh
pio run --target upload
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
- [`docs/plans/`](docs/plans/) — active and completed execution plans
- [`docs/decisions/`](docs/decisions/) — architecture decision records
- [`results/`](results/) — measured test evidence
- `src/main.cpp` — current ESP32 firmware
- `src/oldcode.md` — preserved historical bring-up sketch

The standard engineering loop is: define, specify, plan, implement, automatically verify, review, hardware-test, record results, update documentation and plan, commit, then choose the next bounded task.
