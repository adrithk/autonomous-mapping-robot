# Autonomous closed-room exploration — September 9, 2026

Accepted: simulation-first frontier selection over live SLAM, safe known-space
viewpoints checked by Nav2, one active goal, bounded failure handling, truthful
completion/partial status, stationary confirmation and automatic map saving.
Keep firmware/manual launches unchanged. Implement an independent geometry/policy
core and a ROS adapter; expose start/stop/retry-save services and RViz markers.

Validation: geometry and mission-policy tests, mocked action failures, ROS-specific
adapter tests where Jazzy is available, build/test plus repeated runtime missions
in the original and an occluded world. Record unavailable target validation as
pending, never substitute offline tests for navigation/physical acceptance.

Implementation and results will be recorded below. This plan stays active until
runtime acceptance (collision-free autonomous goals, stop, saved map reload and
honest unreachable-area handling) is met.

## Implementation

Added pure NumPy/SciPy grid/frontier geometry, known-space footprint clearance,
multiple viewpoints, local occupancy-change-aware retries and completion/action
lease guards. ROS adapter uses standard lifecycle/action/GetCostmap/SaveMap APIs,
handles cancellation while goal acceptance is pending, checks health continuously,
distinguishes partial/fault/save failure, and verifies stationary feedback and
saved files. Stop-confirmation failure exits the explorer and shuts its launch
stack down through OnProcessExit. Save failure alone keeps SLAM alive.

Added explore_sim launch, separate RViz view/configuration, alternate occluded
world, CMake Python installation/dependencies and unit/ROS-adapter tests. Forwarded
world selection through existing wrappers without changing their default worlds.
Updated architecture/roadmap/interfaces/testing and WSL Option C. Physical speed,
firmware, manual launches and navigation obstacle checks remain unchanged.

## Verification — September 9

30 offline tests passed including deterministic synthetic occluded-view progress.
12 ROS-dependent tests (10 new adapter checks and 2 existing launch checks) cannot
run on this Mac and are skipped. Python/XML/Bash syntax and diff checks passed.
On a 200x200 synthetic occupancy grid, 50 repeated selection calls averaged about
1.96 ms on this Mac; this is not a Pi or navigation performance measurement.

Attempted colcon build: command not found. No ROS/Gazebo or configured SSH PC
connection is available here, so Jazzy build/test, repeated two-world missions,
collision-free execution, actual map save/reload and physical testing remain
pending. Exact target commands and acceptance checks are in WSL Option C.
The plan remains active; source implementation is not full mission acceptance.

Upstream Jazzy interfaces verified: ComputePathToPose, NavigateToPose, FollowPath,
SaveMap and Costmap2DPublisher/GetCostmap, plus MapSaver's service naming. In
particular FollowPath uses 100-series error codes in Jazzy; TF errors are faults,
not excluded candidates. Only documented spatial/progress errors are retried as
viewpoint failures. Existing explore_lite was inspected; all-blacklisted completion
is deliberately not used as evidence of full coverage in this mission.
