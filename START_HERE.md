# Start here

## What this project is

A custom differential-drive robot at the beginning of a planned path toward ROS 2-based mapping, localization, and navigation.

## What exists now

One PlatformIO/Arduino firmware program in `src/main.cpp` targets an ESP32 development module. It reads `w`, `s`, `a`, `d`, and `x` from a 115200-baud serial connection and sets two PWM/direction motor channels. `pio run` passed on 2026-09-01.

That proves the firmware compiles. It does **not** prove that a board was flashed, motors moved correctly, the pinout matches the robot, or stopping is safe. There are no automated tests or hardware result records yet. No ROS 2 workspace exists.

## Current work

The current milestone is **safe, testable motor command control**. The active bounded task is [specify, implement, and validate a fail-safe serial motor command interface](docs/plans/active/001-safe-motor-command-interface.md). This harness task did not implement that plan.

## Read next

1. [ARCHITECTURE.md](ARCHITECTURE.md) for real versus planned ownership and flows.
2. [ROADMAP.md](ROADMAP.md) for milestone status and acceptance gates.
3. [docs/interfaces.md](docs/interfaces.md) for the current motor/serial contract.
4. [docs/testing.md](docs/testing.md) before changing or energizing hardware.
5. [`docs/plans/active/`](docs/plans/active/) before implementation.

Codex sessions must also follow [AGENTS.md](AGENTS.md). Architectural decisions live in [`docs/decisions/`](docs/decisions/), and measured evidence belongs in [`results/`](results/).

## Build and run

From the repository root:

```sh
pio run
```

Only after checking the board, driver, power, pin assignments, and wheel clearance:

```sh
pio run --target upload
pio device monitor
```

Use `w`, `s`, `a`, `d`, or `x` as documented in [docs/interfaces.md](docs/interfaces.md). The current firmware latches motion indefinitely and has no timeout, so keep independent power removal within reach. There are no ROS build/run commands yet.

