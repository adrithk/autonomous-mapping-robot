# Codex project instructions

This repository develops a differential-drive robot from ESP32 motor bring-up toward ROS 2 mapping and navigation. Repository evidence, not chat history or intent alone, defines project state.

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
- Treat the split above as intended architecture; only the ESP32 open-loop motor command sketch exists today.
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
- Distinguish compile success, automated test success, bench validation, and integrated robot validation.
- Never say hardware-dependent behavior works without a dated result under `results/` containing the setup, measurements, and outcome.
- Code presence is not acceptance evidence. Keep uncertain values marked `TBD` and planned components explicitly labeled.
- Review safety behavior separately; a normal stop command is not automatically an emergency stop.

## Keep project state current

After meaningful work, update the active plan. If an interface changes, update `docs/interfaces.md`; if ownership changes, update `ARCHITECTURE.md`; if acceptance evidence changes, update `ROADMAP.md`; if physical testing occurs, add a result under `results/`. Move a finished plan to `docs/plans/completed/` only after its acceptance criteria are met.

Use this loop: **DEFINE → SPEC → PLAN → IMPLEMENT → AUTOMATED VERIFY → REVIEW → HARDWARE TEST → RECORD RESULTS → UPDATE DOCS/PLAN → COMMIT → NEXT TASK**.

