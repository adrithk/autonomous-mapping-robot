"""Autonomous closed-room simulation. Never starts physical hardware."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription, RegisterEventHandler, EmitEvent
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    manager = Node(package='my_bot', executable='explore', name='exploration_manager', output='screen',
        parameters=[str(package/'config/exploration.yaml'), {'use_sim_time': True,
            'autostart': ParameterValue(LaunchConfiguration('autostart'), value_type=bool),
            'output_dir': LaunchConfiguration('output_dir')}])
    saver = Node(package='nav2_map_server', executable='map_saver_server',
        name='exploration_map_saver', output='screen', parameters=[{'use_sim_time': True,
            'save_map_timeout': 10.0, 'map_subscribe_transient_local': True}])
    lifecycle = Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
        name='exploration_saver_lifecycle', output='screen', parameters=[{'use_sim_time': True,
            'autostart': True, 'node_names': ['exploration_map_saver']}])
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('autostart', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('output_dir', default_value=str(Path.home()/'autonomous-mapping-robot/ros_ws/maps')),
        DeclareLaunchArgument('world', default_value=str(package/'worlds/test_room.sdf')),
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package/'launch/nav_sim.launch.py')),
            launch_arguments={'rviz': 'false', 'world': LaunchConfiguration('world')}.items())]),
        *[RegisterEventHandler(OnProcessExit(target_action=node,
            on_exit=[EmitEvent(event=Shutdown(reason='Exploration component exited'))]))
          for node in (manager, saver, lifecycle)],
        saver, lifecycle, manager,
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
            arguments=['-d', str(package/'config/exploration.rviz')],
            parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
