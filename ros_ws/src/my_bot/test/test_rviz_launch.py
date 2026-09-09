"""Regression: a child rviz=false must not suppress its parent's RViz."""
import ast
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class RvizLaunchChecks(unittest.TestCase):
    def test_child_override_is_scoped(self):
        for name in ('nav_sim.launch.py', 'slam_sim.launch.py', 'explore_sim.launch.py'):
            tree = ast.parse((ROOT/'launch'/name).read_text())
            parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
            overrides = 0
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                    continue
                if node.func.id != 'IncludeLaunchDescription':
                    continue
                # Find the literal override in this include's keyword arguments.
                has_override = any(isinstance(n, ast.Dict) and any(
                    isinstance(k, ast.Constant) and k.value == 'rviz' and
                    isinstance(v, ast.Constant) and v.value == 'false'
                    for k, v in zip(n.keys, n.values)) for n in ast.walk(node))
                if not has_override:
                    continue
                overrides += 1
                ancestor = parents.get(node)
                while ancestor is not None:
                    if isinstance(ancestor, ast.Call) and isinstance(ancestor.func, ast.Name) and ancestor.func.id == 'GroupAction':
                        self.assertTrue(any(k.arg == 'scoped' and isinstance(k.value, ast.Constant)
                                            and k.value.value is True for k in ancestor.keywords))
                        break
                    ancestor = parents.get(ancestor)
                self.assertIsNotNone(ancestor, f'{name}: child rviz override leaks into parent')
            self.assertEqual(overrides, 1)

    @unittest.skipUnless(importlib.util.find_spec('launch_ros'), 'Requires sourced Jazzy installation')
    def test_parent_rviz_selection_with_real_launch_context(self):
        from launch import LaunchContext, LaunchDescription
        from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
        from launch.actions import SetLaunchConfiguration, PushLaunchConfigurations, PopLaunchConfigurations
        from launch.actions import PushEnvironment, PopEnvironment
        from launch.launch_description_sources import PythonLaunchDescriptionSource
        from launch_ros.actions import Node
        from launch.utilities import perform_substitutions

        def module(name):
            spec = importlib.util.spec_from_file_location(name, ROOT/'launch'/name)
            result = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(result)
            return result

        def included(source, context):
            # Exercise the actual two composed launches. External backends need
            # not start (or load Gazebo) to test LaunchContext scope restoration.
            location = source.location
            filename = Path(location if isinstance(location, str) else
                            perform_substitutions(context, location)).name
            if filename == 'slam_sim.launch.py':
                return module(filename).generate_launch_description()
            return LaunchDescription([DeclareLaunchArgument('rviz', default_value='true')])

        for name in ('nav_sim.launch.py', 'slam_sim.launch.py'):
            for enabled in ('true', 'false'):
                context = LaunchContext()
                context.launch_configurations['rviz'] = enabled
                selected = []

                def visit(entity):
                    condition = getattr(entity, 'condition', None)
                    if condition is not None and not condition.evaluate(context):
                        return
                    if isinstance(entity, Node):
                        # No process execution: only evaluate RViz's launch decision.
                        selected.append(entity)
                    elif isinstance(entity, LaunchDescription):
                        for action in entity.entities:
                            visit(action)
                    elif isinstance(entity, (DeclareLaunchArgument, GroupAction,
                                             IncludeLaunchDescription, SetLaunchConfiguration,
                                             PushLaunchConfigurations, PopLaunchConfigurations,
                                             PushEnvironment, PopEnvironment)):
                        for action in entity.execute(context) or []:
                            visit(action)

                with patch.object(PythonLaunchDescriptionSource, 'get_launch_description', included):
                    visit(module(name).generate_launch_description())
                self.assertEqual(len(selected), 1 if enabled == 'true' else 0, (name, enabled))
                self.assertEqual(context.launch_configurations['rviz'], enabled)


if __name__ == '__main__':
    unittest.main()
