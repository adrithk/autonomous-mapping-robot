# Codex project instructions

This repository develops a differential-drive robot from ESP32 encoder-feedback motor control toward ROS 2 autonomous fresh-zone mapping. Repository evidence, not chat history or intent alone, defines project state.

The repository documents the current source of truth, and its requirements, plans, and technical decisions can evolve through discussion with the user. Update the relevant files when an agreed direction changes, and clarify material changes, conflicts, or uncertainties in chat as needed. Keep proposed ideas distinct from accepted decisions, implemented behavior, and verified results.

## Read before substantial work

1. Read `START_HERE.md`.
2. Read `ARCHITECTURE.md`.
3. Read `ROADMAP.md`.
4. Read relevant files under `docs/`, especially `docs/interfaces.md` and `docs/testing.md`.
5. Read the active execution plan under `docs/plans/active/`.
6. Inspect the existing implementation and Git state before changing code.

## Engineering boundaries

- Keep timing-sensitive hardware control on the microcontroller: motor outputs, encoder sampling, low-level wheel-speed control, command watchdogs, and immediate actuator-safe behavior.
- Keep compute-heavy/system-level behavior on the ROS computer: hardware bridging, robot model/TF coordination, sensor drivers, state estimation, SLAM, localization, Nav2, missions, exploration, coverage, and docking orchestration.
- The ESP32 has separate `keyboard` and `ros_serial` builds with shared encoder-feedback wheel control. The serial build compiles and has parser tests but lacks physical validation; the Pi-side ROS package now exists at `ros_ws/src/my_bot`, including the serial plugin, simulation and SLAM launch; physical ROS integration and autonomous exploration remain pending.
- Use the accepted Pi/ESP32 boundary in `docs/decisions/002-ros-control-serial-boundary.md`: ROS 2 and `ros2_control` run on the Raspberry Pi; the ESP32 receives a versioned serial wheel command and does not run micro-ROS in the first version.
- Preserve the keyboard firmware as the default build. `src/main.cpp` and `src/main_ros.cpp` are separately filtered PlatformIO entry points; never compile both Arduino `setup()`/`loop()` definitions together. See decision 003 and active plan 003.
- Prefer standard ROS 2, `ros2_control`, `robot_localization`, SLAM Toolbox, and Nav2 capabilities when they fit. Inspect available packages before creating new abstractions or duplicating framework behavior.
- Keep hardware-specific values centralized in the component that owns them. Record units, frames, rates, and protocol changes in `docs/interfaces.md`.

## Change discipline

- Work from a bounded active plan; do not implement an entire roadmap milestone at once.
- Prefer small, independently testable changes and the simplest design that meets the requirement.
- Preserve useful code and documentation. Do not reorganize speculatively.
- Follow existing style; use explicit names, fixed-width types for wire protocols, and comments for hardware intent or safety constraints rather than restating code.
- Keep unrelated edits out of the change. Inspect `git diff` and never overwrite user work.
- Record durable technical decisions under `docs/decisions/`.

## Verification and truthfulness

- For current firmware changes, run `pio run`; add and run relevant PlatformIO tests when testable logic is introduced.
- When a ROS 2 workspace exists, run the applicable package-scoped or workspace checks, normally `colcon build`, `colcon test`, and `colcon test-result --verbose`.
- `pio run` builds the default `keyboard` environment. For shared firmware changes, verify both `pio run -e keyboard` and `pio run -e ros_serial`, plus the controller and protocol tests.
- Distinguish compile success, automated test success, bench validation, and integrated robot validation.
- Never say hardware-dependent behavior works without a dated result under `results/` containing the setup, measurements, and outcome.
- Code presence is not acceptance evidence. Keep uncertain values marked `TBD` and planned components explicitly labeled.
- Review safety behavior separately; a normal stop command is not automatically an emergency stop.

## Keep project state current

After meaningful work, update the active plan. If an interface changes, update `docs/interfaces.md`; if ownership changes, update `ARCHITECTURE.md`; if acceptance evidence changes, update `ROADMAP.md`; if physical testing occurs, add a result under `results/`. Move a finished plan to `docs/plans/completed/` only after its acceptance criteria are met.

Use this loop: **DEFINE → SPEC → PLAN → IMPLEMENT → AUTOMATED VERIFY → REVIEW → HARDWARE TEST → RECORD RESULTS → UPDATE DOCS/PLAN → COMMIT → NEXT TASK**.
