"""RViz preview only: the GUI supplies synthetic wheel positions."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    return LaunchDescription([
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(package / 'launch/rsp.launch.py'))),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui'),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', str(package / 'config/robot.rviz')]),
    ])
