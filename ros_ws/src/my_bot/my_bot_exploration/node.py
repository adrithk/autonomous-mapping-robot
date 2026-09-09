"""ROS adapter: frontier goals through Nav2, cancellation, and SaveMap lifecycle."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
import uuid

import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.clock import Clock, ClockType
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, qos_profile_sensor_data
from rclpy.time import Time
from geometry_msgs.msg import PoseStamped
from lifecycle_msgs.srv import GetState
from nav_msgs.msg import OccupancyGrid, Odometry
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from nav2_msgs.srv import GetCostmap, SaveMap
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
from std_srvs.srv import Trigger
from tf2_ros import Buffer, TransformListener, TransformException
from visualization_msgs.msg import Marker, MarkerArray
from .core import Grid, frontiers, safe_at, Exclusions, CompletionWindow, ActionGate, failure_kind


def stamp_seconds(stamp):
    return stamp.sec + stamp.nanosec*1e-9


def grid_from(info, data, raw=False):
    q = info.origin.orientation
    yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
    if abs(q.x) > 1e-5 or abs(q.y) > 1e-5:
        raise ValueError('Only planar map origins are supported')
    width, height = (info.size_x, info.size_y) if raw else (info.width, info.height)
    return Grid(np.asarray(data, dtype=np.int16).reshape(height, width),
                info.resolution, info.origin.position.x, info.origin.position.y, yaw)


class Explorer(Node):
    def __init__(self):
        super().__init__('exploration_manager')
        defaults = dict(autostart=True, map_frame='map', base_frame='base_link',
                        odom_frame='odom', robot_radius=.22, minimum_frontier_size=.15, viewpoint_distance=.8,
                        sensor_timeout=5.0, map_timeout=10.0, startup_timeout=120.0,
                        action_timeout=15.0, goal_timeout=180.0, cooldown=30.0,
                        settle_time=2.0, stationary_time=1.0, stop_timeout=15.0,
                        save_timeout=20.0, output_dir='~/autonomous-mapping-robot/ros_ws/maps')
        self.p = {k: self.declare_parameter(k, v).value for k, v in defaults.items()}
        for key, default in defaults.items():
            if isinstance(default, float) and (not math.isfinite(self.p[key]) or self.p[key] <= 0):
                raise ValueError(f'{key} must be finite and positive')
        self.tf = Buffer()
        self.listener = TransformListener(self.tf, self)
        durable = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                             durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.status_pub = self.create_publisher(String, '/exploration/status', durable)
        self.markers = self.create_publisher(MarkerArray, '/exploration/markers', durable)
        self.create_subscription(OccupancyGrid, '/map', self.on_map, durable)
        self.create_subscription(LaserScan, '/scan', self.on_scan, qos_profile_sensor_data)
        self.create_subscription(Odometry, '/diff_drive_controller/odom', self.on_odom, qos_profile_sensor_data)
        self.plan_client = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.nav_client = ActionClient(self, NavigateToPose, '/navigate_to_pose')
        self.cost_client = self.create_client(GetCostmap, '/global_costmap/get_costmap')
        self.save_client = self.create_client(SaveMap, '/exploration_map_saver/save_map')
        names = ('slam_toolbox', 'controller_server', 'planner_server', 'bt_navigator',
                 'behavior_server', 'velocity_smoother', 'collision_monitor', 'exploration_map_saver')
        self.life = {n: self.create_client(GetState, f'/{n}/get_state') for n in names}
        self.life_pending, self.life_values = {}, {}
        self.cost_pending, self.cost_stamp = None, -math.inf
        self.grid, self.costmap = None, None
        self.receipts, self.stamps = {}, {}
        self.map_sequence = 0
        self.robot = (0.0, 0.0)
        self.last_ros_time = None
        self.gate, self.operation = ActionGate(), None
        self.exclusions = Exclusions(self.p['cooldown'])
        self.window = CompletionWindow()
        self.state, self.reason = 'STOPPED', 'Not started'
        self.target = None
        self.candidates = []
        self.pending_finish = None
        self.settle_until, self.settle_sequence = 0.0, 0
        self.stationary_since = None
        self.save_future, self.saved_map, self.mission_dir = None, None, None
        self.goal_count, self.failed_goals = 0, 0
        self.epoch = 0
        self.abort_launch = False
        self.create_service(Trigger, '/exploration/start', self.start_service)
        self.create_service(Trigger, '/exploration/stop', self.stop_service)
        self.create_service(Trigger, '/exploration/retry_save', self.retry_save)
        # Steady timer keeps cancellation/fault handling alive when /clock stops.
        self.timer = self.create_timer(1.0, self.tick, clock=Clock(clock_type=ClockType.STEADY_TIME))
        if self.p['autostart']:
            self.start()
        else:
            self.publish()

    def ros_now(self):
        return self.get_clock().now().nanoseconds*1e-9

    def set_state(self, state, reason):
        if (state, reason) != (self.state, self.reason):
            self.get_logger().info(f'{state}: {reason}')
        self.state, self.reason = state, reason
        self.publish()

    def start(self):
        self.epoch += 1
        self.exclusions = Exclusions(self.p['cooldown'])
        self.window.reset()
        self.target, self.pending_finish = None, None
        self.started = time.monotonic()
        self.goal_count = self.failed_goals = 0
        self.mission_dir = self.saved_map = None
        self.set_state('WAITING', 'Waiting for live SLAM, Nav2, sensors and map TF')

    def start_service(self, request, response):
        if self.gate.ticket is not None or self.save_future is not None or self.state not in ('STOPPED', 'FAULTED', 'COMPLETE', 'PARTIAL'):
            response.success, response.message = False, 'Stop the current mission or resolve the outstanding action/save first'
        else:
            self.start()
            response.success, response.message = True, 'Waiting for readiness; uses the current map (relaunch for a fresh map)'
        return response

    def stop_service(self, request, response):
        if self.state in ('STOPPED', 'COMPLETE', 'PARTIAL', 'FAULTED') and self.gate.ticket is None:
            response.success, response.message = True, 'No exploration goal is active'
            return response
        if self.state in ('SAVING', 'SAVE_FAILED'):
            response.success, response.message = False, 'Robot already stopping/stopped; let save finish or use retry_save'
        else:
            self.stop('STOPPED', 'Stopped by user')
            response.success, response.message = True, 'Cancellation requested; wait for STOPPED status'
        return response

    def retry_save(self, request, response):
        if self.state != 'SAVE_FAILED' or self.save_future is not None:
            response.success, response.message = False, 'No resolved failed save to retry'
        else:
            self.stop(self.final_kind, 'Retrying map save')
            response.success, response.message = True, 'Waiting for stationary odometry before saving'
        return response

    def record(self, key, stamp):
        self.receipts[key] = time.monotonic()
        self.stamps[key] = stamp_seconds(stamp)

    def on_map(self, msg):
        try:
            if msg.header.frame_id != self.p['map_frame']:
                raise ValueError('Map frame does not match configuration')
            self.grid = grid_from(msg.info, msg.data)
            self.map_sequence += 1
            self.record('map', msg.header.stamp)
        except (ValueError, TypeError) as exc:
            self.fault(str(exc))

    def on_scan(self, msg):
        # Empty/no-valid-return messages are not evidence of a working scanner.
        if msg.header.frame_id and msg.ranges and any(math.isfinite(v) and msg.range_min <= v <= msg.range_max for v in msg.ranges):
            self.record('scan', msg.header.stamp)
            self.scan_frame = msg.header.frame_id

    def on_odom(self, msg):
        if msg.header.frame_id != self.p['odom_frame'] or msg.child_frame_id != self.p['base_frame']:
            self.fault('Odometry frame mismatch')
            return
        values = (msg.twist.twist.linear.x, msg.twist.twist.linear.y, msg.twist.twist.angular.z)
        if not all(math.isfinite(v) for v in values):
            self.fault('Nonfinite odometry')
            return
        self.record('odom', msg.header.stamp)
        if math.hypot(*values[:2]) < .01 and abs(values[2]) < .03:
            if self.stationary_since is None:
                self.stationary_since = time.monotonic()
        else:
            self.stationary_since = None

    def poll_dependencies(self, now):
        for name, client in self.life.items():
            if now-self.life_values.get(name, (False, -math.inf))[1] < 2:
                continue
            if name in self.life_pending:
                if now-self.life_pending[name][1] > 5:
                    self.life_values.pop(name, None)
                continue
            if client.service_is_ready():
                future = client.call_async(GetState.Request())
                self.life_pending[name] = (future, now)
                def done(f, name=name):
                    self.life_pending.pop(name, None)
                    try:
                        self.life_values[name] = (f.result().current_state.id == 3, time.monotonic())
                    except Exception:
                        self.life_values[name] = (False, time.monotonic())
                future.add_done_callback(done)
        # Read authoritative full costmap via service; avoids missing incremental
        # updates after a late subscriber joins. Only selection needs this snapshot.
        if self.state not in ('WAITING', 'SELECTING', 'SETTLING'):
            return
        if self.cost_pending is not None or not self.cost_client.service_is_ready():
            return
        self.cost_pending = self.cost_client.call_async(GetCostmap.Request())
        def received(f):
            self.cost_pending = None
            try:
                msg = f.result().map
                if msg.header.frame_id != self.p['map_frame']:
                    raise ValueError('Global costmap is not in map frame')
                self.costmap = grid_from(msg.metadata, msg.data, raw=True)
                self.cost_stamp = time.monotonic()
            except Exception as exc:
                self.fault(f'Costmap request failed: {exc}')
        self.cost_pending.add_done_callback(received)

    def health_error(self, now):
        for key in ('scan', 'odom', 'map'):
            timeout = self.p['map_timeout'] if key == 'map' else self.p['sensor_timeout']
            if now-self.receipts.get(key, -math.inf) > timeout:
                return f'Missing/stale {key}'
            age = self.ros_now()-self.stamps[key]
            if age < -1.5 or age > timeout:
                return f'{key} timestamp is not current: check clocks/lag'
        if not all(self.life_values.get(n, (False, 0))[0] and now-self.life_values[n][1] < 5 for n in self.life):
            return 'SLAM/Nav2/map saver lifecycle not active or unresponsive'
        if not self.nav_client.server_is_ready() or not self.plan_client.server_is_ready():
            return 'Nav2 action server unavailable'
        try:
            tf = self.tf.lookup_transform(self.p['map_frame'], self.p['base_frame'], Time())
            if abs(self.ros_now()-stamp_seconds(tf.header.stamp)) > self.p['sensor_timeout']:
                return 'Robot map transform is stale'
            self.tf.lookup_transform(self.p['base_frame'], self.scan_frame,
                                     Time(seconds=self.stamps['scan']))
            self.robot = (tf.transform.translation.x, tf.transform.translation.y)
            if not all(math.isfinite(v) for v in self.robot):
                return 'Nonfinite robot pose'
            if self.grid is None or not 0 <= self.grid.sample(*self.robot) <= 25:
                return 'Robot is not in known free map space'
        except (TransformException, ValueError) as exc:
            return f'TF unavailable: {exc}'
        return None

    def fault(self, reason):
        if self.state in ('STOPPED', 'COMPLETE', 'PARTIAL', 'SAVE_FAILED'):
            return
        self.stop('FAULTED', reason)

    def stop(self, outcome, reason):
        self.pending_finish = (outcome, reason)
        self.gate.stop()
        self.window.reset()
        self.stop_started = time.monotonic()
        self.stationary_since = None  # require new stationary feedback after cancel
        self.set_state('STOPPING', reason)
        self.cancel_action()

    def cancel_action(self):
        op = self.operation
        if op and op.get('handle') and not op.get('cancel_sent'):
            op['cancel_sent'] = True
            try:
                op['handle'].cancel_goal_async()
            except Exception as exc:
                self.get_logger().error(f'Cancellation failed: {exc}')

    def pose(self, view):
        msg = PoseStamped()
        msg.header.frame_id = self.p['map_frame']
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.pose.position.x, msg.pose.position.y = view.x, view.y
        msg.pose.orientation.z, msg.pose.orientation.w = math.sin(view.yaw/2), math.cos(view.yaw/2)
        return msg

    def send_action(self, kind, view):
        ticket = self.gate.begin()
        op = dict(ticket=ticket, kind=kind, view=view, started=time.monotonic(), handle=None)
        self.operation = op
        client = self.plan_client if kind == 'plan' else self.nav_client
        goal = ComputePathToPose.Goal() if kind == 'plan' else NavigateToPose.Goal()
        if kind == 'plan':
            goal.goal, goal.planner_id, goal.use_start = self.pose(view), 'GridBased', False
        else:
            goal.pose = self.pose(view)
            self.goal_count += 1
        self.target = view
        self.set_state('PLANNING' if kind == 'plan' else 'NAVIGATING', 'Checking viewpoint' if kind == 'plan' else 'Exploring frontier')
        try:
            future = client.send_goal_async(goal)
            future.add_done_callback(lambda f: self.accepted(op, f))
        except Exception as exc:
            self.gate.finish(ticket)
            self.operation = None
            self.fault(f'Action send failed: {exc}')

    def accepted(self, op, future):
        try:
            handle = future.result()
        except Exception as exc:
            if self.gate.current(op['ticket']):
                self.gate.finish(op['ticket'])
                self.operation = None
                self.fault(f'Action acceptance failed: {exc}')
            return
        if not self.gate.current(op['ticket']):
            if handle.accepted:
                handle.cancel_goal_async()
            return
        if not handle.accepted:
            deliver = self.gate.finish(op['ticket'])
            self.operation = None
            if deliver:
                self.fault('Nav2 rejected goal; readiness or goal ownership changed')
            return
        op['handle'] = handle
        op['accepted_at'] = time.monotonic()
        handle.get_result_async().add_done_callback(lambda f: self.result(op, f))
        if self.gate.cancel:
            self.cancel_action()

    def result(self, op, future):
        if not self.gate.current(op['ticket']):
            return
        deliver = self.gate.finish(op['ticket'])
        self.operation = None
        if not deliver:
            return
        try:
            result = future.result()
            outcome = failure_kind(result.status, result.result.error_code, op['kind'] == 'plan')
            if outcome == 'fault':
                self.fault(f'Nav2 {op["kind"]} error {result.result.error_code}: {result.result.error_msg}')
            elif outcome != 'success':
                self.failed_goals += 1
                self.exclusions.add(op['view'], time.monotonic())
                self.set_state('SELECTING', 'Viewpoint failed; trying alternatives')
            elif op['kind'] == 'plan':
                if time.monotonic()-self.cost_stamp > 5:
                    self.set_state('SELECTING', 'Costmap snapshot expired; rechecking before navigation')
                    return
                path = result.result.path.poses
                if not path:
                    raise ValueError('Successful plan returned an empty path')
                endpoint = path[-1].pose.position
                if not safe_at(self.grid, self.costmap, self.p['robot_radius'], endpoint.x, endpoint.y):
                    self.exclusions.add(op['view'], time.monotonic())
                    self.set_state('SELECTING', 'Planner fallback endpoint lacks safe clearance')
                elif self.health_error(time.monotonic()):
                    self.fault('Readiness lost while planning')
                else:
                    # Nav2 replans this checked viewpoint normally while driving.
                    self.send_action('navigate', op['view'])
            else:
                self.exclusions.add(op['view'], time.monotonic())
                self.settle_until = time.monotonic()+self.p['settle_time']
                self.settle_sequence = self.map_sequence
                self.set_state('SETTLING', 'Waiting for new scans/map after arrival')
        except Exception as exc:
            self.fault(f'Action result failed: {exc}')

    def tick(self):
        now = time.monotonic()
        try:
            self._tick(now)
        except Exception as exc:
            self.fault(f'Explorer error: {exc}')
        self.publish()
        if self.abort_launch:
            raise RuntimeError('Stop could not be confirmed; shutting down the exploration launch')

    def _tick(self, now):
        if self.state in ('STOPPED', 'COMPLETE', 'PARTIAL', 'FAULTED', 'SAVE_FAILED'):
            return
        if self.state == 'SAVING':
            if now-self.save_started > self.p['save_timeout']:
                self.set_state('SAVE_FAILED', 'Save response timed out; wait for resolution before retry')
            return
        if self.state == 'STOPPING':
            self.cancel_action()
            if self.gate.ticket is None and now-self.receipts.get('odom', -math.inf) < self.p['sensor_timeout'] and self.stationary_since is not None and now-self.stationary_since >= self.p['stationary_time']:
                outcome, reason = self.pending_finish
                if outcome in ('COMPLETE', 'PARTIAL'):
                    self.final_kind = outcome
                    self.begin_save()
                else:
                    self.set_state(outcome, reason)
            elif now-self.stop_started > self.p['stop_timeout']:
                # Retain the action lease: no restart while its outcome is unknown.
                self.set_state('FAULTED', 'Stop not confirmed; shutting down bringup')
                self.abort_launch = True
            return
        self.poll_dependencies(now)
        error = self.health_error(now)
        current = self.ros_now()
        if self.last_ros_time is not None and current < self.last_ros_time-.01:
            error = 'ROS clock moved backwards; relaunch the mission'
        self.last_ros_time = current
        if self.state == 'WAITING':
            if not error and self.costmap is not None and now-self.cost_stamp < 5:
                self.set_state('SELECTING', 'Ready')
            elif now-self.started > self.p['startup_timeout']:
                self.fault(error or 'No fresh costmap')
            return
        if error:
            self.fault(error)
            return
        if self.operation:
            op = self.operation
            timeout = self.p['goal_timeout'] if op['kind'] == 'navigate' and op.get('handle') else self.p['action_timeout']
            if now-op['started'] > timeout:
                self.fault(f'{op["kind"]} timed out; cancelling')
            return
        if self.state == 'SETTLING':
            if now < self.settle_until or self.map_sequence <= self.settle_sequence:
                return
            self.set_state('SELECTING', 'Map updated')
        if now-self.cost_stamp > 5:
            self.fault('Global costmap service is stale')
            return
        self.candidates, cluster_count = frontiers(self.grid, self.costmap, self.robot,
            self.p['robot_radius'], self.p['minimum_frontier_size'], self.p['viewpoint_distance'])
        choices = [v for v in self.candidates if not self.exclusions.blocked(v, now, self.grid)]
        if choices:
            self.window.reset()
            self.send_action('plan', choices[0])
        else:
            conclusion = 'COMPLETE' if cluster_count == 0 else 'PARTIAL'
            if cluster_count and self.exclusions.waiting_retry(now):
                self.window.reset()
                return
            if self.window.observe(conclusion, self.map_sequence, now):
                self.stop(conclusion, 'No meaningful frontiers remain' if conclusion == 'COMPLETE' else 'Remaining frontiers have no available safe/reachable viewpoint')

    def begin_save(self):
        if not self.save_client.service_is_ready():
            self.set_state('SAVE_FAILED', 'Map saver unavailable; use retry_save')
            return
        try:
            if self.mission_dir is None:
                root = Path(self.p['output_dir']).expanduser().resolve()
                self.mission_dir = root / (datetime.now(timezone.utc).strftime('explore_%Y%m%dT%H%M%SZ_')+uuid.uuid4().hex[:8])
                self.mission_dir.mkdir(parents=True, exist_ok=False)
            # Unique attempt names avoid overwriting a late/partial save.
            self.save_base = self.mission_dir / ('map_'+uuid.uuid4().hex[:8])
            req = SaveMap.Request()
            req.map_topic, req.map_url = '/map', str(self.save_base)
            req.image_format, req.map_mode = 'pgm', 'trinary'
            req.free_thresh, req.occupied_thresh = .25, .65
            self.save_started = time.monotonic()
            self.save_future = self.save_client.call_async(req)
            self.save_future.add_done_callback(self.saved)
            self.set_state('SAVING', 'Robot stationary; saving map')
        except Exception as exc:
            self.save_future = None
            self.set_state('SAVE_FAILED', str(exc))

    def saved(self, future):
        if self.save_future is not future:
            return
        self.save_future = None
        if self.state not in ('SAVING', 'SAVE_FAILED'):
            return  # A fault superseded this request; do not promote it to completion.
        try:
            if not future.result().result:
                raise RuntimeError('Map saver returned failure')
            yaml_file, image_file = self.save_base.with_suffix('.yaml'), self.save_base.with_suffix('.pgm')
            if not all(p.is_file() and p.stat().st_size > 0 for p in (yaml_file, image_file)):
                raise RuntimeError('Map files missing/empty on explorer host')
            self.saved_map = str(yaml_file)
            summary = dict(outcome=self.final_kind, reason=self.pending_finish[1], map=self.saved_map,
                           goals=self.goal_count, failed_goals=self.failed_goals,
                           elapsed_seconds=round(time.monotonic()-self.started, 2),
                           remaining_frontiers=len(self.candidates), physical_validation=False)
            (self.mission_dir/'mission.json').write_text(json.dumps(summary, indent=2)+'\n')
            self.set_state(self.final_kind, self.pending_finish[1]+'; map saved')
        except Exception as exc:
            self.set_state('SAVE_FAILED', str(exc))

    def publish(self):
        if not hasattr(self, 'status_pub'):
            return
        self.status_pub.publish(String(data=json.dumps(dict(state=self.state, reason=self.reason,
            goals=self.goal_count, failed_goals=self.failed_goals, saved_map=self.saved_map))))
        array = MarkerArray()
        clear = Marker()
        clear.action = Marker.DELETEALL
        array.markers.append(clear)
        for i, v in enumerate(self.candidates):
            m = Marker()
            m.header.frame_id = self.p['map_frame']
            m.header.stamp = self.get_clock().now().to_msg()
            m.ns, m.id, m.type, m.action = 'viewpoints', i, Marker.SPHERE, Marker.ADD
            m.pose.position.x, m.pose.position.y, m.pose.position.z = v.x, v.y, .05
            m.pose.orientation.w = 1.0
            m.scale.x = m.scale.y = m.scale.z = .06
            m.color.g, m.color.a = 1.0, .8
            if self.target == v:
                m.color.r, m.color.g = 1.0, .3
                m.scale.x = m.scale.y = m.scale.z = .12
            array.markers.append(m)
        label = Marker()
        label.header.frame_id = self.p['map_frame']
        label.ns, label.id, label.type, label.action = 'status', 0, Marker.TEXT_VIEW_FACING, Marker.ADD
        label.pose.position.x, label.pose.position.y, label.pose.position.z = *self.robot, .5
        label.pose.orientation.w = 1.0
        label.scale.z = .12
        label.color.r = label.color.g = label.color.b = label.color.a = 1.0
        label.text = self.state + ': ' + self.reason
        array.markers.append(label)
        self.markers.publish(array)


def main(args=None):
    rclpy.init(args=args)
    node = Explorer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if rclpy.ok():
            node.stop('STOPPED', 'Explorer interrupted')
            deadline = time.monotonic()+3
            while rclpy.ok() and node.gate.ticket is not None and time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=.1)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
