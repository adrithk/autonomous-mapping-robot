# Verification strategy

Verification has distinct levels. Always report the highest level actually completed:

1. **Build:** code compiles for its target.
2. **Automated test:** repeatable checks assert behavior without the robot.
3. **Bench test:** powered hardware is tested with wheels unloaded or subsystem isolated.
4. **Robot test:** the assembled robot performs a measured test in a controlled space.
5. **Integrated validation:** repeated mission-level trials meet predefined thresholds.

## Automated / Codex-verifiable

### Current checks

Run from the repository root:

```sh
pio run
```

This passed on 2026-09-01. No test cases, lint configuration, CI workflow, ROS workspace, launch files, or configuration validators currently exist.

### Checks to add with relevant features

- Pure command-decoder and watchdog state-machine tests.
- Differential-drive kinematic and encoder conversion tests with known vectors.
- Parser/protocol tests for valid, invalid, truncated, stale, and reordered data.
- Parameter range and configuration schema checks.
- ROS node/unit tests and launch tests when packages exist.
- Planner/mission state-machine tests when custom behavior exists.
- Static analysis and formatting only when configured intentionally for the project.

For future ROS changes, run the applicable package-scoped or workspace commands:

```sh
colcon build
colcon test
colcon test-result --verbose
```

Record command, environment, and exact result in the execution plan. A successful build is not a test pass.

## Physical robot / human-verifiable

Physical work must begin with a test-specific hazard review, stable supports where appropriate, independent power removal within reach, and conservative power/current limits.

| Area | Example measurement/evidence |
|---|---|
| Motor bring-up | Board/driver IDs, wiring revision, unloaded wheel direction per command, stop behavior, current draw, faults |
| Command safety | Stop at boot, loss-of-command timeout, invalid input, reconnect, reset, and independent power-cut behavior |
| Encoders | Counts per wheel revolution in both directions, missed counts, sign convention, sample-rate stability |
| Straight drive | Commanded/measured distance, lateral error, duration, surface, battery condition, repeated trials |
| Rotation | Commanded/measured angle, center displacement, repeated trials |
| Odometry | Position/yaw error over named paths and time; raw and derived logs |
| LiDAR | Mount/alignment, scan orientation, obstruction, range sanity, stationary repeatability |
| SLAM | Environment, bag/config/commit, loop closure, distortion, repeatability, map assessment |
| Navigation | Goal set, success rate, path error, obstacle/recovery behavior, stopping clearance |
| Emergency behavior | Trigger mechanism, stop distance/time, actuator state, recovery requirements |
| Docking | Start poses, success rate, alignment error, charge transition, failure safety |

Thresholds must be chosen in the plan before testing; do not retrofit acceptance criteria to observations.

## Recording results

Store each run in `results/YYYY-MM-DD-short-test-name.md`; add linked logs, bags, plots, photos, or CSV files in `results/YYYY-MM-DD-short-test-name/` if needed. Follow [`results/README.md`](../results/README.md).

Every result must include:

- date, author/operator, Git commit, hardware/config revisions, environment, and test level;
- goal, preconditions/safety setup, procedure, raw observations/measurements, and units;
- explicit pass/fail against predeclared criteria;
- anomalies and follow-up work.

Unrecorded physical observations may guide investigation but do not advance the roadmap.
