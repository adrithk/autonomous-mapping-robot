#pragma once

struct WheelSpeedControllerGains
{
  float proportional;
  float integral;
  float derivative;
  float feedForward;
};

class WheelSpeedController
{
public:
  WheelSpeedController(WheelSpeedControllerGains gains, float maximumOutput,
                       float integralLimit)
      : gains_(gains), maximumOutput_(maximumOutput),
        integralLimit_(integralLimit)
  {
  }

  float update(float targetSpeed, float measuredSpeed, float elapsedSeconds)
  {
    if (targetSpeed == 0.0f || elapsedSeconds <= 0.0f)
    {
      reset();
      return 0.0f;
    }

    const float error = targetSpeed - measuredSpeed;
    const float proposedIntegral =
        clamp(integral_ + error * elapsedSeconds, -integralLimit_, integralLimit_);
    const float derivative = hasPreviousError_
                                 ? (error - previousError_) / elapsedSeconds
                                 : 0.0f;

    float output = calculateOutput(targetSpeed, error, proposedIntegral, derivative);

    const bool saturatedHigh = output > maximumOutput_;
    const bool saturatedLow = output < -maximumOutput_;
    const bool pushesFurtherIntoSaturation =
        (saturatedHigh && error > 0.0f) || (saturatedLow && error < 0.0f);

    if (!pushesFurtherIntoSaturation)
    {
      integral_ = proposedIntegral;
    }
    else
    {
      output = calculateOutput(targetSpeed, error, integral_, derivative);
    }

    previousError_ = error;
    hasPreviousError_ = true;
    return clamp(output, -maximumOutput_, maximumOutput_);
  }

  void reset()
  {
    integral_ = 0.0f;
    previousError_ = 0.0f;
    hasPreviousError_ = false;
  }

private:
  static float clamp(float value, float minimum, float maximum)
  {
    if (value < minimum)
    {
      return minimum;
    }
    if (value > maximum)
    {
      return maximum;
    }
    return value;
  }

  float calculateOutput(float targetSpeed, float error, float integral,
                        float derivative) const
  {
    return gains_.feedForward * targetSpeed + gains_.proportional * error +
           gains_.integral * integral + gains_.derivative * derivative;
  }

  WheelSpeedControllerGains gains_;
  float maximumOutput_;
  float integralLimit_;
  float integral_ = 0.0f;
  float previousError_ = 0.0f;
  bool hasPreviousError_ = false;
};
