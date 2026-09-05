# Safe, testable serial motor command interface

**Status:** Active  
**Owner:** Unassigned  
**Created:** 2026-09-01  
**Updated:** 2026-09-01  
**Related roadmap milestone:** Milestone 1 — motor and encoder hardware

## Goal

Validate deterministic command-loss and stop behavior for the ESP32 motor command paths, then record a controlled bench validation of both channels.

## Current State

`src/main.cpp` uses GPIO 25/26 and 32/33 as BTS7960 `RPWM`/`LPWM` pairs, GPIO 27 as the shared driver enable, and GPIO 34/35/36/39 for encoder inputs. `w`, `s`, `a`, `d`, `x`, and `e` are recognized; unknown bytes stop output. Straight and turn commands now set wheel-speed targets for the preliminary PID implementation. The controller test and PIOArduino firmware build passed on 2026-09-04. Pin polarity, driver behavior, controller stability, and physical stop behavior still require controlled validation.

`pio run` passed on 2026-09-01. No automated tests exist. The current interface is documented in `docs/interfaces.md`.

## Inputs

- Existing firmware and `platformio.ini`.
- Two reported-purchased HiLetgo BTS7960 single-channel motor-driver modules; confirm arrival, exact board revision/datasheet, actual wiring, motor supply limits, logic levels, and whether zero duty coasts or brakes. The reported Cytron MDD10A is damaged and is not a test candidate.
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
- 2026-09-03 — Builder reported purchasing two HiLetgo BTS7960 motor drivers to replace the damaged Cytron, and reported a four-channel level shifter on hand for possible encoder signal conditioning. Neither part has been electrically verified.
- 2026-09-03 — Firmware was rewritten for the planned BTS7960 and encoder GPIO map, including explicit stop-at-boot, unknown-input stop, and a 1000 ms command timeout. `pio run` could not be run because PlatformIO is not installed on the current computer. No hardware validation occurred.
- 2026-09-04 — Added automatic raw left/right encoder-count reporting every 200 ms while a movement command is active. No hardware validation occurred.
- 2026-09-04 — Builder reported that the initial mapping produced right turn for `w`, left turn for `s`, forward for `a`, and reverse for `d`. The command signs were remapped accordingly; the corrected mapping still requires a controlled repeat test.
- 2026-09-04 — Increased straight-drive `w`/`s` duty from 100 to 160 and their timeout to 5000 ms at builder request. Turns remain at duty 100 with a 1000 ms timeout. This higher-power behavior requires another raised-wheel test before floor use.
- 2026-09-04 — Builder reported the remapped `a`/`d` directions were reversed; their wheel commands were swapped. The corrected turn mapping still requires a repeat test.
- 2026-09-04 — Initial encoder-feedback wheel-speed control was implemented under plan 002. Controller checks and the full PIOArduino firmware build passed; hardware PID and stop validation remain pending.

## Decisions

- Keep this plan focused on physical boot, stop, invalid-input, timeout, and power-isolation validation; closed-loop control and ROS transport are tracked separately.
- Extract only enough pure logic for deterministic tests rather than introducing a protocol framework.
- Low-level loss-of-command handling belongs on the ESP32; see [decision 001](../../decisions/001-low-level-high-level-responsibility-split.md).

## Problems / Blockers

- The intended motor drivers are two reported-purchased HiLetgo BTS7960 modules, but their arrival, exact revision, wiring, power limits, safe-state electrical behavior, and motor polarity are not recorded or verified.
- The command timeout value cannot be finalized until the expected command source/update rate is chosen.

These block physical completion, but do not block drafting the state table or testable logic with explicitly provisional parameters.

## Results

- Automated baseline: `pio run` passed on 2026-09-01.
- Preliminary motion/PID observations exist under `results/`, but the repeated safety acceptance result required by this plan does not.

## Follow-up Work

- Encoder electrical bring-up and count/sign validation.
- Closed-loop per-wheel velocity control.
- Versioned ROS-computer transport and `cmd_vel` bridge.
- Independent hardware emergency-stop/power-isolation design.
