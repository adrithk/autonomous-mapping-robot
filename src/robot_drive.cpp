#include "robot_drive.h"

#include <cmath>

#include "wheel_speed_controller.h"
#include "encoder_count_math.h"

namespace
{

constexpr uint8_t kLeftRpwmPin = 25;
constexpr uint8_t kLeftLpwmPin = 26;
constexpr uint8_t kDriverEnablePin = 27;
constexpr uint8_t kRightRpwmPin = 32;
constexpr uint8_t kRightLpwmPin = 33;

constexpr uint8_t kLeftEncoderAPin = 34;
constexpr uint8_t kLeftEncoderBPin = 35;
constexpr uint8_t kRightEncoderAPin = 36;
constexpr uint8_t kRightEncoderBPin = 39;

constexpr uint32_t kPwmFrequencyHz = 20000;
constexpr uint8_t kPwmResolutionBits = 8;
constexpr uint32_t kControlIntervalMs = 20;
constexpr WheelSpeedControllerGains kInitialGains{
    0.020f,
    0.010f,
    0.000f,
    0.048f,
};
constexpr float kMaximumPwm = 200.0f;
constexpr float kIntegralLimit = 4000.0f;
constexpr int8_t kLeftMotorPolarity = -1;
constexpr int8_t kRightMotorPolarity = 1;

volatile int32_t gLeftEncoderCount = 0;
volatile int32_t gRightEncoderCount = 0;
portMUX_TYPE gEncoderMux = portMUX_INITIALIZER_UNLOCKED;

WheelSpeedController gLeftController(kInitialGains, kMaximumPwm, kIntegralLimit);
WheelSpeedController gRightController(kInitialGains, kMaximumPwm, kIntegralLimit);

float gLeftRequestedSpeed = 0.0f;
float gRightRequestedSpeed = 0.0f;
float gLeftTargetSpeed = 0.0f;
float gRightTargetSpeed = 0.0f;
float gLeftMeasuredSpeed = 0.0f;
float gRightMeasuredSpeed = 0.0f;
float gTargetSlewRateCountsPerSecondSquared = 0.0f;
int16_t gLeftControllerOutput = 0;
int16_t gRightControllerOutput = 0;

bool gMotionCommandActive = false;
uint32_t gLastMotionCommandMs = 0;
uint32_t gActiveCommandTimeoutMs = 0;
uint32_t gActiveRampDurationMs = 0;
uint32_t gLastControlMs = 0;
int32_t gPreviousLeftEncoderCount = 0;
int32_t gPreviousRightEncoderCount = 0;

struct EncoderCounts
{
  int32_t left;
  int32_t right;
};

EncoderCounts readEncoderCounts()
{
  EncoderCounts counts;
  portENTER_CRITICAL(&gEncoderMux);
  counts.left = gLeftEncoderCount;
  counts.right = gRightEncoderCount;
  portEXIT_CRITICAL(&gEncoderMux);
  return counts;
}

void writeMotorPwm(uint8_t forwardPin, uint8_t reversePin, int16_t signedPwm)
{
  uint16_t magnitude = signedPwm >= 0 ? signedPwm : -signedPwm;
  if (magnitude > 255)
  {
    magnitude = 255;
  }

  if (signedPwm > 0)
  {
    ledcWrite(reversePin, 0);
    ledcWrite(forwardPin, magnitude);
  }
  else if (signedPwm < 0)
  {
    ledcWrite(forwardPin, 0);
    ledcWrite(reversePin, magnitude);
  }
  else
  {
    ledcWrite(forwardPin, 0);
    ledcWrite(reversePin, 0);
  }
}

float moveToward(float current, float requested, float maximumChange)
{
  if (current < requested)
  {
    const float increased = current + maximumChange;
    return increased < requested ? increased : requested;
  }
  if (current > requested)
  {
    const float decreased = current - maximumChange;
    return decreased > requested ? decreased : requested;
  }
  return requested;
}

void IRAM_ATTR onLeftEncoderAChange()
{
  const bool encoderA = digitalRead(kLeftEncoderAPin);
  const bool encoderB = digitalRead(kLeftEncoderBPin);
  portENTER_CRITICAL_ISR(&gEncoderMux);
  gLeftEncoderCount = encoderStep(gLeftEncoderCount, encoderA == encoderB);
  portEXIT_CRITICAL_ISR(&gEncoderMux);
}

void IRAM_ATTR onRightEncoderAChange()
{
  const bool encoderA = digitalRead(kRightEncoderAPin);
  const bool encoderB = digitalRead(kRightEncoderBPin);
  portENTER_CRITICAL_ISR(&gEncoderMux);
  gRightEncoderCount = encoderStep(gRightEncoderCount, encoderA == encoderB);
  portEXIT_CRITICAL_ISR(&gEncoderMux);
}

void updateController(uint32_t nowMs)
{
  const uint32_t elapsedMs = nowMs - gLastControlMs;
  if (elapsedMs < kControlIntervalMs)
  {
    return;
  }

  gLastControlMs = nowMs;
  const float elapsedSeconds = elapsedMs / 1000.0f;
  const EncoderCounts counts = readEncoderCounts();
  gLeftMeasuredSpeed =
      encoderDelta(counts.left, gPreviousLeftEncoderCount) / elapsedSeconds;
  gRightMeasuredSpeed =
      encoderDelta(counts.right, gPreviousRightEncoderCount) / elapsedSeconds;
  gPreviousLeftEncoderCount = counts.left;
  gPreviousRightEncoderCount = counts.right;

  const float maximumTargetChange =
      gTargetSlewRateCountsPerSecondSquared * elapsedSeconds;
  gLeftTargetSpeed =
      moveToward(gLeftTargetSpeed, gLeftRequestedSpeed, maximumTargetChange);
  gRightTargetSpeed =
      moveToward(gRightTargetSpeed, gRightRequestedSpeed, maximumTargetChange);

  gLeftControllerOutput = static_cast<int16_t>(gLeftController.update(
      gLeftTargetSpeed, gLeftMeasuredSpeed, elapsedSeconds));
  gRightControllerOutput = static_cast<int16_t>(gRightController.update(
      gRightTargetSpeed, gRightMeasuredSpeed, elapsedSeconds));

  writeMotorPwm(kLeftRpwmPin, kLeftLpwmPin,
                gLeftControllerOutput * kLeftMotorPolarity);
  writeMotorPwm(kRightRpwmPin, kRightLpwmPin,
                gRightControllerOutput * kRightMotorPolarity);
}

} // namespace

namespace RobotDrive
{

void begin()
{
  pinMode(kDriverEnablePin, OUTPUT);
  digitalWrite(kDriverEnablePin, LOW);

  ledcAttach(kLeftRpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kLeftLpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kRightRpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kRightLpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  stop();

  pinMode(kLeftEncoderAPin, INPUT);
  pinMode(kLeftEncoderBPin, INPUT);
  pinMode(kRightEncoderAPin, INPUT);
  pinMode(kRightEncoderBPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(kLeftEncoderAPin),
                  onLeftEncoderAChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(kRightEncoderAPin),
                  onRightEncoderAChange, CHANGE);

  const EncoderCounts initialCounts = readEncoderCounts();
  gPreviousLeftEncoderCount = initialCounts.left;
  gPreviousRightEncoderCount = initialCounts.right;
  gLastControlMs = millis();

  digitalWrite(kDriverEnablePin, HIGH);
}

void commandWheelSpeeds(float leftCountsPerSecond,
                        float rightCountsPerSecond, uint32_t timeoutMs,
                        uint32_t rampDurationMs)
{
  gLeftRequestedSpeed = leftCountsPerSecond;
  gRightRequestedSpeed = rightCountsPerSecond;
  gMotionCommandActive =
      leftCountsPerSecond != 0.0f || rightCountsPerSecond != 0.0f;
  gLastMotionCommandMs = millis();
  gActiveCommandTimeoutMs = timeoutMs;
  gActiveRampDurationMs = rampDurationMs;

  const float largestTarget =
      fmaxf(fabsf(leftCountsPerSecond), fabsf(rightCountsPerSecond));
  if (rampDurationMs == 0)
  {
    gTargetSlewRateCountsPerSecondSquared = largestTarget;
    gLeftTargetSpeed = leftCountsPerSecond;
    gRightTargetSpeed = rightCountsPerSecond;
    gLeftController.reset();
    gRightController.reset();
  }
  else
  {
    gTargetSlewRateCountsPerSecondSquared =
        largestTarget / (rampDurationMs / 1000.0f);
  }
}

void stop()
{
  gLeftRequestedSpeed = 0.0f;
  gRightRequestedSpeed = 0.0f;
  gLeftTargetSpeed = 0.0f;
  gRightTargetSpeed = 0.0f;
  gLeftControllerOutput = 0;
  gRightControllerOutput = 0;
  gMotionCommandActive = false;
  gLeftController.reset();
  gRightController.reset();
  writeMotorPwm(kLeftRpwmPin, kLeftLpwmPin, 0);
  writeMotorPwm(kRightRpwmPin, kRightLpwmPin, 0);
}

DriveUpdateEvent update(uint32_t nowMs)
{
  if (gMotionCommandActive)
  {
    const uint32_t elapsedMs = nowMs - gLastMotionCommandMs;
    const uint32_t rampStartMs =
        gActiveCommandTimeoutMs > gActiveRampDurationMs
            ? gActiveCommandTimeoutMs - gActiveRampDurationMs
            : 0;
    if (elapsedMs >= rampStartMs)
    {
      gLeftRequestedSpeed = 0.0f;
      gRightRequestedSpeed = 0.0f;
    }
    if (elapsedMs >= gActiveCommandTimeoutMs)
    {
      stop();
      return DriveUpdateEvent::CommandTimedOut;
    }
  }

  updateController(nowMs);
  return DriveUpdateEvent::None;
}

DriveTelemetry telemetry()
{
  const EncoderCounts counts = readEncoderCounts();
  return DriveTelemetry{
      gLeftRequestedSpeed,
      gRightRequestedSpeed,
      gLeftTargetSpeed,
      gRightTargetSpeed,
      gLeftMeasuredSpeed,
      gRightMeasuredSpeed,
      gLeftControllerOutput,
      gRightControllerOutput,
      counts.left,
      counts.right,
  };
}

bool motionCommandActive()
{
  return gMotionCommandActive;
}

} // namespace RobotDrive
