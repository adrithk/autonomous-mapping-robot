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
pio run -e keyboard -e ros_serial
```

Both firmware entry points share the wheel controller. Native tests cover controller
logic, encoder arithmetic and serial parsing. The ROS package adds transport,
model and launch/configuration checks. No CI workflow is configured.

For ROS changes, run the applicable package-scoped or workspace commands:

```sh
cd ros_ws
colcon build --packages-select my_bot
colcon test --packages-select my_bot
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

## Native firmware tests

From the repository root, compile and run each standalone test:

```sh
for name in encoder_count_math ros_serial_protocol wheel_speed_controller; do
  clang++ -std=c++11 -Wall -Wextra -Werror -Iinclude "test/${name}_test.cpp" -o "/tmp/${name}_test"
  "/tmp/${name}_test"
done
```

These cover parsing/conversion and controller logic, not live USB timing or ROS.
The [physical demonstration](../results/2026-09-10-real-room-mapping-navigation.md)
is separate evidence; it does not measure protocol fault-response timing.

## ROS package checks

From `ros_ws/src/my_bot`, follow [VALIDATION.md](../ros_ws/src/my_bot/VALIDATION.md)
for native serial/conformance checks. Use a Python environment with pytest, Xacro, PyYAML, NumPy and SciPy:

```sh
python3 -m pytest test/ -q
```

ROS-dependent compilation and plugin loading require Ubuntu/ROS; native tests
cannot substitute for `colcon build`, `colcon test` and physical acceptance.

## Nav2 checks — September 8, 2026

`test/test_navigation.py` under the ROS package adds command-type/limit, collision
bounds, live-map and dependency checks. Its ROS-only check generates both launches,
checks server executables and verifies clock rewrites; it is skipped without ROS.
The existing colcon test command runs it automatically. See plan 008 for required
runtime goal, cancellation, blocked-goal and repeatability checks; offline success
does not establish obstacle avoidance.
