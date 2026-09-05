# Open-loop encoder observation

**Date:** 2026-09-04
**Operator:** Builder
**Git commit:** 5a32d38 plus uncommitted bring-up firmware
**Test level:** Diagnostic robot/bench observations; not an acceptance test
**Hardware revision:** Two reported HiLetgo BTS7960 modules and two reported DFRobot-like encoder motors
**Configuration:** PWM duty 160; raw encoder totals reported every 200 ms

## Goal

Check that both encoder counts change consistently in forward and reverse before implementing wheel-speed control.

## Acceptance criteria

No criteria were declared before these observations, so this record cannot advance an acceptance checkpoint.

## Safety setup

Forward was reported on the ground. Reverse was reported with the wheels raised. Other safety details were not recorded.

## Environment and equipment

Surface, battery voltage, robot load, and measurement instruments were not recorded.

## Procedure

The builder issued `w` for forward and `s` for reverse and supplied the serial encoder totals.

## Measurements and observations

- Forward on ground: both counts increased. The stable portion was approximately 3440 left and 3290 right counts/s, indicating the right wheel was roughly 4-5% slower at equal PWM.
- Reverse with wheels raised: both counts decreased. Across approximately five seconds, the averages were about -3280 left and -3270 right counts/s.
- Both signals appeared monotonic and stable at the 200 ms reporting interval.

## Result

Inconclusive as an acceptance test. The observations are sufficient to choose provisional controller signs and initial targets, but not final gains or encoder calibration.

## Anomalies

Forward and reverse used different load conditions, so their speeds are not directly comparable.

## Artifacts

Raw serial data was supplied in the project conversation and summarized here.

## Follow-up

Measure counts per wheel revolution and perform controlled PID tuning with recorded battery voltage and repeated trials.
