#include "ros_serial_protocol.h"

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
  assert(feed(parser, checkedFrame("C,1,42,3000,-1800"), command) ==
         ParseResult::CommandReady);
  assert(command.type == MessageType::WheelCommand);
  assert(command.sequence == 42);
  assert(command.leftCountsPerSecond == 3000);
  assert(command.rightCountsPerSecond == -1800);

  assert(feed(parser, checkedFrame("X,1,43"), command) ==
         ParseResult::StopReady);
  assert(command.type == MessageType::Stop);
  assert(command.sequence == 43);

  assert(feed(parser, "C,1,44,1,2*0000\n", command) ==
         ParseResult::BadChecksum);
  assert(feed(parser, checkedFrame("C,2,44,1,2"), command) ==
         ParseResult::BadFormat);
  assert(feed(parser, checkedFrame("C,1,44,1"), command) ==
         ParseResult::BadFormat);

  std::string oversized(kMaximumFrameLength + 10, 'A');
  oversized += '\n';
  assert(feed(parser, oversized, command) == ParseResult::Overflow);

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
      "S,1,42,1000,10,-10,3000,-3000,144,-146,3*";
  assert(std::strncmp(stateFrame, kExpectedStatePayload,
                      std::strlen(kExpectedStatePayload)) == 0);

  return 0;
}
