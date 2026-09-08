"""Offline structural checks; these do not replace a Gazebo smoke test."""
import ast
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

import xacro
import yaml

ROOT = Path(__file__).resolve().parents[1]


def model(simulation=False, lidar=True):
    text = xacro.process_file(str(ROOT / 'description/robot.urdf.xacro'), mappings={
        'simulation': str(simulation).lower(), 'include_lidar': str(lidar).lower(),
        'controllers_file': str(ROOT / 'config/controllers.yaml'),
    }).toxml()
    return ET.fromstring(text)


class ModelChecks(unittest.TestCase):
    def test_frames_and_mass_for_all_variants(self):
        for sim in (False, True):
            for lidar in (False, True):
                with self.subTest(sim=sim, lidar=lidar):
                    tree = model(sim, lidar)
                    links = {n.attrib['name'] for n in tree.findall('link')}
                    children = set()
                    reached = {'base_link'}
                    joints = tree.findall('joint')
                    for joint in joints:
                        parent = joint.find('parent').attrib['link']
                        child = joint.find('child').attrib['link']
                        self.assertIn(parent, links)
                        self.assertIn(child, links)
                        self.assertNotIn(child, children)
                        children.add(child)
                    for _ in links:
                        for joint in joints:
                            if joint.find('parent').attrib['link'] in reached:
                                reached.add(joint.find('child').attrib['link'])
                    self.assertEqual(links - children, {'base_link'})
                    self.assertEqual(reached, links)
                    self.assertEqual('laser' in links, lidar)
                    total = 0.0
                    for link in tree.findall('link'):
                        if link.attrib['name'] == 'base_link':
                            continue  # Massless reference is lumped with the fixed chassis in Gazebo.
                        inertial = link.find('inertial')
                        self.assertIsNotNone(inertial)
                        mass = float(inertial.find('mass').attrib['value'])
                        self.assertGreater(mass, 0)
                        total += mass
                        values = inertial.find('inertia').attrib
                        diagonal = [float(values[k]) for k in ('ixx', 'iyy', 'izz')]
                        self.assertTrue(all(math.isfinite(v) and v > 0 for v in diagonal))
                        for v in diagonal:
                            self.assertLessEqual(2*v, sum(diagonal) + 1e-12)
                    self.assertAlmostEqual(total, 1.6)
                    self.assertEqual(tree.find('ros2_control') is not None, sim)
                    if not sim:
                        self.assertEqual(tree.findall('gazebo'), [])

    def test_geometry_matches_controller(self):
        tree = model(True)
        config = yaml.safe_load((ROOT/'config/controllers.yaml').read_text())
        drive = config['diff_drive_controller']['ros__parameters']
        joints = {j.attrib['name']: j for j in tree.findall('joint')}
        positions = []
        for side in ('left', 'right'):
            name = side + '_wheel_joint'
            self.assertEqual(drive[side + '_wheel_names'], [name])
            joint = joints[name]
            self.assertEqual(joint.attrib['type'], 'continuous')
            self.assertEqual(joint.find('axis').attrib['xyz'], '0 1 0')
            xyz = [float(x) for x in joint.find('origin').attrib['xyz'].split()]
            positions.append(xyz[1])
            self.assertAlmostEqual(xyz[2], drive['wheel_radius'])
            cylinder = tree.find(f"link[@name='{side}_wheel']/collision/geometry/cylinder")
            self.assertAlmostEqual(float(cylinder.attrib['radius']), drive['wheel_radius'])
            width = float(cylinder.attrib['length'])
        self.assertAlmostEqual(positions[0] - positions[1], drive['wheel_separation'])
        self.assertAlmostEqual(drive['wheel_separation'] + width, 0.215)
        origin = [float(x) for x in joints['chassis_joint'].find('origin').attrib['xyz'].split()]
        size = [float(x) for x in tree.find("link[@name='chassis']/collision/geometry/box").attrib['size'].split()]
        self.assertAlmostEqual(origin[0] + size[0]/2, 0.18)
        self.assertAlmostEqual(origin[0] - size[0]/2, -0.08)
        self.assertAlmostEqual(origin[2] - size[2]/2, 0.04)
        max_wheel = (drive['linear.x.max_velocity'] + drive['angular.z.max_velocity']*drive['wheel_separation']/2)/drive['wheel_radius']
        self.assertLess(max_wheel, float(joints['left_wheel_joint'].find('limit').attrib['velocity']))

    def test_simulation_interfaces_and_sensor(self):
        tree = model(True)
        control = tree.find('ros2_control')
        self.assertEqual(control.find('hardware/plugin').text, 'gz_ros2_control/GazeboSimSystem')
        for joint in control.findall('joint'):
            self.assertEqual([x.attrib['name'] for x in joint.findall('command_interface')], ['velocity'])
            self.assertEqual({x.attrib['name'] for x in joint.findall('state_interface')}, {'position', 'velocity'})
        params = tree.find("gazebo/plugin[@name='gz_ros2_control::GazeboSimROS2ControlPlugin']/parameters")
        self.assertTrue(Path(params.text).is_file())
        sensor = tree.find("gazebo[@reference='laser']/sensor")
        self.assertEqual(sensor.attrib['type'], 'gpu_lidar')
        self.assertEqual(sensor.find('gz_frame_id').text, 'laser')
        self.assertEqual(sensor.find('topic').text, '/scan')
        origin = tree.find("joint[@name='laser_joint']/origin")
        self.assertEqual([float(x) for x in origin.attrib['xyz'].split()], [0, 0, 0.1])
        self.assertIsNone(model(True, False).find("gazebo[@reference='laser']/sensor"))
        bridge = yaml.safe_load((ROOT/'config/gz_bridge.yaml').read_text())
        self.assertEqual({x['ros_topic_name'] for x in bridge}, {'/clock', '/scan'})
        self.assertTrue(all(x['direction'] == 'GZ_TO_ROS' for x in bridge))
        world = ET.parse(ROOT/'worlds/test_room.sdf')
        plugins = {x.attrib['name'] for x in world.findall('world/plugin')}
        self.assertIn('gz::sim::systems::Sensors', plugins)
        self.assertIn('gz::sim::systems::Physics', plugins)

    def test_hardware_and_default_isolation(self):
        base = str(ROOT / 'description/robot.urdf.xacro')
        self.assertIsNone(model().find('ros2_control'))
        tree = ET.fromstring(xacro.process_file(base, mappings={
            'hardware': 'true', 'serial_device': '/dev/serial/by-id/test',
        }).toxml())
        controls = tree.findall('ros2_control')
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0].find('hardware/plugin').text, 'my_bot/Esp32System')
        self.assertEqual(tree.findall('gazebo'), [])
        params = {x.attrib['name']: x.text for x in controls[0].findall('hardware/param')}
        self.assertEqual(params['serial_device'], '/dev/serial/by-id/test')
        self.assertEqual(float(params['left_counts_per_revolution']), 4185)
        self.assertEqual(float(params['right_counts_per_revolution']), 4185)
        for joint in controls[0].findall('joint'):
            self.assertEqual([i.attrib['name'] for i in joint.findall('command_interface')], ['velocity'])
            self.assertEqual({i.attrib['name'] for i in joint.findall('state_interface')}, {'position', 'velocity'})
        for truth in ('true', '1'):
            with self.assertRaises(xacro.XacroException):
                xacro.process_file(base, mappings={'hardware': truth, 'simulation': truth})
        plugin = ET.parse(ROOT / 'esp32_hardware.xml').find('class')
        self.assertEqual(plugin.attrib['name'], controls[0].find('hardware/plugin').text)
        self.assertEqual(plugin.attrib['base_class_type'], 'hardware_interface::SystemInterface')

    def test_controller_clocks_and_hardware_limits(self):
        sim = yaml.safe_load((ROOT/'config/controllers.yaml').read_text())
        real = yaml.safe_load((ROOT/'config/controllers_hardware.yaml').read_text())
        for name in ('controller_manager', 'diff_drive_controller', 'joint_state_broadcaster'):
            self.assertTrue(sim[name]['ros__parameters'].pop('use_sim_time'))
            self.assertFalse(real[name]['ros__parameters'].pop('use_sim_time'))
        self.assertEqual(sim, real)
        drive = real['diff_drive_controller']['ros__parameters']
        peak = (drive['linear.x.max_velocity'] +
                drive['angular.z.max_velocity'] * drive['wheel_separation']/2) / drive['wheel_radius']
        self.assertLessEqual(peak, 6.0)

    def test_slam_frames_ranges_and_display(self):
        params = yaml.safe_load((ROOT/'config/slam.yaml').read_text())['slam_toolbox']['ros__parameters']
        self.assertTrue(params['use_sim_time'])
        self.assertEqual(params['mode'], 'mapping')
        self.assertEqual((params['map_frame'], params['odom_frame'], params['base_frame']),
                         ('map', 'odom', 'base_link'))
        self.assertEqual(params['scan_topic'], '/scan')
        sensor = model(True).find("gazebo[@reference='laser']/sensor/lidar/range")
        self.assertEqual(params['min_laser_range'], float(sensor.find('min').text))
        self.assertEqual(params['max_laser_range'], float(sensor.find('max').text))
        display = yaml.safe_load((ROOT/'config/slam.rviz').read_text())['Visualization Manager']
        self.assertEqual(display['Global Options']['Fixed Frame'], 'map')
        maps = [d for d in display['Displays'] if d['Class'] == 'rviz_default_plugins/Map']
        self.assertEqual(len(maps), 1)
        self.assertEqual(maps[0]['Topic']['Value'], '/map')
        self.assertEqual(maps[0]['Topic']['Durability Policy'], 'Transient Local')
        self.assertEqual(display['Views']['Current']['Class'], 'rviz_default_plugins/TopDownOrtho')

    def test_obstacle_room_clearance(self):
        world = ET.parse(ROOT/'worlds/test_room.sdf').getroot().find('world')
        boxes = []
        for item in world.findall('model'):
            if item.attrib['name'] != 'obstacle' and not item.attrib['name'].startswith('box_'):
                continue
            x, y, z, *_ = map(float, item.find('pose').text.split())
            sx, sy, sz = map(float, item.find('link/collision/geometry/box/size').text.split())
            self.assertEqual(item.find('static').text, 'true')
            self.assertEqual(item.find('link/visual/geometry/box/size').text,
                             item.find('link/collision/geometry/box/size').text)
            self.assertAlmostEqual(z, sz/2)
            box = (x-sx/2, x+sx/2, y-sy/2, y+sy/2)
            self.assertTrue(all(abs(v) < 1.75 for v in box))
            # Keep a 0.45 m square around the spawn point clear.
            self.assertTrue(box[0] > .225 or box[1] < -.225 or box[2] > .225 or box[3] < -.225)
            boxes.append(box)
        self.assertEqual(len(boxes), 6)
        for i, a in enumerate(boxes):
            for b in boxes[i+1:]:
                self.assertTrue(a[1] < b[0] or b[1] < a[0] or a[3] < b[2] or b[3] < a[2])

    def test_file_syntax(self):
        for path in (ROOT/'launch').glob('*.py'):
            ast.parse(path.read_text())
        for path in (ROOT/'config').glob('*.yaml'):
            yaml.safe_load(path.read_text())
        for path in (ROOT/'config').glob('*.rviz'):
            yaml.safe_load(path.read_text())
        ET.parse(ROOT/'package.xml')


if __name__ == '__main__':
    unittest.main()
