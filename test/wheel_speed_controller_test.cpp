#include "wheel_speed_controller.h"

#include <cassert>
#include <cmath>

namespace
{

bool approximatelyEqual(float first, float second, float tolerance = 0.001f)
{
  return std::fabs(first - second) <= tolerance;
}

} // namespace

int main()
{
  const WheelSpeedControllerGains gains{0.02f, 0.01f, 0.0f, 0.05f};
  WheelSpeedController controller(gains, 255.0f, 4000.0f);

  assert(approximatelyEqual(controller.update(0.0f, 0.0f, 0.02f), 0.0f));
  assert(approximatelyEqual(controller.update(1000.0f, 1000.0f, 0.02f), 50.0f));
  assert(controller.update(1000.0f, 0.0f, 0.02f) > 50.0f);

  controller.reset();
  assert(controller.update(-1000.0f, 0.0f, 0.02f) < 0.0f);

  controller.reset();
  assert(approximatelyEqual(controller.update(10000.0f, 0.0f, 0.02f), 255.0f));

  return 0;
}
