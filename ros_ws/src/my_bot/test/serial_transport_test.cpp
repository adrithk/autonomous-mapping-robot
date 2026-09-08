#include "my_bot/serial_transport.hpp"
#include <atomic>
#include <cassert>
#include <cmath>
#include <fcntl.h>
#include <iostream>
#include <limits>
#ifdef __APPLE__
#include <util.h>
#else
#include <pty.h>
#endif
#include <stdexcept>
#include <thread>
#include <unistd.h>
using namespace my_bot;
using namespace std::chrono_literals;

struct FakeEsp32 {
  int master{-1}, slave{-1};
  char path[256]{};
  std::atomic<bool> quit{false}, emit{true}, acknowledge{true}, reboot{false}, corrupt{false};
  std::atomic<int> stops{0}, commands{0};
  std::atomic<unsigned> status{0};
  std::thread worker;
  FakeEsp32() {
    assert(openpty(&master,&slave,path,nullptr,nullptr)==0);
    fcntl(master,F_SETFL,O_NONBLOCK);
    worker=std::thread([this] {
      uint32_t ack=0xfffffffdU, ms=1000;
      std::string input;
      auto next=std::chrono::steady_clock::now();
      while (!quit) {
        char buf[256]; const auto n=::read(master,buf,sizeof(buf));
        for (ssize_t i=0;i<n;++i) {
          if (buf[i]!='\n') { input+=buf[i]; continue; }
          const auto star=input.find('*');
          assert(star!=std::string::npos);
          assert(std::stoul(input.substr(star+1),nullptr,16)==crc16(input.substr(0,star)));
          assert(input.substr(1,3)==",2,");
          const uint32_t seq=std::stoul(input.substr(4));
          if (input[0]=='X') { ack=seq; ++stops; }
          else { assert(input[0]=='C'); if (acknowledge) ack=seq; ++commands; }
          input.clear();
        }
        if (std::chrono::steady_clock::now()>=next) {
          if (reboot.exchange(false)) {ms=0;ack=0;}
          ms+=50;
          if (emit) {
            auto line=frame("S,2,"+std::to_string(ack)+","+std::to_string(ms)+",4185,-4185,666,-666,0,0,"+std::to_string(status.load()));
            if (corrupt) line[0]='Q';
            // Split a telemetry frame across reads to exercise stream assembly.
            ::write(master,line.data(),7);
            ::write(master,line.data()+7,line.size()-7);
          }
          next=std::chrono::steady_clock::now()+50ms;
        }
        std::this_thread::sleep_for(2ms);
      }
    });
  }
  ~FakeEsp32() {quit=true;worker.join();::close(master);::close(slave);}
};
template<class F> bool fails(F fn) {try {fn();return false;}catch(const std::exception &){return true;}}
void cycles(SerialTransport &port, int count) {
  for (int i=0;i<count;++i) {port.receive();port.command(1.25,-2.5);std::this_thread::sleep_for(20ms);}
}
int main() {
  assert(crc16("123456789")==0x29b1);
  EncoderState state;
  auto good=frame("S,2,4294967295,200,4185,-4185,666,-666,0,0,0"); good.pop_back();
  assert(parse_state(good,state)); assert(state.counts[0]==4185 && state.counts[1]==-4185);
  assert(state.ack==0xffffffffU);
  for (const auto &payload : {"S,1,0,1,0,0,0,0,0,0,0", "S,2,0,1,0,0,0,0,0,0,65536",
      "S,2,0,1,2147483648,0,0,0,0,0,0", "S,2,0,1,0,0,0,0,0,0,0,", "S,2,0,1,0,0,0,0,0,0,nan"}) {
    auto line=frame(payload);line.pop_back();assert(!parse_state(line,state));
  }
  good[3]='1';assert(!parse_state(good,state));
  assert(count_delta(INT32_MIN,INT32_MAX)==1);
  assert(count_delta(INT32_MAX,INT32_MIN)==-1);
  assert(count_delta(-4185,0)==-4185);
  {
    FakeEsp32 fake; SerialTransport port; port.connect(fake.path,1000);
    assert(fake.stops>=1); cycles(port,20); assert(fake.commands>=19);
    assert(fails([&]{port.command(NAN,0);}));
    assert(fails([&]{port.command(6.01,0);}));
    const int before=fake.stops;port.disconnect();std::this_thread::sleep_for(30ms);
    assert(fake.stops>before);
    port.connect(fake.path,1000);cycles(port,5); // Retained ACK, no ESP reboot required.
    fake.acknowledge=false;
    assert(fails([&]{cycles(port,20);})); // Fresh feedback alone cannot hide lost commands.
  }
  {
    FakeEsp32 fake; SerialTransport port;port.connect(fake.path,1000);cycles(port,3);
    fake.corrupt=true;
    assert(fails([&]{cycles(port,20);})); // CRC failure cannot refresh telemetry freshness.
  }
  {
    FakeEsp32 fake;SerialTransport port;port.connect(fake.path,1000);cycles(port,3);
    fake.reboot=true;
    assert(fails([&]{cycles(port,10);}));
  }
  {
    FakeEsp32 fake;fake.emit=false;SerialTransport port;
    assert(fails([&]{port.connect(fake.path,150);})); assert(!port.connected());
  }
  {
    FakeEsp32 fake;SerialTransport port;port.connect(fake.path,1000);cycles(port,3);
    fake.emit=false;assert(fails([&]{cycles(port,20);}));
    port.disconnect();assert(fails([&]{port.command(1,1);}));
  }
  {
    FakeEsp32 fake;SerialTransport port;port.connect(fake.path,1000);cycles(port,3);
    fake.status=16;assert(fails([&]{cycles(port,10);}));
  }
  {
    FakeEsp32 fake;SerialTransport port;port.connect(fake.path,1000);
    std::this_thread::sleep_for(250ms);
    assert(fails([&]{port.receive();})); // Buffered telemetry cannot conceal a host stall.
  }
  std::cout << "Protocol, wraparound, handshake, reconnect, stale ACK/CRC and reboot tests passed\n";
}
