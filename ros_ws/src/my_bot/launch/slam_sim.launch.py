"""Gazebo + fresh-map SLAM; intentionally no hardware mode."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    slam = Path(get_package_share_directory('slam_toolbox'))
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=str(package/'worlds/test_room.sdf')),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        # Keep the child RViz override from disabling this parent's RViz.
        GroupAction(scoped=True, actions=[IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package/'launch/sim.launch.py')),
            launch_arguments={'rviz': 'false', 'world': LaunchConfiguration('world')}.items())]),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(slam/'launch/online_async_launch.py')),
            launch_arguments={'use_sim_time': 'true', 'autostart': 'true',
                              'use_lifecycle_manager': 'false',
                              'slam_params_file': str(package/'config/slam.yaml')}.items()),
        Node(package='rviz2', executable='rviz2', output='screen',
             arguments=['-d', str(package/'config/slam.rviz')],
             parameters=[{'use_sim_time': True}],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
