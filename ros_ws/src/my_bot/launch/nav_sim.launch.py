"""Gazebo + fresh-map SLAM + click-to-go Nav2. Do not run WASD concurrently."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package/'launch/slam_sim.launch.py')),
            launch_arguments={'rviz': 'false'}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package/'launch/navigation.launch.py')),
            launch_arguments={'use_sim_time': 'true'}.items()),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', str(package/'config/navigation.rviz')],
             parameters=[{'use_sim_time': True}],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
