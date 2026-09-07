#include "ros_serial_protocol.h"
#include "ros_wheel_units.h"
#include <cmath>

#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>

namespace
{

std::string checkedFrame(const std::string &payload)
{
  char checksum[8];
  std::snprintf(checksum, sizeof(checksum), "*%04X\n",
                RosSerialProtocol::crc16CcittFalse(payload.data(),
                                                   payload.size()));
  return payload + checksum;
}

RosSerialProtocol::ParseResult feed(RosSerialProtocol::Parser &parser,
                                    const std::string &text,
                                    RosSerialProtocol::CommandFrame &frame)
{
  RosSerialProtocol::ParseResult result =
      RosSerialProtocol::ParseResult::Incomplete;
  for (const char byte : text)
  {
    result = parser.push(byte, frame);
  }
  return result;
}

} // namespace

int main()
{
  using namespace RosSerialProtocol;

  assert(crc16CcittFalse("123456789", 9) == 0x29B1);

  Parser parser;
  CommandFrame command{};
  assert(feed(parser, checkedFrame("C,2,42,1.25,-2.5"), command) ==
         ParseResult::CommandReady);
  assert(command.type == MessageType::WheelCommand);
  assert(command.sequence == 42);
  assert(command.leftRadiansPerSecond == 1.25);
  assert(command.rightRadiansPerSecond == -2.5);

  assert(feed(parser, checkedFrame("X,2,43"), command) ==
         ParseResult::StopReady);
  assert(command.type == MessageType::Stop);
  assert(command.sequence == 43);

  assert(feed(parser, "C,2,44,1,2*0000\n", command) ==
         ParseResult::BadChecksum);
  assert(feed(parser, checkedFrame("C,1,44,1,2"), command) ==
         ParseResult::BadFormat);
  assert(feed(parser, checkedFrame("C,2,44,1"), command) ==
         ParseResult::BadFormat);

  std::string oversized(kMaximumFrameLength + 10, 'A');
  oversized += '\n';
  assert(feed(parser, oversized, command) == ParseResult::Overflow);

  assert(feed(parser, std::string(kMaximumFrameLength - 1, 'A'), command) ==
         ParseResult::Incomplete);
  assert(parser.push('A', command) == ParseResult::Overflow);
  // A command appended to an overflowed frame must be discarded through newline.
  assert(feed(parser, checkedFrame("C,2,45,100,100"), command) ==
         ParseResult::Overflow);
  assert(feed(parser, checkedFrame("C,2,46,100,100"), command) ==
         ParseResult::CommandReady);
  assert(command.sequence == 46);

  assert(isNewerSequence(11, 10));
  assert(!isNewerSequence(10, 10));
  assert(!isNewerSequence(9, 10));
  assert(isNewerSequence(0, 0xFFFFFFFFU));

  StateFrame state{42, 1000, 10, -10, 3000, -3000, 144, -146, 3};
  char stateFrame[kMaximumFrameLength];
  const size_t stateLength = formatStateFrame(stateFrame, sizeof(stateFrame), state);
  assert(stateLength > 0);
  assert(stateFrame[stateLength - 1] == '\n');
  constexpr char kExpectedStatePayload[] =
      "S,2,42,1000,10,-10,3000,-3000,144,-146,3*";
  assert(std::strncmp(stateFrame, kExpectedStatePayload,
                      std::strlen(kExpectedStatePayload)) == 0);

  for (const std::string token : {"nan", "inf", "-inf", "1e309", "1e-999", "0x1p0", " 1", "1x", "", ".", "1.2.3"})
  {
    assert(feed(parser, checkedFrame("C,2,50," + token + ",0"), command) == ParseResult::BadFormat);
  }
  assert(feed(parser, checkedFrame("C,2,50,1e-3,-0.5"), command) == ParseResult::CommandReady);
  assert(std::fabs(command.leftRadiansPerSecond - 0.001) < 1e-12);
  assert(feed(parser, checkedFrame("X,1,51"), command) == ParseResult::BadFormat);
  assert(feed(parser, checkedFrame("C,2,51,1,2,3"), command) == ParseResult::BadFormat);
  std::string hidden = checkedFrame("C,2,52,1,2");
  hidden.insert(hidden.size() - 1, 1, '\0');
  assert(feed(parser, hidden, command) == ParseResult::BadFormat);

  float left = 0, right = 0;
  assert(RosWheelUnits::convertCommand(1, -1, left, right));
  assert(std::fabs(left - 666.0634368396) < 0.001);
  assert(std::fabs(right + 666.0634368396) < 0.001);
  assert(RosWheelUnits::convertCommand(0, -0.0, left, right));
  assert(left == 0 && right == 0);
  assert(RosWheelUnits::convertCommand(RosWheelUnits::kLeftMaximumRadiansPerSecond,
      -RosWheelUnits::kRightMaximumRadiansPerSecond, left, right));
  assert(left == 4000 && right == -4000);
  assert(!RosWheelUnits::convertCommand(RosWheelUnits::kLeftMaximumRadiansPerSecond + 1e-6, 0, left, right));
  assert(!RosWheelUnits::convertCommand(0, -RosWheelUnits::kRightMaximumRadiansPerSecond - 1e-6, left, right));
  assert(!RosWheelUnits::convertCommand(std::numeric_limits<double>::infinity(), 0, left, right));
  assert(!RosWheelUnits::convertCommand(0, std::numeric_limits<double>::quiet_NaN(), left, right));
  assert(feed(parser, checkedFrame("C,2,53,4.50407,-2.70244"), command) == ParseResult::CommandReady);
  assert(RosWheelUnits::convertCommand(command.leftRadiansPerSecond, command.rightRadiansPerSecond, left, right));
  assert(std::fabs(left - 3000) < 0.02 && std::fabs(right + 1800) < 0.02);
  char tooSmall[8];
  assert(formatStateFrame(tooSmall, sizeof(tooSmall), state) == 0);
  return 0;
}
