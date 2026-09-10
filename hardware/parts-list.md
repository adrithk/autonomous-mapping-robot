# Hardware inventory

Updated September 10, 2026. The assembled prototype is shown in the
[physical demonstration](../results/2026-09-10-real-room-mapping-navigation.md).
Component identities and dimensions below are builder-reported unless noted;
initial operation does not establish electrical ratings or calibrated accuracy.

## Components

| Component | Role and recorded status |
|---|---|
| Raspberry Pi 5, 8 GB | ROS 2 Jazzy on Ubuntu 24.04 ARM64; used in physical mapping/navigation. Purchased as a CanaKit 128 GB kit; storage model remains unrecorded. |
| ESP32 development board | Encoder sampling and wheel-speed control; PlatformIO target `esp32dev`. Exact board variant is TBD. |
| Two encoder gearmotors | Reported 12 V, 131:1, 83 RPM, 45 kg·cm; exact model and rated/stall currents are TBD. Both directions have operated. |
| Two BTS7960 driver modules | One per motor; used in recorded motion and tracking tests. Exact board revision, continuous-current and thermal limits are unverified. |
| Four-channel level shifter | Reported BSS138-style module on encoder signals. Counts observed; voltage levels and edge quality require measurement. |
| RPLIDAR A1M8 | Mounted 360-degree scanner; physical demonstration used GPIO UART at 115200 baud and observed `/scan` near 6.7 Hz. |
| Drive wheels and caster | Reported Pololu wheels on a custom printed chassis; exact wheel/hub and caster models are TBD. |
| Printed chassis and mounts | [STEP assembly and STL parts](cad/README.md) include chassis, caster mount, LiDAR holder and pillars. Printed revision/material are unrecorded. |
| Tattu LiPo battery | Reported on hand; model, cell count, capacity and compatibility remain TBD. The September 10 demonstration uses tethered power. |

The former Cytron MDD10A driver was reported damaged and is retired.

## Preliminary geometry and calibration

| Parameter | Value | Basis |
|---|---:|---|
| Wheel radius | 0.040 m | Builder-reported; loaded radius uncalibrated |
| Wheel-center separation | 0.205 m | Updated after motor relocation; replaces the earlier 0.233 m value |
| Outside tire width | 0.215 m | Builder-reported |
| Axle to front / rear | 0.180 / 0.080 m | Builder-reported |
| Individual tire width | 0.010 m | Inferred for identical tires |
| Chassis underside clearance | 0.040 m | Modeling assumption |
| LiDAR scan plane | x=0, y=0, z=0.10 m, yaw=0 | Preliminary mount relative to floor-level axle midpoint |
| Encoder resolution | 4185 counts/revolution per wheel | Approximate 41850 counts over ten rotations; formal calibration pending |
| Robot mass | 1.6 kg | Simulation assumption; final assembly not weighed |

The front faces the caster. Geometry lives in the ROS package's
`description/dimensions.xacro`; firmware and host conversion constants must agree.
Simulation mass, inertia and contact properties are estimates, not measured specifications.

## Measurements still needed

- Final loaded dimensions, LiDAR offsets and repeatable encoder calibration.
- Battery and regulator ratings, motor stall current, fuse sizing and power distribution.
- Wiring diagram with GPIOs, signal levels, common grounds and connector ratings.
- Driver enable polarity, braking/coasting behavior and measured independent power removal.

[Interface and pin assignments](../docs/interfaces.md) · [Physical test procedures](../docs/testing.md) · [Dated results](../results/README.md)
