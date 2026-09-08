"""Gazebo Harmonic simulation only; never opens an ESP32 serial port."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription
from launch.actions import RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    gazebo_package = Path(get_package_share_directory('ros_gz_sim'))
    spawn = Node(
        package='ros_gz_sim', executable='create', output='screen',
        arguments=['-name', 'mapping_robot', '-topic', '/robot_description',
                   '-z', '0.02', '-allow_renaming', 'false'],
    )
    joints = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['joint_state_broadcaster', '-c', '/controller_manager',
                   '--controller-manager-timeout', '60'],
    )
    drive = Node(
        package='controller_manager', executable='spawner', output='screen',
        arguments=['diff_drive_controller', '-c', '/controller_manager',
                   '--controller-manager-timeout', '60'],
    )

    def after_success(next_actions):
        def callback(event, context):
            if event.returncode != 0:
                return [EmitEvent(event=Shutdown(reason='Simulation startup process failed'))]
            return next_actions
        return callback

    return LaunchDescription([
        DeclareLaunchArgument('world', default_value=str(package / 'worlds/test_room.sdf')),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(package / 'launch/rsp.launch.py')),
            launch_arguments={'simulation': 'true', 'use_sim_time': 'true',
                              'include_lidar': 'true'}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gazebo_package / 'launch/gz_sim.launch.py')),
            launch_arguments={'gz_args': ['-r -v 2 ', LaunchConfiguration('world')],
                              'on_exit_shutdown': 'true'}.items(),
        ),
        Node(package='ros_gz_bridge', executable='parameter_bridge', output='screen',
             parameters=[{'config_file': str(package / 'config/gz_bridge.yaml'),
                          'use_sim_time': True}]),
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=after_success([joints]))),
        RegisterEventHandler(OnProcessExit(target_action=joints, on_exit=after_success([drive]))),
        RegisterEventHandler(OnProcessExit(target_action=drive, on_exit=after_success([]))),
        spawn,
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', str(package / 'config/simulation.rviz')],
             parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
