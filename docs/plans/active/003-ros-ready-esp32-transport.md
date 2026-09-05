# ROS-ready ESP32 transport and selectable firmware builds

**Status:** Active — next implementation task
**Owner:** Builder with Codex implementation support
**Created:** 2026-09-04
**Updated:** 2026-09-05
**Related roadmap milestone:** ROS-ready ESP32 command interface

## Goal

Add a separately selectable, ROS-ready serial firmware build for the ESP32 while
preserving the current keyboard/PID build and its behavior. Validate the protocol
with a non-ROS host harness before depending on Raspberry Pi or ROS installation.

## Current State

`src/main.cpp` is the only Arduino entry point. It implements keyboard commands,
encoder acquisition, 50 Hz wheel control, PID/feed-forward, target ramps, PWM output,
and timeouts. It builds and its controller unit test passes. A raised-wheel test of
the preceding 400 ms straight ramp showed stable +/-3000 counts/s tracking. The
current 300 ms straight and 100 ms turn ramps still require physical validation.

`main_ros.cpp`, the framed protocol, parser tests, the second PlatformIO environment,
and the computer-side harness now exist and pass automated checks. They have not been
physically tested. No ROS workspace or ROS package exists.

## Inputs

- Current GPIO map, polarity, controller limits, and measured encoder signs.
- Proposed serial contract in `docs/interfaces.md`.
- Decisions 001, 002, and 003 under `docs/decisions/`.
- Exact encoder counts per wheel revolution remains `TBD`; the wire format therefore
  uses counts and counts/s, with ROS conversion deferred to the Pi-side plugin.

## Outputs

- `src/main_ros.cpp` as a thin ROS-serial firmware entry point.
- `keyboard` and `ros_serial` PlatformIO environments with exclusive source filters.
- Shared drivetrain runtime used by both entry points without behavioral duplication.
- Fixed-buffer protocol parser/encoder with automated tests.
- Small host-side protocol harness that does not require ROS.
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
7. Commands and telemetry use fixed-width integer fields and the versioned framing,
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
- a small host harness under `tools/` or another clearly documented location
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
6. Add telemetry serialization and a computer-side harness that sends command/stop
   frames and validates returned state.
7. Run automated checks and review boot, timeout, malformed input, integer bounds,
   timer wraparound, and reconnect behavior.
8. Perform a raised-wheel hardware test from the host harness and record the result.
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
- The ROS-serial build can be driven by the non-ROS host harness in both directions.
- No invalid/stale input or disconnect can keep a motion lease alive beyond 250 ms.
- Explicit stop and boot produce zero commanded PWM.
- Protocol documentation and captured test frames agree byte for byte.
- A dated raised-wheel result records three successful timeout/disconnect trials.

## Progress

- 2026-09-04 — Architecture and protocol specified.
- 2026-09-05 — Added mutually exclusive `keyboard` and `ros_serial` builds, shared drivetrain runtime, `main_ros.cpp`, fixed-buffer CRC/sequence parser, state framing, 250 ms watchdog, protocol tests, and a non-ROS Python harness.
- 2026-09-05 — Both firmware environments built and the wheel-controller and protocol tests passed. Hardware validation remains pending.

## Decisions

- Use a Pi-side `ros2_control` plugin rather than micro-ROS; see decision 002.
- Use exclusive PlatformIO entry points rather than compiling two `setup()`/`loop()`
  definitions; see decision 003.
- Keep encoder counts/counts-per-second on the wire until calibration is measured.

## Problems / Blockers

- Counts per wheel revolution is unknown, but it does not block counts/s transport.
- Exact Raspberry Pi and LiDAR variants are unknown; neither blocks host-harness
  protocol development.

## Results

Automated build and unit checks passed on 2026-09-05. No hardware result exists for the ROS-serial firmware.

## Follow-up Work

- Raspberry Pi OS/ROS installation and the `ros2_control` hardware plugin.
- Geometry calibration, robot description, odometry, LiDAR, TF, and SLAM.
- Nav2, frontier exploration, automatic startup, and map saving.
