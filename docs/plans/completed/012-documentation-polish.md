# Documentation polish — September 10, 2026

## Scope

Polish the existing portfolio presentation: lead with the physical demonstration,
clarify custom engineering contributions, consolidate operating instructions, and
remove duplicated setup walkthroughs, empty placeholders and template boilerplate.
Synchronize the standalone `my_bot` repository and commit/push both repositories
as subsequently requested. Preserve source behavior, existing working changes, licenses, CAD/media, technical
decisions and dated evidence. Recruiter and robotics hiring-manager reviews guide
the edits. Historical plans remain records rather than current user guides.

## Acceptance

- README retains the demonstrated teleoperated mapping / saved-map Nav2 scope.
- Build, simulation, hardware, interface and verification instructions remain reachable.
- Removed documents leave no broken local links or CMake installation references.
- Current status agrees with dated evidence; no performance claims are invented.
- Inspect the final diff and verify existing code/configuration work is preserved.

## Completed changes

- Led the README with the physical demo, condensed repeated explanations and kept
  the distinction between teleoperated mapping and operator-selected Nav2 goals.
- Consolidated simulation/SLAM/navigation instructions; removed WSL walkthroughs,
  duplicate presentation pages, empty map/electronics placeholders, generic
  PlatformIO documentation and two unreferenced simulation placeholders.
- Corrected stale Pi/LiDAR/physical-operation status and reconnect wording. Kept
  unmeasured calibration and fault-response behavior explicit.
- Preserved technical decisions, active engineering plans, dated evidence, CAD,
  licenses and all pre-existing code/configuration changes. The removed WSL
  guide's pending latched-teleop instructions remain covered by HARDWARE.md.
- Updated CMake's installed-document list. No runtime behavior changed in this
  documentation pass. User-requested publication also includes existing latched
  teleop, the one-revolution helper and the existing ros_serial default selection.
- Synchronized the standalone `my_bot` package, including newer navigation,
  exploration source/history, configuration and teleop changes. Adapted external
  documentation links for that repository; runtime files match byte-for-byte.
- Two independent recruiter/engineering reviews completed; final material findings
  were resolved without adding unsupported performance claims.

## Verification — September 10, 2026

Environment: macOS, existing PlatformIO installation, clang++, Python environment
with Xacro, PyYAML, NumPy and SciPy. No ROS Jazzy/colcon or attached robot.

- `pio run -e keyboard -e ros_serial`: both builds passed.
- Native C++11 encoder, controller and protocol tests with warnings as errors:
  all passed.
- Native C++17 serial transport/fault tests and firmware-conformance harness:
  passed.
- `python -m unittest discover -s ros_ws/src/my_bot/test -p 'test_*.py' -v`:
  44 discovered, 32 passed, 12 ROS-dependent skips. Same outcome in standalone
  `my_bot` using `-s test`.
- Seven offline one-revolution target/guard checks passed; no physical test implied.
- Local document links/anchors, shell-block syntax, CMake document installation
  references and mirrored runtime-file equality checked.
- `git diff --check`: passed in both repositories.

ROS build/plugin loading, Gazebo runtime and physical verification were not run.
These remain separate from this documentation and repository-sync acceptance.

## README follow-up — September 10, 2026

User requested more depth on SLAM and Nav2 while retaining the polished layout.
Expanded the existing system section to explain scan matching, pose graphs, loop
closure, occupancy grids, AMCL, global/local planning and command execution.
Checked algorithm descriptions against upstream SLAM Toolbox/Nav2 documentation
and project settings against slam.yaml, nav2.yaml and navigation.launch.py.
Simulation-specific settings remain clearly scoped; no new physical acceptance
or custom-algorithm claims. Documentation links/anchors and diff whitespace
checks passed. No executable changes or new hardware results; prior build/test
results are unchanged.
