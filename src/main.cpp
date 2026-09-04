#include <Arduino.h>

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
  constexpr uint8_t kManualDuty = 100;
  constexpr uint32_t kCommandTimeoutMs = 1000;
  constexpr uint32_t kEncoderReportIntervalMs = 200;

  volatile int32_t gLeftEncoderCount = 0;
  volatile int32_t gRightEncoderCount = 0;
  portMUX_TYPE gEncoderMux = portMUX_INITIALIZER_UNLOCKED;

  bool gMotionCommandActive = false;
  uint32_t gLastMotionCommandMs = 0;
  uint32_t gLastEncoderReportMs = 0;

  void stopMotors()
  {
    ledcWrite(kLeftRpwmPin, 0);
    ledcWrite(kLeftLpwmPin, 0);
    ledcWrite(kRightRpwmPin, 0);
    ledcWrite(kRightLpwmPin, 0);
    gMotionCommandActive = false;
  }

  void setMotorDuty(uint8_t forwardPin, uint8_t reversePin, int16_t signedDuty)
  {
    const uint8_t duty = static_cast<uint8_t>(constrain(abs(signedDuty), 0, 255));

    if (signedDuty > 0)
    {
      ledcWrite(reversePin, 0);
      ledcWrite(forwardPin, duty);
    }
    else if (signedDuty < 0)
    {
      ledcWrite(forwardPin, 0);
      ledcWrite(reversePin, duty);
    }
    else
    {
      ledcWrite(forwardPin, 0);
      ledcWrite(reversePin, 0);
    }
  }

  void commandWheels(int16_t leftDuty, int16_t rightDuty)
  {
    setMotorDuty(kLeftRpwmPin, kLeftLpwmPin, leftDuty);
    setMotorDuty(kRightRpwmPin, kRightLpwmPin, rightDuty);
    gMotionCommandActive = (leftDuty != 0) || (rightDuty != 0);
    gLastMotionCommandMs = millis();
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

  void printEncoderCounts()
  {
    int32_t leftCount;
    int32_t rightCount;

    portENTER_CRITICAL(&gEncoderMux);
    leftCount = gLeftEncoderCount;
    rightCount = gRightEncoderCount;
    portEXIT_CRITICAL(&gEncoderMux);

    Serial.printf("encoders left=%ld right=%ld\n", static_cast<long>(leftCount),
                  static_cast<long>(rightCount));
  }

  void handleCommand(char command)
  {
    switch (command)
    {
    case 'w':
      commandWheels(kManualDuty, kManualDuty);
      break;
    case 's':
      commandWheels(-kManualDuty, -kManualDuty);
      break;
    case 'a':
      commandWheels(-kManualDuty, kManualDuty);
      break;
    case 'd':
      commandWheels(kManualDuty, -kManualDuty);
      break;
    case 'x':
      stopMotors();
      break;
    case 'e':
      printEncoderCounts();
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

  // GPIO 34-39 have no internal pull resistors. The external level-shifter board
  // provides the signal pull-ups, so these pins are plain inputs.
  pinMode(kLeftEncoderAPin, INPUT);
  pinMode(kLeftEncoderBPin, INPUT);
  pinMode(kRightEncoderAPin, INPUT);
  pinMode(kRightEncoderBPin, INPUT);
  attachInterrupt(digitalPinToInterrupt(kLeftEncoderAPin), onLeftEncoderAChange, CHANGE);
  attachInterrupt(digitalPinToInterrupt(kRightEncoderAPin), onRightEncoderAChange, CHANGE);

  // Outputs were set to zero before enabling the BTS7960 modules.
  digitalWrite(kDriverEnablePin, HIGH);

  Serial.println("ESP32 BTS7960 drive bring-up ready");
  Serial.println("Commands: w/s/a/d move, x stop, e encoder counts");
  Serial.println("Motion timeout: 1000 ms; resend a movement command to continue.");
}

void loop()
{
  while (Serial.available() > 0)
  {
    handleCommand(static_cast<char>(Serial.read()));
  }

  if (gMotionCommandActive && (millis() - gLastMotionCommandMs >= kCommandTimeoutMs))
  {
    stopMotors();
    Serial.println("Stopped: command timeout");
  }

  if (gMotionCommandActive &&
      (millis() - gLastEncoderReportMs >= kEncoderReportIntervalMs))
  {
    gLastEncoderReportMs = millis();
    printEncoderCounts();
  }
}
