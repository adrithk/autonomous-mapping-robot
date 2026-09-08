#pragma once
#include <array>
#include <chrono>
#include <cstdint>
#include <deque>
#include <string>

namespace my_bot {
struct EncoderState {
  uint32_t ack{}, milliseconds{};
  std::array<int32_t, 2> counts{}, speed{};
  std::array<int16_t, 2> pwm{};
  uint16_t status{};
};
uint16_t crc16(const std::string &payload);
std::string frame(const std::string &payload);
bool parse_state(const std::string &line, EncoderState &state);
int64_t count_delta(int32_t current, int32_t previous);

// Bounded, nonblocking serial I/O in read/write; only lifecycle handshake waits.
class SerialTransport {
public:
  using Clock = std::chrono::steady_clock;
  ~SerialTransport();
  SerialTransport() = default;
  SerialTransport(const SerialTransport &) = delete;
  SerialTransport &operator=(const SerialTransport &) = delete;
  void connect(const std::string &device, int startup_ms = 4000);
  void disconnect() noexcept;
  void receive();
  void command(double left, double right);
  void check_health() const;
  const EncoderState &state() const { return state_; }
  bool connected() const { return fd_ >= 0; }
private:
  void send(const std::string &payload);
  int fd_{-1};
  bool have_state_{false}, active_{false}, discarding_{false};
  EncoderState state_{};
  std::string incoming_;
  uint32_t sequence_{};
  uint16_t initial_status_{};
  Clock::time_point last_state_{};
  std::deque<std::pair<uint32_t, Clock::time_point>> pending_;
};
}
