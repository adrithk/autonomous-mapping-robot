# Start here: simulation or real robot

**Mapping: [SLAM mapping and updated obstacle room](SLAM.md)** — pull/update instructions,
WASD mapping and manual map saving.

- **Windows/WSL simulation:** follow [WSL_SETUP.md](WSL_SETUP.md).
- **Pi + ESP32:** follow [HARDWARE.md](HARDWARE.md).
- Default `ros2 launch my_bot bringup.launch.py` selects Gazebo.
- Explicit `mode:=hardware serial_device:=/dev/serial/by-id/YOUR_ESP32` selects real control.

The C++ hardware plugin is included but disabled by default. Offline tests pass;
the builder has now demonstrated initial WSL simulation and laser visualization.
See [initial simulation evidence](docs/results/2026-09-07-initial-simulation.md).
Physical mapping and autonomous path planning are shown in the [project demo](../../../README.md#demo).

# Mapping robot description (ROS 2 Jazzy)

Preliminary URDF/Xacro, RViz preview, and estimated Gazebo Harmonic simulation, adapted from Josh Newans'
[my_bot template](https://github.com/joshnewans/my_bot) under Apache-2.0.
Simulation uses ros2_control to drive simulated wheels and publish wheel odometry.
The default simulation does not open an ESP32 connection or run SLAM/Nav2.
The separate `slam_sim.launch.py` starts SLAM; the opt-in hardware plugin is implemented
and is used in the physical demonstration. Do not mistake GUI joint positions for encoder feedback.

## Dimensions and frames

All geometry is in `description/dimensions.xacro`, in metres.

| Input | Value | Evidence |
|---|---:|---|
| Wheel radius | 0.040 | Builder-reported |
| Wheel center separation | 0.205 | Builder confirmed after motor relocation |
| Outside tire width | 0.215 | Builder-reported |
| Individual tire width | 0.010 | Inferred assuming identical tires |
| Axle to front / rear | 0.180 / 0.080 | Builder-approved; total 0.260 |
| Chassis underside clearance | 0.040 | Builder-authorized assumption |
| Plate thickness | 0.005 | Visual approximation |
| Caster radius | 0.020 | Visual approximation; not measured |

`base_link` is on the ground below the drive-axle midpoint. +X points toward
the front caster, +Y left, +Z up. Both wheel joints rotate about +Y; positive
rotation represents forward rolling. Wheel centers sit 0.040 m above ground.
The chassis is a thin rectangular approximation of the whole envelope, including
the front extension, not an exact outline of the circular plate in the photos.
The caster is a fixed sphere placeholder, not a swivel mechanism model.

For Nav2, the provisional rectangular footprint relative to base_link
is `[[0.18, 0.1075], [0.18, -0.1075], [-0.08, -0.1075], [-0.08, 0.1075]]`.
Recheck wires, final payload and caster sweep before navigating. URDF collision
geometry alone does not configure Nav2's footprint.

LiDAR is enabled with a builder-authorized provisional mount: x=0, y=0,
z=0.10 m, yaw=0 (level, facing forward). "6 cm above the wheels" is interpreted
as 6 cm above the axle centers, which are 4 cm above the floor. These are
assumptions, not measurements. The blue LiDAR cylinder is a visual placeholder
(radius 3.5 cm, height 2.5 cm), not measured sensor geometry. Laser x/y are measured from the axle
midpoint, z from the floor to the scan plane, yaw in radians about +Z. The launch
requires positive z when enabling LiDAR. Its driver frame must match `laser`.
No IMU is modeled. Estimated inertias and mass distribution are provided for
simulation only; they do not establish real physical behavior.

## Build and preview on Ubuntu 24.04 / ROS 2 Jazzy

Clone the consolidated repository as described in [WSL_SETUP.md](WSL_SETUP.md).
The package lives at `~/autonomous-mapping-robot/ros_ws/src/my_bot`.

```bash
source /opt/ros/jazzy/setup.bash
cd ~/autonomous-mapping-robot/ros_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot
source install/setup.bash
ros2 launch my_bot display.launch.py
```

RViz and the joint slider window require a graphical desktop, not plain SSH alone.
Blue marks the front support. Preview uses synthetic joint states; never run the
GUI publisher alongside real hardware feedback.

For eventual hardware use, run `ros2 launch my_bot rsp.launch.py` and supply
real `/joint_states` from ros2_control. Confirm or override the provisional LiDAR mount before actual mapping
using the `include_lidar`, `laser_x`, `laser_y`, `laser_z`, and `laser_yaw` arguments.
The configured diff_drive_controller owns `odom -> base_link`; SLAM owns `map -> odom`.
Neither transform is faked by this package.

`description/robot.urdf` is a generated snapshot including the provisional LiDAR for generic URDF viewers.
After changing dimensions, regenerate it with:

```bash
cd ~/autonomous-mapping-robot/ros_ws/src/my_bot
xacro description/robot.urdf.xacro -o description/robot.urdf
```

## Verification status

See [VALIDATION.md](VALIDATION.md) and [PLAN.md](PLAN.md). Offline checks are recorded,
and the builder demonstrated initial WSL driving and laser display on September 7, 2026.
Revision-pinned Jazzy build/test evidence, repeatable startup, SLAM export, and physical
validation remain pending. This Mac cannot execute ROS/Gazebo checks.
