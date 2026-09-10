# Demonstrated capabilities

Updated September 10, 2026. This page summarizes the implemented system and recorded demonstrations.

| Capability | Implementation and evidence |
|---|---|
| Motor control | ESP32 encoder-feedback wheel-speed control with feed-forward/PI, command ramps and watchdogs |
| ROS integration | Pi-side ros2_control serial plugin, differential-drive controller, wheel odometry and robot TF |
| Physical LiDAR | RPLIDAR A1M8 connected to the Pi through GPIO UART; scan publication demonstrated |
| Room mapping | Keyboard teleoperation with SLAM Toolbox, live RViz visualization and manual map saving |
| Autonomous path planning | Nav2 plans and drives to destinations selected in RViz, using AMCL localization on the saved map |
| Simulation | Gazebo differential-drive model, simulated LiDAR, SLAM and Nav2 integration |

The [physical demonstration record](results/2026-09-10-real-room-mapping-navigation.md)
contains the room photographs, navigation recordings and their evidence limits.
The [initial simulated SLAM result](results/2026-09-08-simulated-lidar-slam.md)
documents the earlier simulation demonstration. Recorded movement and map output
are distinct from quantitative accuracy or reliability measurements.
