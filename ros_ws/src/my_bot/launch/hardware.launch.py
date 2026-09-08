"""Real ESP32 control only; no simulated sensors or synthetic joint states."""
from pathlib import Path
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, RegisterEventHandler, EmitEvent
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def start_hardware(context):
    package = Path(get_package_share_directory('my_bot'))
    port = LaunchConfiguration('serial_device').perform(context)
    if not port.startswith('/'):
        raise ValueError('Hardware requires an explicit absolute serial_device path')
    description = xacro.process_file(str(package / 'description/robot.urdf.xacro'), mappings={
        'hardware': 'true', 'simulation': 'false', 'serial_device': port,
    }).toxml()
    # Hardware YAML uses wall time for manager and both controllers.
    config = str(package / 'config/controllers_hardware.yaml')
    manager = Node(package='controller_manager', executable='ros2_control_node',
                   parameters=[config, {'use_sim_time': False}], output='screen',
                   remappings=[('~/robot_description', '/robot_description')])
    joints = Node(package='controller_manager', executable='spawner', output='screen',
                  arguments=['joint_state_broadcaster', '-c', '/controller_manager',
                             '--controller-manager-timeout', '30'])
    drive = Node(package='controller_manager', executable='spawner', output='screen',
                 arguments=['diff_drive_controller', '-c', '/controller_manager',
                            '--controller-manager-timeout', '30', '--param-file', config])

    def start_drive(event, context):
        if event.returncode != 0:
            return [EmitEvent(event=Shutdown(reason='Joint-state broadcaster startup failed'))]
        return [drive]

    def check_drive(event, context):
        if event.returncode != 0:
            return [EmitEvent(event=Shutdown(reason='Drive controller startup failed'))]
        return []

    return [
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': description, 'use_sim_time': False}], output='screen'),
        RegisterEventHandler(OnProcessExit(target_action=manager,
            on_exit=[EmitEvent(event=Shutdown(reason='Hardware controller manager exited'))])),
        RegisterEventHandler(OnProcessExit(target_action=joints, on_exit=start_drive)),
        RegisterEventHandler(OnProcessExit(target_action=drive, on_exit=check_drive)),
        manager, joints,
        Node(package='rviz2', executable='rviz2', arguments=['-d', str(package/'config/hardware.rviz')],
             parameters=[{'use_sim_time': False}], condition=IfCondition(LaunchConfiguration('rviz'))),
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('serial_device', default_value=''),
        DeclareLaunchArgument('rviz', default_value='false', choices=['true', 'false']),
        OpaqueFunction(function=start_hardware),
    ])
