#include "my_bot/serial_transport.hpp"
#include <algorithm>
#include <cerrno>
#include <charconv>
#include <cmath>
#include <fcntl.h>
#include <iomanip>
#include <locale>
#include <sstream>
#include <stdexcept>
#include <sys/file.h>
#include <termios.h>
#include <thread>
#include <unistd.h>
#include <vector>

namespace my_bot {
namespace {
bool newer(uint32_t a, uint32_t b) { return a != b && uint32_t(a-b) < 0x80000000U; }
template<class T> bool integer(const std::string &s, T &out, int base = 10) {
  if (s.empty()) return false;
  const auto result = std::from_chars(s.data(), s.data()+s.size(), out, base);
  return result.ec == std::errc{} && result.ptr == s.data()+s.size();
}
}
uint16_t crc16(const std::string &payload) {
  uint16_t crc = 0xffff;
  for (unsigned char byte : payload) {
    crc ^= uint16_t(byte) << 8;
    for (int i=0; i<8; ++i) crc = crc & 0x8000 ? (crc << 1)^0x1021 : crc << 1;
  }
  return crc;
}
std::string frame(const std::string &payload) {
  std::ostringstream out;
  out.imbue(std::locale::classic());
  out << payload << '*' << std::uppercase << std::hex << std::setw(4)
      << std::setfill('0') << crc16(payload) << '\n';
  return out.str();
}
bool parse_state(const std::string &line, EncoderState &state) {
  const auto star = line.find('*');
  if (line.size() > 127 || star == std::string::npos || line.size()-star != 5) return false;
  uint16_t crc;
  if (!integer(line.substr(star+1), crc, 16) || crc != crc16(line.substr(0, star))) return false;
  std::vector<std::string> fields;
  std::istringstream input(line.substr(0, star));
  for (std::string token; std::getline(input, token, ',');) fields.push_back(token);
  if (fields.size()!=11 || fields[0]!="S" || fields[1]!="2" || line[star-1]==',') return false;
  EncoderState result;
  if (!integer(fields[2], result.ack) || !integer(fields[3], result.milliseconds) ||
      !integer(fields[4], result.counts[0]) || !integer(fields[5], result.counts[1]) ||
      !integer(fields[6], result.speed[0]) || !integer(fields[7], result.speed[1]) ||
      !integer(fields[8], result.pwm[0]) || !integer(fields[9], result.pwm[1]) ||
      !integer(fields[10], result.status)) return false;
  state = result;
  return true;
}
int64_t count_delta(int32_t current, int32_t previous) {
  const uint32_t delta = uint32_t(current)-uint32_t(previous);
  return delta <= 0x7fffffffU ? int64_t(delta) : int64_t(delta)-0x100000000LL;
}
SerialTransport::~SerialTransport() { disconnect(); }
void SerialTransport::send(const std::string &payload) {
  const auto bytes = frame(payload);
  if (fd_ < 0 || bytes.size()>127 || ::write(fd_, bytes.data(), bytes.size()) != ssize_t(bytes.size()))
    throw std::runtime_error("ESP32 serial write failed/partial; restart bringup");
}
void SerialTransport::connect(const std::string &device, int startup_ms) {
  disconnect();
  fd_ = ::open(device.c_str(), O_RDWR | O_NOCTTY | O_NONBLOCK);
  if (fd_ < 0) throw std::runtime_error("Cannot open ESP32 serial device: " + device);
  try {
    if (flock(fd_, LOCK_EX | LOCK_NB) < 0) throw std::runtime_error("ESP32 device is already locked");
    termios options{};
    if (tcgetattr(fd_, &options) != 0) throw std::runtime_error("Cannot read serial settings");
    cfmakeraw(&options);
    cfsetispeed(&options, B115200); cfsetospeed(&options, B115200);
    options.c_cflag |= CLOCAL | CREAD;
    options.c_cflag &= ~(CSTOPB | PARENB | CRTSCTS);
    options.c_cc[VMIN]=0; options.c_cc[VTIME]=0;
    if (tcsetattr(fd_, TCSANOW, &options)!=0 || tcflush(fd_, TCIOFLUSH)!=0)
      throw std::runtime_error("Cannot configure serial device");
    have_state_=false; active_=false; discarding_=false; incoming_.clear(); pending_.clear();
    const auto deadline=Clock::now()+std::chrono::milliseconds(startup_ms);
    auto last_stop=Clock::time_point{};
    bool sent_stop=false;
    uint32_t stop_sequence=0, stop_milliseconds=0;
    while (Clock::now()<deadline) {
      receive();
      if (have_state_ && sent_stop && state_.ack==stop_sequence &&
          newer(state_.milliseconds, stop_milliseconds) && state_.pwm[0]==0 && state_.pwm[1]==0) {
        sequence_=stop_sequence; initial_status_=state_.status; active_=true;
        return;
      }
      if (have_state_ && Clock::now()-last_stop>std::chrono::milliseconds(100)) {
        stop_sequence=state_.ack+1; stop_milliseconds=state_.milliseconds;
        send("X,2,"+std::to_string(stop_sequence));
        sent_stop=true; last_stop=Clock::now();
      }
      std::this_thread::sleep_for(std::chrono::milliseconds(5));
    }
    throw std::runtime_error("No fresh version-2 stop acknowledgement from ESP32");
  } catch (...) { disconnect(); throw; }
}
void SerialTransport::disconnect() noexcept {
  if (fd_ >= 0) {
    // Best effort only. Lost USB/power or a partial write still relies on ESP32 watchdog.
    try { if (have_state_) send("X,2,"+std::to_string(active_ ? sequence_+1 : state_.ack+1)); } catch (...) {}
    ::close(fd_);
  }
  fd_=-1; active_=false; have_state_=false; pending_.clear(); incoming_.clear();
}
void SerialTransport::receive() {
  if (fd_<0) throw std::runtime_error("ESP32 serial connection is closed");
  if (active_ && Clock::now()-last_state_>std::chrono::milliseconds(200))
    throw std::runtime_error("Host feedback loop stalled; restart bringup");
  // Limit total work per 50 Hz controller iteration, including malformed streams.
  std::array<char, 512> bytes{};
  for (int batch=0; batch<8; ++batch) {
    const auto n=::read(fd_, bytes.data(), bytes.size());
    if (n<0) {
      if (errno==EAGAIN || errno==EWOULDBLOCK || errno==EINTR) break;
      throw std::runtime_error("ESP32 serial read failed");
    }
    if (n==0) break;
    for (ssize_t i=0; i<n; ++i) {
      const char c=bytes[i];
      if (c=='\r') continue;
      if (c!='\n') {
        if (incoming_.size()>=127) { discarding_=true; incoming_.clear(); }
        if (!discarding_) incoming_+=c;
        continue;
      }
      EncoderState next;
      const bool valid=!discarding_ && parse_state(incoming_, next);
      incoming_.clear(); discarding_=false;
      if (!valid) continue;  // Invalid traffic never refreshes freshness.
      if (active_ && have_state_) {
        if (next.milliseconds==state_.milliseconds) continue;
        if (!newer(next.milliseconds, state_.milliseconds))
          throw std::runtime_error("ESP32 reboot/time regression; restart bringup");
        if (newer(next.ack, sequence_) || (next.ack!=state_.ack && !newer(next.ack, state_.ack)))
          throw std::runtime_error("Unexpected ESP32 acknowledgement; restart bringup");
        if ((next.status & ~initial_status_) != 0)
          throw std::runtime_error("New ESP32 status fault; restart bringup");
      }
      state_=next; have_state_=true; last_state_=Clock::now();
      while (!pending_.empty() && (next.ack==pending_.front().first || newer(next.ack,pending_.front().first)))
        pending_.pop_front();
    }
  }
}
void SerialTransport::check_health() const {
  const auto timeout=std::chrono::milliseconds(200);
  if (!active_ || !have_state_ || Clock::now()-last_state_>timeout)
    throw std::runtime_error("ESP32 telemetry stale or hardware inactive");
  if (!pending_.empty() && Clock::now()-pending_.front().second>timeout)
    throw std::runtime_error("ESP32 command acknowledgements stalled");
}
void SerialTransport::command(double left, double right) {
  check_health();
  if (!std::isfinite(left) || !std::isfinite(right) || std::abs(left)>6.0 || std::abs(right)>6.0)
    throw std::runtime_error("Invalid wheel rad/s command (maximum 6.0)");
  if (pending_.size()>=32) throw std::runtime_error("ESP32 acknowledgement queue full");
  std::ostringstream payload;
  payload.imbue(std::locale::classic());
  payload << "C,2," << ++sequence_ << ',' << std::fixed << std::setprecision(6) << left << ',' << right;
  send(payload.str()); pending_.emplace_back(sequence_,Clock::now());
}
}
