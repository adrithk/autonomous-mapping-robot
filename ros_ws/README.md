# ROS workspace

The complete `my_bot` package is at [src/my_bot](src/my_bot/README.md).
Run `colcon build --packages-select my_bot` and `colcon test --packages-select my_bot`
from this directory in ROS 2 Jazzy, then `colcon test-result --verbose`.
[Full setup](src/my_bot/WSL_SETUP.md).

## Import provenance

Copied September 7, 2026 from `https://github.com/adrithk/my_bot`, commit
`10c2beb58b34006a5841c2e3cba88462cb117117`. Every Git-tracked file was retained,
including the original simulation photograph, tests, planning records and
[Apache-2.0 license](src/my_bot/LICENSE.md). Code, configuration and assets are
unchanged; documentation paths/status were updated for this repository.
The source repository was not deleted or rewritten. There is no nested Git repository.

The original robot-description template is credited to Josh Newans in the package
README. The imported license is scoped to that package; a license for the original
firmware and other project materials remains a maintainer decision (TBD).

The final import includes the completed parallel audit’s plugin-loading test and
audit record. That ROS-dependent test awaits Ubuntu execution.
