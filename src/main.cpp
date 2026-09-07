#include <Arduino.h>

#include "robot_drive.h"

namespace
{

  constexpr uint32_t kReportIntervalMs = 200;
  constexpr uint32_t kStraightTimeoutMs = 5000;
  constexpr uint32_t kTurnTimeoutMs = 1000;
  constexpr uint32_t kStraightRampMs = 300;
  constexpr uint32_t kTurnRampMs = 100;
  constexpr float kStraightTargetCountsPerSecond = 3000.0f;
  constexpr float kTurnTargetCountsPerSecond = 1800.0f;

  uint32_t gLastReportMs = 0;

  void printTelemetry()
  {
    const DriveTelemetry state = RobotDrive::telemetry();
    Serial.printf(
        "pid left_command=%.0f left_target=%.0f left_speed=%.0f left_pwm=%d "
        "left_count=%ld right_command=%.0f right_target=%.0f right_speed=%.0f "
        "right_pwm=%d right_count=%ld\n",
        state.leftRequestedCountsPerSecond, state.leftTargetCountsPerSecond,
        state.leftMeasuredCountsPerSecond, state.leftControllerPwm,
        static_cast<long>(state.leftEncoderCount),
        state.rightRequestedCountsPerSecond, state.rightTargetCountsPerSecond,
        state.rightMeasuredCountsPerSecond, state.rightControllerPwm,
        static_cast<long>(state.rightEncoderCount));
  }

  void handleCommand(char command)
  {
    switch (command)
    {
    case 'w':
      RobotDrive::commandWheelSpeeds(kStraightTargetCountsPerSecond,
                                     kStraightTargetCountsPerSecond,
                                     kStraightTimeoutMs, kStraightRampMs);
      break;
    case 's':
      RobotDrive::commandWheelSpeeds(-kStraightTargetCountsPerSecond,
                                     -kStraightTargetCountsPerSecond,
                                     kStraightTimeoutMs, kStraightRampMs);
      break;
    case 'a':
      RobotDrive::commandWheelSpeeds(-kTurnTargetCountsPerSecond,
                                     kTurnTargetCountsPerSecond, kTurnTimeoutMs,
                                     kTurnRampMs);
      break;
    case 'd':
      RobotDrive::commandWheelSpeeds(kTurnTargetCountsPerSecond,
                                     -kTurnTargetCountsPerSecond, kTurnTimeoutMs,
                                     kTurnRampMs);
      break;
    case 'x':
      RobotDrive::stop();
      break;
    case 'e':
    {
      const DriveTelemetry state = RobotDrive::telemetry();
      Serial.printf("left_count=%ld right_count=%ld\n",
                    static_cast<long>(state.leftEncoderCount),
                    static_cast<long>(state.rightEncoderCount));
      break;
    }
    case '\r':
    case '\n':
      break;
    default:
      RobotDrive::stop();
      Serial.printf("Stopped: unknown command '%c'\n", command);
      break;
    }
  }

} // namespace

void setup()
{
  Serial.begin(115200);
  RobotDrive::begin();
  gLastReportMs = millis();

  Serial.println("ESP32 encoder-feedback wheel control ready");
  Serial.println("Commands: w/s/a/d move, x stop, e encoder counts");
  Serial.println("Straight target: 3000 counts/s for 5000 ms; ramp: 300 ms");
  Serial.println("Turn target: 1800 counts/s for 1000 ms; ramp: 100 ms");
}

void loop()
{
  while (Serial.available() > 0)
  {
    handleCommand(static_cast<char>(Serial.read()));
  }

  const uint32_t nowMs = millis();
  if (RobotDrive::update(nowMs) == DriveUpdateEvent::CommandTimedOut)
  {
    Serial.println("Stopped: command timeout");
  }

  if (RobotDrive::motionCommandActive() &&
      nowMs - gLastReportMs >= kReportIntervalMs)
  {
    gLastReportMs = nowMs;
    printTelemetry();
  }
}
