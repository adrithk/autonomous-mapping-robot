#pragma once

#include <Arduino.h>

struct DriveTelemetry
{
  float leftRequestedCountsPerSecond;
  float rightRequestedCountsPerSecond;
  float leftTargetCountsPerSecond;
  float rightTargetCountsPerSecond;
  float leftMeasuredCountsPerSecond;
  float rightMeasuredCountsPerSecond;
  int16_t leftControllerPwm;
  int16_t rightControllerPwm;
  int32_t leftEncoderCount;
  int32_t rightEncoderCount;
};

enum class DriveUpdateEvent : uint8_t
{
  None,
  CommandTimedOut
};

namespace RobotDrive
{

void begin();
void commandWheelSpeeds(float leftCountsPerSecond,
                        float rightCountsPerSecond, uint32_t timeoutMs,
                        uint32_t rampDurationMs);
void stop();
DriveUpdateEvent update(uint32_t nowMs);
DriveTelemetry telemetry();
bool motionCommandActive();

} // namespace RobotDrive
