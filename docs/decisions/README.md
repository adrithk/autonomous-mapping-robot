# Architecture decision records

Use a decision record when a durable technical choice affects component ownership, safety, interfaces, dependencies, or multiple future tasks. Do not create records merely to fill this directory.

Current records:

- [001: Separate low-level control from ROS autonomy](001-low-level-high-level-responsibility-split.md)
- [002: Use ros2_control on the Pi and a serial-controlled ESP32](002-ros-control-serial-boundary.md)
- [003: Keep keyboard and ROS-serial firmware as separate selectable builds](003-selectable-firmware-entry-points.md)

Name records `NNN-short-title.md` using the next available number. Include:

```md
# NNN: Decision title

**Status:** Proposed | Accepted | Superseded
**Date:** YYYY-MM-DD

## Context
## Decision
## Alternatives considered
## Reasoning
## Consequences
```

If history does not record which alternatives were considered, say so rather than inventing them. Link superseding and superseded records in both files.
