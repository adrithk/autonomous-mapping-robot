# Verification on 2026-09-07

Environment: macOS, clang++ C++17, local Python with Xacro 2.1.1/PyYAML.

Passed:
- Six test_model.py tests: frames/geometry/inertia, simulated sensor/bridge,
  real/default/sim model isolation, plugin declaration, clocks and speed limits,
  Python/XML/YAML syntax.
- Native serial transport test with -Wall -Wextra -Werror and pseudo-terminal ESP32:
  CRC and numeric bounds, partial telemetry, initial stop ACK, ACK sequence wrap,
  commands, explicit stop, retained-sequence reconnect, CRC corruption, dropped
  telemetry, stalled ACK, reboot, new status fault, host stalls and startup timeout.
- Firmware conformance harness against current autonomous-mapping-robot header:
  actual ESP32 parser accepts host C/X frames, host parser accepts firmware S frames.
- git diff --check.

To repeat native tests without ROS from this package directory:

```bash
c++ -std=c++17 -Wall -Wextra -Werror -pthread -Iinclude \
  src/serial_transport.cpp test/serial_transport_test.cpp -lutil -o /tmp/serial-test
/tmp/serial-test
python3 test/test_model.py
```

Protocol conformance against the firmware in this consolidated repository:

```bash
c++ -std=c++17 -Wall -Wextra -Werror -pthread -Iinclude \
  -I../../../include src/serial_transport.cpp \
  test/firmware_conformance.cpp -o /tmp/conformance-test
/tmp/conformance-test
```

Not run: ROS-dependent esp32_system.cpp compilation, pluginlib loading,
colcon build/test, Gazebo physics/rendering, WSL graphics, real USB/Pi or robot tests.
No ROS installation, Linux runtime or attached Pi was available. WSL_SETUP.md has
commands for those remaining checks; physical tests are listed in HARDWARE.md.

## User-observed simulation result — 2026-09-07

Recorded [initial simulation implementation](docs/results/2026-09-07-initial-simulation.md) with the builder's original photo. Gazebo launch, WASD driving,
10 Hz simulated scans and RViz display were reported working. The screenshot
confirms visible scan returns with RViz status Ok. This supersedes earlier pending
statements for the initial simulation smoke test only; physical validation,
repeatable startup, odometry accuracy and SLAM remain pending.
