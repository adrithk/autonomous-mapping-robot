# Start here

## What this project is

A custom differential-drive robot at the beginning of a planned path toward ROS 2-based autonomous indoor mapping. The final behavior is to create and save a fresh map of a zone after the robot is placed there and turned on; saved-map navigation is out of scope.

## What exists now

One PlatformIO/Arduino firmware program in `src/main.cpp` targets an ESP32 development module. It reads `w`, `s`, `a`, `d`, and `x` from a 115200-baud serial connection, measures raw encoder speed at 50 Hz, and runs one preliminary feed-forward/PI wheel-speed controller per BTS7960-driven motor. Straight commands target 3000 counts/s for up to 5000 ms with 300 ms acceleration/deceleration ramps; turns target 1800 counts/s for up to 1000 ms with 100 ms ramps. Controller telemetry is emitted every 200 ms. The controller test and PIOArduino firmware build passed on 2026-09-04.

The build and controller test prove that this revision compiles and its basic bounded-control calculations behave as asserted. A 2026-09-04 raised-wheel forward/reverse test showed stable tracking at +/-3000 counts/s without sustained oscillation. It does **not** prove ground-load performance, straight-line accuracy, calibrated wheel speed, or safe stopping. No ROS 2 workspace exists.

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

Use `w`, `s`, `a`, `d`, or `x` as documented in [docs/interfaces.md](docs/interfaces.md). Straight commands time out after 5 seconds and turns after 1 second; keep independent power removal within reach because these software stops are not an emergency stop. There are no ROS build/run commands yet.
