#!/usr/bin/env python3
"""Raised-wheel, forward one-revolution check using ROS encoder feedback.

Stop all teleop/Nav2 publishers first. Visual tyre marks independently check the
encoder calibration; reaching 2*pi in ROS alone does not prove that calibration.
"""
import math
import time
from pathlib import Path

JOINTS = ('left_wheel_joint', 'right_wheel_joint')
TARGET = 2 * math.pi
TOLERANCE = 0.05  # radians (about 3 degrees); not a measured accuracy guarantee


def wheel_targets(travel):
    if len(travel) != 2 or not all(math.isfinite(v) for v in travel):
        raise RuntimeError('Invalid encoder feedback')
    if any(v < -0.15 or v > TARGET + 0.20 for v in travel):
        raise RuntimeError('Wrong encoder direction or excessive overshoot')
    remaining = [TARGET - v for v in travel]
    return [0.0 if v <= TOLERANCE else min(2.5, 2.0 * v) for v in remaining]


def main():
    import rclpy
    import yaml
    from ament_index_python.packages import get_package_share_directory
    from geometry_msgs.msg import TwistStamped
    from sensor_msgs.msg import JointState
    from rclpy.qos import qos_profile_sensor_data

    config = Path(get_package_share_directory('my_bot')) / 'config/controllers_hardware.yaml'
    params = yaml.safe_load(config.read_text())['diff_drive_controller']['ros__parameters']
    radius, separation = params['wheel_radius'], params['wheel_separation']
    if not all(math.isfinite(v) and v > 0 for v in (radius, separation)):
        raise RuntimeError('Invalid controller geometry')
    rclpy.init()
    node = rclpy.create_node('wheel_revolution_test')
    topic = '/diff_drive_controller/cmd_vel'
    publisher = node.create_publisher(TwistStamped, topic, 10)
    feedback = None

    def receive(msg):
        nonlocal feedback
        try:
            indexes = [msg.name.index(name) for name in JOINTS]
            positions = [msg.position[i] for i in indexes]
            velocities = [msg.velocity[i] for i in indexes]
            stamp = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
            if all(math.isfinite(v) for v in positions + velocities):
                feedback = (positions, velocities, stamp, time.monotonic())
        except (ValueError, IndexError):
            pass

    subscription = node.create_subscription(JointState, '/joint_states', receive,
                                            qos_profile_sensor_data)

    def publish(wheels=(0.0, 0.0)):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = radius * (wheels[0] + wheels[1]) / 2
        msg.twist.angular.z = radius * (wheels[1] - wheels[0]) / separation
        publisher.publish(msg)

    def check_feedback():
        now = node.get_clock().now().nanoseconds * 1e-9
        if (feedback is None or time.monotonic() - feedback[3] > 0.3
                or not -0.1 <= now - feedback[2] <= 0.3):
            raise RuntimeError('Encoder feedback missing/stale; stopping')

    try:
        print('Keep wheels raised. Target: one FORWARD revolution of each wheel.', flush=True)
        deadline = time.monotonic() + 5
        while feedback is None or publisher.get_subscription_count() == 0:
            rclpy.spin_once(node, timeout_sec=0.05)
            if time.monotonic() > deadline:
                raise RuntimeError('Hardware controller/encoder feedback unavailable')
        # Allow discovery and obtain a stationary, fresh starting sample.
        deadline = time.monotonic() + 1
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.02)
        if node.count_publishers(topic) != 1:
            raise RuntimeError('Stop other WASD/Nav2 command publishers first')
        check_feedback()
        if any(abs(v) > 0.1 for v in feedback[1]):
            raise RuntimeError('Wheels must be stationary before the test')
        start = feedback[0][:]
        deadline = time.monotonic() + 20
        while True:
            rclpy.spin_once(node, timeout_sec=0.02)
            check_feedback()
            if node.count_publishers(topic) != 1:
                raise RuntimeError('Another motion publisher appeared')
            travel = [v - initial for v, initial in zip(feedback[0], start)]
            targets = wheel_targets(travel)
            if targets == [0.0, 0.0]:
                break
            if time.monotonic() > deadline:
                raise RuntimeError('20-second test timeout; stopping')
            publish(targets)
        # Send zero and measure final encoder travel after motion settles.
        deadline = time.monotonic() + 2
        stationary_since = None
        while True:
            publish()
            rclpy.spin_once(node, timeout_sec=0.02)
            check_feedback()
            now = time.monotonic()
            if all(abs(v) < 0.1 for v in feedback[1]):
                stationary_since = now if stationary_since is None else stationary_since
            else:
                stationary_since = None
            if stationary_since is not None and now - stationary_since >= 0.5:
                break
            if now > deadline:
                raise RuntimeError('Could not confirm stationary wheels; remove motor power')
        travel = [v - initial for v, initial in zip(feedback[0], start)]
        print('Encoder-estimated revolutions: left=%.4f right=%.4f' % tuple(v / TARGET for v in travel))
        if any(abs(v - TARGET) > TOLERANCE for v in travel):
            print('Outside target tolerance; inspect stopping/overshoot before repeating.')
        print('Compare tyre marks: physical rotation is NOT verified by encoder values alone.')
    finally:
        if rclpy.ok():
            for _ in range(10):
                publish()
                time.sleep(0.02)
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
