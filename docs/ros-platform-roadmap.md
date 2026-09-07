# ROS 2 platform roadmap

**Status:** Planned; no ROS workspace exists yet
**Target:** Raspberry Pi running 64-bit Ubuntu 24.04 and ROS 2 Jazzy
**Updated:** 2026-09-04

## Product behavior

The completed robot is placed in an unknown, bounded indoor zone and started. It
checks that the drivetrain, encoder feedback, LiDAR data, and transforms are healthy;
creates a fresh map while autonomously exploring reachable space; stops; and saves
the resulting map and run data. Loading an old map and accepting user navigation
goals are outside the initial product.

## Chosen system boundary

ROS 2 runs on the Raspberry Pi. The ESP32 does not join the ROS graph and does not
subscribe directly to a ROS topic. A `ros2_control` hardware plugin on the Pi owns the
USB serial connection and exposes two wheel velocity command interfaces plus wheel
position/velocity state interfaces. The standard ROS 2 Jazzy
`diff_drive_controller` receives body velocity commands and converts them to left and
right wheel commands.

```text
frontier explorer -> Nav2 NavigateToPose
                           |
                           v
                 Nav2 controller output
                           |
                           v
      diff_drive_controller ~/cmd_vel (TwistStamped)
                           |
                  wheel velocity interfaces
                           |
                           v
 custom ros2_control SystemInterface on Raspberry Pi
                           |
                 versioned USB serial
                           |
                           v
 ESP32: watchdog -> ramps -> wheel PID -> BTS7960 -> motors
                           ^
                           |
                        encoders

LiDAR driver -> /scan --------------------------+
wheel odometry -> odom -> base_link             |
robot_state_publisher -> base_link -> laser      v
                                              SLAM Toolbox
                                                  |
                                         /map and map -> odom
```

The ESP32 PID remains the innermost control loop. ROS requests motion; it does not
replace the local motor controller. Loss of valid serial commands must stop the
motors locally even if the Pi or ROS process fails.

## Planned repository layout

```text
src/main.cpp                         keyboard/PID firmware entry point
src/main_ros.cpp                     ROS-serial firmware entry point (planned)
include/ and lib/                    shared drivetrain and protocol code
platformio.ini                       keyboard and ros_serial build environments
ros_ws/src/
  mapping_robot_description/         URDF/Xacro, meshes, dimensions, TF
  mapping_robot_hardware/            ros2_control serial SystemInterface
  mapping_robot_bringup/             controller, LiDAR, SLAM, Nav2 configs/launch
  mapping_robot_exploration/         selected/configured frontier exploration
```

Package names are planned names and may be adjusted once the ROS workspace is
created. Do not create all packages during the ESP32 transport task.

## Implementation stages

### 0. Record hardware and geometry

- Record the exact Raspberry Pi model/RAM, power supply, storage, cooling, OS image,
  and USB connections after they arrive.
- Record the exact LiDAR model, electrical requirements, interface, mount height,
  scan direction, and supported ROS 2 driver.
- Measure encoder counts per output-shaft revolution, loaded wheel radius, and the
  center-to-center wheel separation.
- Recheck PID with the final Pi/LiDAR payload before declaring drivetrain tuning
  complete.

**Gate:** exact hardware and calibrated geometry are recorded; the Pi power rail is
verified under load.

### 1. Create the ROS-serial ESP32 firmware

- Preserve the current keyboard firmware as the default build.
- Add a separately selected `ros_serial` PlatformIO environment and
  `src/main_ros.cpp`; source filters must compile exactly one Arduino entry point.
- Reuse the same motor pins, encoder acquisition, wheel controllers, ramps, output
  limits, and electrical polarity as the tested firmware.
- Implement the proposed framed protocol in `docs/interfaces.md` with a fixed receive
  buffer, validation, sequence tracking, explicit stop, and a 250 ms command
  watchdog.
- Validate command and telemetry framing with focused protocol tests before the
  Raspberry Pi is configured.

**Gate:** keyboard and ROS-serial firmware builds pass; parser tests pass;
invalid, stale, oversized, and corrupt input cannot sustain motion; a dated raised-
wheel serial-control result is recorded.

### 2. Bring up the Raspberry Pi

- Install 64-bit Ubuntu 24.04 and ROS 2 Jazzy from released packages.
- Install development tools, initialize `rosdep`, create `ros_ws`, and verify basic
  ROS publisher/subscriber communication.
- Configure a stable device name for the ESP32 using `/dev/serial/by-id/` or a udev
  rule rather than assuming `/dev/ttyUSB0`.
- Verify the Pi and LiDAR power budget, cooling, startup, and clean shutdown.

**Gate:** ROS 2 starts after reboot, the ESP32 device is stable across reconnects,
and no motor motion occurs during Pi boot or serial discovery.

### 3. Add robot description and ros2_control

- Create the two wheel joints and fixed LiDAR transform in URDF/Xacro.
- Implement a C++ `hardware_interface::SystemInterface` that sends ROS wheel
  rad/s in version-2 serial frames and converts returned encoder counts/counts-per-second
  to radians/rad/s for wheel state.
- Configure `controller_manager`, `joint_state_broadcaster`, and
  `diff_drive_controller` with measured wheel radius and separation.
- Let `diff_drive_controller` publish wheel odometry and `odom -> base_link` initially.
  Do not add `robot_localization` until another useful odometry source exists or
  measured evidence shows it is needed.

**Gate:** ROS keyboard teleoperation commands both wheels, feedback appears as wheel
joint state, odometry signs and units are correct, and stopping the bridge triggers
the ESP32 watchdog.

### 4. Integrate LiDAR and transforms

- Install the vendor-supported Jazzy driver for the exact LiDAR.
- Publish `sensor_msgs/msg/LaserScan` on `/scan`.
- Publish the static `base_link -> laser` transform from the measured mount.
- Verify scan direction, angular zero, range limits, timestamps, frame name, and that
  the chassis does not significantly block the scan plane.

**Gate:** stationary and slow-motion scans display correctly in RViz and the TF tree
contains one unambiguous path between `odom`, `base_link`, and `laser`.

### 5. Produce the first map under manual teleoperation

- Configure SLAM Toolbox online asynchronous mapping with `/scan`, `odom`,
  `base_link`, and `map` frames.
- Drive slowly by keyboard while monitoring the map, odometry, scan alignment, and
  loop closure.
- Save both a standard occupancy map and the run configuration/logs.

**Gate:** two manually driven runs of the same small area produce recognizable,
consistent maps without large tears or duplicated walls.

### 6. Add Nav2 motion execution

- Configure the robot footprint, local/global costmaps, velocity/acceleration limits,
  planner, controller, behaviors, collision monitoring where supported, and command
  timeouts.
- Run Nav2 while SLAM Toolbox is mapping; Nav2 supplies safe motion to requested
  poses but does not decide where unexplored space is.
- Validate short goals before allowing autonomous exploration.

**Gate:** repeated short goals succeed without collisions, loss of localization, or
failure to stop after command loss.

### 7. Add autonomous frontier exploration and map saving

- Select a Jazzy-compatible frontier exploration package only after checking its
  maintenance state, license, interfaces, and behavior in simulation/on the robot.
- The explorer reads the live occupancy map, chooses reachable frontiers, and sends
  `NavigateToPose` goals to Nav2.
- Add a small mission coordinator that waits for system health, starts exploration,
  handles no-frontier/failure/time limits, stops the robot, and invokes map saving.
- Make the mapping launch start automatically at boot only after manual integrated
  operation is reliable.

**Gate:** placing and starting the robot produces and saves a fresh map without the
operator selecting navigation goals.

### 8. Validate the finished behavior

- Repeat mapping in at least three bounded indoor environments.
- Record maps, bags/logs, configuration, commit, hardware revision, completion
  reason, run time, interventions, and failures.
- Repeat the same environment twice to assess map consistency.

**Gate:** the evidence supports every capability claimed in the README and resume.

## Initial ROS interfaces

| Interface | Owner/consumer | Planned type or role |
|---|---|---|
| `diff_drive_controller/cmd_vel` | Nav2/teleop -> controller | `geometry_msgs/msg/TwistStamped` |
| `diff_drive_controller/odom` | controller -> SLAM/Nav2 | `nav_msgs/msg/Odometry` |
| `joint_states` | joint state broadcaster | `sensor_msgs/msg/JointState` |
| `/scan` | LiDAR driver -> SLAM/Nav2 | `sensor_msgs/msg/LaserScan` |
| `/map` | SLAM Toolbox -> exploration/Nav2 | `nav_msgs/msg/OccupancyGrid` |
| `NavigateToPose` | explorer -> Nav2 | Nav2 action |
| `map -> odom` | SLAM Toolbox | TF transform |
| `odom -> base_link` | diff drive controller initially | TF transform |
| `base_link -> laser` | robot state publisher | fixed TF transform |

Exact namespaces and remappings must be captured in launch/config files when those
packages exist.

## Explicit exclusions for the first working version

- No IMU or IMU fusion.
- No micro-ROS on the ESP32.
- No saved-map localization or user-selected navigation mode.
- No docking, vacuum subsystem, cloud service, or custom SLAM algorithm.
- No autonomous exploration until teleoperation, odometry, LiDAR, TF, SLAM, and
  short Nav2 goals pass independently.

## Primary references

- [ROS 2 Jazzy installation documentation](https://docs.ros.org/en/jazzy/Installation.html)
- [ros2_control Jazzy differential-drive controller](https://control.ros.org/jazzy/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)
- [Nav2 first-time robot setup guide](https://docs.nav2.org/jazzy/configuration_and_development/first_time_robot_setup_guide/)
- [Nav2 navigating while mapping with SLAM Toolbox](https://docs.nav2.org/jazzy/tutorials/general_tutorials/navigation2_with_slam/navigation2_with_slam/)
- [SLAM Toolbox Jazzy package documentation](https://docs.ros.org/en/ros2_packages/jazzy/api/slam_toolbox/)
