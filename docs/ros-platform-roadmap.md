# ROS 2 platform workflow

The Raspberry Pi runs ROS 2 Jazzy on Ubuntu 24.04. The ESP32 owns encoder
sampling, wheel-speed control, motor outputs and the serial-command watchdog.

## Mapping

Keyboard teleoperation commands reach the differential-drive controller. The Pi
sends wheel targets through the serial hardware plugin; encoder feedback supplies
wheel odometry. SLAM Toolbox combines odometry and LiDAR observations into the
occupancy map shown in RViz. The operator saves the map using Nav2's map saver.

## Autonomous path planning

Map server loads the saved occupancy map. AMCL estimates the robot's pose from
LiDAR observations and odometry. A destination selected in RViz is passed to Nav2,
which plans a path and controls movement through the same drivetrain interface.
AMCL and SLAM Toolbox are separate localization modes and are not run together.

[Architecture](../ARCHITECTURE.md) · [Physical demonstration](../results/2026-09-10-real-room-mapping-navigation.md)
