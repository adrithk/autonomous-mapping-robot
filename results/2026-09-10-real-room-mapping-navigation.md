# Real-room teleoperated SLAM and saved-map Nav2 demonstration

**Date:** September 10, 2026 (media supplied and reviewed).

**Operator:** Adrith, user-reported physical operation.

**Git commit:** Running Pi/ESP32 revisions were not captured; the documentation commit does not identify the tested binaries.

**Test level:** Integrated physical demonstration, reviewed retrospectively.

**Hardware revision:** Assembled differential-drive prototype; exact CAD/electronics revisions not recorded.

**Configuration:** Raspberry Pi 5, Ubuntu 24.04 ARM64 / ROS 2 Jazzy, ESP32 serial wheel control, mounted RPLIDAR A1M8, SLAM Toolbox, Nav2 and RViz. Physical dimensions were reported to match simulation; independent measurement was not supplied.

## Goal and acceptance criteria

Document initial manual mapping followed by navigation using the saved map.
There was no revision-pinned acceptance protocol or instrumented trial series.
These artifacts document operation; they do not establish quantitative accuracy or reliability.

## Safety setup and environment

A furnished indoor office with hard flooring. The physical photograph and video
show a trailing power cable: this is a tethered demonstration, not an untethered
power-system test. Independent emergency-stop, watchdog, disconnect and power
measurements were not recorded in these assets.

## Procedure reported by the operator

1. Bring up the Pi/ESP32 hardware interface, wheel odometry and robot transforms.
2. Run the A1M8 driver over GPIO UART (`/dev/ttyAMA0`, 115200 baud).
3. Drive using keyboard teleoperation while SLAM Toolbox builds the room map.
4. Save the map with Nav2's map saver.
5. Load the saved map with map server and AMCL, set an initial pose in RViz, and
   use Nav2 for navigation to selected destinations. This mode uses localization
   against the existing map instead of starting a fresh SLAM map.

## Measurements and observations

- The supplied photos show the physical robot in the room and an RViz occupancy
  map with room boundaries, robot representation and laser returns.
- Earlier terminal evidence in the same session shows `/scan` at approximately
  **6.707 Hz**. This is a topic-rate observation, not a LiDAR accuracy test.
- Map-saver output reports **101 × 105 cells at 0.05 m/cell**, saved successfully
  to `/home/adrithk/maps/room_20260910_130718.yaml` and `.pgm`. Grid dimensions are
  not measured room dimensions or a coverage percentage. Those files have not
  been supplied to this repository.
- `IMG_7716.mov` (49.41 seconds) shows the physical robot changing position and
  heading in the room; the power cable remains visible.
- `IMG_8248.mov` (50.67 seconds) shows RViz with a room map, laser returns and a
  robot representation changing position. The clips provide physical and display
  perspectives; no frame-accurate synchronization is claimed.
- The operator identifies the recordings as Nav2 operation. Video alone does
  not expose action results, command ownership, planner settings or arrival error.

## Result and limitations

**Initial demonstration recorded.** The operator reports successful teleoperated
mapping and Nav2 navigation. The media visually supports room-map display and
physical movement. This is autonomous path planning and navigation: the operator
selects the destination, while Nav2 plans and executes movement.

The clips do not establish complete-room coverage, a repeated success rate or
measured odometry accuracy. Earlier startup/teleop issues in the session are not
claimed resolved by a measured regression test. Physical fault handling was not
measured in these recordings.

## Artifacts and processing

- [Robot during teleoperated mapping](../media/real-room/teleoperation-robot.jpg)
- [Physical-room SLAM map in RViz](../media/real-room/teleoperation-slam-map.jpg)
- [Physical Nav2 recording](../media/real-room/nav2-robot.mp4), from `IMG_7716.mov`
- [RViz navigation recording](../media/real-room/nav2-rviz.mp4), from `IMG_8248.mov`

Photographs are copied unchanged. Videos retain full duration and playback speed
as portrait H.264 MP4 copies. The physical recording's HDR video is converted to
SDR and its standard audio track retained as AAC; the RViz recording has no audio
track. The 4K RViz source is reduced to 720 pixels wide. Container metadata and
auxiliary phone data tracks are omitted. Poster images are extracted video frames.
Original MOV files are retained outside Git and unchanged.
