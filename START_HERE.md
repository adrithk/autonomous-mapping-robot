# Start here

## What this project is

A custom differential-drive robot at the beginning of a planned path toward ROS 2-based autonomous indoor mapping. The final behavior is to create and save a fresh map of a zone after the robot is placed there and turned on; saved-map navigation is out of scope.

## What exists now

Two mutually exclusive PlatformIO/Arduino firmware builds target the ESP32. The default `keyboard` build reads `w`, `s`, `a`, `d`, and `x`. The `ros_serial` build accepts versioned checksummed version-2 left/right rad/s commands (converted internally using preliminary 4185 counts/revolution), emits state at 20 Hz, and enforces a 250 ms command watchdog. Both use the shared 50 Hz encoder-feedback wheel controller in `src/robot_drive.cpp`. Both builds and the controller/protocol tests pass.

The build/tests prove compilation and bounded parser/controller behavior. A 2026-09-04 raised-wheel forward/reverse test showed stable tracking at +/-3000 counts/s using the preceding 400 ms ramp. A later qualitative ground observation reported very slight rightward drift, but no measured ground acceptance test exists. The current ramps and new ROS-serial firmware have not been physically tested. No Raspberry Pi ROS 2 workspace exists.

## Current work

The current bounded task is completing the Pi-side ROS connection and then performing raised-wheel validation of the ROS-ready ESP32 transport. Follow [active plan 003](docs/plans/active/003-ros-ready-esp32-transport.md).

The intended Pi/ROS sequence is specified in [docs/ros-platform-roadmap.md](docs/ros-platform-roadmap.md). The accepted boundary is a Pi-side `ros2_control` hardware plugin over USB serial; the ESP32 remains a non-ROS device that owns PID and watchdog behavior.

## Read next

1. [ARCHITECTURE.md](ARCHITECTURE.md) for real versus planned ownership and flows.
2. [ROADMAP.md](ROADMAP.md) for milestone status and acceptance gates.
3. [docs/interfaces.md](docs/interfaces.md) for the current motor/serial contract.
4. [docs/testing.md](docs/testing.md) before changing or energizing hardware.
5. [docs/ros-platform-roadmap.md](docs/ros-platform-roadmap.md) for the complete ROS implementation order.
6. [`docs/plans/active/`](docs/plans/active/) before implementation, especially plan 003 for the next task.

Codex sessions must also follow [AGENTS.md](AGENTS.md). Architectural decisions live in [`docs/decisions/`](docs/decisions/), and measured evidence belongs in [`results/`](results/).

## Build and run

From the repository root, the default command builds the keyboard firmware:

```sh
pio run
```

Build the ROS-serial firmware explicitly with `pio run -e ros_serial`.

Only after checking the board, driver, power, pin assignments, and wheel clearance:

```sh
pio run -e keyboard --target upload
pio device monitor
```

Use `w`, `s`, `a`, `d`, or `x` as documented in [docs/interfaces.md](docs/interfaces.md). Straight commands time out after 5 seconds and turns after 1 second; keep independent power removal within reach because these software stops are not an emergency stop. There are no ROS build/run commands yet.

Pi-side source update (2026-09-07): the sibling `my_bot` now includes the opt-in ESP32
SystemInterface and default-Gazebo bringup. See active plan 004 and its WSL_SETUP.md.
Only offline tests have passed; Ubuntu/ROS and physical acceptance remain pending.

2026-09-07 user evidence update: [initial simulation implementation](results/2026-09-07-initial-simulation.md)
records working WSL Gazebo/WASD and 10 Hz simulated LiDAR display, with photo.
Initial simulation smoke testing is now observed; physical and SLAM acceptance
remain pending. Exact PC revision and repeatable startup have not been recorded.
