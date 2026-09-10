# System architecture

Updated September 10, 2026. The repository contains two ESP32 entry points and one
ROS 2 Jazzy package, `my_bot`. The target mission is fresh-zone autonomous mapping;
saved-map navigation is an intermediate physical demonstration. Docking and vacuum
control remain outside the current scope.

## Ownership and implementation

| Component | Owner / source | Implementation and validation |
|---|---|---|
| Encoder sampling, PWM, feed-forward/PI | ESP32 `src/robot_drive.cpp` | Shared 50 Hz controller; earlier raised-wheel tracking recorded |
| Keyboard command entry point | ESP32 `src/main.cpp` | Timed movement, encoder reporting, stop commands |
| Serial command entry point | ESP32 `src/main_ros.cpp` | v2 CRC/sequence framing, 20 Hz telemetry, 250 ms watchdog; initial physical operation reported; fault/stop acceptance pending |
| Serial hardware plugin | `ros_ws/src/my_bot/src/esp32_system.cpp` and `serial_transport.cpp` | Implemented; offline transport tests; ROS plugin loading and initial physical operation reported; fault/stop acceptance pending |
| Wheel commands and odometry | Standard `diff_drive_controller` | Configured for simulation and hardware; measured odometry acceptance pending |
| Robot description and transforms | `my_bot/description/`, robot_state_publisher | Xacro and preliminary geometry; offline checks |
| Simulation | Gazebo Harmonic and `gz_ros2_control` | Initial WSL driving/scans demonstrated; repeatable startup and dynamics checks remain |
| Mapping | SLAM Toolbox; simulation wrapper `slam_sim.launch.py` and upstream physical launch | Simulation and initial physical teleoperated mapping; manual map save reported |
| Physical LiDAR driver | Upstream `rplidar_ros` on the Pi | A1M8 via GPIO UART; scan publication and physical mapping demonstrated; full TF/calibration checks pending |
| Nav2 click-to-go navigation | `my_bot/launch/nav_sim.launch.py`; Nav2/AMCL saved-map workflow | Simulation implementation plus initial physical saved-map navigation demonstration; repeated acceptance pending |
| Exploration and automatic save | `my_bot/my_bot_exploration`, `explore_sim.launch.py` | Simulation implementation; offline verification, target runtime acceptance pending |

## Control and data flow

In hardware mode, stamped body velocity commands reach `diff_drive_controller`.
It converts them into left/right rad/s commands for `my_bot/Esp32System`, which owns
USB serial at 115200 baud. The ESP32 converts rad/s into local counts/s targets and
returns raw encoder counts and speed. The host converts feedback into radians and
rad/s. The preliminary encoder calibration is 4185 counts/revolution per wheel.

The host requires fresh telemetry and an acknowledged stop at startup. Telemetry
or ACK stalls beyond 200 ms, new firmware faults, time regression, or I/O failures
fault control and attempt a stop. Reconnection is deliberate; previous commands
are not automatically replayed. The ESP32 independently enforces its 250 ms lease.
These are source behaviors with offline coverage, awaiting measured physical trials.

Simulation uses Gazebo wheel interfaces instead of the serial plugin. The default
ROS bringup selects simulation; `mode:=hardware` requires an explicit serial device.
Simulation uses `/clock`; hardware uses wall time. The two backends are exclusive.

## Frames and configuration

The configured chain is `map -> odom -> base_link -> laser`. SLAM Toolbox owns
`map -> odom` when the SLAM launch runs; `diff_drive_controller` owns `odom -> base_link`;
AMCL instead owns `map -> odom` in saved-map localization mode; do not run both
localization sources together. `robot_state_publisher` owns robot link transforms. No IMU is modeled, and
`robot_localization` is deferred until another useful odometry source exists.

- `platformio.ini`: mutually exclusive firmware source filters. Use explicit environments.
- `src/robot_drive.cpp`: motor/encoder pins, controller gains, limits and polarity.
- `include/ros_wheel_units.h`: ROS firmware wheel-unit conversion.
- `ros_ws/src/my_bot/description/dimensions.xacro`: preliminary robot geometry.
- `ros_ws/src/my_bot/config/`: controller geometry/limits, clocks, bridge, SLAM and RViz.
- `ros_ws/src/my_bot/description/simulation_parameters.xacro`: estimated simulation physics.

Geometry is provisional: wheel radius 0.040 m, center separation 0.205 m and LiDAR
scan plane 0.10 m above the floor. Hardware inventory and measurement provenance
live in [hardware/parts-list.md](hardware/parts-list.md); simulation estimates are
not physical calibration. Exact units, topics, GPIOs and transport framing are in
[docs/interfaces.md](docs/interfaces.md).

## Hardware and acceptance

The reported platform uses an ESP32, two encoder gearmotors, two BTS7960 modules,
a level shifter, battery, wheels, and printed chassis. The Pi 5 and RPLIDAR A1M8
are present in the [September 10 physical demonstration](results/2026-09-10-real-room-mapping-navigation.md),
which uses tethered power. Physical calibration and repeated integration acceptance
remain pending.
The earlier Cytron driver is retired. Independent power isolation, electrical
ratings, and repeated stop tests remain to be documented.

See [testing](docs/testing.md), [dated results](results/README.md), and the
[roadmap](ROADMAP.md) for the distinction between source, automated checks,
observed operation, and integrated acceptance.
