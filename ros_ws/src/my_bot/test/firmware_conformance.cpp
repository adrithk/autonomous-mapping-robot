#include "ros_serial_protocol.h"
#include "my_bot/serial_transport.hpp"
#include <cassert>
#include <string>
int main() {
  RosSerialProtocol::Parser parser;
  RosSerialProtocol::CommandFrame command{};
  auto result=RosSerialProtocol::ParseResult::Incomplete;
  for (char c : my_bot::frame("C,2,123,1.250000,-2.500000")) result=parser.push(c,command);
  assert(result==RosSerialProtocol::ParseResult::CommandReady);
  assert(command.leftRadiansPerSecond==1.25 && command.rightRadiansPerSecond==-2.5);
  for (char c : my_bot::frame("X,2,124")) result=parser.push(c,command);
  assert(result==RosSerialProtocol::ParseResult::StopReady);
  char bytes[128];
  RosSerialProtocol::StateFrame state{124,500,4185,-4185,666,-666,0,0,0};
  auto n=RosSerialProtocol::formatStateFrame(bytes,sizeof(bytes),state);
  assert(n>0);
  my_bot::EncoderState feedback;
  assert(my_bot::parse_state(std::string(bytes,n-1),feedback));
  assert(feedback.ack==124 && feedback.counts[1]==-4185);
}
