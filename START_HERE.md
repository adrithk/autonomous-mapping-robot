# Start here

Read the [project overview](README.md) for the showcase, architecture summary, and simulation quick start.
This repository contains ESP32 firmware and the complete ROS package at
[`ros_ws/src/my_bot/`](ros_ws/src/my_bot/). The separate source repository is retained;
this checkout is now the consolidated project entry point.

## Work with the project

- Simulation setup: [WSL / Ubuntu guide](ros_ws/src/my_bot/WSL_SETUP.md).
- Autonomous simulation: [exploration guide](ros_ws/src/my_bot/EXPLORATION.md), [active plan 009](docs/plans/active/009-autonomous-exploration.md). Runtime acceptance remains pending.
- Navigation with live SLAM: [Nav2 guide](ros_ws/src/my_bot/NAVIGATION.md), [copy/paste WSL workflow](docs/WSL_COPY_PASTE.md).
- Mapping and export: [SLAM guide](ros_ws/src/my_bot/SLAM.md).
- Physical bringup: [hardware guide](ros_ws/src/my_bot/HARDWARE.md).
- Firmware: select `pio run -e keyboard` or `pio run -e ros_serial` explicitly.
- Contributor context: [architecture](ARCHITECTURE.md), [interfaces](docs/interfaces.md),
  [testing](docs/testing.md), and [roadmap](ROADMAP.md).
- Portfolio assets still needed: [completion checklist](docs/project-completion.md).

## Current execution

Firmware, the ROS hardware plugin, simulation, and simulation SLAM source exist.
Initial simulation driving/scans and [physical teleoperated mapping and saved-map
Nav2 navigation](results/2026-09-10-real-room-mapping-navigation.md) are documented.
Repeated physical integration checks and autonomous exploration acceptance remain pending.
Plans [003](docs/plans/active/003-ros-ready-esp32-transport.md),
[004](docs/plans/active/004-pi-hardware-interface.md), and
[005](docs/plans/active/005-simulation-slam.md) retain the remaining validation gates.
Do not close hardware plans based on documentation polish.

Follow [AGENTS.md](AGENTS.md) for engineering work. Historical progress entries
record the state at their date; the [roadmap](ROADMAP.md) summarizes current status.
