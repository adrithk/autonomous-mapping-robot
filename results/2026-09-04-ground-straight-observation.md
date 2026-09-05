# Ground straight-drive observation

**Date:** 2026-09-04
**Operator:** Builder
**Git commit:** `504b7f9` or later working firmware; exact flashed revision not recorded
**Test level:** Diagnostic robot observation; not an acceptance test
**Hardware revision:** Current assembled differential-drive base
**Configuration:** Ground `w` command; surface, distance, payload, battery voltage, and ramp revision not recorded

## Goal

Capture the builder's qualitative report of ground straight-line behavior for future
payload tuning.

## Acceptance criteria

No quantitative threshold or procedure was declared before the observation.

## Safety setup

Not recorded.

## Environment and equipment

Not recorded.

## Procedure

The builder commanded forward motion with `w` on the ground and visually assessed
the path.

## Measurements and observations

The robot was reported to drive nearly straight while turning very slightly to the
right. No distance, lateral displacement, encoder telemetry, surface, battery state,
or final payload was recorded. The Raspberry Pi and LiDAR were not installed.

## Result

**Inconclusive.** The observation suggests usable preliminary ground behavior but
cannot close the PID acceptance criteria. No gain adjustment is justified from this
single qualitative run, especially before final payload installation.

## Anomalies

Very slight rightward drift.

## Artifacts

Builder report in the project conversation; no separate log or video.

## Follow-up

After the Raspberry Pi and LiDAR are securely mounted, perform three measured
straight runs over a fixed distance and record lateral error, encoder telemetry,
battery voltage, surface, and payload.
