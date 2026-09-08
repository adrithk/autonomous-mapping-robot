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

The original firmware build passed on 2026-09-01. On 2026-09-04, the wheel-speed controller test and firmware build passed after PID integration. On 2026-09-05, the `keyboard` and `ros_serial` firmware environments built and the wheel-controller and ROS-serial protocol tests passed. The ROS package, launch/configuration files and offline validators now exist under `ros_ws/src/my_bot`; no CI workflow is configured.

### Checks to add with relevant features

- Pure command-decoder and watchdog state-machine tests.
- Differential-drive kinematic and encoder conversion tests with known vectors.
- Parser/protocol tests for valid, invalid, truncated, stale, and reordered data.
- Parameter range and configuration schema checks.
- ROS node/unit tests and launch tests when packages exist.
- Planner/mission state-machine tests when custom behavior exists.
- Static analysis and formatting only when configured intentionally for the project.

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

## ROS serial version 2 checks (2026-09-07)

Both `pio run -e keyboard -e ros_serial` environments passed. Native tests:

```sh
clang++ -std=c++11 -Wall -Wextra -Werror -Iinclude test/ros_serial_protocol_test.cpp -o /tmp/ros-protocol-test
/tmp/ros-protocol-test
clang++ -std=c++11 -Wall -Wextra -Werror -Iinclude test/wheel_speed_controller_test.cpp -o /tmp/wheel-controller-test
/tmp/wheel-controller-test
```

These cover parsing/conversion and controller logic, not live USB timing or ROS.
No physical or ROS integration result is claimed.

## Imported ROS package checks

From `ros_ws/src/my_bot`, follow [VALIDATION.md](../ros_ws/src/my_bot/VALIDATION.md)
for native serial/conformance checks. Use a Python environment with Xacro and PyYAML:

```sh
python3 test/test_model.py
python3 test/test_teleop.py
```

ROS-dependent compilation and plugin loading require Ubuntu/ROS; native tests
cannot substitute for `colcon build`, `colcon test` and physical acceptance.
