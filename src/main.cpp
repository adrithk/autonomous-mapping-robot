#include <Arduino.h>

#include "wheel_speed_controller.h"

namespace
{

// BTS7960 motor-driver inputs. One driver module controls each motor.
constexpr uint8_t kLeftRpwmPin = 25;
constexpr uint8_t kLeftLpwmPin = 26;
constexpr uint8_t kDriverEnablePin = 27;
constexpr uint8_t kRightRpwmPin = 32;
constexpr uint8_t kRightLpwmPin = 33;

// Encoder inputs after the 5 V-to-3.3 V level shifter.
constexpr uint8_t kLeftEncoderAPin = 34;
constexpr uint8_t kLeftEncoderBPin = 35;
constexpr uint8_t kRightEncoderAPin = 36; // ESP32 board label: VP
constexpr uint8_t kRightEncoderBPin = 39; // ESP32 board label: VN

constexpr uint32_t kPwmFrequencyHz = 20000;
constexpr uint8_t kPwmResolutionBits = 8;
constexpr uint32_t kControlIntervalMs = 20;
constexpr uint32_t kEncoderReportIntervalMs = 200;
constexpr uint32_t kStraightCommandTimeoutMs = 5000;
constexpr uint32_t kTurnCommandTimeoutMs = 1000;
constexpr uint32_t kStraightRampDurationMs = 300;
constexpr uint32_t kTurnRampDurationMs = 100;

// Initial targets and gains are based on the 2026-09-04 observations. They are
// deliberately conservative and must be tuned on the physical robot.
constexpr float kStraightTargetCountsPerSecond = 3000.0f;
constexpr float kTurnTargetCountsPerSecond = 1800.0f;
constexpr float kTargetSlewRateCountsPerSecondSquared =
    kStraightTargetCountsPerSecond / (kStraightRampDurationMs / 1000.0f);
constexpr float kTurnTargetSlewRateCountsPerSecondSquared =
    kTurnTargetCountsPerSecond / (kTurnRampDurationMs / 1000.0f);
constexpr WheelSpeedControllerGains kInitialGains{
    0.020f, // proportional
    0.010f, // integral
    0.000f, // derivative: disabled initially because raw speed is noisy
    0.048f  // feed-forward PWM per target count/second
};
constexpr float kMaximumPwm = 200.0f;
constexpr float kIntegralLimit = 4000.0f;

// Positive controller output means robot-forward wheel rotation. The left
// driver's electrical polarity is reversed relative to that convention.
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
int16_t gLeftControllerOutput = 0;
int16_t gRightControllerOutput = 0;

bool gMotionCommandActive = false;
uint32_t gLastMotionCommandMs = 0;
uint32_t gActiveCommandTimeoutMs = 0;
uint32_t gActiveRampDurationMs = 0;
float gActiveTargetSlewRateCountsPerSecondSquared = 0.0f;
uint32_t gLastControlMs = 0;
uint32_t gLastEncoderReportMs = 0;
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

void stopMotors()
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

void commandWheelSpeeds(float leftTarget, float rightTarget, uint32_t timeoutMs,
                        uint32_t rampDurationMs,
                        float targetSlewRateCountsPerSecondSquared)
{
  gLeftRequestedSpeed = leftTarget;
  gRightRequestedSpeed = rightTarget;
  gMotionCommandActive = (leftTarget != 0.0f) || (rightTarget != 0.0f);
  gLastMotionCommandMs = millis();
  gActiveCommandTimeoutMs = timeoutMs;
  gActiveRampDurationMs = rampDurationMs;
  gActiveTargetSlewRateCountsPerSecondSquared =
      targetSlewRateCountsPerSecondSquared;
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
  gLeftEncoderCount += (encoderA == encoderB) ? 1 : -1;
  portEXIT_CRITICAL_ISR(&gEncoderMux);
}

void IRAM_ATTR onRightEncoderAChange()
{
  const bool encoderA = digitalRead(kRightEncoderAPin);
  const bool encoderB = digitalRead(kRightEncoderBPin);

  portENTER_CRITICAL_ISR(&gEncoderMux);
  gRightEncoderCount += (encoderA == encoderB) ? 1 : -1;
  portEXIT_CRITICAL_ISR(&gEncoderMux);
}

void updateWheelSpeedControl(uint32_t nowMs)
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
      (counts.left - gPreviousLeftEncoderCount) / elapsedSeconds;
  gRightMeasuredSpeed =
      (counts.right - gPreviousRightEncoderCount) / elapsedSeconds;
  gPreviousLeftEncoderCount = counts.left;
  gPreviousRightEncoderCount = counts.right;

  const float maximumTargetChange =
      gActiveTargetSlewRateCountsPerSecondSquared * elapsedSeconds;
  gLeftTargetSpeed = moveToward(gLeftTargetSpeed, gLeftRequestedSpeed,
                                maximumTargetChange);
  gRightTargetSpeed = moveToward(gRightTargetSpeed, gRightRequestedSpeed,
                                 maximumTargetChange);

  const float leftOutput = gLeftController.update(
      gLeftTargetSpeed, gLeftMeasuredSpeed, elapsedSeconds);
  const float rightOutput = gRightController.update(
      gRightTargetSpeed, gRightMeasuredSpeed, elapsedSeconds);

  gLeftControllerOutput = static_cast<int16_t>(leftOutput);
  gRightControllerOutput = static_cast<int16_t>(rightOutput);

  writeMotorPwm(kLeftRpwmPin, kLeftLpwmPin,
                gLeftControllerOutput * kLeftMotorPolarity);
  writeMotorPwm(kRightRpwmPin, kRightLpwmPin,
                gRightControllerOutput * kRightMotorPolarity);
}

void printControllerTelemetry()
{
  const EncoderCounts counts = readEncoderCounts();
  Serial.printf(
      "pid left_command=%.0f left_target=%.0f left_speed=%.0f left_pwm=%d "
      "left_count=%ld right_command=%.0f right_target=%.0f right_speed=%.0f "
      "right_pwm=%d right_count=%ld\n",
      gLeftRequestedSpeed, gLeftTargetSpeed, gLeftMeasuredSpeed,
      gLeftControllerOutput, static_cast<long>(counts.left),
      gRightRequestedSpeed, gRightTargetSpeed, gRightMeasuredSpeed,
      gRightControllerOutput, static_cast<long>(counts.right));
}

void handleCommand(char command)
{
  switch (command)
  {
  case 'w':
    commandWheelSpeeds(kStraightTargetCountsPerSecond,
                       kStraightTargetCountsPerSecond,
                       kStraightCommandTimeoutMs, kStraightRampDurationMs,
                       kTargetSlewRateCountsPerSecondSquared);
    break;
  case 's':
    commandWheelSpeeds(-kStraightTargetCountsPerSecond,
                       -kStraightTargetCountsPerSecond,
                       kStraightCommandTimeoutMs, kStraightRampDurationMs,
                       kTargetSlewRateCountsPerSecondSquared);
    break;
  case 'a':
    commandWheelSpeeds(-kTurnTargetCountsPerSecond,
                       kTurnTargetCountsPerSecond, kTurnCommandTimeoutMs,
                       kTurnRampDurationMs,
                       kTurnTargetSlewRateCountsPerSecondSquared);
    break;
  case 'd':
    commandWheelSpeeds(kTurnTargetCountsPerSecond,
                       -kTurnTargetCountsPerSecond, kTurnCommandTimeoutMs,
                       kTurnRampDurationMs,
                       kTurnTargetSlewRateCountsPerSecondSquared);
    break;
  case 'x':
    stopMotors();
    break;
  case 'e':
    printControllerTelemetry();
    break;
  case '\r':
  case '\n':
    // Terminal line endings are ignored and do not extend the motion timeout.
    break;
  default:
    stopMotors();
    Serial.printf("Stopped: unknown command '%c'\n", command);
    break;
  }
}

} // namespace

void setup()
{
  Serial.begin(115200);

  pinMode(kDriverEnablePin, OUTPUT);
  digitalWrite(kDriverEnablePin, LOW);

  ledcAttach(kLeftRpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kLeftLpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kRightRpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  ledcAttach(kRightLpwmPin, kPwmFrequencyHz, kPwmResolutionBits);
  stopMotors();

  // GPIO 34-39 have no internal pull resistors. The external level shifter
  // provides the signal pull-ups, so these pins are plain inputs.
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
  gLastEncoderReportMs = gLastControlMs;

  // Outputs were set to zero before enabling the BTS7960 modules.
  digitalWrite(kDriverEnablePin, HIGH);

  Serial.println("ESP32 encoder-feedback wheel control ready");
  Serial.println("Commands: w/s/a/d move, x stop, e telemetry");
  Serial.println("Straight target: 3000 counts/s for 5000 ms");
  Serial.println("Straight acceleration/deceleration ramp: 300 ms");
  Serial.println("Turn target: 1800 counts/s for 1000 ms");
  Serial.println("Turn acceleration/deceleration ramp: 100 ms");
}

void loop()
{
  while (Serial.available() > 0)
  {
    handleCommand(static_cast<char>(Serial.read()));
  }

  const uint32_t nowMs = millis();
  const uint32_t commandElapsedMs = nowMs - gLastMotionCommandMs;

  if (gMotionCommandActive &&
      commandElapsedMs >=
          (gActiveCommandTimeoutMs - gActiveRampDurationMs))
  {
    gLeftRequestedSpeed = 0.0f;
    gRightRequestedSpeed = 0.0f;
  }

  if (gMotionCommandActive &&
      (commandElapsedMs >= gActiveCommandTimeoutMs))
  {
    stopMotors();
    Serial.println("Stopped: command timeout");
  }

  updateWheelSpeedControl(nowMs);

  if (gMotionCommandActive &&
      (nowMs - gLastEncoderReportMs >= kEncoderReportIntervalMs))
  {
    gLastEncoderReportMs = nowMs;
    printControllerTelemetry();
  }
}
