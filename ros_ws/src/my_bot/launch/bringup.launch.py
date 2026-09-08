"""Select one backend. Simulation is default; hardware requires an explicit port."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def select_backend(context):
    package = Path(get_package_share_directory('my_bot'))
    mode = LaunchConfiguration('mode').perform(context)
    args = {'rviz': LaunchConfiguration('rviz').perform(context)}
    if mode == 'hardware':
        port = LaunchConfiguration('serial_device').perform(context)
        if not port.startswith('/'):
            raise ValueError('Hardware mode requires serial_device:=/dev/serial/by-id/YOUR_ESP32')
        args['serial_device'] = port
    elif mode != 'sim':
        raise ValueError('mode must be sim or hardware')
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(str(package / 'launch' / f'{mode}.launch.py')),
        launch_arguments=args.items())]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('mode', default_value='sim', choices=['sim', 'hardware']),
        DeclareLaunchArgument('serial_device', default_value=''),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        OpaqueFunction(function=select_backend),
    ])
