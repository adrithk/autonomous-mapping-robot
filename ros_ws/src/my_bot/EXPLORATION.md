# Autonomous closed-room exploration (simulation first)

The explorer chooses goals; Nav2 plans/drives and avoids obstacles; SLAM builds a
fresh map. Physical execution is not validated. No firmware changes or automatic
return-to-start/docking are included. Keep doors closed: this version has no drawn
geofence and may explore through any open doorway.

## Launch and controls

Install dependencies/build with the root docs/WSL_COPY_PASTE.md exploration option.
Stop every previous navigation/simulation/teleop launch before running:

```bash
ros2 launch my_bot explore_sim.launch.py
```

This launches the existing simulated robot, SLAM, Nav2, a lifecycle map saver,
exploration manager and an exploration-specific RViz view. Green spheres are
candidate viewpoints; orange is the selected goal; text reports mission state.
The click-to-go toolbar is intentionally absent to avoid goal ownership conflicts.
Do not run WASD or send RViz goals while exploring. Existing manual launches remain.

```bash
ros2 topic echo /exploration/status
ros2 service call /exploration/stop std_srvs/srv/Trigger '{}'
ros2 service call /exploration/start std_srvs/srv/Trigger '{}'
ros2 service call /exploration/retry_save std_srvs/srv/Trigger '{}'
```

Stop returns acknowledgement of the request; wait for STOPPED status to establish
cancelled navigation and fresh stationary odometry. A pending action keeps its
lease until Nav2 supplies a terminal result. If stopping cannot be confirmed in
15 seconds, the explorer exits and its launch shuts down the stack; this is not a
physical emergency stop. Ctrl+C shuts down the entire simulation. Start reuses the
current map; relaunch the simulation for a fresh map. Retry-save is available only
after a save has failed and its outstanding request has resolved.

Options: `rviz:=false`, `autostart:=false`, `output_dir:=/absolute/directory`, and
`world:=/absolute/path/to/world.sdf`. The output directory belongs to the ROS host;
explorer and map saver must share its filesystem.

## How selection works

The independent Python core detects free cells adjacent to unknown cells, groups
frontiers, and drops clusters shorter than 0.15 m. It generates viewpoints within
0.8 m, on known free space with a known-free sightline to the frontier. Occupancy
clearance includes the robot's conservative 0.22 m padded circle plus grid-cell
boundary allowance. Raw Nav2 costs reject inscribed/lethal/unknown candidates.
Several anchors per cluster avoid relying on an obstructed centroid. Larger
frontiers and shorter straight-line travel receive higher priority; Nav2 then
checks actual reachability using ComputePathToPose. No second path planner is
implemented. A returned fallback endpoint also has to satisfy clearance.

The ROS adapter evaluates at most once per second, keeps one goal active, and
lets Nav2 perform its existing replanning/recoveries. After arrival it waits for
new map data. A failed or unproductive viewpoint is retried after 30 seconds;
a second failure at unchanged local map information excludes it until that local
map changes. The cooldown does not by itself count as mission completion.
Unknown/TF/server errors are faults, not unreachable frontiers.

A full current global costmap is requested from the standard GetCostmap service
only during readiness/selection/settling. This avoids assembling a potentially
incomplete map from late-subscribed incremental updates. Geometry work uses
NumPy/SciPy. Native plugin/firmware timings are unaffected.

## Completion and saving

The manager requires active SLAM/Nav2/map-saver lifecycle nodes, fresh scan/map/
odometry and valid map/base/laser TF. It monitors time jumps and uses steady-time
watchdogs so pausing /clock cannot freeze stop handling. Sensor freshness allows
5 seconds and map freshness 10 seconds; these mission-level limits do not replace
Nav2 collision-monitor expiry or the motor command watchdog. A long Gazebo pause
can fault the mission; resume by relaunching, not by treating the pause as coverage.

With no eligible goal, it requires at least three new map messages spanning five
seconds, then cancels motion and requires new stationary odometry for one second.

- COMPLETE: no meaningful frontiers remain in the current map.
- PARTIAL: meaningful frontiers remain but all available viewpoints are exhausted,
  unsafe or unreachable. This is never presented as full coverage.
- STOPPED / FAULTED: user stop or unhealthy system; no automatic success/save claim.
- SAVE_FAILED: map-saving service/filesystem failure; map and SLAM stay running.

Each completed/partial mission writes a unique directory containing a map YAML,
PGM image and mission.json under ~/autonomous-mapping-robot/ros_ws/maps by default.
The status message includes the YAML path. Save success is reported only after the
service succeeds, both files exist/nonempty, and the summary is written. Existing
maps are not overwritten. Saving is not proof of map accuracy: unknown space
behind walls/objects and clusters below the noise threshold may remain.

## Verification and limits

Offline tests cover clearance, transforms between grid/world coordinates, map
resizing, candidate ordering, exclusions, completion windows and action leases.
A synthetic ray fixture checks that successive viewpoints reveal space behind a
partition; it is not Gazebo, Nav2, localization or dynamics validation. ROS-only
adapter tests use fake action results for rejection, delayed acceptance/cancel,
stale callbacks, missing sensors and map-save failures; they require Jazzy.

Target acceptance remains mandatory: run both worlds repeatedly; observe multiple
autonomous goals without collisions; confirm stop/cancel, unreachable outcomes,
and map reload. Record world, Git revision, ROS test results, logs, duration and
outcome. A Pi run additionally requires physical LiDAR/odometry/TF validation.

Reference interfaces checked against Jazzy: nav2_msgs ComputePathToPose,
NavigateToPose, FollowPath, GetCostmap, SaveMap; nav2_map_server MapSaver and
nav2_costmap_2d Costmap2DPublisher. Existing explore_lite was inspected; its default
all-blacklisted completion behavior does not provide this mission's distinction
between partial and complete, so the mission policy is explicit here.
