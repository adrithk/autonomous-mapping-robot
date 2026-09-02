# Subsystem interfaces

Unknown values are deliberately marked `TBD`. Update this file in the same change as any interface modification.

## Current USB serial motor command interface

**Owner:** `src/main.cpp` on the ESP32  
**Transport:** Arduino `Serial` over the board's serial connection  
**Configured rate:** 115200 baud  
**Framing:** one byte read at a time; no packet framing, checksum, sequence number, acknowledgement, or version  
**Update behavior:** polled continuously in `loop()`; no guaranteed frequency is specified  
**Units:** commands are categorical; the fixed PWM value is a raw 8-bit duty count, not velocity

| Input byte | Left output | Right output | Intended motion |
|---|---|---|---|
| `w` | direction `false`, duty 100 | direction `false`, duty 100 | Forward |
| `s` | direction `true`, duty 100 | direction `true`, duty 100 | Reverse |
| `a` | direction `true`, duty 100 | direction `false`, duty 100 | Turn left in place |
| `d` | direction `false`, duty 100 | direction `true`, duty 100 | Turn right in place |
| `x` | duty 0 | duty 0 | Stop |
| any other byte | unchanged | unchanged | No action |

Each received byte is echoed with `Serial.println()`. Line endings sent by a terminal are therefore consumed and echoed as additional unrecognized bytes, but they do not alter the last motor output.

### Known limitations

- Motion remains latched indefinitely if communication stops.
- There is no explicit stop during `setup()`, command timestamp, timeout, validity response, speed argument, telemetry, or driver-fault input.
- `forward = false` and `backward = true` are intended semantics only; electrical polarity and physical wheel direction are unverified.
- The preserved `src/oldcode.md` used `forward = true`, opposite the current sketch, and contains no test record resolving the discrepancy.
- This interface is a bring-up control, not a suitable final ROS transport contract.

## Current motor driver output interface

**Owner:** ESP32 firmware  
**PWM:** 20 kHz, 8-bit resolution, Arduino LEDC API  
**Reported driver:** Cytron MDD10A; exact board revision and wiring are unverified  
**Reported motors:** two expected 12 V metal DC gearmotors with encoders, 131:1, 83 RPM, 45 kg.cm; exact manufacturer/model is unconfirmed  
**Electrical levels, enable polarity, braking/coasting behavior, and motor rated/stall current:** `TBD`

| Channel | PWM GPIO | Direction GPIO |
|---|---:|---:|
| Left | 25 | 26 |
| Right | 33 | 32 |

Pin assignments and fixed duty are currently compiled into `src/main.cpp`. They require schematic/wiring and bench verification before being treated as authoritative hardware configuration.

## ROS 2 interfaces

None exist. There are no topics, services, actions, nodes, parameters, message types, launch files, or ROS packages in the repository.

Before adding a ROS bridge, specify at minimum:

- command and telemetry message schemas, versioning, units, ranges, timestamps, rates, and timeout behavior;
- responsibility for converting `geometry_msgs/msg/Twist` to wheel targets;
- encoder/odometry publication ownership and covariance;
- diagnostic and hardware-fault reporting;
- reconnect, malformed-message, and stale-command behavior.

Prefer standard ROS message types at the ROS boundary. Do not invent a custom service or action when standard ROS 2 or Nav2 interfaces already express the operation.

## TF frames and coordinate conventions

No transforms are published and no coordinate convention has been committed. Frame names, parent/child relationships, publishers, wheel geometry, sensor mounts, and REP-103/REP-105 conformance must be specified when the robot description/odometry plan begins. Likely ROS frame names are discussed only as future context in [ARCHITECTURE.md](../ARCHITECTURE.md), not as an implemented contract.
