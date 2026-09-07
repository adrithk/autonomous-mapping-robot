#pragma once

#include <cmath>

// Calibration belongs to the ROS-serial adapter, not the shared keyboard PID.
namespace RosWheelUnits
{
constexpr double kTwoPi = 6.28318530717958647692;
// Preliminary builder report: approximately 41850 counts over 10 wheel turns.
constexpr double kLeftCountsPerRevolution = 4185.0;
constexpr double kRightCountsPerRevolution = 4185.0;
constexpr double kMaximumCountsPerSecond = 4000.0;
constexpr double kLeftMaximumRadiansPerSecond =
    kMaximumCountsPerSecond * kTwoPi / kLeftCountsPerRevolution;
constexpr double kRightMaximumRadiansPerSecond =
    kMaximumCountsPerSecond * kTwoPi / kRightCountsPerRevolution;

inline bool convertCommand(double leftRadiansPerSecond,
                           double rightRadiansPerSecond,
                           float &leftCountsPerSecond,
                           float &rightCountsPerSecond)
{
  if (!std::isfinite(leftRadiansPerSecond) ||
      !std::isfinite(rightRadiansPerSecond) ||
      std::fabs(leftRadiansPerSecond) > kLeftMaximumRadiansPerSecond ||
      std::fabs(rightRadiansPerSecond) > kRightMaximumRadiansPerSecond)
  {
    return false;
  }
  // Clamp only floating-point roundoff at the already-validated endpoints.
  const double left = leftRadiansPerSecond * kLeftCountsPerRevolution / kTwoPi;
  const double right = rightRadiansPerSecond * kRightCountsPerRevolution / kTwoPi;
  leftCountsPerSecond = static_cast<float>(
      std::fmax(-kMaximumCountsPerSecond, std::fmin(kMaximumCountsPerSecond, left)));
  rightCountsPerSecond = static_cast<float>(
      std::fmax(-kMaximumCountsPerSecond, std::fmin(kMaximumCountsPerSecond, right)));
  return true;
}
} // namespace RosWheelUnits
