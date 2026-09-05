# Encoder-feedback wheel-speed PID

**Status:** Active
**Owner:** Builder with Codex implementation support
**Created:** 2026-09-04
**Updated:** 2026-09-04
**Related roadmap milestone:** Implement and test wheel-speed PID

## Goal

Replace direct keyboard-to-PWM control with one fixed-rate encoder-feedback wheel-speed controller per motor while preserving the existing keyboard bring-up interface and command-loss stop behavior.

## Current State

The ESP32 reads both quadrature encoders and drives two BTS7960 modules. Builder-supplied observations show stable forward and reverse encoder changes, but counts per wheel revolution and final controller gains remain unverified.

## Inputs

- Forward ground observation at PWM 160: approximately 3440 left and 3290 right counts/s.
- Reverse raised-wheel observation at PWM 160: approximately -3280 counts/s on both wheels.
- Intended first straight target: 3000 counts/s.
- Existing GPIO map and 115200-baud keyboard interface.

## Outputs

- Testable wheel-speed controller logic.
- Two ESP32 wheel-speed control loops with telemetry.
- Firmware build result and controlled tuning results.

## Requirements

1. Run both control loops at a nominal 50 Hz using actual elapsed time.
2. Derive measured speed from encoder-count change without assuming unverified counts per revolution.
3. Limit controller output to the 8-bit PWM range.
4. Prevent integral accumulation beyond an explicit bound.
5. Reset controller state on stop and target-direction changes.
6. Preserve stop-at-boot, unknown-input stop, and command timeouts.
7. Report target speed, measured speed, controller output, and raw counts.
8. Ramp straight-drive targets up and down over 300 ms and turn targets over 100 ms while preserving immediate safety stops.

## Files / Components Involved

- `include/wheel_speed_controller.h`
- `test/wheel_speed_controller_test.cpp`
- `src/main.cpp`
- `docs/interfaces.md`
- `results/`

## Implementation Steps

1. Record the supplied encoder observations without treating them as an acceptance test.
2. Add bounded controller logic and focused automated checks.
3. Replace direct PWM commands with signed counts-per-second targets.
4. Build firmware and run controller checks.
5. Tune on raised wheels, then under controlled floor load.

## Automated Verification

- Compile and run `test/wheel_speed_controller_test.cpp` with the local C++ compiler.
- Run PIOArduino firmware build using the installed PlatformIO environment.

## Hardware Verification

With wheels raised first, command forward and reverse and inspect target, measured speed, output, and count signs. Then tune straight motion on the ground using repeated short runs with an accessible power disconnect. Record gains and repeated measured results.

## Acceptance Criteria

- Automated controller checks and firmware build pass.
- Both measured speeds converge without sustained oscillation during raised-wheel tests.
- Three ground trials show both wheels tracking the same straight target within a predefined tolerance.
- Stop and timeout behavior still pass after PID integration.

## Progress

- 2026-09-04 — Plan created from builder-supplied forward and reverse encoder observations; implementation started.
- 2026-09-04 — Added two 50 Hz wheel controllers, counts/s targets, PWM limiting, anti-windup, target-change reset, timeouts, and controller telemetry.
- 2026-09-04 — Standalone controller checks and the full PIOArduino ESP32 build passed. Hardware tuning remains pending.
- 2026-09-04 — Added a 7500 counts/s² target slew limit. Straight commands ramp up over 400 ms and begin ramping down 400 ms before their five-second timeout; explicit and safety stops remain immediate.
- 2026-09-04 — Raised-wheel `w`/`s` telemetry passed the convergence criterion at +/-3000 counts/s with no sustained oscillation. Ground-load tuning and measured stop validation remain pending.
- 2026-09-04 — Revised straight ramps from 400 ms to 300 ms and added 100 ms acceleration/deceleration ramps to turns. The controller test and full ESP32 firmware build passed; this revision still requires a new raised-wheel check.

## Decisions

- Control in encoder counts per second until counts per wheel revolution are physically measured.
- Begin with feed-forward plus PI; derivative gain starts at zero to avoid amplifying raw encoder-speed noise.

## Problems / Blockers

- Final gains require physical tuning.
- Counts per wheel revolution remain unmeasured, so rad/s conversion is deferred.

## Results

- Diagnostic observation: [`../../../results/2026-09-04-open-loop-encoder-observation.md`](../../../results/2026-09-04-open-loop-encoder-observation.md)
- Raised-wheel tracking: [`../../../results/2026-09-04-raised-wheel-pid-tracking.md`](../../../results/2026-09-04-raised-wheel-pid-tracking.md)
- Automated controller test: passed locally on 2026-09-04.
- PIOArduino `esp32dev` firmware build: passed locally on 2026-09-04.

## Follow-up Work

- Convert the interface from counts/s to rad/s after encoder resolution is measured.
- Add the versioned ROS-computer transport only after PID acceptance.
