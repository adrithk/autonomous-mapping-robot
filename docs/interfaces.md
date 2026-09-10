# Subsystem interfaces

Unknown values are deliberately marked `TBD`. Update this file in the same change as any interface modification.

## Keyboard serial command interface

**Owner:** `src/main.cpp` on the ESP32  
**Transport:** Arduino `Serial` over the board's serial connection  
**Configured rate:** 115200 baud  
**Framing:** one byte read at a time; no packet framing, checksum, sequence number, acknowledgement, or version  
**Update behavior:** polled continuously in `loop()`; `w`/`s` ramp up over 300 ms, ramp down during the final 300 ms, and stop after 5000 ms. `a`/`d` ramp up over 100 ms, ramp down during the final 100 ms, and stop after 1000 ms. Explicit, invalid-input, and timeout stops remain immediate.
**Units:** keyboard commands select fixed signed encoder-count-per-second targets; counts/revolution remains unverified

| Input byte | Left target | Right target | Intended motion |
|---|---|---|---|
| `w` | +3000 counts/s | +3000 counts/s | Forward for up to 5 seconds |
| `s` | -3000 counts/s | -3000 counts/s | Reverse for up to 5 seconds |
| `a` | -1800 counts/s | +1800 counts/s | Left turn for up to 1 second |
| `d` | +1800 counts/s | -1800 counts/s | Right turn for up to 1 second |
| `x` | 0 counts/s | 0 counts/s | Stop and reset both controllers |
| `e` | unchanged | unchanged | Print encoder counts |
| carriage return / newline | unchanged | unchanged | Ignored; does not renew the motion lease |
| any other byte | both PWM outputs 0 | both PWM outputs 0 | Stop |

The firmware prints startup, timeout, and unknown-command messages. While a motion
command is active, it prints each wheel's requested command, ramped target counts/s,
measured counts/s, controller PWM, and raw count every 200 ms. The `e` command prints
only `left_count=<count> right_count=<count>` immediately, without resetting either
count. It does not echo every received byte.

### Known limitations

- Controller calculations have automated checks and the firmware builds. Raised-wheel forward/reverse tracking passed at +/-3000 counts/s on 2026-09-04; ground-load performance remains unverified.
- There is no variable-speed command, driver-fault input, or framed/acknowledged transport.
- Counts/revolution is unverified, so targets and measurements cannot yet be converted reliably to rad/s.
- Initial gains and left/right electrical polarity require controlled hardware validation.
- This interface is a bring-up control, not a suitable final ROS transport contract.

## Current motor driver output interface

**Owner:** ESP32 firmware  
**PWM:** 20 kHz, 8-bit resolution, Arduino LEDC API; controller output limited to 200
**Motor drivers:** two reported HiLetgo BTS7960 single-channel modules, one per motor. Their basic movement has been demonstrated, but exact board revision, electrical limits, thermal behavior, and safe-state behavior remain unverified. The former Cytron MDD10A is reported damaged and must not be used.
**Reported motors:** two expected 12 V metal DC gearmotors with encoders, 131:1, 83 RPM, 45 kg.cm; exact manufacturer/model is unconfirmed  
**Electrical levels, enable polarity, braking/coasting behavior, and motor rated/stall current:** `TBD`

| Channel | BTS7960 GPIOs | Verification status |
|---|---|---|
| Shared enable | GPIO 27 to all four `R_EN`/`L_EN` pins | Reported connected; external 10 kΩ pull-down intended; electrical safe-state test pending |
| Left | GPIO 25 `RPWM` + GPIO 26 `LPWM` | Motion and PID telemetry observed; exact electrical verification pending |
| Right | GPIO 32 `RPWM` + GPIO 33 `LPWM` | Motion and PID telemetry observed; exact electrical verification pending |

## Current encoder input interface

**Owner:** ESP32 firmware
**Electrical path:** encoder A/B signals -> four-channel 5 V-to-3.3 V level shifter -> ESP32 inputs
**Acquisition:** interrupt on each A channel; B is read to infer direction. Count differences are converted to counts/s at a nominal 50 Hz using actual elapsed time. Counts are not yet calibrated to wheel position or rad/s.

**Controller:** one controller per wheel using initial gains `Kp=0.020`, `Ki=0.010`, `Kd=0.000`, and feed-forward `0.048 PWM/(count/s)`. Integral magnitude is limited to 4000 count-seconds and output to PWM 200. Straight targets use a 10000 counts/s² slew limit for a 300 ms ramp to 3000 counts/s; turn targets use an 18000 counts/s² limit for a 100 ms ramp to 1800 counts/s. These values are provisional pending physical tuning.

| Wheel | A input | B input |
|---|---:|---:|
| Left | GPIO 34 | GPIO 35 |
| Right | GPIO 36 (`VP`) | GPIO 39 (`VN`) |

Both encoder count signs have been observed in forward and reverse. Signal voltage, count resolution, missed-count behavior, and the exact level-shifter electrical performance remain unverified. GPIO 34-39 have no internal pull resistors; the external level shifter must provide suitable pull-ups.

Pin assignments, gains, limits, and polarity are shared by both firmware entry points in `src/robot_drive.cpp`. The reported four-channel level shifter is used for encoder signals, not motor-driver control inputs; its electrical behavior still requires measurement.

## ROS-ready USB serial protocol

**Implementation:** `src/main_ros.cpp` and `include/ros_serial_protocol.h`
**Build environment:** `ros_serial`
**Transport:** USB serial at 115200 baud, ASCII, newline-delimited
**Protocol version:** 2
**Command rate:** intended 50 Hz from the Pi
**ESP32 watchdog:** 250 ms from the last valid, newer command frame
**Telemetry rate:** 20 Hz
**Wire units:** commands in wheel rad/s; feedback remains encoder counts and counts/s.
The ESP32 converts commands; the Pi plugin converts feedback to radians and rad/s.

Every payload is followed by `*HHHH\n`, where `HHHH` is four uppercase hexadecimal
digits containing CRC-16/CCITT-FALSE over every ASCII byte before `*` (polynomial
`0x1021`, initial value `0xFFFF`, no reflection, no final XOR). Carriage returns are
ignored. Frames longer than the fixed 128-byte receive buffer are rejected.
The buffer reserves one byte for the string terminator. The first byte exceeding
127 buffered bytes immediately stops both wheel controllers and latches the overflow
status, without waiting for a newline or watchdog expiry. Remaining input in that
frame is discarded through the next newline; a subsequent valid, newer command may
resume motion.

| Direction | Frame payload before CRC | Meaning |
|---|---|---|
| Pi -> ESP32 | `C,2,SEQ,LEFT_RAD_S,RIGHT_RAD_S` | Set signed wheel rad/s targets; converted magnitude must not exceed 4000 counts/s |
| Pi -> ESP32 | `X,2,SEQ` | Stop immediately and reset both wheel controllers |
| ESP32 -> Pi | `S,2,ACK,ESP_MS,LEFT_COUNT,RIGHT_COUNT,LEFT_CPS,RIGHT_CPS,LEFT_PWM,RIGHT_PWM,STATUS` | State and acknowledgement telemetry |

Command fields accept finite decimal/scientific notation with a decimal point (`.`),
no whitespace, NaN, infinity or hexadecimal numbers. Version 1 is rejected to prevent
confusing counts/s with rad/s. Both command and state frames now carry version 2.

`include/ros_wheel_units.h` centralizes preliminary left/right calibration at
**4185 counts/revolution**, from the builder's approximate 41850 counts over ten
full wheel rotations on each wheel. This is a reported estimate, not a recorded
calibration acceptance test. Conversion is `counts/s = rad/s * 4185 / (2*pi)`;
1 rad/s is approximately 666.06344 counts/s. The per-wheel command limit is
`4000 * 2*pi / 4185` rad/s (approximately 6.0054). Shared PID and keyboard units
remain counts/s. Invalid values do not acknowledge a sequence or renew the lease.

The Pi plugin sends wheel rad/s directly in `C,2` frames with CRC and
new sequence numbers, and convert raw `S,2` feedback using `2*pi / 4185`.
It implements count wraparound, reboot/reset, stale telemetry, reconnect and
activation/deactivation checks; physical validation remains pending.
A USB reconnect without an ESP32 reboot retains the last sequence: the host must
synchronize rather than assume its sequence can restart at zero.

`SEQ`/`ACK` are unsigned 32-bit sequence numbers. Only newer command sequences are
accepted, using wraparound-safe comparison. A valid zero/zero command and `X` both
stop immediately. Invalid version, format, checksum, range, overflow, duplicate, or
older sequence does not refresh the watchdog. USB reconnect does not replay a prior
command because the ESP32 boots stopped and requires a new valid frame.

Status bits are latched until reboot in this first implementation:

| Bit | Value | Meaning |
|---:|---:|---|
| 0 | `0x0001` | Command watchdog expired |
| 1 | `0x0002` | Receive buffer overflow |
| 2 | `0x0004` | Invalid frame format/version |
| 3 | `0x0008` | Invalid CRC |
| 4 | `0x0010` | Wheel target out of range |
| 5 | `0x0020` | Duplicate or stale sequence |

This protocol builds and has parser/CRC unit tests, but it has not been uploaded or
bench-tested. The Pi-side plugin is included under `ros_ws/src/my_bot`.

## ROS 2 interfaces

The package is `ros_ws/src/my_bot`. Its `my_bot/Esp32System` plugin exports two
wheel rad/s command interfaces and radians/rad/s state interfaces. The configured
`diff_drive_controller` receives `geometry_msgs/msg/TwistStamped` at
`/diff_drive_controller/cmd_vel`, publishes `/diff_drive_controller/odom`, and owns
`odom -> base_link`. The ESP32 remains a non-ROS serial endpoint.

Preliminary geometry is wheel radius 0.040 m, separation 0.205 m, outer width
0.215 m, front/rear axle extents 0.180/0.080 m. These supersede the historical
0.233 m separation. `base_link` is at floor height under the axle midpoint; +X
points toward the front caster, +Y left, +Z up. The provisional laser scan plane
is centered at z=0.10 m, level/yaw zero. Final loaded dimensions remain uncalibrated.

ROS bringup defaults to Gazebo; `mode:=hardware` requires `serial_device` explicitly.
Hardware uses wall time; simulation uses `/clock`. The host requires fresh v2
telemetry and an acknowledged stop at startup. Telemetry or ACK stalls above 200 ms,
new status faults, reboot/time regression or I/O failure fault control and attempt
a stop. Reconnection is deliberate. Previously latched firmware bits are logged;
repeated occurrences of the same bit are not observable. The ESP32 watchdog remains
independent. See [hardware operation](../ros_ws/src/my_bot/HARDWARE.md).

## TF and mapping

Configured tree: `map -> odom -> base_link -> laser`. SLAM Toolbox owns
`map -> odom` in the separate SLAM launch; diff_drive_controller owns `odom -> base_link`;
robot_state_publisher owns robot link transforms. The simulated scanner publishes
`/scan` in `laser` at 15 Hz; the physical LiDAR driver remains to be integrated.
SLAM uses simulation time and 0.05 m/cell resolution. Manual map export saves YAML
and an occupancy image. The operator saves the map explicitly.

Offline transport/model checks and initial user-observed simulation are recorded.
Physical timing, calibrated odometry, SLAM map export and integrated mission
acceptance remain pending; see [testing](testing.md) and [roadmap](../ROADMAP.md).

## Nav2 simulation interfaces — September 8, 2026

`nav_sim.launch.py` composes simulation + live SLAM + Nav2, using `/clock`.
`/navigate_to_pose` accepts `nav2_msgs/action/NavigateToPose` in map coordinates.
NavFn plans using the live `/map`; local obstacles come from `/scan`; navigation
reads `/diff_drive_controller/odom`. The Nav2 collision radius is 0.215 m plus
0.005 m padding, conservatively enclosing the offset robot footprint.

Controller and recovery behaviors publish TwistStamped to `/cmd_vel_nav`;
velocity_smoother outputs TwistStamped to `/cmd_vel_smoothed`; collision_monitor
outputs TwistStamped to `/diff_drive_controller/cmd_vel`. Commands are capped
at 0.20 m/s and 0.6 rad/s, with 0.3 m/s² and 1.5 rad/s² acceleration limits.
The smoother input timeout is 0.2 s; monitor scan timeout is 0.5 s; existing wheel
command timeout is 0.25 s. These settings are not measured stopping guarantees.

Teleop must be stopped before launching Nav2 because it directly publishes to the
wheel controller, bypassing this pipeline. Mode switching currently uses separate
exclusive launch sessions; there is no automatic command multiplexer. Physical
navigation and autonomous frontier goal selection remain unimplemented/unverified.

### Navigation TF timing (September 8, preliminary simulation tuning)

SLAM map->odom publication remains scan-stamped with a 1.5 s transform_timeout
margin. DWB, global costmap, behavior server and BT navigator use a bounded 1.5 s
transform_tolerance. Local costmap and collision monitor retain 0.2 s. These
parameters have different framework semantics (publication offset vs lookup wait
or acceptable transform age); they are not motor or overall goal timeouts.
The change is a mitigation for reported TF aborts pending PC runtime verification.

Navigation planner fallback tolerance is 0.15 m; final approach tolerance remains
0.08 m relative to the planned endpoint. Costmap publication may use incremental
`costmap_updates` messages; consumers must subscribe to updates as RViz does.
Internal costmap update rates and obstacle resolution are unchanged.
