# Subsystem interfaces

Unknown values are deliberately marked `TBD`. Update this file in the same change as any interface modification.

## Current USB serial motor command interface

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
the same telemetry immediately. It does not echo every received byte.

### Known limitations

- Controller calculations have automated checks and the firmware builds. Raised-wheel forward/reverse tracking passed at +/-3000 counts/s on 2026-09-04; ground-load performance remains unverified.
- There is no variable-speed command, driver-fault input, or framed/acknowledged transport.
- Counts/revolution is unverified, so targets and measurements cannot yet be converted reliably to rad/s.
- Initial gains and left/right electrical polarity require controlled hardware validation.
- This interface is a bring-up control, not a suitable final ROS transport contract.

## Current motor driver output interface

**Owner:** ESP32 firmware  
**PWM:** 20 kHz, 8-bit resolution, Arduino LEDC API; controller output limited to 200
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
**Acquisition:** interrupt on each A channel; B is read to infer direction. Count differences are converted to counts/s at a nominal 50 Hz using actual elapsed time. Counts are not yet calibrated to wheel position or rad/s.

**Controller:** one controller per wheel using initial gains `Kp=0.020`, `Ki=0.010`, `Kd=0.000`, and feed-forward `0.048 PWM/(count/s)`. Integral magnitude is limited to 4000 count-seconds and output to PWM 200. Straight targets use a 10000 counts/s² slew limit for a 300 ms ramp to 3000 counts/s; turn targets use an 18000 counts/s² limit for a 100 ms ramp to 1800 counts/s. These values are provisional pending physical tuning.

| Wheel | A input | B input |
|---|---:|---:|
| Left | GPIO 34 | GPIO 35 |
| Right | GPIO 36 (`VP`) | GPIO 39 (`VN`) |

The level shifter, encoder wire order, signal voltage, count sign, and count resolution are unverified. GPIO 34-39 have no internal pull resistors; the intended external level shifter must provide suitable pull-ups.

Pin assignments, targets, gains, limits, and polarity are currently compiled into `src/main.cpp`. The code builds, but it requires BTS7960 wiring review and controlled hardware tuning before being treated as a validated configuration. The reported four-channel level shifter is intended for encoder signals, not motor-driver control inputs; its electrical behavior remains unverified.

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
