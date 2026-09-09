"""Open only the navigation RViz view against an already running simulation."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    return LaunchDescription([
        Node(package='rviz2', executable='rviz2', name='rviz2', output='screen',
             arguments=['-d', str(package/'config/navigation.rviz')],
             parameters=[{'use_sim_time': True}]),
    ])
