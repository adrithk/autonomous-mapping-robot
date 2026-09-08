# Code audit — 2026-09-07

Scope: existing ESP32 firmware and my_bot description, dependencies, controllers,
launch sequencing, clocks/TF, serial protocol, teleoperation and simulation SLAM.
No new navigation, physical LiDAR driver or physical SLAM functionality was added.

## Findings and changes

- Fixed signed encoder rollover in the sibling firmware: both ISR increments and
  control-loop differences now wrap deliberately. Native boundary tests cover both
  directions. This preserves normal drive commands, gains and watchdog behavior.
- Added a ROS-dependent hardware_plugin_test to CTest. It loads my_bot/Esp32System
  using pluginlib, configures its interfaces and rejects an invalid joint layout.
  It never activates hardware or opens serial. This is necessary because Gazebo
  loads its own plugin, so successful simulation does not validate the real plugin.
- Reviewed package dependencies, plugin export, Xacro modes, controller joint names,
  radians/count conversion, limits, launch sequencing and fault handling. No further
  demonstrated runtime defect was found in those paths during this review.
- Simulation uses /clock throughout; hardware controllers use wall time. Only the
  differential-drive controller publishes odom->base_link; SLAM publishes map->odom.
  Scan frames/ranges match the model and SLAM configuration. No custom RViz shader
  exists in this repository. No speculative shader, QoS or timing changes were made.

## Verification actually performed

Mac environment: clang++, AddressSanitizer and UndefinedBehaviorSanitizer;
Python with Xacro 2.1.1 and PyYAML. All completed successfully:

- Both PlatformIO firmware builds: keyboard and ros_serial.
- Three firmware native suites: controller, serial protocol/conversion, encoder rollover.
- Host pseudo-terminal transport/fault suite and actual firmware-parser conformance.
- Eight model/configuration tests and three teleoperation tests.
- Diff whitespace checks for audit changes.

The new hardware_plugin_test has NOT been compiled or run here: this Mac has no
ROS/colcon/Linux runtime. Existing builder screenshots show an earlier Ubuntu build
and tests passed, but do not validate this new test. Run on Jazzy Ubuntu 24.04:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros_ws
colcon build --symlink-install --packages-select my_bot
source install/setup.bash
colcon test --packages-select my_bot --event-handlers console_direct+
colcon test-result --verbose
```

## What the screenshots establish

Controllers activated, scan data and odom->laser transforms were observed, and
RViz logged receipt of a 79 x 79 map. Thus there is evidence of initial map output,
not proof of accurate mapping, loop closure, map saving or reliable startup.
Registering sensor is an informational message, not a completion progress bar.
A topic echo/rate command subscribes to /scan; it does not publish LiDAR data.

RViz reported an indexed-map shader error even with software rendering. The same
error has been reported upstream on Jazzy on a Pi 5, so it is NOT established as
WSL-only and switching computers is not a guaranteed fix. The exact local graphics
failure remains unresolved. TF queue-drop messages also need timestamp validation
if persistent; they are not proof that /scan is absent.

References checked:
- https://github.com/ros2/rviz/issues/1279
- https://github.com/ros2/rviz/pull/459
- https://control.ros.org/jazzy/doc/ros2_control/hardware_interface/doc/writing_new_hardware_component.html
- https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/launch/online_async_launch.py

## Remaining real-robot acceptance

Hardware plugin load and physical USB/watchdog/reconnect tests are still required.
The physical LiDAR driver and real SLAM launch are not yet implemented. Before
adding them, confirm encoder calibration/direction, loaded dimensions and actual
laser mount, then validate odometry, live scan timestamps and TF on the Pi. Mapping
can run without RViz, but that does not establish the GUI works or the map is valid.
