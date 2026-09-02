# 001: Separate low-level control from ROS autonomy

**Status:** Accepted as intended architecture  
**Date:** 2026-09-01 (migrated from the initial README; original decision date not recorded)

## Context

The initial repository README describes a differential-drive robot with an ESP32 and a future Ubuntu 24.04/ROS 2 Jazzy computer. Timing-sensitive actuator and sensor acquisition work needs different failure and scheduling behavior from mapping and navigation workloads.

## Decision

The ESP32 will own direct motor outputs, encoder sampling, local wheel-speed control, command-loss handling, and immediate actuator-safe behavior. The ROS computer will own hardware bridging, robot model/TF coordination, sensor processing, state estimation, SLAM, localization, Nav2, and mission-level autonomy.

Only ESP32 open-loop motor output exists today. This record sets intended ownership; it does not assert that the planned components are implemented.

## Alternatives considered

The Git history does not record evaluated alternatives. In particular, it does not establish whether motor control on the ROS computer, micro-ROS on the ESP32, or a standard `ros2_control` hardware architecture was explicitly compared.

## Reasoning

The split preserves deterministic, local handling of actuator timing and command loss while allowing compute-heavy autonomy to use established ROS 2 packages. It also avoids making a networked or general-purpose process the only path to a safe actuator state.

## Consequences

- The microcontroller-to-computer protocol must carry commands, timestamps/validity, feedback, and diagnostics with defined failure behavior.
- Safety must be layered; ESP32 stop behavior does not replace independent power isolation or system hazard analysis.
- ROS-side implementations should reuse standard ROS 2, `ros2_control`, `robot_localization`, SLAM Toolbox, and Nav2 interfaces where appropriate.
- The exact odometry computation boundary and transport technology remain future decisions.

