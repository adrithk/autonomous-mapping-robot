# Autonomous mapping robot roadmap

**Last updated:** 2026-09-04
**Current stage:** Initial wheel-speed PID tuning

The only product goal is a two-wheel differential-drive robot that can be placed in
an unknown indoor zone, turned on, autonomously explore it, and save a fresh map with
SLAM Toolbox. The project will not use an IMU. The drivetrain will be completed and
tested independently before Raspberry Pi, LiDAR, and ROS integration. Loading old
maps or navigating to user-selected goals is outside this roadmap.

## Build order

1. **Finish and verify the physical drivetrain** — Install both BTS7960 drivers,
   encoders, level shifter, power distribution, fuse, and accessible motor-power
   disconnect. Confirm every rail and signal with motor power off before testing.

2. **Prove simple keyboard driving** — Use a small ESP32 bring-up program to accept
   keyboard commands for forward, reverse, left, right, and stop. Verify boot-stop,
   command timeout, individual wheel direction, turning, and stopping first with the
   wheels raised and then at low speed on the floor. The existing firmware is only a
   preliminary unbuilt draft until these tests are recorded.

3. **Validate encoder feedback** — Read both quadrature encoders on the ESP32,
   measure counts per wheel revolution, determine the correct sign in both
   directions, and calculate wheel speed in rad/s at a fixed update rate. Do not begin
   PID tuning until the counts and speed measurements are reliable.

4. **Implement and test wheel-speed PID** — Run one local controller per wheel on the
   ESP32. Each controller compares a target wheel speed with encoder-measured speed
   and adjusts BTS7960 PWM. Add output limits, integral anti-windup, safe direction
   changes, and command-loss behavior. Record straight-drive, reverse, and turn tests.

5. **Add the ROS-ready ESP32 command interface** — After PID passes, replace the
   temporary keyboard command format with a versioned serial interface for left/right
   wheel-speed targets, encoder state, measured wheel speeds, timestamps, and faults.
   Test it first with a small computer-side test program; full ROS is not required for
   that protocol test. The ESP32 keeps PID and immediate stopping locally.

6. **Begin ROS setup and bridge the drivetrain** — Install the Raspberry Pi, its
   regulated supply, storage/cooling, and ROS 2 Jazzy. Normally a Raspberry Pi ROS
   node or `ros2_control` hardware interface subscribes to `/cmd_vel`, converts the
   requested linear/angular motion into wheel-speed targets, and sends those targets
   over serial. The ESP32 does not need to subscribe directly to ROS topics unless a
   deliberate micro-ROS design is chosen. Verify ROS keyboard teleoperation and wheel
   feedback before adding mapping.

7. **Integrate wheel odometry, LiDAR, and TF** — Install the 2D LiDAR; publish wheel
   odometry and laser scans with correct units, timestamps, and frames. Calibrate
   loaded wheel radius and track width, then verify one coherent
   `odom -> base_link -> laser` TF tree. No IMU or IMU fusion is planned.

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
| 3 | ROS-ready ESP32 serial protocol, then Pi and ROS 2 setup |
| 4 | ROS bridge, robot model, and wheel odometry |
| 5 | LiDAR integration, calibrated TF, and first map |
| 6 | Repeatable autonomous mapping with automatic map saving |
| 7+ | Tuning and autonomous-mapping validation across three environments |

Status is evidence-based. Code compilation is not hardware validation. Record physical
tests under [`results/`](results/) and keep the active execution plan under
[`docs/plans/active/`](docs/plans/active/).
