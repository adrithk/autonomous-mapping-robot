# Autonomous Differential-Drive Mapping Robot

This repository contains the earliest firmware for a custom differential-drive robot intended to grow into a ROS 2 mapping and navigation platform.

## Project status

The project is in the **motor-control bring-up** stage. The current ESP32 firmware accepts single-character commands over USB serial and drives left and right PWM/direction outputs. The firmware builds successfully, but the repository contains no recorded physical test results, so motor motion, wiring, direction, and stopping behavior are **not yet verified**.

Encoders, IMU, LiDAR, an onboard ROS computer, ROS 2 packages, odometry, SLAM, localization, Nav2, exploration, docking, and a vacuum subsystem are not implemented in this repository.

## Current firmware behavior

- Target: ESP32 development module using Arduino and PlatformIO
- Serial: 115200 baud
- Commands: `w` forward, `s` reverse, `a` turn left, `d` turn right, `x` stop
- Motor outputs: PWM on GPIO 25/33 and direction on GPIO 26/32
- PWM configuration: 20 kHz, 8-bit, fixed duty value 100/255

This is open-loop bring-up code. It has no command timeout, encoder feedback, velocity controller, or verified emergency-stop mechanism. Do not operate it around people or with the wheels loaded until the safety checks in [docs/testing.md](docs/testing.md) are followed.

## Intended architecture

The intended design separates time-sensitive motor and encoder work on the ESP32 from higher-level sensing, state estimation, mapping, and navigation on a future ROS 2 computer. See [ARCHITECTURE.md](ARCHITECTURE.md) for implemented and planned component ownership.

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
