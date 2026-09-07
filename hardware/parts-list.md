# Robot parts list

**Last updated:** 2026-09-05
**Project stage:** ROS-ready ESP32 transport bench validation

This is the source of truth for hardware believed to be on hand, still needed, or not yet selected. "On hand" means the part was reported by the builder; it does not mean its exact variant, electrical compatibility, wiring, or operation has been verified.

Add product links, exact model numbers, and measured values as they become available. Keep unknown values marked `TBD` rather than guessing.

## Reported on hand

| Qty. | Part | Reported description | Exact model / link | Details still needed | Verification state |
|---:|---|---|---|---|---|
| 2 expected | DC gearmotor with encoder | 12 V metal DC geared motor with encoder; 131:1; 83 RPM; 45 kg.cm | Possible match from earlier project chat: DFRobot FIT0185; **not confirmed** | Confirm exact model; encoder voltage; counts per wheel revolution; rated and stall current | Both motors and encoder directions have operated; exact specifications remain unverified |
| 1 | Microcontroller board | ESP32 development board | Exact board/variant and link `TBD` | Variant; input voltage limits; available GPIO; USB connector; whether it supports the intended Bluetooth mode | Firmware targets PlatformIO `esp32dev`; physical board not identified or verified |
| 1 | Battery | Tattu LiPo battery | Exact model and link `TBD` | Cell count; nominal/max voltage; capacity in mAh; discharge rating; connector; charger; measured condition | Reported on hand; compatibility not verified |
| 2 expected | Drive wheels | Pololu wheels | Exact model, diameter, width, hub type, and link `TBD` | Confirm quantity; motor-shaft fit; measured loaded radius | Reported on hand; exact wheel unknown |
| 1 | Chassis | Custom 3D-printed differential-drive chassis | CAD/print file and material `TBD` | Material; revision; dimensions; wheelbase/track width; mounting points; fasteners; center of mass | Reported built; dimensions not recorded |
| 1 | 2D LiDAR | Slamtec RPLIDAR A1M8 2D 360-degree scanner | RPLIDAR A1M8; product link `TBD` | Confirm physical model/revision, included adapter/cables, power requirements, scan specifications, ROS 2 Jazzy driver, and mounting transform | Order screenshot supplied 2026-09-05 shows delivered; operation and integration unverified |

## Reported drivetrain dimensions

**Geometry revision pending (2026-09-06):** the builder moved the motors. The
previous wheel separation and footprint below are historical and must not be used
for the new layout without confirmation. Ask the builder for updated wheel
separation, axle position relative to the chassis, and outer footprint before
configuring ROS body-velocity commands, odometry, robot description, or navigation.
Recheck LiDAR offsets against the new wheel-axis midpoint after final mounting.
Wheel radius remains provisionally 0.040 m unless the wheels changed; confirm its
loaded value during calibration. Existing ESP32 counts/s commands need no geometry
change solely because the motors moved.

Builder clarification on 2026-09-05: wheel separation is **23.3 cm (0.233 m)**
and wheel radius is **4 cm (0.040 m)**. These supersede the earlier ambiguous
11.65 cm radius report. Measurement procedure and final-payload loaded radius
remain unverified; encoder counts per wheel revolution remain `TBD` for each wheel.
Assumed robot mass: **1600 g (1.6 kg)**, per builder instruction on 2026-09-05.
This is a working assumption, not a measured final-payload mass. No weighing
reminder is requested.
Builder-reported footprint dimensions: **27 cm front-to-back, 24 cm side-to-side
(outside tire edge to outside tire edge, confirmed by builder 2026-09-06)**.
Confirm that all dimensions include protrusions/final payload
before using them as the navigation footprint. Footprint position relative to the
wheel-axis midpoint remains `TBD`.
Total robot height and LiDAR height are `TBD` until the Raspberry Pi is installed
and mounting is finalized. The builder withdrew the earlier 18 cm total height
on 2026-09-06; do not use it for configuration.

## Purchased / awaiting integration

| Qty. | Part | Reported description | Exact model / link | Details still needed | Verification state |
|---:|---|---|---|---|---|
| 2 | Motor drivers | HiLetgo BTS7960 43 A single-channel H-bridge motor-driver modules; one per drive motor | Amazon listing / board revision `TBD` | Exact board labeling; logic thresholds; cooling; real continuous-current capability; motor/battery compatibility | Connected and used for motion/PID observations; electrical and thermal limits remain unverified |
| 1 | Logic-level shifter | Four-channel bidirectional BSS138-style level-shifter module used for encoder signals | Exact listing `TBD` | Measure encoder/output voltage, confirm pull-up behavior and edge quality | Connected and encoder counts observed; electrical performance not measured |
| 1 kit | Onboard ROS computer kit | CanaKit Raspberry Pi 5 Starter Kit PRO - Turbine Black (128GB Edition), 8GB RAM | Raspberry Pi 5, 8GB RAM; CanaKit kit product link `TBD` | Confirm delivered contents, power-supply rating, cooling, connectors, and robot mounting/power budget | Ordered 2026-09-04; screenshot supplied 2026-09-05 shows “Arriving Wednesday”; not yet received or tested |
| 1, included in kit | Storage for ROS computer | 128GB edition of the CanaKit Raspberry Pi 5 kit above | Storage medium, manufacturer, and model `TBD` | Confirm actual media type/capacity and endurance; prepare Ubuntu Server 24.04 LTS 64-bit for ROS 2 Jazzy | Awaiting kit delivery; 128GB is from the listing title, not a physical inspection |

The LiDAR and Raspberry Pi kit identities and delivery statuses above come from the
builder's Amazon order screenshot supplied on 2026-09-05. Both orders were placed
2026-09-04. Listing titles establish purchased variants, not verified specifications
or included accessories; confirm those against the delivered hardware. Personal
shipping and order identifiers are intentionally omitted.

## Retired / do not use

| Qty. | Part | Reported description | Status |
|---:|---|---|---|
| 1 | Cytron MDD10A dual-channel motor driver | Former planned motor driver | Reported damaged (“fried”); do not connect or use for this build without separate diagnosis and repair |

## Not yet acquired or selected

| Qty. | Part | Purpose | Selection details to decide | Status |
|---:|---|---|---|---|
| As needed | LiDAR cables and mount | Secure RPLIDAR A1M8 installation and routing | Confirm supplied adapter/cables, any additional cable length, strain relief, and printed mount | Inventory delivered accessories before purchasing additional cables; mount remains needed |

## Power, safety, and integration items to confirm

These may already be present, but they have not been identified yet.

| Qty. | Part | Why it is needed | Required information / action |
|---:|---|---|---|
| 1 | LiPo balance charger | Charges the battery safely | Must match the battery chemistry, cell count, connector, and balance connector |
| 1 | Main fuse and holder | Protects the battery wiring from excessive current | Size only after motor stall current, driver limits, wire gauge, and expected load are known |
| 1 | Main power switch / accessible motor-power disconnect | Allows motor power to be removed without relying on software | Choose a DC-rated device for the measured maximum current; keep it reachable during tests |
| 1 | 5 V regulator for the ROS computer | Powers a future Raspberry Pi from the robot battery | Input range must include the battery's fully charged voltage; output current must meet the selected computer and USB sensor load |
| 1 | Regulated supply for ESP32 and encoder logic | Keeps logic power within limits | Exact rail arrangement is `TBD`; do not assume the encoder signals are safe for 3.3 V GPIO |
| 1 | Encoder signal conditioning | Four-channel BSS138-style logic-level shifter reported on hand; intended to protect ESP32 inputs if encoder A/B signals are 5 V | Measure both encoder outputs first; confirm the shifter's HV=5 V, LV=3.3 V, common-ground wiring, channel mapping, and signal quality before relying on it |
| 1 | Power distribution and common-ground wiring | Distributes battery and logic power predictably | Record a wiring diagram, connector types, wire gauges, grounding, and branch protection before integration |
| As needed | Connectors, wire, terminals, heat-shrink, and strain relief | Reliable motor, battery, encoder, and logic connections | Select for voltage/current and use polarized connectors where practical |
| 1 | USB data cable | Programs and monitors the ESP32 | Match the exact board connector; verify it supports data, not charging only |
| 1 | Caster, ball caster, or chassis skid | Provides the third support point for a two-wheel differential-drive base | Confirm whether this is already part of the printed chassis |
| As needed | Fasteners, standoffs, and vibration isolation | Secures electronics and sensors | Match the printed chassis and selected boards; keep wiring away from wheels |

## Optional later additions

- Physical emergency-stop hardware appropriate to the final battery and motor current.
- Motor current and battery voltage monitoring.
- Bumper/contact sensors or other short-range obstacle sensors.
- Battery fuel-gauge or low-voltage warning hardware.
- Cooling for the ROS computer if required by the selected model and enclosure.

## Checks required before powered testing

1. Record the battery cell count, fully charged voltage, capacity, discharge rating, connector, and compatible charger.
2. Confirm both motors are identical and find the motor's rated and stall current. Verify the driver, battery, connectors, wiring, and protection can handle the load.
3. Confirm the exact BTS7960 board labeling and actual ESP32-to-driver wiring, including shared ground, logic supply, enable/PWM polarity, and stop/coast/brake behavior. Do not power the reported damaged Cytron MDD10A.
4. Power the encoder from its specified supply, disconnect its A/B lines from the ESP32, and measure their high voltage. Never apply a signal above the ESP32 input limit.
5. Record wheel diameter, loaded wheel radius, and left-to-right wheel-center distance in millimetres.
6. Keep the wheels unloaded and an independent motor-power disconnect within reach during initial tests.

## Update checklist

When adding a product link, also record its manufacturer, exact part number, quantity, important electrical/mechanical specifications, and whether the value comes from a datasheet or a measurement. Physical test results belong under [`../results/`](../results/), not in this inventory.
