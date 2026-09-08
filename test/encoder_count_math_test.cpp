#include "encoder_count_math.h"
#include <cassert>
#include <cstdio>
#include <initializer_list>

int main()
{
  assert(encoderStep(INT32_MAX, true) == INT32_MIN);
  assert(encoderStep(INT32_MIN, false) == INT32_MAX);
  assert(encoderDelta(INT32_MIN, INT32_MAX) == 1);
  assert(encoderDelta(INT32_MAX, INT32_MIN) == -1);
  assert(encoderDelta(INT32_MIN + 79, INT32_MAX) == 80);
  assert(encoderDelta(INT32_MAX - 79, INT32_MIN) == -80);
  assert(encoderDelta(42, 42) == 0);
  for (int32_t start : {INT32_MIN, INT32_MAX, int32_t(0), int32_t(-123)}) {
    int32_t value = start;
    for (int i = 0; i < 100; ++i) value = encoderStep(value, true);
    assert(encoderDelta(value, start) == 100);
    for (int i = 0; i < 100; ++i) value = encoderStep(value, false);
    assert(value == start);
  }
  std::puts("Encoder rollover tests passed");
}
