#pragma once

#include <stdint.h>

// Signed wire counts wrap modulo 2^32; avoid signed-overflow undefined behavior.
constexpr int32_t encoderStep(int32_t count, bool forward)
{
  return forward ? (count == INT32_MAX ? INT32_MIN : count + 1)
                 : (count == INT32_MIN ? INT32_MAX : count - 1);
}

// Assumes fewer than 2^31 encoder edges between control samples.
inline int32_t encoderDelta(int32_t current, int32_t previous)
{
  int64_t delta = static_cast<int64_t>(current) - previous;
  if (delta > INT32_MAX) delta -= INT64_C(4294967296);
  if (delta < INT32_MIN) delta += INT64_C(4294967296);
  return static_cast<int32_t>(delta);
}
