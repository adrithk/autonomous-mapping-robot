# Capability roadmap

Status is evidence-based. Code that compiles is not considered hardware-complete; physical acceptance requires a dated record under `results/`.

| Milestone | Status | Current evidence | Acceptance gate |
|---|---|---|---|
| 0. Repository and platform foundation | **In progress** | PlatformIO project builds; source-of-truth docs, plan structure, and a preliminary reported-hardware parts list exist; exact variants remain incomplete | Repeatable setup/build instructions, baseline automated checks, known hardware recorded, and docs match repository |
| 1. Motor and encoder hardware | **In progress** | Open-loop ESP32 PWM/direction command sketch exists; builder-reported drivetrain parts are recorded but unverified | Safe boot/timeout behavior, pinout and power path recorded, both wheels pass direction/stop tests, encoders produce measured counts |
| 2. Wheel velocity control and odometry | **Not started** | No encoders, kinematics, controller, or tests | Calibrated wheel geometry; tested velocity loops; measured straight/rotation behavior; odometry interface and drift results |
| 3. IMU and state estimation | **Not started** | No device or code | Mounting/calibration recorded; orientation verified; selected standard filter produces validated fused estimate |
| 4. ROS 2 platform integration and robot model | **Not started** | No ROS workspace | Build/test-clean ROS packages, hardware bridge, URDF, coherent TF tree, launch/config validation |
| 5. LiDAR integration | **Not started** | No device or code | Stable scan publication, mounting transform, alignment and obstruction tests recorded |
| 6. SLAM | **Not started** | No ROS or sensor pipeline | Repeatable map creation with recorded bag/run and documented map-quality assessment |
| 7. Localization | **Not started** | No saved maps or localization config | Repeatable pose convergence/recovery in a saved map with measured results |
| 8. Nav2 navigation | **Not started** | No Nav2 config | Repeated goal completion, obstacle handling, recovery, and safe stopping meet defined thresholds |
| 9. Autonomous exploration | **Not started** | No mission behavior | Bounded-area exploration meets coverage and return behavior criteria |
| 10. Coverage planning | **Not started** | No requirements or planner | Coverage metric, exclusions, path execution, and repeatability criteria defined and met |
| 11. Docking and charging | **Not started** | Mentioned only as a possible future capability | Requirements, electrical safety, detection/alignment, repeated docking and charge-transition results |
| 12. Vacuum subsystem | **Not started** | No repository evidence or requirements | Scope, hardware ownership, safety, controls, and performance criteria first defined, then validated |
| 13. Full-system validation | **Not started** | Subsystems unavailable | Endurance, fault response, navigation mission, logs, and regression evidence meet an approved test plan |

## Current milestone

**Milestone 1 — motor and encoder hardware**, narrowed to safe motor-command bring-up. The immediate plan is [001-safe-motor-command-interface.md](docs/plans/active/001-safe-motor-command-interface.md). Encoder work follows only after motor actuation can be commanded and stopped predictably.

## Progress rules

- **Completed:** every milestone acceptance gate has evidence; hardware gates link to physical results.
- **In progress:** bounded work or partial evidence exists, but at least one gate remains unmet.
- **Not started:** no accepted implementation/evidence exists, even if the feature appears in design intent.
- **Blocked:** use only when a named dependency prevents meaningful work; record that dependency in the active plan.

Milestone status changes must update this file and the relevant execution plan. Do not advance a milestone based solely on code presence, a successful compile, or an unrecorded manual observation.
