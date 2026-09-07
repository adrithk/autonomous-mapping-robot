# Autonomous mapping robot roadmap

**Last updated:** 2026-09-04
**Current stage:** ROS-ready ESP32 transport bench validation; final-payload PID validation deferred

The only product goal is a two-wheel differential-drive robot that can be placed in
an unknown indoor zone, turned on, autonomously explore it, and save a fresh map with
SLAM Toolbox. The project will not use an IMU. The drivetrain is being validated
independently before Raspberry Pi, LiDAR, and ROS integration. Loading old
maps or navigating to user-selected goals is outside this roadmap.

The detailed Raspberry Pi and ROS platform sequence is defined in
[`docs/ros-platform-roadmap.md`](docs/ros-platform-roadmap.md). Status below is based
only on repository code and dated results.

## Build order

1. **Finish and verify the physical drivetrain — in progress.** Both BTS7960 drivers,
   encoders, level shifter, power distribution, fuse, and accessible motor-power
   disconnect must be installed and documented. Motor/encoder operation has been
   observed, but exact electrical ratings, protection, and safe-state behavior remain
   incompletely recorded.

2. **Prove simple keyboard driving — functionally demonstrated; formal safety checks
   remain.** The ESP32 accepts
   keyboard commands for forward, reverse, left, right, and stop. Verify boot-stop,
   command timeout, individual wheel direction, turning, and stopping first with the
   wheels raised and then at low speed on the floor. Movement has been reported, but
   repeated measured boot/stop/timeout tests are not yet recorded.

3. **Validate encoder feedback — partially complete.** Both quadrature encoders are
   read on the ESP32 and their forward/reverse signs have been observed. Next,
   measure counts per wheel revolution, determine the correct sign in both
   directions under the final wiring, and calculate wheel speed in rad/s at a fixed
   update rate.

4. **Implement and test wheel-speed PID — implemented; final validation pending.** One
   local controller per wheel runs at 50 Hz with feed-forward/PI control, output
   limits, integral bounding, target ramps, and command timeouts. Raised-wheel
   tracking passed with the preceding 400 ms ramp. A qualitative ground run was
   nearly straight with slight right drift. Preserve the gains until the Pi/LiDAR
   payload is mounted, then run measured ground trials.

5. **Add the ROS-ready ESP32 command interface — implemented; bench validation
   pending.** The default keyboard build and separately selected `main_ros.cpp` build
   share drivetrain control. The versioned serial interface, fixed-buffer parser,
   CRC, sequence checking, telemetry, 250 ms watchdog, and protocol tests exist, and
   both firmware environments build. Raised-wheel timeout,
   malformed-input, disconnect, and reconnect tests remain.

6. **Begin ROS setup and bridge the drivetrain — planned.** Install the Raspberry Pi,
   regulated supply, storage/cooling, Ubuntu 24.04, and ROS 2 Jazzy. Implement the
   accepted Pi-side `ros2_control` `SystemInterface`; configure
   `joint_state_broadcaster` and `diff_drive_controller`; and verify ROS keyboard
   teleoperation, joint feedback, wheel odometry, reconnect behavior, and ESP32
   watchdog stopping. The ESP32 will not directly subscribe to ROS topics.

7. **Integrate wheel odometry, LiDAR, and TF — planned.** Install the exact LiDAR and
   its supported ROS driver; publish `/scan`; add the measured `base_link -> laser`
   transform; and verify one coherent `odom -> base_link -> laser` tree. Use
   `diff_drive_controller` odometry initially. No IMU or IMU fusion is planned, and
   `robot_localization` is deferred unless another useful odometry source is added.

8. **Run autonomous mapping** — Configure SLAM Toolbox, map saving, and a
   frontier-exploration component. SLAM builds the map; exploration selects reachable
   unknown regions; a minimal Nav2 configuration executes those exploration goals
   safely. The mapping run starts after sensor/TF health checks, stops when no useful
   frontiers remain or a safety condition occurs, and saves the map, configuration,
   and run artifacts.

9. **Validate and present the project** — Record autonomous mapping trials across
   three indoor environments. Commit the maps, configurations, test results, wiring
   diagram, bill of materials, setup guide, and a short demo video so every
   completed-project claim is supported by GitHub evidence.

## Acceptance checkpoints

- **Motors ready:** both wheels pass boot, direction, stop, and timeout bench tests.
- **Hardware ready:** all installed parts and power rails are identified and verified.
- **PID ready:** both wheels track commanded speeds and the robot drives and turns repeatably.
- **Transport ready:** both selectable firmware builds pass; corrupt/stale serial data and disconnects cannot sustain motion beyond the 250 ms watchdog.
- **ROS ready:** the workspace builds/tests and ROS teleoperation reports valid wheel state.
- **Sensors ready:** wheel odometry, LiDAR, and TF run without timestamp or frame errors.
- **Autonomous mapping ready:** two autonomous runs produce consistent maps of the same environment and end with the robot stopped and a saved map.
- **Portfolio ready:** documented autonomous-mapping trials cover three environments.

## Reference implementations for future stages

These are design references, not drop-in code. Match interfaces, safety behavior,
and measured hardware values to this robot before reusing an idea.

- [NavBot hardware](https://github.com/vinay-lanka/navbot_hardware): reference for
  a similar differential-drive base with two encoder-feedback wheel PID controllers.
  Use it during encoder bring-up and local wheel-speed PID work.
- [Ben May's SLAMbot project](https://www.benmay.co.uk/portfolio-slambot-real):
  reference for the later ROS/SLAM project structure and integration direction.
  Use it after the independently tested drivetrain is ready for ROS hardware.

## Aggressive schedule at 25 focused hours per week

| Week | Target |
|---:|---|
| 1 | Complete wiring and verify safe keyboard-controlled drivetrain |
| 2 | Encoder acquisition, wheel-speed PID, and measured drive tests |
| 3 | ROS-ready ESP32 serial protocol and tests |
| 4 | Pi setup, ros2_control bridge, robot model, and wheel odometry |
| 5 | LiDAR integration, calibrated TF, and first map |
| 6 | Repeatable autonomous mapping with automatic map saving |
| 7+ | Tuning and autonomous-mapping validation across three environments |

Status is evidence-based. Code compilation is not hardware validation. Record physical
tests under [`results/`](results/) and keep the active execution plan under
[`docs/plans/active/`](docs/plans/active/).

2026-09-07 implementation note: sibling my_bot now includes the ESP32 v2 hardware
plugin and default-simulation/opt-in-hardware bringup. Offline checks passed; ROS
runtime and physical acceptance remain pending, so milestone acceptance is unchanged.

2026-09-07 user evidence update: [initial simulation implementation](results/2026-09-07-initial-simulation.md)
records working WSL Gazebo/WASD and 10 Hz simulated LiDAR display, with photo.
Initial simulation smoke testing is now observed; physical and SLAM acceptance
remain pending. Exact PC revision and repeatable startup have not been recorded.
