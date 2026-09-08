# Final presentation checklist

The repository presentation is prepared. The following artifacts turn its TBD
slots into a reproducible finished-project showcase. Send the files and measurements
when available; they can be added directly without redesigning the documentation.

## What to supply

- [ ] One clear landscape photo of the fully assembled robot, plus wiring and sensor-mount close-ups.
- [ ] A hosted 60–120 second demo: startup, autonomous movement, live mapping, stop, saved map.
- [ ] Photo/map pairs from one or two rooms, including original YAML + occupancy images and readable previews.
- [ ] Dated results: room dimensions, mapping time, mapped area, map resolution, repeat runs/success count, and limitations.
- [ ] Final parts/BOM with exact models, cost if known, power wiring, protection and calibration measurements.
- [ ] Chassis CAD, STEP/STL exports, print settings, fasteners and assembly notes.
- [ ] Reproducible Ubuntu/ROS setup and build/test output tied to the demonstrated commit.
- [ ] Physical stop/watchdog/disconnect, odometry, LiDAR/TF and mapping acceptance records.
- [ ] Scope of personal contributions and any additional collaborators or borrowed assets requiring credit.
- [ ] Maintainer's license choice for original firmware/docs; retain the imported ROS license.

## Where everything goes

| Material | Destination |
|---|---|
| Hero photo / demo link | [media](../media/README.md), then root README |
| Room photographs and maps | [maps](../maps/README.md) |
| Measurements and test procedure | [results](../results/README.md) |
| Models and assembly | [hardware/cad](../hardware/cad/README.md) |
| Wiring and power diagram | [hardware/electronics](../hardware/electronics/README.md) |
| Final inventory and calibration | [parts list](../hardware/parts-list.md) and [interfaces](interfaces.md) |

## Before calling the robot complete

Physical ROS integration, real LiDAR operation, autonomous exploration, and automatic
map saving still need implementation or validation as shown in the [roadmap](../ROADMAP.md).
Photos alone do not establish these capabilities. Each completed claim should point
to the relevant dated result; keep remaining ideas in the roadmap.

After the final repeatable run, replace the README demo placeholder and update its status with measured
outcomes, close only plans whose criteria passed, and create a release for the
exact demonstrated revision. Resume wording can then cite the measured outcome,
custom firmware/ROS integration, and linked demo without speculative numbers.
