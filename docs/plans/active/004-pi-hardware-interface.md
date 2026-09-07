# Pi hardware interface and selectable simulation

Date: 2026-09-07. Status: implementation/offline checks complete; runtime acceptance pending.

## Bounded scope

Implement my_bot/Esp32System in the sibling ROS package, speaking the existing
ESP32 v2 protocol. Default to Gazebo; real bringup explicitly selects a serial port.
Check plugin registration/build dependencies, Xacro, YAML clocks/limits, Python launch
syntax, unit conversion, USB framing, sequence synchronization and fault stopping.
Keep ESP32 firmware unchanged. SLAM/Nav2/LiDAR hardware driver are follow-up tasks.

## Implemented

- Standard Jazzy SystemInterface with two velocity command and position/velocity state interfaces.
- POSIX 115200 serial connection with a fresh stop-ACK handshake; preliminary4185
  counts/revolution feedback conversion, signed count wraparound, 200 ms telemetry
  and acknowledgement health checks, stop on fault and deliberate reconnect only.
- Mutually exclusive hardware/simulation Xacro and launch; simulation default.
- Separate clock settings with common geometry and conservative velocity limits.
- WSL source bundle and setup/teleop instructions in sibling WSL_SETUP.md.

## Offline verification (2026-09-07)

Six model tests pass for geometry, inertias/frames, sensor wiring, backend isolation,
YAML clocks/limits, XML/Python syntax and plugin declarations. Native C++17 transport
and pseudo-terminal tests pass with clang++ -Wall -Wextra -Werror, covering CRC,
field bounds, handshake, ACK wrap, reconnect, malformed/stale feedback, stalled ACK,
reboot, new status faults and host stalls. A compatibility harness compiled against
this repository's actual ros_serial_protocol.h accepts host C/X frames and decodes
firmware S frames. No ESP32 source edits were required in this task.

## Remaining acceptance

- On Ubuntu 24.04: colcon build/test/test-result; load plugin via controller_manager.
- On WSL2: launch Gazebo, confirm active controllers, wheel motion, odometry and scans.
- On Pi: upload ESP32 ROS build; raised-wheel direction/stop/watchdog/disconnect trials
  and dated results before ground driving. Final geometry/calibration remains provisional.

No ROS/Gazebo installation or Pi was available here. Do not mark this plan complete
until runtime checks are recorded. Existing transport plan 003 physical criteria
remain open.

2026-09-07 user evidence update: [initial simulation implementation](../../../results/2026-09-07-initial-simulation.md)
records working WSL Gazebo/WASD and 10 Hz simulated LiDAR display, with photo.
Initial simulation smoke testing is now observed; physical and SLAM acceptance
remain pending. Exact PC revision and repeatable startup have not been recorded.
