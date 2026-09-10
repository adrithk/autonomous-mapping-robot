# Real ESP32 control (opt-in)

Default: `ros2 launch my_bot bringup.launch.py` starts **simulation**. The hardware
library is compiled but is never loaded by the simulation model. Stop one launch
before starting the other; the mode switch is a restart, not a live transfer.
Do not run preview joint publishers alongside either control mode.

## Pi first connection

1. Install Ubuntu 24.04 arm64 and ROS 2 Jazzy, then follow the [package build steps](README.md#build). This is a ROS computer package, not ESP32 firmware.
2. Upload the **ros_serial version 2** build from autonomous-mapping-robot to the
   ESP32. Select `pio run -e ros_serial -t upload` explicitly; the keyboard firmware does not speak this protocol.
3. Connect ESP32 to the Pi with a USB **data** cable. Close any serial monitor.
4. Add your Pi user to the serial group, then log out/in:
   `sudo usermod -aG dialout "$USER"`. Locate the ESP32 with `ls -l /dev/serial/by-id/`.
   Identify it by unplugging/reconnecting the ESP32, especially once LiDAR is attached.
5. Raise both drive wheels for initial testing and have motor-power removal within
   reach. Confirm the newly mounted wheels still move toward the front caster
   for positive commands. Calibration is provisional: 4185 counts/revolution each.
6. Enable hardware explicitly, replacing the example device path:

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 launch my_bot bringup.launch.py mode:=hardware rviz:=false \
  serial_device:=/dev/serial/by-id/YOUR_ESP32
```

In another Pi terminal (SSH is fine):

```bash
source /opt/ros/jazzy/setup.bash
source ~/autonomous-mapping-robot/ros_ws/install/setup.bash
ros2 run my_bot teleop_wasd --ros-args \
  -p use_sim_time:=false -p frame_id:=base_link \
  -p speed:=0.05 -p turn:=0.3 -r cmd_vel:=/diff_drive_controller/cmd_vel
```

`w` forward, `s` reverse, `a` left, `d` right; space or `x` stops. Hold a direction
key for repeats; the teleop sends zero after 0.2 s without another key event. The initial
OS key-repeat delay can cause a pause. Ctrl-C ends teleoperation. The controller also has an independent 0.25 s message timeout. This is ordinary stopping, not an emergency stop.

For press-once operation, add `-p latched:=true` to the teleop command. W/A/S/D
then persist until X/Space (or another direction). Releasing a key does not stop;
controller/ESP32 watchdogs still require loss of messages, not operator inactivity.
Keep power removal accessible and verify stopping with raised wheels.

## What runs where

Pi: TwistStamped body velocity -> diff_drive_controller -> wheel rad/s ->
`my_bot/Esp32System` -> CRC-framed USB commands. ESP32: rad/s -> counts/s ->
existing local PID. Raw encoder telemetry returns through the plugin as wheel
position (radians) and velocity (rad/s); controller publishes odometry/TF.

- Wire contract: 115200, 8N1, protocol 2, C/X/S messages defined in the [interface specification](../../../docs/interfaces.md). No third-party Arduino text protocol works here.
- Joint order/names: left_wheel_joint, right_wheel_joint. Velocity command and
  position/velocity state interfaces on both. No effort command or IMU.
- `description/hardware.xacro` owns feedback calibration; keep it synchronized
  with firmware `include/ros_wheel_units.h` if counts/revolution changes.
- Hardware YAML uses real time; simulation YAML uses `/clock`. Geometry matches; speed
  limits differ: simulation permits faster linear motion. Physical limits: 0.15 m/s and 0.75 rad/s;
  the plugin additionally scales wheel pairs to at most 6 rad/s, preserving curvature.
- Serial port is explicitly selected, raw, nonblocking and advisory-locked. Close
  other serial programs (programs that ignore advisory locks can still interfere).
- Activation waits up to 4 seconds for v2 telemetry, synchronizes to its ACK,
  sends a new stop and requires a fresh stop ACK with zero PWM before enabling commands.
- Runtime read/write work is bounded. Feedback or command ACK stalls over 200 ms,
  ESP32 clock regression/reboot, I/O failure or a newly latched firmware fault
  fail control and close the connection. Invalid CRC does not refresh freshness.
- Previously latched status bits are logged at activation; firmware cannot clear
  them without reboot. A repeat of an already-latched bit cannot be distinguished.
- Disconnect/deactivate/error/destruction attempt a stop. Delivery is best effort;
  the ESP32's independent 250 ms watchdog remains required. No automatic reconnect
  or replay of the last target: stop bringup, fix the issue, and relaunch deliberately.
- Counts are unwrapped using signed 32-bit modular deltas. ROS position starts at
  zero for each process; reboot causes a fault rather than an odometry jump.

## Before ground driving / SLAM

Verify zero PWM at startup, wheel directions and feedback signs, zero commands,
explicit stop, host termination, bad frames, and unplug/reconnect while moving.
Record three watchdog/disconnect trials in the [results directory](../../../results/README.md).
Then measure travel/turn accuracy under the final payload and correct geometry.

## Mapping and navigation

Hardware bringup starts drivetrain control and robot transforms; it does not start
a LiDAR driver, SLAM or Nav2. The [September 10 demonstration](../../../results/2026-09-10-real-room-mapping-navigation.md)
used upstream `rplidar_ros` with an A1M8 on GPIO UART (`/dev/ttyAMA0`, 115200 baud),
publishing `/scan` in frame `laser`.

For physical mapping, SLAM Toolbox combines scans and wheel odometry while the
operator drives, then saves an occupancy map. For navigation, stop teleop and SLAM,
load that map with map server and AMCL, initialize the pose in RViz, and use Nav2
to reach selected goals. Physical nodes use wall time. Confirm the mounted laser
transform and loaded wheel geometry before reproducing the setup.

The demonstration's exact running revisions and complete launch configuration
were not captured. This repository's `nav_sim.launch.py` is for simulation;
it is not a packaged reproduction of the physical saved-map launch.

## Verification limits

Native tests exercise the transport with an emulated ESP32, including handshake,
CRC, stale feedback and fault cases. Offline checks cover model/configuration and
launch contracts. Initial physical plugin operation, mapping and navigation are
recorded; revision-pinned ROS build/test results, calibrated odometry, repeated
startup and physical fault/stop timing remain open measurements.

## Visual one-revolution check

Keep the hardware launch running, stop all WASD/Nav2 publishers, and mark both
tyres against a fixed reference with both wheels raised. From the consolidated `autonomous-mapping-robot` repository root
in a sourced Pi shell using the same ROS domain as the launch, run:

```bash
python3 tools/wheel_revolution_test.py
```

The standalone script aims for one forward revolution of each wheel, slows toward
the encoder endpoint, then commands zero and checks stationary feedback. It prints
final encoder-estimated revolutions. Compare actual tyre marks independently; ROS
reporting one revolution does not establish correct encoder calibration. There is
no guaranteed exact stop angle. Geometry comes from installed hardware controller
YAML, which must match the running controller. Timeout/feedback checks do not replace
independent motor-power removal. Target ROS/physical testing remains pending.
