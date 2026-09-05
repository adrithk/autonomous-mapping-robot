# 003: Keep keyboard and ROS-serial firmware as separate selectable builds

**Status:** Accepted for the next firmware change
**Date:** 2026-09-04

## Context

The known keyboard/PID firmware must remain available while a ROS-ready serial entry
point is developed. Two Arduino source files that both define `setup()` and `loop()`
cannot be linked into one PlatformIO build.

## Decision

Keep `src/main.cpp` as the keyboard entry point and add `src/main_ros.cpp` for the
ROS-serial entry point. Add `keyboard` and `ros_serial` PlatformIO environments with
source filters so exactly one entry point is compiled. Set `keyboard` as the default
environment so an ordinary build/upload preserves current behavior.

Shared motor, encoder, PID, ramp, and safety logic must be extracted into reusable
code rather than copied into two independently drifting implementations.

## Consequences

- `pio run` continues to build the keyboard firmware by default.
- `pio run -e ros_serial` explicitly builds the serial-controlled firmware.
- Both builds must pass after any shared drivetrain change.
- Adding the second entry point requires a behavior-preserving refactor of the current
  monolithic firmware before the new protocol is layered on top.
