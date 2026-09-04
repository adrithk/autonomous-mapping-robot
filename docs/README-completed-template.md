# Autonomous Indoor Mapping Robot

> Use this document to replace the repository root `README.md` only after every
> claimed capability has code and dated test evidence under `results/`.

## Overview

This project is a custom differential-drive robot that autonomously maps unknown,
bounded indoor zones. Place it in a clear zone, turn it on, and it explores reachable
unknown space, creates a 2D occupancy map, then saves the map and run artifacts.

The project does not require saved-map localization or user-selected navigation goals.
Its single mission is autonomous fresh-zone mapping.

## Demo

<!-- Replace with a short hosted video or GIF after integrated validation. -->

`TBD: add autonomous mapping demo`

## What it does

- Starts with motor outputs disabled and validates hardware health before moving.
- Uses wheel encoders and local ESP32 PID loops for repeatable wheel-speed control.
- Uses a 360-degree 2D LiDAR and SLAM Toolbox to build a map while moving.
- Selects reachable unexplored frontiers and drives to them automatically.
- Stops when no useful reachable frontier remains, or when a safety/fault condition occurs.
- Saves the resulting map, configuration, logs, and run metadata.

## System architecture

```text
Frontier exploration
        |
        v
Minimal Nav2 motion executor
        |
        v
ROS wheel targets --> serial bridge --> ESP32
                                      |
                                      v
                    per-wheel PID + watchdog + diagnostics
                                      |
                                      v
                         BTS7960 drivers --> DC motors
                                      ^
                                      |
                                  wheel encoders

LiDAR + wheel odometry --> TF / state estimation --> SLAM Toolbox --> saved map
```

The ESP32 owns low-level, timing-sensitive actuator control. The Raspberry Pi runs
ROS 2, sensor drivers, state estimation, SLAM, exploration, map saving, and the
internal motion stack used to reach exploration frontiers.

## Hardware

| Component | Role |
|---|---|
| ESP32 | Encoder acquisition, wheel PID, motor-driver outputs, watchdog, telemetry |
| Two DC gearmotors with quadrature encoders | Differential-drive motion and wheel feedback |
| Two BTS7960 motor-driver modules | One bidirectional driver per motor |
| Raspberry Pi 5 | ROS 2 compute, sensor processing, SLAM, exploration, map saving |
| 360-degree 2D LiDAR | Range scans for mapping and obstacle detection |
| Battery, fuse, disconnect, and regulators | Protected motor and logic power |
| 3D-printed chassis | Mechanical platform and electronics mounting |

Record exact part numbers, electrical ratings, firmware versions, and calibration
values in [`hardware/parts-list.md`](../hardware/parts-list.md).

## Software

- ESP32 firmware: PlatformIO / Arduino C++
- ROS distribution: ROS 2 Jazzy on Ubuntu 24.04
- Wheel control: local encoder-feedback PID on ESP32
- Robot interfaces: `ros2_control` and a versioned ESP32 transport
- State estimation: `robot_localization`
- Mapping: SLAM Toolbox
- Autonomous exploration: frontier selection plus minimal Nav2 motion execution

## Run flow

1. Place the robot in a clear, bounded indoor zone and verify that the physical motor-power disconnect is reachable.
2. Turn on the robot; it completes sensor, transport, and TF health checks with motors disabled.
3. The mapping run starts a new SLAM session and frontier exploration selects reachable unknown areas.
4. The robot stops when the zone has no useful reachable frontiers, a configured run limit is reached, or a safety/fault condition occurs.
5. Retrieve the saved map and run artifacts from the Raspberry Pi.

## Safety limitations

- A 2D LiDAR only detects objects that intersect its scan plane.
- Do not operate near stairs, drop-offs, cables, small floor objects, pets, or people until appropriate additional sensing and safety controls are validated.
- The ESP32 watchdog is not a replacement for the physical motor-power disconnect.

## Repository layout

```text
firmware/              ESP32 motor, encoder, PID, watchdog, and protocol code
ros_ws/                ROS 2 packages, launch files, and configuration
hardware/
  cad/                 Parametric CAD source, exports, renders, and assembly notes
  electronics/         Wiring diagrams, pin maps, and power-distribution drawings
docs/                  Setup, calibration, and design documentation
results/               Dated bench, robot, and integrated validation records
maps/                  Saved maps and metadata from representative runs
```

Adapt the paths above to the actual final repository layout; do not leave placeholder
directories or links in the replacement README.

## CAD models and Git workflow

Keep editable mechanical design files under `hardware/cad/` and use Git for source,
documentation, and lightweight exports:

```text
hardware/cad/
  source/              Native CAD files or parametric source
  exports/             STL and STEP files needed to reproduce the robot
  renders/             Images used by the README and assembly guide
  assembly.md          Part list, print settings, fasteners, and assembly notes
```

Use Git LFS for large binary CAD files, high-resolution renders, and large meshes.
Commit lightweight sources, STEP/STL release exports, and a clear change note for each
mechanical revision. Tag the CAD revision used for each integrated mapping result so
test evidence can be traced to the exact chassis and sensor-mount geometry.

## Validation evidence

Link the final records here after validation:

- Motor, watchdog, encoder, and PID bench result: `TBD`
- LiDAR/odometry/TF integration result: `TBD`
- Autonomous mapping results for three indoor environments: `TBD`
- Representative saved map: `TBD`
- Demo video: `TBD`

## Development status

For the current implementation state and active work, see the live
[README](../README.md), [roadmap](../ROADMAP.md), and
[test records](../results/README.md).
