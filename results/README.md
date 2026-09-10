# Recorded results

These records distinguish software checks, observed demonstrations and measured
hardware tests. Each report describes its setup, observations and limits.

| Date | Record |
|---|---|
| September 10, 2026 | [Physical room mapping and saved-map Nav2 demonstration](2026-09-10-real-room-mapping-navigation.md) |
| September 9, 2026 | [Initial Pi teleoperation observations](2026-09-09-pi-teleop.md) |
| September 9, 2026 | [Offline exploration checks — historical scope](2026-09-09-exploration-offline.md) |
| September 8, 2026 | [Interactive simulated LiDAR SLAM](2026-09-08-simulated-lidar-slam.md) |
| September 7, 2026 | [Initial Gazebo simulation](2026-09-07-initial-simulation.md) |
| September 7, 2026 | [ROS code audit](../ros_ws/src/my_bot/docs/results/2026-09-07-code-audit.md) |
| September 4, 2026 | [Raised-wheel feedback tracking](2026-09-04-raised-wheel-pid-tracking.md) |
| September 4, 2026 | [Ground straight-drive observation](2026-09-04-ground-straight-observation.md) |
| September 4, 2026 | [Open-loop encoder observation](2026-09-04-open-loop-encoder-observation.md) |

## Recording a new test

Use `YYYY-MM-DD-short-test-name.md`, with associated media/logs in a same-named
directory. Include date, operator, source revision, configuration, test level,
procedure, observations with units, outcome and anomalies. State pass/fail only
against criteria defined before the run. Link the record from its execution plan
and update project status when the evidence changes.

See [testing](../docs/testing.md) for automated commands and physical measurements.
