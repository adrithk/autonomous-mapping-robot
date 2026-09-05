#!/usr/bin/env python3
"""Send ROS-serial test frames without requiring ROS 2."""

import argparse
import time


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return crc


def frame(payload: str) -> bytes:
    encoded = payload.encode("ascii")
    return encoded + f"*{crc16_ccitt_false(encoded):04X}\n".encode("ascii")


def acknowledged_sequence(raw_frame: bytes) -> int | None:
    try:
        payload, checksum_text = raw_frame.rstrip(b"\r\n").rsplit(b"*", 1)
        if int(checksum_text, 16) != crc16_ccitt_false(payload):
            return None
        fields = payload.decode("ascii").split(",")
        if len(fields) != 12 or fields[0:2] != ["S", "1"]:
            return None
        return int(fields[2])
    except (ValueError, UnicodeDecodeError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("port", help="ESP32 serial device, preferably /dev/serial/by-id/...")
    parser.add_argument("--left", type=int, default=0, help="left target in counts/s")
    parser.add_argument("--right", type=int, default=0, help="right target in counts/s")
    parser.add_argument("--seconds", type=float, default=1.0)
    args = parser.parse_args()

    try:
        import serial
    except ImportError as error:
        raise SystemExit("Install pyserial first: python3 -m pip install pyserial") from error

    with serial.Serial(args.port, 115200, timeout=0.1) as connection:
        sequence = 1
        sync_deadline = time.monotonic() + 0.5
        while time.monotonic() < sync_deadline:
            response = connection.readline()
            acknowledged = acknowledged_sequence(response) if response else None
            if acknowledged is not None:
                sequence = (acknowledged + 1) & 0xFFFFFFFF
                break

        deadline = time.monotonic() + max(0.0, args.seconds)
        while time.monotonic() < deadline:
            connection.write(frame(f"C,1,{sequence},{args.left},{args.right}"))
            sequence = (sequence + 1) & 0xFFFFFFFF
            response = connection.readline()
            if response:
                print(response.decode("ascii", errors="replace").rstrip())
            time.sleep(0.02)
        connection.write(frame(f"X,1,{sequence}"))


if __name__ == "__main__":
    main()
