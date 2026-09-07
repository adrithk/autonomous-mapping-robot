#include <Arduino.h>

#include <cmath>

#include "robot_drive.h"
#include "ros_serial_protocol.h"

namespace
{

constexpr uint32_t kCommandWatchdogMs = 250;
constexpr uint32_t kCommandRampMs = 100;
constexpr uint32_t kTelemetryIntervalMs = 50;
constexpr int32_t kMaximumTargetCountsPerSecond = 4000;

constexpr uint16_t kStatusCommandTimeout = 1U << 0;
constexpr uint16_t kStatusReceiveOverflow = 1U << 1;
constexpr uint16_t kStatusBadFormat = 1U << 2;
constexpr uint16_t kStatusBadChecksum = 1U << 3;
constexpr uint16_t kStatusOutOfRange = 1U << 4;
constexpr uint16_t kStatusStaleSequence = 1U << 5;

RosSerialProtocol::Parser gParser;
bool gHasAcceptedSequence = false;
uint32_t gLastAcceptedSequence = 0;
uint32_t gLastTelemetryMs = 0;
uint16_t gLatchedStatusBits = 0;

bool sequenceIsAcceptable(uint32_t sequence)
{
  return !gHasAcceptedSequence ||
         RosSerialProtocol::isNewerSequence(sequence, gLastAcceptedSequence);
}

void acceptSequence(uint32_t sequence)
{
  gHasAcceptedSequence = true;
  gLastAcceptedSequence = sequence;
}

void handleFrame(const RosSerialProtocol::CommandFrame &frame,
                 RosSerialProtocol::ParseResult result)
{
  if (!sequenceIsAcceptable(frame.sequence))
  {
    gLatchedStatusBits |= kStatusStaleSequence;
    return;
  }

  if (result == RosSerialProtocol::ParseResult::StopReady)
  {
    acceptSequence(frame.sequence);
    RobotDrive::stop();
    return;
  }

  if (frame.leftCountsPerSecond < -kMaximumTargetCountsPerSecond ||
      frame.leftCountsPerSecond > kMaximumTargetCountsPerSecond ||
      frame.rightCountsPerSecond < -kMaximumTargetCountsPerSecond ||
      frame.rightCountsPerSecond > kMaximumTargetCountsPerSecond)
  {
    gLatchedStatusBits |= kStatusOutOfRange;
    return;
  }

  acceptSequence(frame.sequence);
  if (frame.leftCountsPerSecond == 0 && frame.rightCountsPerSecond == 0)
  {
    RobotDrive::stop();
    return;
  }
  RobotDrive::commandWheelSpeeds(frame.leftCountsPerSecond,
                                 frame.rightCountsPerSecond,
                                 kCommandWatchdogMs, kCommandRampMs);
}

void readSerialFrames()
{
  while (Serial.available() > 0)
  {
    RosSerialProtocol::CommandFrame frame{};
    const RosSerialProtocol::ParseResult result =
        gParser.push(static_cast<char>(Serial.read()), frame);
    switch (result)
    {
    case RosSerialProtocol::ParseResult::CommandReady:
    case RosSerialProtocol::ParseResult::StopReady:
      handleFrame(frame, result);
      break;
    case RosSerialProtocol::ParseResult::Overflow:
      gLatchedStatusBits |= kStatusReceiveOverflow;
      RobotDrive::stop();
      break;
    case RosSerialProtocol::ParseResult::BadFormat:
      gLatchedStatusBits |= kStatusBadFormat;
      break;
    case RosSerialProtocol::ParseResult::BadChecksum:
      gLatchedStatusBits |= kStatusBadChecksum;
      break;
    case RosSerialProtocol::ParseResult::Incomplete:
      break;
    }
  }
}

void sendTelemetry(uint32_t nowMs)
{
  const DriveTelemetry drive = RobotDrive::telemetry();
  const RosSerialProtocol::StateFrame state{
      gHasAcceptedSequence ? gLastAcceptedSequence : 0,
      nowMs,
      drive.leftEncoderCount,
      drive.rightEncoderCount,
      static_cast<int32_t>(std::lround(drive.leftMeasuredCountsPerSecond)),
      static_cast<int32_t>(std::lround(drive.rightMeasuredCountsPerSecond)),
      drive.leftControllerPwm,
      drive.rightControllerPwm,
      gLatchedStatusBits,
  };
  char frame[RosSerialProtocol::kMaximumFrameLength];
  const size_t frameLength =
      RosSerialProtocol::formatStateFrame(frame, sizeof(frame), state);
  if (frameLength > 0)
  {
    Serial.write(reinterpret_cast<const uint8_t *>(frame), frameLength);
  }
}

} // namespace

void setup()
{
  Serial.begin(115200);
  RobotDrive::begin();
  gLastTelemetryMs = millis();
}

void loop()
{
  readSerialFrames();

  const uint32_t nowMs = millis();
  if (RobotDrive::update(nowMs) == DriveUpdateEvent::CommandTimedOut)
  {
    gLatchedStatusBits |= kStatusCommandTimeout;
  }

  if (nowMs - gLastTelemetryMs >= kTelemetryIntervalMs)
  {
    gLastTelemetryMs = nowMs;
    sendTelemetry(nowMs);
  }
}
