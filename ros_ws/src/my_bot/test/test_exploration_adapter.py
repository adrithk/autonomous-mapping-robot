"""ROS adapter regression tests with fake actions; no hardware or motion launched."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@unittest.skipUnless(importlib.util.find_spec('rclpy'), 'Requires sourced Jazzy')
class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import rclpy
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        import rclpy
        rclpy.shutdown()

    def setUp(self):
        from my_bot_exploration.node import Explorer
        self.node = Explorer()
        self.node.timer.cancel()
        self.node.started = time.monotonic()

    def tearDown(self):
        self.node.destroy_node()

    def future(self, result):
        from rclpy.task import Future
        f = Future()
        f.set_result(result)
        return f

    def operation(self):
        ticket = self.node.gate.begin()
        from my_bot_exploration.core import Viewpoint
        view = Viewpoint(1., 1., 0., 1., 1., 1., 'test')
        op = dict(ticket=ticket, kind='plan', view=view, started=time.monotonic(), handle=None)
        self.node.operation = op
        return op

    def test_rejection_faults_instead_of_claiming_complete(self):
        op = self.operation()
        self.node.accepted(op, self.future(NS(accepted=False)))
        self.assertEqual(self.node.state, 'STOPPING')
        self.assertEqual(self.node.pending_finish[0], 'FAULTED')
        self.assertIsNone(self.node.gate.ticket)

    def test_stop_during_pending_acceptance_cancels_late_handle(self):
        op = self.operation()
        self.node.stop('STOPPED', 'test')
        from rclpy.task import Future
        handle = Mock(accepted=True)
        handle.get_result_async.return_value = Future()
        self.node.accepted(op, self.future(handle))
        handle.cancel_goal_async.assert_called_once()
        self.assertIsNotNone(self.node.gate.ticket)
        self.node.result(op, self.future(NS(status=5, result=NS(error_code=0))))
        self.assertIsNone(self.node.gate.ticket)
        self.assertEqual(self.node.state, 'STOPPING')

    def test_stale_result_cannot_clear_new_action(self):
        op = self.operation()
        self.node.gate.finish(op['ticket'])
        second = self.node.gate.begin()
        self.node.result(op, self.future(None))
        self.assertTrue(self.node.gate.current(second))

    def test_missing_sensor_is_not_completion(self):
        self.assertIn('scan', self.node.health_error(time.monotonic()))
        self.node.state = 'SELECTING'
        self.node.poll_dependencies = Mock()
        self.node._tick(time.monotonic())
        self.assertEqual(self.node.pending_finish[0], 'FAULTED')

    def test_save_failure_is_retryable_but_not_complete(self):
        f = self.future(NS(result=False))
        self.node.save_future = f
        self.node.state = 'SAVING'
        self.node.saved(f)
        self.assertEqual(self.node.state, 'SAVE_FAILED')
        self.assertIsNone(self.node.saved_map)

    def test_successful_save_requires_files_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            self.node.mission_dir = Path(directory)
            self.node.save_base = Path(directory)/'map'
            self.node.final_kind = 'PARTIAL'
            self.node.pending_finish = ('PARTIAL', 'unreachable')
            self.node.save_base.with_suffix('.yaml').write_text('image: map.pgm\n')
            self.node.save_base.with_suffix('.pgm').write_bytes(b'P5\n1 1\n255\n\x00')
            f = self.future(NS(result=True))
            self.node.save_future = f
            self.node.state = 'SAVING'
            self.node.saved(f)
            self.assertEqual(self.node.state, 'PARTIAL')
            self.assertTrue((Path(directory)/'mission.json').exists())

    def test_navigation_abort_excludes_viewpoint_but_tf_error_faults(self):
        op = self.operation()
        op['kind'] = 'navigate'
        self.node.result(op, self.future(NS(status=6, result=NS(error_code=105, error_msg='no progress'))))
        self.assertEqual(self.node.state, 'SELECTING')
        self.assertEqual(self.node.failed_goals, 1)
        op = self.operation()
        op['kind'] = 'navigate'
        self.node.result(op, self.future(NS(status=6, result=NS(error_code=102, error_msg='TF unavailable'))))
        self.assertEqual(self.node.pending_finish[0], 'FAULTED')

    def test_unconfirmed_stop_requests_whole_launch_shutdown(self):
        self.operation()
        self.node.stop('STOPPED', 'test')
        self.node._tick(self.node.stop_started+16)
        self.assertTrue(self.node.abort_launch)
        self.assertEqual(self.node.state, 'FAULTED')
        self.assertIsNotNone(self.node.gate.ticket)

    def test_late_save_cannot_override_new_fault(self):
        f = self.future(NS(result=True))
        self.node.save_future = f
        self.node.state = 'FAULTED'
        self.node.saved(f)
        self.assertEqual(self.node.state, 'FAULTED')
        self.assertIsNone(self.node.saved_map)

    def test_launch_generates_and_installed_executable_exists(self):
        from ament_index_python.packages import get_package_prefix
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('explore_launch', root/'launch/explore_sim.launch.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(module.generate_launch_description().entities)
        self.assertTrue((Path(get_package_prefix('my_bot'))/'lib/my_bot/explore').is_file())


if __name__ == '__main__':
    unittest.main()
