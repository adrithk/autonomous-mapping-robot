# Nav2 click-to-go simulation

2026-09-08. Implement a separate simulation launch combining existing SLAM/Gazebo
with standard Nav2 planner, controller, behaviors, navigator, velocity smoother
and collision monitor. Configure conservative circular collision bounds enclosing
the offset robot footprint, known-space planning, stamped commands and sim time.
Do not implement frontier exploration, AMCL, physical navigation or new firmware.
Existing WASD-only and SLAM-only launches remain available.

Acceptance: offline configuration/launch checks; Jazzy build/test and runtime
startup; goal reached around an obstacle; canceled goal stops motion; blocked goal
fails without collision; SLAM updates while moving; repeat on a fresh launch.
Mac offline checks cannot establish Linux/Gazebo/physical acceptance.
Update the copy/paste WSL guide with dependencies, goals, cancellation and logs;
commit and push the implementation and explicitly report runtime limits.

## Implementation and offline verification

Added navigation.launch.py, nav_sim.launch.py, nav2.yaml and navigation.rviz;
registered dependencies, installation and navigation tests. Updated WSL workflow
and NAVIGATION.md with goals, cancellation, diagnostics and manual-mode switching.
Fourteen offline checks passed (3 navigation, 8 model, 3 teleop); one ROS-dependent
launch/install/clock test skipped on macOS. Bash documentation syntax and diff
whitespace checks passed. No firmware change. ROS/colcon/Gazebo is unavailable on
this Mac, so target build, new hardware-plugin test and runtime acceptance remain
pending on the PC. Do not mark this plan complete until the runtime criteria pass.

## RViz launch bug correction — September 8

User reported Terminal 1 never opened RViz; manual old SLAM view opened without
Nav2 controls. Found rviz=false launch-argument leakage from unscoped child includes
in both nav_sim and slam_sim. Isolated overrides with scoped GroupAction, retained
parent rviz option and enabled process output. Added rviz_navigation.launch.py for
opening the correct navigation UI independently and updated the WSL workflow.

Fifteen offline tests passed; two ROS-only tests skipped. The new static regression
was also run against the prior committed nav_sim launch and correctly failed.
The ROS-only regression evaluates both parents with rviz=true/false using actual
launch scoping, replacing external backends and never starting processes. Target
ROS tests and actual WSL window visibility remain pending. No firmware changes.

Source semantics checked in ros2/launch Jazzy actions/include_launch_description.py
and actions/group_action.py: include arguments become SetLaunchConfiguration;
scoped groups push/pop configurations. This is a launch defect, separate from the
previous shader warning investigation.

## Map-transform abort mitigation — September 8

Reviewed launch clock propagation, TF frame ownership, DWB configuration, SLAM
TF publication and command-chain settings. No frame-name mismatch found in the
checked configuration. Upstream Jazzy DWB rejects an extrapolated lookup when the
latest transform exceeds transform_tolerance; ControllerTFError aborts immediately
rather than using failure_tolerance. SLAM publishes scan-stamped map->odom TF plus
transform_timeout. Thus increasing goal patience would not address this error.

Raised SLAM's TF margin and DWB/global-costmap/behavior/navigator transform
allowances to 0.5 seconds. This is a bounded timing mitigation, not a confirmed
root-cause fix: the PC's failing transform timestamps are unavailable. Kept local
odometry and collision-monitor allowances, sensor expiry, velocity limits,
footprint and watchdogs unchanged. Did not restamp old observations as current.
Updated WSL diagnostic commands to capture individual TF links, odometry stamps,
clock publishers, node clocks and effective timing parameters; added launch-log
capture for the preceding upstream error details.

Verification: 15 offline tests passed, 2 ROS-dependent tests skipped; diff check
passed. ROS/Gazebo/colcon is unavailable on this Mac. Goal completion and physical
Pi acceptance remain unverified; repeat the runtime acceptance tests on the PC.

References checked:
- https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_dwb_controller/nav_2d_utils/src/tf_help.cpp
- https://github.com/ros-navigation/navigation2/blob/jazzy/nav2_controller/src/controller_server.cpp
- https://github.com/SteveMacenski/slam_toolbox/blob/jazzy/src/slam_toolbox_common.cpp

## Follow-up: larger simulation TF allowance

User reports continued difficulty at 0.5 s and requested substantially more
buffer. Increased SLAM transform_timeout and DWB/global-costmap/behavior/navigator
transform_tolerance to 1.5 s. This permits older map corrections and is provisional
simulation tuning, not verified physical-robot tuning. It does not repair missing
TF or mixed clocks. The scan rate remains 10 Hz: increasing it adds processing
load and does not establish that observations will arrive sooner on an overloaded
WSL host. Local-costmap and collision-monitor transform tolerances remain 0.2 s;
sensor expiry and motor watchdogs remain unchanged.

Offline verification: 15 tests passed, 2 ROS-only tests skipped. Runtime goal
completion still needs PC verification; prior 0.5 s mitigation was insufficient
according to the user. If the same abort persists, inspect the preceding TF error
and timestamps from nav2-launch.log before increasing allowances again.
