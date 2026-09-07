# 004: Accept wheel rad/s in ROS-serial firmware

**Status:** Accepted, implemented; physical validation pending
**Date:** 2026-09-07

At the builder's request, version 2 accepts left/right wheel rad/s and converts
commands on the ESP32 in a ROS-only adapter. Shared PID and the default keyboard
build retain counts/s and unchanged behavior. Preliminary calibration is 4185
counts/revolution on both wheels (approximately 41850 over ten turns reported).
Constants are centralized in `include/ros_wheel_units.h`.

Version 1 is rejected because silently reinterpreting existing counts/s commands
as rad/s is unsafe. CRC, sequence checks, watchdog, explicit stop and the equivalent
4000 counts/s bound remain. Feedback retains raw counts/counts/s, with version 2.

The Pi still needs a custom ros2_control SystemInterface for USB framing,
sequence/reconnect handling, feedback conversion and lifecycle safety. It sends
wheel rad/s directly; ESP32 does not become a ROS subscriber. This amends command
conversion ownership in decision 002 without moving the wheel PID to the Pi.

Compile and native tests cannot establish ROS or physical compatibility; upload,
watchdog/reconnect tests and integrated Pi validation are still required.
