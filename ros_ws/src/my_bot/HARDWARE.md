# Real ESP32 control (opt-in)

Default: `ros2 launch my_bot bringup.launch.py` starts **simulation**. The hardware
library is compiled but is never loaded by the simulation model. Stop one launch
before starting the other; the mode switch is a restart, not a live transfer.
Do not run preview joint publishers alongside either control mode.

## Pi first connection

1. Install Ubuntu 24.04 arm64 and ROS 2 Jazzy, then clone/build this package as in
   SIMULATION.md. This is a ROS computer package, not ESP32 firmware.
2. Upload the **ros_serial version 2** build from autonomous-mapping-robot to the
   ESP32. The default keyboard firmware will not answer this protocol.
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

## What runs where

Pi: TwistStamped body velocity -> diff_drive_controller -> wheel rad/s ->
`my_bot/Esp32System` -> CRC-framed USB commands. ESP32: rad/s -> counts/s ->
existing local PID. Raw encoder telemetry returns through the plugin as wheel
position (radians) and velocity (rad/s); controller publishes odometry/TF.

- Wire contract: 115200, 8N1, protocol 2, C/X/S messages defined in the firmware
  repository's `docs/interfaces.md`. No third-party Arduino text protocol works here.
- Joint order/names: left_wheel_joint, right_wheel_joint. Velocity command and
  position/velocity state interfaces on both. No effort command or IMU.
- `description/hardware.xacro` owns feedback calibration; keep it synchronized
  with firmware `include/ros_wheel_units.h` if counts/revolution changes.
- Hardware YAML uses real time; simulation YAML uses `/clock`. Geometry and speed
  limits are otherwise identical and checked by tests. Limits: 0.15 m/s and 0.75 rad/s;
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
Record three watchdog/disconnect trials in the firmware repository's results/.
Then measure travel/turn accuracy under the final payload and correct geometry.

Hardware bringup does **not** start a LiDAR driver, SLAM or Nav2. It publishes the
provisional laser transform only. Next add the A1M8 driver publishing `/scan` in
frame `laser`, confirm the physical mount and odometry, then add SLAM Toolbox.

## Verification limits

The transport is tested with an emulated ESP32 over a pseudo-terminal. Xacro,
YAML, plugin declarations and launch syntax are checked offline. ROS plugin loading,
colcon build/test evidence and real hardware still require Ubuntu/Pi execution.
Initial Gazebo/WSLg driving and laser display were user-observed; see the
[simulation result](docs/results/2026-09-07-initial-simulation.md). Repeatable startup
and revision-pinned validation remain pending; that smoke test does not validate
the physical hardware plugin.

References: [Jazzy hardware component API](https://control.ros.org/jazzy/doc/api/classhardware__interface_1_1SystemInterface.html),
[Jazzy differential-drive controller](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html),
[Jazzy Gazebo integration](https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html).
