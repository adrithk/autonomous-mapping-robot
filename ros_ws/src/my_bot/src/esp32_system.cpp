#include "my_bot/serial_transport.hpp"
#include <hardware_interface/system_interface.hpp>
#include <hardware_interface/types/hardware_interface_type_values.hpp>
#include <pluginlib/class_list_macros.hpp>
#include <rclcpp/rclcpp.hpp>
#include <algorithm>
#include <array>
#include <cmath>
#include <set>
#include <stdexcept>
#include <vector>

namespace my_bot {
class Esp32System : public hardware_interface::SystemInterface {
  using Callback = hardware_interface::CallbackReturn;
  using Result = hardware_interface::return_type;
public:
  Callback on_init(const hardware_interface::HardwareInfo &info) override {
    if (SystemInterface::on_init(info)!=Callback::SUCCESS) return Callback::ERROR;
    try {
      if (info.joints.size()!=2) throw std::runtime_error("Exactly two wheel joints required");
      for (size_t i=0; i<2; ++i) {
        const auto &joint=info.joints[i];
        const std::string expected=i==0 ? "left_wheel_joint" : "right_wheel_joint";
        std::set<std::string> states;
        for (const auto &state : joint.state_interfaces) states.insert(state.name);
        if (joint.name!=expected || joint.command_interfaces.size()!=1 ||
            joint.command_interfaces[0].name!="velocity" || joint.state_interfaces.size()!=2 ||
            states!=std::set<std::string>{"position", "velocity"})
          throw std::runtime_error("Wheel joint names/order/interfaces do not match ESP32 adapter");
        const auto key=i==0 ? "left_counts_per_revolution" : "right_counts_per_revolution";
        const auto &text=info.hardware_parameters.at(key);
        size_t used=0; const double cpr=std::stod(text,&used);
        if (used!=text.size() || !std::isfinite(cpr) || cpr<=0)
          throw std::runtime_error("Invalid encoder calibration");
        radians_per_count_[i]=6.28318530717958647692/cpr;
        max_speed_=std::min(max_speed_, 4000*radians_per_count_[i]*0.999);
      }
      device_=info.hardware_parameters.at("serial_device");
      if (device_.empty() || device_[0]!='/') throw std::runtime_error("Set absolute serial_device path");
    } catch (const std::exception &e) { report(e); return Callback::ERROR; }
    return Callback::SUCCESS;
  }
  std::vector<hardware_interface::StateInterface> export_state_interfaces() override {
    std::vector<hardware_interface::StateInterface> result;
    for (size_t i=0;i<2;++i) {
      result.emplace_back(info_.joints[i].name,"position",&position_[i]);
      result.emplace_back(info_.joints[i].name,"velocity",&velocity_[i]);
    }
    return result;
  }
  std::vector<hardware_interface::CommandInterface> export_command_interfaces() override {
    std::vector<hardware_interface::CommandInterface> result;
    for (size_t i=0;i<2;++i) result.emplace_back(info_.joints[i].name,"velocity",&command_[i]);
    return result;
  }
  Callback on_configure(const rclcpp_lifecycle::State &) override {
    command_.fill(0); position_.fill(0); velocity_.fill(0); active_=false;
    return Callback::SUCCESS; // Serial opens only on explicit hardware activation.
  }
  Callback on_activate(const rclcpp_lifecycle::State &) override {
    try {
      transport_.connect(device_);
      previous_counts_=transport_.state().counts;
      command_.fill(0); velocity_.fill(0); active_=true;
      RCLCPP_INFO(rclcpp::get_logger("Esp32System"),
        "ESP32 v2 stop acknowledged; calibration is preliminary; latched status=0x%04x",
        transport_.state().status);
      return Callback::SUCCESS;
    } catch (const std::exception &e) { report(e); stop(); return Callback::ERROR; }
  }
  Callback on_deactivate(const rclcpp_lifecycle::State &) override { stop(); return Callback::SUCCESS; }
  Callback on_cleanup(const rclcpp_lifecycle::State &) override { stop(); return Callback::SUCCESS; }
  Callback on_shutdown(const rclcpp_lifecycle::State &) override { stop(); return Callback::SUCCESS; }
  Callback on_error(const rclcpp_lifecycle::State &) override { stop(); return Callback::SUCCESS; }
  Result read(const rclcpp::Time &, const rclcpp::Duration &) override {
    if (!active_) return Result::OK;
    try {
      transport_.receive(); transport_.check_health();
      const auto &state=transport_.state();
      for (size_t i=0;i<2;++i) {
        position_[i]+=count_delta(state.counts[i], previous_counts_[i])*radians_per_count_[i];
        velocity_[i]=state.speed[i]*radians_per_count_[i];
      }
      previous_counts_=state.counts;
      return Result::OK;
    } catch (const std::exception &e) { report(e); stop(); return Result::ERROR; }
  }
  Result write(const rclcpp::Time &, const rclcpp::Duration &) override {
    if (!active_) return Result::OK;
    try {
      if (!std::isfinite(command_[0]) || !std::isfinite(command_[1]))
        throw std::runtime_error("Nonfinite ROS wheel command");
      // Scale both wheels together to preserve curvature at the firmware bound.
      const double peak=std::max(std::abs(command_[0]), std::abs(command_[1]));
      const double scale=peak>max_speed_ ? max_speed_/peak : 1.0;
      transport_.command(command_[0]*scale,command_[1]*scale);
      return Result::OK;
    } catch (const std::exception &e) { report(e); stop(); return Result::ERROR; }
  }
private:
  void report(const std::exception &e) { RCLCPP_ERROR(rclcpp::get_logger("Esp32System"), "%s", e.what()); }
  void stop() { active_=false; command_.fill(0); velocity_.fill(0); transport_.disconnect(); }
  SerialTransport transport_;
  std::string device_;
  bool active_{false};
  double max_speed_{6.0};
  std::array<double,2> position_{}, velocity_{}, command_{}, radians_per_count_{};
  std::array<int32_t,2> previous_counts_{};
};
}
PLUGINLIB_EXPORT_CLASS(my_bot::Esp32System, hardware_interface::SystemInterface)
