# Start here

Read the [project overview](README.md) for the showcase, architecture summary, and simulation quick start.
This repository contains ESP32 firmware and the complete ROS package at
[`ros_ws/src/my_bot/`](ros_ws/src/my_bot/). The separate source repository is retained;
this checkout is now the consolidated project entry point.

## Work with the project

- Simulation setup: [WSL / Ubuntu guide](ros_ws/src/my_bot/WSL_SETUP.md).
- Navigation with live SLAM: [Nav2 guide](ros_ws/src/my_bot/NAVIGATION.md), [copy/paste WSL workflow](docs/WSL_COPY_PASTE.md).
- Mapping and export: [SLAM guide](ros_ws/src/my_bot/SLAM.md).
- Physical bringup: [hardware guide](ros_ws/src/my_bot/HARDWARE.md).
- Firmware: select `pio run -e keyboard` or `pio run -e ros_serial` explicitly.
- Contributor context: [architecture](ARCHITECTURE.md), [interfaces](docs/interfaces.md),
  [testing](docs/testing.md), and [capability summary](ROADMAP.md).

## Current operation

The robot maps rooms through keyboard teleoperation and SLAM Toolbox, then uses
AMCL and Nav2 for autonomous path planning on the saved map. See the
[physical demonstration](results/2026-09-10-real-room-mapping-navigation.md).

Follow [AGENTS.md](AGENTS.md) for engineering work. Dated plans and test records
preserve development history; the [capability summary](ROADMAP.md) describes the
current project.
