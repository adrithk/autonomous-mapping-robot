// Load the installed plugin through the same registry used by ros2_control.
// No serial port is opened: activation remains a separate physical test.
#include <hardware_interface/system_interface.hpp>
#include <pluginlib/class_loader.hpp>
#include <rclcpp/rclcpp.hpp>
#include <cassert>
#include <iostream>

int main(int argc, char **argv)
{
  rclcpp::init(argc, argv);
  pluginlib::ClassLoader<hardware_interface::SystemInterface> loader(
    "hardware_interface", "hardware_interface::SystemInterface");
  {
    auto plugin = loader.createSharedInstance("my_bot/Esp32System");
    hardware_interface::HardwareInfo info{};
    info.name = "Esp32Drive";
    info.type = "system";
    info.hardware_parameters = {{"serial_device", "/dev/not-opened-by-this-test"},
      {"left_counts_per_revolution", "4185"}, {"right_counts_per_revolution", "4185"}};
    for (const auto *name : {"left_wheel_joint", "right_wheel_joint"}) {
      hardware_interface::ComponentInfo joint{};
      joint.name = name;
      joint.type = "joint";
      hardware_interface::InterfaceInfo velocity{};
      velocity.name = "velocity";
      hardware_interface::InterfaceInfo position{};
      position.name = "position";
      joint.command_interfaces.push_back(velocity);
      joint.state_interfaces = {position, velocity};
      info.joints.push_back(joint);
    }
    assert(plugin->on_init(info) == hardware_interface::CallbackReturn::SUCCESS);
    assert(plugin->on_configure(rclcpp_lifecycle::State()) ==
      hardware_interface::CallbackReturn::SUCCESS);
    auto states = plugin->export_state_interfaces();
    auto commands = plugin->export_command_interfaces();
    assert(states.size() == 4 && commands.size() == 2);
    assert(commands[0].get_name() == "left_wheel_joint/velocity");
    assert(commands[1].get_name() == "right_wheel_joint/velocity");
    for (const auto &state : states) assert(state.get_value() == 0.0);
    auto invalid = loader.createSharedInstance("my_bot/Esp32System");
    info.joints.pop_back();
    assert(invalid->on_init(info) == hardware_interface::CallbackReturn::ERROR);
  }
  rclcpp::shutdown();
  std::cout << "Plugin registry, initialization and interfaces passed\n";
}
