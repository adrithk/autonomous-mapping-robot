# Exploration implementation: offline evidence only

Setup: macOS development workspace; temporary Python environment with xacro,
PyYAML, NumPy 2.5.3 and SciPy 1.18.1. No physical robot attached. No ROS/Jazzy,
colcon or Gazebo available on this host.

Command:

```bash
/tmp/my-bot-urdf-venv/bin/python -m unittest discover -s ros_ws/src/my_bot/test -p 'test_*.py'
```

Outcome: 30 passed; 12 skipped because ROS is unavailable. The ray-visibility
fixture required multiple safe viewpoints and revealed over 500 cells behind its
partition. This fixture contains no ROS actions, physics or SLAM and must not be
reported as a successful robot simulation mission. ROS adapter failure tests are
present but require target execution. Source/launch Python, XML and 38 Bash blocks
parsed successfully; git diff whitespace check passed.

Informational microcheck: 50 frontier searches of a 200x200 synthetic grid averaged
1.96 ms/search on this Mac, returning 9 candidates. No Pi speedup is established.

`colcon build --packages-select my_bot` could not run (command not found).
Still required: Jazzy package build/tests; two fresh runs of both Gazebo worlds;
no collisions; autonomous destination progression; stop/fault handling; truthful
PARTIAL for unreachable frontiers; real SaveMap service result and YAML/PGM reload.
See WSL_COPY_PASTE.md Option C. Physical deployment is not accepted by this result.
