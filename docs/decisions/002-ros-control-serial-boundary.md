# 002: Use ros2_control on the Pi and a serial-controlled ESP32

**Status:** Accepted as intended architecture
**Date:** 2026-09-04

## Context

The robot needs to accept velocity commands from ROS 2 while retaining deterministic
motor control and command-loss stopping on the ESP32. The ESP32 currently runs
encoder-feedback wheel PID and has no ROS client or framed transport.

## Decision

ROS 2 Jazzy will run on the Raspberry Pi. A custom C++
`hardware_interface::SystemInterface` will connect `ros2_control` to the ESP32 over
USB serial. The standard `diff_drive_controller` will convert body velocity commands
into left/right wheel velocity commands and compute wheel odometry from returned
joint feedback.

The ESP32 will not be a ROS node and will not use micro-ROS in the first version. Its
ROS-serial firmware will accept framed wheel targets, run the existing local PID,
enforce its own watchdog, and return encoder/controller state.

## Reasoning

- It retains local, deterministic actuator behavior if the Pi or ROS process stalls.
- It lets Nav2 and teleoperation use standard ROS controller interfaces.
- It avoids placing DDS, ROS executors, and ROS distribution compatibility on the
  small controller.
- It gives simulation and physical hardware the same wheel-level ROS interface.

## Consequences

- The Pi-side hardware plugin owns ROS-unit conversion and serial reconnect behavior.
- The wire protocol must be versioned, bounded, testable, and independent of ROS
  message serialization.
- Encoder counts per revolution, loaded wheel radius, and wheel separation must be
  measured before odometry can be accepted.
- The ESP32 is indirectly controlled by ROS, but it does not literally subscribe to
  a ROS topic.

## Alternatives considered

- **micro-ROS on ESP32:** rejected for the first version because it adds executor,
  transport-agent, memory, and ROS-version complexity without improving the local
  PID boundary.
- **Custom ROS bridge node without ros2_control:** viable for early experiments, but
  rejected as the target architecture because it would duplicate standard wheel
  command/state integration.
- **Motor PID on the Raspberry Pi:** rejected because USB/OS scheduling and Pi failure
  must not be the only protection against stale actuator commands.
