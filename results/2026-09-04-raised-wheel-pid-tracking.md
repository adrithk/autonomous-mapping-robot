# Raised-wheel PID tracking

**Date:** 2026-09-04
**Operator:** Builder
**Git commit:** `5a32d38` plus uncommitted PID/ramp firmware
**Test level:** Bench
**Hardware revision:** ESP32, two BTS7960 motor drivers, and two quadrature-encoder gearmotors
**Configuration:** Wheels raised; 50 Hz controller; target +/-3000 counts/s; 400 ms target ramp; `Kp=0.020`, `Ki=0.010`, `Kd=0`, feed-forward `0.048 PWM/(count/s)`; five-second command timeout

## Goal

Check forward and reverse unloaded wheel-speed tracking, ramp behavior, encoder signs, and visible timeout behavior with the preliminary controller.

## Acceptance criteria

The active PID plan required both measured speeds to converge without sustained oscillation during raised-wheel tests. Ground tracking and stop-safety acceptance are separate tests.

## Safety setup

The builder reported that the robot was tested in the air with the wheels unloaded. Battery voltage, current limiting, supports, and power-disconnect arrangement were not recorded.

## Environment and equipment

ESP32 serial telemetry at 115200 baud. Exact motor model, battery voltage, instrumentation, and mechanical support were not recorded.

## Procedure

With the wheels raised, the builder sent `w`, allowed its five-second timeout, and then sent `s`. The ESP32 reported requested speed, ramped target, encoder-measured speed, controller PWM, and accumulated encoder counts every 200 ms.

## Measurements and observations

- Forward ramp telemetry advanced from 0 to approximately 1545 counts/s and then 3000 counts/s across two reporting intervals, consistent with the configured 400 ms ramp.
- At the full +3000 counts/s target, the left wheel generally measured 3050 counts/s, occasionally 3100 counts/s. The right wheel generally measured 3000 counts/s, occasionally 3050 counts/s.
- Steady forward PWM settled near 142-144 left and 145-146 right.
- Reverse ramp telemetry advanced from 0 to approximately -1575 counts/s and then -3000 counts/s.
- At the full -3000 counts/s target, both wheels generally measured -3000 counts/s, with occasional -2950 or -3050 samples.
- Steady reverse PWM settled near -146 on both wheels.
- Before each timeout, the requested command changed to zero and the ramped target reached approximately +/-1500 counts/s at the next reported midpoint. The firmware then printed `Stopped: command timeout` at the five-second limit.
- Encoder counts increased during `w` and decreased during `s`, matching the controller convention.
- The beginning of the supplied transcript contained duplicated and malformed text. Later complete telemetry records were internally consistent; the malformed section was not used for measurements.

## Result

**Pass** for the predeclared raised-wheel convergence criterion. Both wheels converged to the requested unloaded speed without sustained oscillation in forward and reverse.

This does not establish ground-load tuning, straight-line driving, calibrated wheel speed, or a measured safe stop. The timeout message was observed, but no post-stop zero-PWM telemetry was captured.

## Anomalies

- The left forward wheel ran approximately 1.7-3.3% above target in the reported steady samples.
- The initial serial transcript was corrupted or duplicated.
- No current, voltage, wheel RPM, or counts-per-revolution measurement was captured.

## Artifacts

Raw telemetry was supplied in the project conversation. No separate log file was captured.

## Follow-up

1. Test `x` and timeout stopping with explicit post-stop PWM telemetry.
2. Perform three short controlled ground runs and record lateral drift, both measured wheel speeds, surface, battery voltage, and travel distance.
3. Measure encoder counts per output-shaft revolution before converting the controller interface to rad/s.
