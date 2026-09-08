# ROS-ready ESP32 transport and selectable firmware builds

**Status:** Source implemented — physical acceptance pending
**Owner:** Builder with Codex implementation support
**Created:** 2026-09-04
**Updated:** 2026-09-07
**Related roadmap milestone:** ROS-ready ESP32 command interface

## Goal

Add a separately selectable, ROS-ready serial firmware build for the ESP32 while
preserving the current keyboard/PID build and its behavior. Validate its protocol
logic before depending on Raspberry Pi or ROS installation.

## Current State

`src/main.cpp` is the keyboard Arduino entry point; `src/main_ros.cpp` is separately selected. It implements keyboard commands,
encoder acquisition, 50 Hz wheel control, PID/feed-forward, target ramps, PWM output,
and timeouts. It builds and its controller unit test passes. A raised-wheel test of
the preceding 400 ms straight ramp showed stable +/-3000 counts/s tracking. The
current 300 ms straight and 100 ms turn ramps still require physical validation.

`main_ros.cpp`, the framed protocol, parser tests, the second PlatformIO environment,
now exist and pass automated checks. They have not been
physically tested. The ROS package is included at `ros_ws/src/my_bot`; see plan 004.

## Inputs

- Current GPIO map, polarity, controller limits, and measured encoder signs.
- Proposed serial contract in `docs/interfaces.md`.
- Decisions 001, 002, and 003 under `docs/decisions/`.
- Preliminary builder measurement: approximately 41850 counts/10 turns on each wheel
  gives 4185 counts/revolution. Version 2 commands use rad/s; feedback retains raw units.

## Outputs

- `src/main_ros.cpp` as a thin ROS-serial firmware entry point.
- `keyboard` and `ros_serial` PlatformIO environments with exclusive source filters.
- Shared drivetrain runtime used by both entry points without behavioral duplication.
- Fixed-buffer protocol parser/encoder with automated tests.
- Updated interface/build documentation and verification results.

## Requirements

1. The default `pio run` build must preserve keyboard firmware behavior.
2. `pio run -e ros_serial` must compile only `main_ros.cpp` as the Arduino entry point.
3. Both entry points must reuse one implementation of motor output, encoder sampling,
   target ramps, PID, polarity, output limiting, and stop behavior.
4. Protocol parsing must not allocate Arduino `String` objects or accept unbounded
   input; use a fixed buffer and reject overflow.
5. Only valid, in-order command frames refresh the 250 ms motion watchdog.
6. Explicit stop, watchdog expiry, parser overflow, and boot must produce zero motor
   output. A single malformed frame does not refresh the lease; subsequent valid
   frames may recover unless a latched hardware fault is introduced later.
7. Commands use finite decimal rad/s; telemetry and sequences use fixed-width integer fields and the versioned framing,
   units, checksum, and limits specified in `docs/interfaces.md`.
8. Sequence wraparound must be handled intentionally; replayed/out-of-order frames
   must not extend motion.
9. Host disconnect/reconnect must never cause a previous command to resume.
10. Do not create the ROS workspace or fake hardware-dependent measurements in this
    task.

## Files / Components Involved

- `platformio.ini`
- `src/main.cpp`
- `src/main_ros.cpp` (new)
- focused shared files under `include/`, `lib/`, or `src/`
- `test/`
- `docs/interfaces.md`, `docs/testing.md`, `START_HERE.md`, and this plan

## Implementation Steps

1. Add tests around reusable command/watchdog/ramp behavior before moving code.
2. Extract the shared drivetrain runtime in small steps; build and test the keyboard
   firmware after each behavior-affecting step.
3. Add PlatformIO `keyboard` and `ros_serial` environments with `keyboard` as
   `default_envs`; verify source-filter behavior before adding the new entry point.
4. Implement and test the fixed-buffer frame parser, CRC-16/CCITT-FALSE calculation,
   range checks, and sequence handling without attached hardware.
5. Add `main_ros.cpp` using the shared drivetrain runtime and protocol implementation.
6. Add and test telemetry serialization.
7. Run automated checks and review boot, timeout, malformed input, integer bounds,
   timer wraparound, and reconnect behavior.
8. Perform a raised-wheel hardware test through the future Pi-side connection and record the result.
9. Update project state; do not mark the plan complete until every criterion passes.

## Automated Verification

- Current controller unit test.
- New native parser, CRC, sequence, bounds, watchdog, and frame-serialization tests.
- `pio run` for the default keyboard environment after it exists.
- `pio run -e keyboard` and `pio run -e ros_serial` after both environments exist.
- `git diff --check`.

Do not claim these new commands passed until their environments and tests exist.

## Hardware Verification

With wheels raised and independent motor-power removal available:

1. Boot/reboot with the host disconnected and verify no motion.
2. Send valid forward, reverse, turn, zero, and explicit-stop frames.
3. Stop frames for longer than 250 ms while moving and measure the stop latency.
4. Send bad CRC, malformed, overlong, stale-sequence, and out-of-range frames.
5. Disconnect and reconnect USB while the last command was nonzero.
6. Confirm telemetry signs, sequence acknowledgement, counts, measured speeds, PWM,
   and status flags.
7. Repeat safety-critical cases three times and record a dated result.

## Acceptance Criteria

- Both firmware environments build and all protocol/controller tests pass.
- The keyboard build retains its documented command behavior.
- The ROS-serial build accepts documented command frames and emits documented state frames.
- No invalid/stale input or disconnect can keep a motion lease alive beyond 250 ms.
- Explicit stop and boot produce zero commanded PWM.
- Protocol documentation and captured test frames agree byte for byte.
- A dated raised-wheel result records three successful timeout/disconnect trials.

## Progress

- 2026-09-07 — Updated only ROS firmware/protocol to version 2 rad/s commands,
  with ROS-only conversion constants at preliminary 4185 counts/revolution per wheel.
  Keyboard main and shared drivetrain/controller files unchanged. Both PlatformIO
  environments built successfully. Native controller and expanded protocol/conversion
  tests passed with clang++ C++11, warnings as errors. Tests cover decimal/scientific
  input, invalid/nonfinite/overflow values, version-1 rejection, CRC, sequence wrapping,
  buffer overflow, embedded NUL, conversion signs/zero/limits and state formatting.
  Physical validation and Pi plugin integration remain pending; plan stays active.

- 2026-09-06 — At builder request, the separate `my_bot` package now includes
  estimated 1.6 kg mass distribution/inertias, contact parameters, Jazzy
  `gz_ros2_control`, simulated LiDAR, a local room, controller configuration and
  simulation launch. Four local structural tests passed; no Gazebo/ROS runtime
  was available on this Mac. This does not implement the Pi serial hardware
  plugin or validate the ESP32; those tasks and physical acceptance remain open.

- 2026-09-06 — Created preliminary kinematic description in the separate sibling
  `my_bot` package at the builder's request; local Xacro/geometry/syntax checks
  passed. Revised geometry is recorded in interfaces and parts list. No ROS
  runtime or hardware validation occurred; the serial bridge remains unimplemented.

- 2026-09-05 — Simplified keyboard `e` output to left/right raw encoder counts only; periodic motion telemetry is unchanged. `pio run` and `git diff --check` passed. Upload and hardware verification pending.

- 2026-09-04 — Architecture and protocol specified.
- 2026-09-05 — Added mutually exclusive `keyboard` and `ros_serial` builds, shared drivetrain runtime, `main_ros.cpp`, fixed-buffer CRC/sequence parser, state framing, 250 ms watchdog, and protocol tests.
- 2026-09-05 — Both firmware environments built and the wheel-controller and protocol tests passed. Hardware validation remains pending.
- 2026-09-05 — Fixed receive overflow to report on the first excess byte and immediately call `RobotDrive::stop()`, without waiting for newline or watchdog expiry. Added parser regression checks for the buffer boundary, discarded frame remainder, and recovery on the next frame. On macOS, `pio run` (default keyboard) and `pio run -e ros_serial` passed using the installed PlatformIO executable; both native tests compiled with `clang++ -std=c++11 -Wall -Wextra -Werror -Iinclude` and executed successfully. Physical overflow-stop validation remains pending.

Pre-push check on 2026-09-05: both firmware environments built successfully with
`pio run -e keyboard -e ros_serial`; both native controller/protocol tests passed
with `clang++ -std=c++11 -Wall -Wextra -Werror -Iinclude`, and `git diff --check`
passed. The parts list now records the purchased Pi 5 kit and delivered RPLIDAR
A1M8. Builder-reported wheel separation (0.233 m) and radius (0.040 m) are recorded
as provisional geometry; encoder calibration and physical serial validation remain
pending.

## Decisions

- Use a Pi-side `ros2_control` plugin rather than micro-ROS; see decision 002.
- Use exclusive PlatformIO entry points rather than compiling two `setup()`/`loop()`
  definitions; see decision 003.
- Decision 004: ROS-only ESP32 adapter converts rad/s commands; feedback retains raw counts/counts-per-second.

## Problems / Blockers

- 2026-09-06 — Builder moved the motors. Ask for revised wheel separation and
  axle/chassis offsets before ROS motion/odometry configuration, and revised
  footprint/LiDAR offsets before TF/navigation setup. Previous geometry is stale;
  counts/s transport testing can proceed without these measurements.

- Preliminary 4185 counts/revolution per wheel needs repeatable calibration validation.
- Raspberry Pi 5 (8GB) and RPLIDAR A1M8 are identified in the parts list;
  Pi setup and physical serial validation remain pending.

## Results

Automated build and unit checks passed on 2026-09-05. No hardware result exists for the ROS-serial firmware.

## Follow-up Work

- Raspberry Pi OS/ROS installation and the `ros2_control` hardware plugin.
- Geometry calibration, robot description, odometry, LiDAR, TF, and SLAM.
- Nav2, frontier exploration, automatic startup, and map saving.

2026-09-07: Pi plugin source now exists in sibling my_bot; see active plan 004.
Its offline tests do not satisfy this plan's physical watchdog/reconnect criteria.

## Repository consolidation — 2026-09-07

The full ROS package is now in `ros_ws/src/my_bot` in this repository. Earlier
sibling-package references are historical. Source behavior and pending physical
acceptance are unchanged. See [current status](../../../ROADMAP.md).
