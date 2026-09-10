# my_bot — ROS 2 robot integration

ROS 2 Jazzy package for the indoor mapping robot: a custom ESP32 hardware plugin,
differential-drive control, robot description, Gazebo simulation and SLAM/Nav2 integration.
See the [project README](../../../README.md) for physical demonstrations.
The package is also mirrored in [adrithk/my_bot](https://github.com/adrithk/my_bot);
the commands below use the consolidated repository, which includes the firmware and tools.

## Build

Requires Ubuntu 24.04, ROS 2 Jazzy, `ros-dev-tools` and an initialized `rosdep`.
Simulation also requires Gazebo Harmonic and a working graphics environment.
The package declares its ROS and Gazebo dependencies for `rosdep`.

```bash
source /opt/ros/jazzy/setup.bash
git clone https://github.com/adrithk/autonomous-mapping-robot.git
cd autonomous-mapping-robot/ros_ws
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --packages-select my_bot --symlink-install
source install/setup.bash
colcon test --packages-select my_bot
colcon test-result --verbose
```

For an existing checkout, run the dependency/build/test steps from `ros_ws`.
In each new terminal, source ROS and this workspace's `install/setup.bash`.

| Mode | Command / guide |
|---|---|
| Model preview | `ros2 launch my_bot display.launch.py` |
| Gazebo driving | `ros2 launch my_bot bringup.launch.py` |
| Simulated mapping | `ros2 launch my_bot slam_sim.launch.py` |
| Simulated navigation with live SLAM | `ros2 launch my_bot nav_sim.launch.py` |
| Pi + ESP32 | [Hardware guide](HARDWARE.md) — explicit serial device required |

Run one control mode at a time. The model preview uses synthetic joint states;
close it before simulation or hardware operation. The [simulation guide](SIMULATION.md)
covers teleoperation, map saving and navigation.

### ESP32 firmware

Install PlatformIO and build from the repository root. Select the entry point explicitly:

```bash
pio run -e keyboard
pio run -e ros_serial
```

`keyboard` provides direct serial-key control; `ros_serial` speaks the ROS wheel
protocol. Both share the controller implementation. Add `-t upload` to the chosen
build command when flashing an attached ESP32.

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


## Model snapshot

`description/robot.urdf` is a generated snapshot for generic URDF viewers.
After changing dimensions, regenerate it from the package directory:

```bash
xacro description/robot.urdf.xacro -o description/robot.urdf
```

Geometry is preliminary; simulation masses, inertias and contact properties are
estimates. [Hardware inventory](../../../hardware/parts-list.md) records their provenance.

## Verification and attribution

[Testing](../../../docs/testing.md) describes the automated checks and remaining
physical measurements. [Dated results](../../../results/README.md) include initial
simulation and physical mapping/navigation demonstrations.

Adapted from [Josh Newans’ my_bot template](https://github.com/joshnewans/my_bot)
under [Apache-2.0](LICENSE.md). Import provenance is in the [workspace README](../../README.md).
