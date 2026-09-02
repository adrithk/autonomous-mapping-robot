# Safe, testable serial motor command interface

**Status:** Active  
**Owner:** Unassigned  
**Created:** 2026-09-01  
**Updated:** 2026-09-01  
**Related roadmap milestone:** Milestone 1 — motor and encoder hardware

## Goal

Make the existing ESP32 open-loop motor command path deterministic, fail-safe on command loss, and automatically testable, then record a controlled bench validation of both channels.

## Current State

`src/main.cpp` reads one serial byte and directly selects fixed left/right PWM and direction. `w`, `s`, `a`, `d`, and `x` are recognized; other bytes leave outputs unchanged. Motion has no timeout. Pin polarity, driver behavior, and physical wheel motion have no repository evidence.

`pio run` passed on 2026-09-01. No automated tests exist. The current interface is documented in `docs/interfaces.md`.

## Inputs

- Existing firmware and `platformio.ini`.
- Reported Cytron MDD10A motor driver; confirm the exact board revision/datasheet, actual wiring, motor supply limits, and whether zero duty coasts or brakes.
- A chosen command timeout based on expected command/update rate; currently `TBD`.
- Bench equipment and a means to remove motor power independently.

## Outputs

- A small, hardware-independent command decoder/state model with automated tests.
- ESP32 integration that explicitly stops on boot, invalid/stale command, and chosen fault cases.
- Updated serial and motor interface documentation.
- Dated bench result under `results/` covering both channels and fail-safe behavior.

## Requirements

1. Outputs enter a documented safe state at boot before command processing.
2. Valid commands map deterministically to left/right direction and bounded duty.
3. Invalid input has explicitly specified behavior; line endings cannot accidentally prolong a motion lease.
4. Motion stops when no fresh valid motion command arrives within the specified timeout.
5. Stop behavior and timeout timing do not depend on blocking delays.
6. Command decoding and timeout transitions are testable without attached motors.
7. Duty bounds, GPIO ownership, polarity, and coast/brake assumptions are documented.
8. A normal serial stop must not be described as a hardware emergency stop.

## Files / Components Involved

- `src/main.cpp`
- New focused header/source files under `include/` or `lib/` only if inspection shows they improve testability
- `platformio.ini` and `test/` for a native or otherwise appropriate PlatformIO test environment
- `docs/interfaces.md`, `docs/testing.md`, this plan, and `results/`
- ESP32, motor driver, two motors, power supply, and independent power removal

## Implementation Steps

1. Record the actual driver, wiring, supply, safe-state behavior, and target timeout; stop if these inputs cannot be established.
2. Specify a command/state table including boot, valid motion, explicit stop, invalid byte, stale command, reset, and reconnect behavior.
3. Extract the smallest pure logic boundary needed to test decoding and timeout transitions; avoid a general protocol framework.
4. Add automated cases for every state-table row and time boundary.
5. Integrate the tested behavior into ESP32 output handling with an explicit boot stop and bounded duty.
6. Build firmware and run all tests; review changes for unsafe latching or wraparound/timing errors.
7. Perform unloaded, current-limited bench tests and record measured results.
8. Update interfaces, roadmap evidence, and this plan; move it to `completed/` only if every acceptance criterion passes.

## Automated Verification

- `pio run`
- PlatformIO test command for the test environment added by this plan (exact environment name to be chosen in implementation and recorded here)
- Review test output for decoder mapping, invalid input, timeout boundary, timer wraparound, and stop transitions

Do not add a test command to project documentation until it exists and runs in this repository.

## Hardware Verification

With wheels unloaded, a current-limited motor supply, and independent power removal within reach:

1. Record board, driver, wiring revision, supply voltage/current limit, firmware commit, and timeout.
2. Verify outputs remain stopped during boot/reset and before the first valid command.
3. Send each command and record both wheel directions, PWM behavior, and current.
4. Stop explicitly and measure/observe the resulting driver and wheel state.
5. While commanding motion, disconnect/stop serial traffic and measure time to safe state.
6. Test invalid bytes and terminal line endings without extending motion beyond the specified lease.
7. Repeat critical stop/timeout cases at least three times.
8. Save the result as `results/YYYY-MM-DD-motor-command-bench.md`.

## Acceptance Criteria

- Firmware builds and all new automated tests pass reproducibly.
- Every documented command and timeout transition has an automated assertion.
- No motion output can remain commanded indefinitely after command loss.
- Both channels pass boot, direction, explicit-stop, invalid-input, and timeout bench checks for at least three trials.
- The bench result includes measured timeout values and identifies coast/brake behavior.
- `docs/interfaces.md`, `ARCHITECTURE.md`, `ROADMAP.md`, and this plan reflect the verified state without overstating emergency-stop capability.

## Progress

- 2026-09-01 — Repository audited; firmware build passed; plan created. No feature implementation or hardware verification performed.
- 2026-09-01 — Builder reported a Cytron MDD10A, two expected 12 V 131:1 encoder gearmotors, a Tattu LiPo, Pololu wheels, an ESP32, and a printed chassis. Exact variants and electrical/mechanical details remain unverified; see the [parts list](../../../hardware/parts-list.md).

## Decisions

- Keep the task limited to safe open-loop command bring-up; encoder acquisition and closed-loop speed control are follow-up plans.
- Extract only enough pure logic for deterministic tests rather than introducing a protocol framework.
- Low-level loss-of-command handling belongs on the ESP32; see [decision 001](../../decisions/001-low-level-high-level-responsibility-split.md).

## Problems / Blockers

- The motor driver model is reported as Cytron MDD10A, but its exact revision, wiring, power limits, safe-state electrical behavior, and motor polarity are not recorded or verified.
- The command timeout value cannot be finalized until the expected command source/update rate is chosen.

These block physical completion, but do not block drafting the state table or testable logic with explicitly provisional parameters.

## Results

- Automated baseline: `pio run` passed on 2026-09-01.
- Hardware results: none.

## Follow-up Work

- Encoder electrical bring-up and count/sign validation.
- Closed-loop per-wheel velocity control.
- Versioned ROS-computer transport and `cmd_vel` bridge.
- Independent hardware emergency-stop/power-isolation design.
