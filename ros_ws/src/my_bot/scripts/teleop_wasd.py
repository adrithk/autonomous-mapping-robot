#!/usr/bin/env python3
"""Focused-terminal WASD teleoperation; stamped ROS commands with a wall-time deadman."""
import math
import os
import select
import sys
import termios
import time
import tty


class KeyboardCommand:
    def __init__(self, speed=0.1, turn=0.5):
        if not all(math.isfinite(v) and v > 0 for v in (speed, turn)):
            raise ValueError('speed and turn must be finite and positive')
        self.speed, self.turn = speed, turn
        self.motion = (0.0, 0.0)
        self.expires = 0.0

    def key(self, key, now):
        self.motion = {'w': (self.speed, 0.0), 's': (-self.speed, 0.0),
                       'a': (0.0, self.turn), 'd': (0.0, -self.turn)}.get(key, (0.0, 0.0))
        self.expires = now + 0.2

    def value(self, now):
        return self.motion if now < self.expires else (0.0, 0.0)


def main():
    import rclpy
    from geometry_msgs.msg import TwistStamped

    if not sys.stdin.isatty():
        raise SystemExit('Run teleop_wasd in an interactive Ubuntu/SSH terminal.')
    rclpy.init()
    node = rclpy.create_node('teleop_wasd')
    old_settings = termios.tcgetattr(sys.stdin.fileno())
    publisher = node.create_publisher(TwistStamped, 'cmd_vel', 10)

    def publish(motion):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = frame_id
        msg.twist.linear.x, msg.twist.angular.z = motion
        publisher.publish(msg)

    frame_id = 'base_link'
    try:
        command = KeyboardCommand(node.declare_parameter('speed', 0.1).value,
                                  node.declare_parameter('turn', 0.5).value)
        frame_id = node.declare_parameter('frame_id', 'base_link').value
        print('Hold W/A/S/D (lowercase): forward/left/back/right. Space or X: stop. Ctrl-C: quit.')
        print('Stops after 0.2 s without key repeats; initial keyboard repeat delay may pause motion.')
        tty.setcbreak(sys.stdin.fileno())
        while rclpy.ok():
            # Process /clock even while idle. Expiry uses monotonic time so pausing
            # Gazebo cannot preserve an old nonzero keyboard command.
            rclpy.spin_once(node, timeout_sec=0.0)
            if select.select([sys.stdin], [], [], 0.02)[0]:
                keys = os.read(sys.stdin.fileno(), 32)
                if not keys:
                    break
                for key in keys.decode('ascii', errors='replace'):
                    command.key(key, time.monotonic())
            publish(command.value(time.monotonic()))
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_settings)
        if rclpy.ok():
            publish((0.0, 0.0))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
