# Autonomous Indoor Mapping Robot

**ROS 2 Jazzy • SLAM Toolbox • Nav2 • ros2_control • Gazebo • ESP32**

A custom differential-drive robot that builds maps of indoor rooms and navigates to destinations selected in RViz. Built around a 3D-printed chassis, Raspberry Pi 5 and 360-degree LiDAR, it connects embedded wheel-speed control with a complete ROS 2 mapping and navigation stack.

Mapping uses keyboard teleoperation with **SLAM Toolbox**. Once the map is saved, **AMCL** localizes the robot and **Nav2** plans and drives the route to each selected goal.

## Demo

### Real-room mapping

| Physical robot | Room map in RViz |
|:---:|:---:|
| <img src="media/real-room/teleoperation-robot.jpg" alt="Custom robot with mounted LiDAR during room mapping" width="380"> | <img src="media/real-room/teleoperation-slam-map.jpg" alt="Room occupancy map and LiDAR returns displayed in RViz" width="380"> |

The robot was driven through the room while LiDAR scans and encoder-based odometry supplied SLAM Toolbox with observations. The resulting occupancy map was saved for navigation.

### Nav2 navigation on the saved map

| Robot navigating · 49 s | RViz navigation view · 51 s |
|:---:|:---:|
| [![Watch the physical navigation recording](media/real-room/nav2-robot-poster.jpg)](media/real-room/nav2-robot.mp4) | [![Watch the RViz navigation recording](media/real-room/nav2-rviz-poster.jpg)](media/real-room/nav2-rviz.mp4) |

Click a preview to watch or download the full-speed recording. On GitHub, use **View raw / Download** if playback is unavailable.

These initial demonstrations use operator-selected goals and tethered power. Setup, observations and measurement limits are documented in the [September 10 demonstration record](results/2026-09-10-real-room-mapping-navigation.md).

## Engineering highlights

- **Custom ROS hardware interface:** a C++ `ros2_control` plugin connects the standard differential-drive controller to the ESP32. The versioned serial protocol carries wheel commands and encoder feedback, with CRC checks, sequence tracking and an acknowledged stop at startup.
- **Embedded feedback control:** shared 50 Hz feed-forward/PI wheel controllers handle encoder sampling, command ramps and bounded motor outputs. An independent 250 ms watchdog stops commands that expire.
- **Mapping and navigation integration:** robot-specific Xacro, launch files, controller settings and TF connect wheel odometry and LiDAR to SLAM Toolbox, AMCL and Nav2.
- **Simulation and mechanical design:** Gazebo Harmonic provides a differential-drive model, simulated LiDAR and an obstacle room for integration testing. [STEP and STL files](hardware/cad/README.md) include the chassis, caster mount and LiDAR holder.

## How it works

The Raspberry Pi handles perception, localization and route planning. The ESP32 handles motor outputs and wheel-speed control, keeping command-loss handling independent of the ROS computer.

```text
Mapping:     LiDAR + wheel odometry → SLAM Toolbox → Saved map
Navigation:  Saved map + LiDAR + wheel odometry → AMCL localization

RViz goal → Nav2 → diff_drive_controller → Custom ros2_control plugin
                                                      │ USB serial
                                                      ▼
                                                ESP32 wheel PI → Motors
                                                      ▲
                                                   Encoders
```

### SLAM: turning laser scans into a room map

**Simultaneous Localization and Mapping (SLAM)** solves two connected problems: building a map of an unfamiliar space and estimating the robot's position within it. The RPLIDAR supplies a 360-degree slice of surrounding surfaces, while wheel encoders estimate how far the robot has moved between scans.

[SLAM Toolbox](https://github.com/SteveMacenski/slam_toolbox/tree/jazzy) uses **scan matching** to align overlapping laser observations and refine that motion estimate. It links successive robot poses into a **pose graph**. When a previously visited area is recognized, **loop closure** adds a constraint that lets the optimizer correct accumulated drift across the trajectory. The included [SLAM configuration](ros_ws/src/my_bot/config/slam.yaml) enables scan matching and loop closure with a Ceres solver.

The output is an **occupancy grid**: a spatial representation of free, occupied and unobserved areas. This project uses 5 cm map cells, displays the map and live laser returns in RViz, and exports the occupancy image with its scale and origin in a YAML file. Mapping is teleoperated; the saved map becomes the reference for autonomous navigation.

### Nav2: turning a destination into motion

For the physical saved-map workflow, **Adaptive Monte Carlo Localization (AMCL)** estimates the robot's position and heading. Its particle filter maintains candidate poses, predicts their movement from odometry, and weighs them against how well the current laser scan agrees with the map. This keeps navigation tied to observations of the room as the wheels turn. [AMCL documentation](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/others/configuring_amcl/).

The operator then selects a destination and final heading in RViz. Nav2 separates finding a route from deciding how to drive the next part of it. The repository's [simulation navigation configuration](ros_ws/src/my_bot/config/nav2.yaml) makes that pipeline explicit:

- **Global planning:** NavFn uses Dijkstra search to find a route through known free space. Costmaps combine the map with laser observations; obstacle inflation assigns higher costs near walls and furniture to encourage clearance.
- **Local trajectory control:** DWB evaluates candidate forward and turning motions against obstacle costs, path alignment and progress toward the goal. The controller is configured to update at 20 Hz, repeatedly choosing the next velocity command as the robot moves.
- **Motion execution:** velocity smoothing limits acceleration, and a collision monitor checks laser observations before commands reach the drivetrain. The differential-drive controller converts body motion into wheel targets, which the ESP32 tracks using encoder feedback.

[NavFn](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/planners_plugins/configuring_navfn/) and [DWB](https://docs.nav2.org/jazzy/configuration_and_development/configuration_guide/controller_plugins/dwb_controller/) provide the planning and control algorithms; this project's integration connects them to the custom robot. The physical recordings demonstrate saved-map navigation with AMCL, while the included simulation launch runs Nav2 alongside live SLAM. Exact physical-run planner settings and measured obstacle-response performance were not captured.

Mapping and saved-map localization run as separate modes. In simulation, Gazebo replaces the serial hardware interface while retaining the ROS controllers and robot model.

[System architecture](ARCHITECTURE.md) · [Serial protocol and interfaces](docs/interfaces.md) · [Hardware inventory](hardware/parts-list.md)

## Simulation

![Gazebo obstacle room and the SLAM occupancy map in RViz](results/2026-09-08-simulated-lidar-slam/simulated-lidar-slam.png)

Gazebo models the robot in a room with six interior obstacles; RViz displays the map built from simulated laser scans. The simulation supports teleoperation, SLAM and Nav2 integration using estimated physical parameters. [Recorded simulation result](results/2026-09-08-simulated-lidar-slam.md).

To try it on Ubuntu 24.04 with ROS 2 Jazzy and Gazebo Harmonic, follow the [build instructions](ros_ws/src/my_bot/README.md#build), then launch:

```bash
ros2 launch my_bot slam_sim.launch.py
```

The [simulation guide](ros_ws/src/my_bot/SIMULATION.md) covers driving, map export and Nav2 goals. For the assembled robot, use the [hardware guide](ros_ws/src/my_bot/HARDWARE.md).

## Verification

Automated checks cover wheel-control logic, protocol parsing, encoder rollover, host/firmware compatibility, emulated serial faults and ROS model/configuration consistency. Dated records also document raised-wheel tracking, simulated mapping and the physical room demonstration.

The demonstrations establish initial operation; map accuracy, navigation repeatability and physical stop timing have not been quantified. See [recorded results](results/README.md) and [verification instructions](docs/testing.md).

## Repository

| Location | Contents |
|---|---|
| [src/](src/) and [include/](include/) | ESP32 firmware and shared control/protocol logic |
| [ros_ws/src/my_bot/](ros_ws/src/my_bot/) | ROS hardware plugin, robot model, launch files, configuration and simulation |
| [hardware/](hardware/) | CAD files, component inventory and preliminary geometry |
| [test/](test/) and [ROS tests](ros_ws/src/my_bot/test/) | Firmware logic, serial transport and ROS integration checks |
| [results/](results/README.md) | Dated demonstrations and test evidence |

## Credits

Custom work includes the ESP32 firmware, serial transport and ROS hardware plugin, and robot-specific model, simulation and mapping integration. The robot description began with [Josh Newans’ my_bot template](https://github.com/joshnewans/my_bot), whose [Apache-2.0 license](ros_ws/src/my_bot/LICENSE.md) is retained. ROS 2, ros2_control, Gazebo, SLAM Toolbox and Nav2 provide the underlying robotics frameworks.
