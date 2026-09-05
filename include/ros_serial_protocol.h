#pragma once

#include <cerrno>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace RosSerialProtocol
{

constexpr uint32_t kProtocolVersion = 1;
constexpr size_t kMaximumFrameLength = 128;

enum class MessageType : uint8_t
{
  WheelCommand,
  Stop
};

struct CommandFrame
{
  MessageType type;
  uint32_t sequence;
  int32_t leftCountsPerSecond;
  int32_t rightCountsPerSecond;
};

struct StateFrame
{
  uint32_t acknowledgedSequence;
  uint32_t espMilliseconds;
  int32_t leftEncoderCount;
  int32_t rightEncoderCount;
  int32_t leftCountsPerSecond;
  int32_t rightCountsPerSecond;
  int16_t leftPwm;
  int16_t rightPwm;
  uint16_t statusBits;
};

enum class ParseResult : uint8_t
{
  Incomplete,
  CommandReady,
  StopReady,
  Overflow,
  BadFormat,
  BadChecksum
};

inline uint16_t crc16CcittFalse(const char *data, size_t length)
{
  uint16_t crc = 0xFFFF;
  for (size_t index = 0; index < length; ++index)
  {
    crc ^= static_cast<uint16_t>(static_cast<uint8_t>(data[index])) << 8;
    for (uint8_t bit = 0; bit < 8; ++bit)
    {
      crc = (crc & 0x8000) != 0 ? static_cast<uint16_t>((crc << 1) ^ 0x1021)
                                : static_cast<uint16_t>(crc << 1);
    }
  }
  return crc;
}

inline bool isNewerSequence(uint32_t candidate, uint32_t previous)
{
  return static_cast<int32_t>(candidate - previous) > 0;
}

inline bool parseUnsigned(const char *text, uint32_t &value)
{
  if (text == nullptr || *text == '\0' || *text == '-')
  {
    return false;
  }
  errno = 0;
  char *end = nullptr;
  const unsigned long parsed = std::strtoul(text, &end, 10);
  if (errno != 0 || *end != '\0' ||
      parsed > std::numeric_limits<uint32_t>::max())
  {
    return false;
  }
  value = static_cast<uint32_t>(parsed);
  return true;
}

inline bool parseSigned(const char *text, int32_t &value)
{
  if (text == nullptr || *text == '\0')
  {
    return false;
  }
  errno = 0;
  char *end = nullptr;
  const long parsed = std::strtol(text, &end, 10);
  if (errno != 0 || *end != '\0' ||
      parsed < std::numeric_limits<int32_t>::min() ||
      parsed > std::numeric_limits<int32_t>::max())
  {
    return false;
  }
  value = static_cast<int32_t>(parsed);
  return true;
}

inline char *nextToken(char *&cursor)
{
  if (cursor == nullptr)
  {
    return nullptr;
  }
  char *token = cursor;
  char *separator = std::strchr(cursor, ',');
  if (separator == nullptr)
  {
    cursor = nullptr;
  }
  else
  {
    *separator = '\0';
    cursor = separator + 1;
  }
  return token;
}

class Parser
{
public:
  ParseResult push(char byte, CommandFrame &frame)
  {
    if (byte == '\r')
    {
      return ParseResult::Incomplete;
    }
    if (byte != '\n')
    {
      if (length_ + 1 >= sizeof(buffer_))
      {
        overflowed_ = true;
      }
      else if (!overflowed_)
      {
        buffer_[length_++] = byte;
      }
      return ParseResult::Incomplete;
    }

    if (overflowed_)
    {
      reset();
      return ParseResult::Overflow;
    }
    buffer_[length_] = '\0';
    const ParseResult result = parse(frame);
    reset();
    return result;
  }

private:
  ParseResult parse(CommandFrame &frame)
  {
    char *asterisk = std::strrchr(buffer_, '*');
    if (asterisk == nullptr || std::strlen(asterisk + 1) != 4)
    {
      return ParseResult::BadFormat;
    }

    char *checksumEnd = nullptr;
    const unsigned long receivedChecksum =
        std::strtoul(asterisk + 1, &checksumEnd, 16);
    if (*checksumEnd != '\0' || receivedChecksum > 0xFFFF)
    {
      return ParseResult::BadFormat;
    }
    const uint16_t expectedChecksum =
        crc16CcittFalse(buffer_, static_cast<size_t>(asterisk - buffer_));
    if (expectedChecksum != static_cast<uint16_t>(receivedChecksum))
    {
      return ParseResult::BadChecksum;
    }
    *asterisk = '\0';

    char *cursor = buffer_;
    char *type = nextToken(cursor);
    char *versionText = nextToken(cursor);
    char *sequenceText = nextToken(cursor);
    uint32_t version = 0;
    uint32_t sequence = 0;
    if (!parseUnsigned(versionText, version) || version != kProtocolVersion ||
        !parseUnsigned(sequenceText, sequence))
    {
      return ParseResult::BadFormat;
    }

    if (std::strcmp(type, "X") == 0 && cursor == nullptr)
    {
      frame = CommandFrame{MessageType::Stop, sequence, 0, 0};
      return ParseResult::StopReady;
    }
    if (std::strcmp(type, "C") != 0)
    {
      return ParseResult::BadFormat;
    }

    char *leftText = nextToken(cursor);
    char *rightText = nextToken(cursor);
    if (cursor != nullptr || !parseSigned(leftText, frame.leftCountsPerSecond) ||
        !parseSigned(rightText, frame.rightCountsPerSecond))
    {
      return ParseResult::BadFormat;
    }
    frame.type = MessageType::WheelCommand;
    frame.sequence = sequence;
    return ParseResult::CommandReady;
  }

  void reset()
  {
    length_ = 0;
    overflowed_ = false;
  }

  char buffer_[kMaximumFrameLength]{};
  size_t length_ = 0;
  bool overflowed_ = false;
};

inline size_t formatStateFrame(char *output, size_t outputSize,
                               const StateFrame &state)
{
  char payload[kMaximumFrameLength];
  const int payloadLength = std::snprintf(
      payload, sizeof(payload), "S,1,%lu,%lu,%ld,%ld,%ld,%ld,%d,%d,%u",
      static_cast<unsigned long>(state.acknowledgedSequence),
      static_cast<unsigned long>(state.espMilliseconds),
      static_cast<long>(state.leftEncoderCount),
      static_cast<long>(state.rightEncoderCount),
      static_cast<long>(state.leftCountsPerSecond),
      static_cast<long>(state.rightCountsPerSecond), state.leftPwm,
      state.rightPwm, state.statusBits);
  if (payloadLength < 0 || static_cast<size_t>(payloadLength) >= sizeof(payload))
  {
    return 0;
  }
  const uint16_t checksum =
      crc16CcittFalse(payload, static_cast<size_t>(payloadLength));
  const int frameLength = std::snprintf(output, outputSize, "%s*%04X\n", payload,
                                        static_cast<unsigned>(checksum));
  if (frameLength < 0 || static_cast<size_t>(frameLength) >= outputSize)
  {
    return 0;
  }
  return static_cast<size_t>(frameLength);
}

} // namespace RosSerialProtocol
