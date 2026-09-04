# Subsystem interfaces

Unknown values are deliberately marked `TBD`. Update this file in the same change as any interface modification.

## Current USB serial motor command interface

**Owner:** `src/main.cpp` on the ESP32  
**Transport:** Arduino `Serial` over the board's serial connection  
**Configured rate:** 115200 baud  
**Framing:** one byte read at a time; no packet framing, checksum, sequence number, acknowledgement, or version  
**Update behavior:** polled continuously in `loop()`; motion commands must arrive at least every 1000 ms or the ESP32 stops both motors
**Units:** commands are categorical; the fixed PWM value is a raw 8-bit duty count, not velocity

| Input byte | Left output | Right output | Intended motion |
|---|---|---|---|
| `w` | `RPWM` duty 100, `LPWM` 0 | `RPWM` duty 100, `LPWM` 0 | Nominal forward; physical direction unverified |
| `s` | `RPWM` 0, `LPWM` duty 100 | `RPWM` 0, `LPWM` duty 100 | Nominal reverse; physical direction unverified |
| `a` | `RPWM` 0, `LPWM` duty 100 | `RPWM` duty 100, `LPWM` 0 | Nominal left turn; physical direction unverified |
| `d` | `RPWM` duty 100, `LPWM` 0 | `RPWM` 0, `LPWM` duty 100 | Nominal right turn; physical direction unverified |
| `x` | both PWM outputs 0 | both PWM outputs 0 | Stop |
| `e` | unchanged | unchanged | Print encoder counts |
| carriage return / newline | unchanged | unchanged | Ignored; does not renew the motion lease |
| any other byte | both PWM outputs 0 | both PWM outputs 0 | Stop |

The firmware prints startup, timeout, and unknown-command messages. While a motion
command is active, it prints raw left/right encoder counts every 200 ms. The `e`
command prints the same counts immediately. It does not echo every received byte.

### Known limitations

- There is no valid build result for this firmware revision because PlatformIO is unavailable on the current computer.
- There is no speed argument, wheel-speed telemetry, driver-fault input, or framed/acknowledged transport.
- The `RPWM`/`LPWM` direction convention is code intent only; electrical polarity and physical wheel direction are unverified.
- This interface is a bring-up control, not a suitable final ROS transport contract.

## Current motor driver output interface

**Owner:** ESP32 firmware  
**PWM:** 20 kHz, 8-bit resolution, Arduino LEDC API  
**Intended replacement drivers:** two HiLetgo BTS7960 single-channel modules, one per motor; reported purchased but exact board revision, arrival, and wiring are unverified. The former Cytron MDD10A is reported damaged and must not be used.
**Reported motors:** two expected 12 V metal DC gearmotors with encoders, 131:1, 83 RPM, 45 kg.cm; exact manufacturer/model is unconfirmed  
**Electrical levels, enable polarity, braking/coasting behavior, and motor rated/stall current:** `TBD`

| Channel | BTS7960 GPIOs | Verification status |
|---|---|---|
| Shared enable | GPIO 27 to all four `R_EN`/`L_EN` pins | Intended wiring; requires external 10 kΩ pull-down to ground and bench verification |
| Left | GPIO 25 `RPWM` + GPIO 26 `LPWM` | Code present; wiring and behavior unverified |
| Right | GPIO 32 `RPWM` + GPIO 33 `LPWM` | Code present; wiring and behavior unverified |

## Current encoder input interface

**Owner:** ESP32 firmware
**Electrical path:** encoder A/B signals -> four-channel 5 V-to-3.3 V level shifter -> ESP32 inputs
**Acquisition:** interrupt on each A channel; B is read to infer direction. Counts are raw transitions, not calibrated wheel position or velocity. Raw totals are reported every 200 ms while motion is commanded and on demand with `e`.

| Wheel | A input | B input |
|---|---:|---:|
| Left | GPIO 34 | GPIO 35 |
| Right | GPIO 36 (`VP`) | GPIO 39 (`VN`) |

The level shifter, encoder wire order, signal voltage, count sign, and count resolution are unverified. GPIO 34-39 have no internal pull resistors; the intended external level shifter must provide suitable pull-ups.

Pin assignments and fixed duty are currently compiled into `src/main.cpp`. They require build, BTS7960-specific wiring/specification review, and bench verification before being treated as authoritative hardware configuration. The reported four-channel level shifter is intended for encoder signals, not motor-driver control inputs; its electrical behavior is also unverified.

## ROS 2 interfaces

None exist. There are no topics, services, actions, nodes, parameters, message types, launch files, or ROS packages in the repository.

The planned default is a Raspberry Pi bridge node or `ros2_control` hardware
interface that subscribes to `geometry_msgs/msg/Twist` commands on `/cmd_vel`,
converts linear/angular velocity into left/right wheel-speed targets, and sends those
targets to the ESP32 over a versioned USB serial protocol. The ESP32 will run both
wheel PID loops and the command watchdog, then return encoder counts, measured wheel
speeds, and fault state. Direct ROS topic subscription on the ESP32 would require
micro-ROS and is an alternative, not the current default.

Before adding a ROS bridge, specify at minimum:

- command and telemetry message schemas, versioning, units, ranges, timestamps, rates, and timeout behavior;
- the exact owner and parameters for converting `geometry_msgs/msg/Twist` to wheel targets;
- encoder/odometry publication ownership and covariance;
- diagnostic and hardware-fault reporting;
- reconnect, malformed-message, and stale-command behavior.

Prefer standard ROS message types at the ROS boundary. Do not invent a custom service or action when standard ROS 2 or Nav2 interfaces already express the operation.

## TF frames and coordinate conventions

No transforms are published and no coordinate convention has been committed. Frame names, parent/child relationships, publishers, wheel geometry, sensor mounts, and REP-103/REP-105 conformance must be specified when the robot description/odometry plan begins. Likely ROS frame names are discussed only as future context in [ARCHITECTURE.md](../ARCHITECTURE.md), not as an implemented contract.
