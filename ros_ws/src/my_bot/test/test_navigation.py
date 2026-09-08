"""Contract checks plus ROS-only launch/install checks; not navigation acceptance."""
import ast
import importlib.util
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT/'config/nav2.yaml').read_text())


def params(name):
    return CONFIG[name]['ros__parameters']


def load_launch(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'launch'/name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class NavigationChecks(unittest.TestCase):
    def test_velocity_chain_and_bounds(self):
        drive = yaml.safe_load((ROOT/'config/controllers.yaml').read_text())['diff_drive_controller']['ros__parameters']
        follow = params('controller_server')['FollowPath']
        smooth = params('velocity_smoother')
        for name in ('controller_server', 'behavior_server', 'velocity_smoother', 'collision_monitor'):
            self.assertTrue(params(name)['enable_stamped_cmd_vel'])
        for name in ('controller_server', 'bt_navigator', 'velocity_smoother'):
            self.assertEqual(params(name)['odom_topic'], '/diff_drive_controller/odom')
        self.assertLessEqual(follow['max_vel_x'], smooth['max_velocity'][0])
        self.assertLessEqual(smooth['max_velocity'][0], drive['linear.x.max_velocity'])
        self.assertLessEqual(smooth['max_velocity'][2], drive['angular.z.max_velocity'])
        self.assertLessEqual(smooth['max_accel'][0], drive['linear.x.max_acceleration'])
        self.assertLessEqual(smooth['max_accel'][2], drive['angular.z.max_acceleration'])
        self.assertLess(smooth['velocity_timeout'], drive['cmd_vel_timeout'])
        wheel_peak = (smooth['max_velocity'][0] + smooth['max_velocity'][2]*drive['wheel_separation']/2)/drive['wheel_radius']
        self.assertLess(wheel_peak, 6.0)
        monitor = params('collision_monitor')
        self.assertEqual(monitor['cmd_vel_in_topic'], '/cmd_vel_smoothed')
        self.assertEqual(monitor['cmd_vel_out_topic'], '/diff_drive_controller/cmd_vel')
        self.assertEqual(monitor['scan']['topic'], '/scan')
        self.assertLessEqual(monitor['source_timeout'], .5)

    def test_footprint_and_live_map(self):
        # Obtain the true configured extents from the Xacro rather than duplicating them.
        import xacro
        tree = ET.fromstring(xacro.process_file(str(ROOT/'description/robot.urdf.xacro')).toxml())
        sx, _, _ = map(float, tree.find("link[@name='chassis']/collision/geometry/box").attrib['size'].split())
        x, _, _ = map(float, tree.find("joint[@name='chassis_joint']/origin").attrib['xyz'].split())
        wheel_y = float(tree.find("joint[@name='left_wheel_joint']/origin").attrib['xyz'].split()[1])
        width = float(tree.find("link[@name='left_wheel']/collision/geometry/cylinder").attrib['length'])
        enclosing_radius = math.hypot(max(abs(x-sx/2), abs(x+sx/2)), wheel_y+width/2)
        for name, frame in [('local_costmap', 'odom'), ('global_costmap', 'map')]:
            p = CONFIG[name][name]['ros__parameters']
            self.assertTrue(p['use_sim_time'])
            self.assertEqual(p['global_frame'], frame)
            self.assertEqual(p['robot_base_frame'], 'base_link')
            self.assertGreaterEqual(p['robot_radius'], enclosing_radius)
            self.assertGreater(p['inflation_layer']['inflation_radius'], p['robot_radius'])
            self.assertEqual(p['obstacle_layer']['scan']['topic'], '/scan')
        layer = CONFIG['global_costmap']['global_costmap']['ros__parameters']['static_layer']
        self.assertTrue(layer['map_subscribe_transient_local'])
        self.assertEqual(layer['map_topic'], '/map')
        self.assertFalse(params('planner_server')['GridBased']['allow_unknown'])
        self.assertNotIn('amcl', CONFIG)
        self.assertNotIn('map_server', CONFIG)

    def test_launch_and_dependencies(self):
        tree = ast.parse((ROOT/'launch/navigation.launch.py').read_text())
        servers = next(ast.literal_eval(n.value) for n in tree.body
                       if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SERVERS' for t in n.targets))
        declared = {x.text for x in ET.parse(ROOT/'package.xml').findall('exec_depend')}
        for pkg, name in servers:
            self.assertIn(pkg, declared)
            self.assertIn(name, CONFIG)
        for pkg in ('nav2_common', 'nav2_dwb_controller', 'nav2_navfn_planner', 'nav2_rviz_plugins'):
            self.assertIn(pkg, declared)
        ast.parse((ROOT/'launch/nav_sim.launch.py').read_text())
        display = yaml.safe_load((ROOT/'config/navigation.rviz').read_text())
        self.assertIn('nav2_rviz_plugins/Navigation 2', [p['Class'] for p in display['Panels']])
        self.assertIn('nav2_rviz_plugins/GoalTool', [p['Class'] for p in display['Visualization Manager']['Tools']])
        self.assertEqual(display['Visualization Manager']['Global Options']['Fixed Frame'], 'map')

    @unittest.skipUnless(importlib.util.find_spec('launch_ros'), 'Requires sourced Jazzy installation')
    def test_ros_launch_generation_and_clock_rewrite(self):
        from launch import LaunchContext
        from ament_index_python.packages import get_package_prefix
        from nav2_common.launch import RewrittenYaml
        for name in ('navigation.launch.py', 'nav_sim.launch.py'):
            module = load_launch(name)
            description = module.generate_launch_description()
            self.assertTrue(description.entities)
        for pkg, executable in load_launch('navigation.launch.py').SERVERS:
            self.assertTrue((Path(get_package_prefix(pkg))/'lib'/pkg/executable).is_file())
        context = LaunchContext()
        rewritten = RewrittenYaml(source_file=str(ROOT/'config/nav2.yaml'),
                                  param_rewrites={'use_sim_time': 'false'}, convert_types=True)
        path = Path(rewritten.perform(context))
        try:
            config = yaml.safe_load(path.read_text())
            self.assertFalse(config['/**']['ros__parameters']['use_sim_time'])
            for name in ('local_costmap', 'global_costmap'):
                self.assertFalse(config[name][name]['ros__parameters']['use_sim_time'])
        finally:
            path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
