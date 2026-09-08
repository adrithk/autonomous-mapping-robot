"""Publish description for hardware or simulation; no synthetic joint feedback."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import xacro


def create_publisher(context):
    names = ('include_lidar', 'laser_x', 'laser_y', 'laser_z', 'laser_yaw')
    values = {name: LaunchConfiguration(name).perform(context) for name in names}
    if values['include_lidar'].lower() == 'true':
        import math
        for name in names[1:]:
            if not math.isfinite(float(values[name])):
                raise ValueError(f'{name} must be finite')
        if float(values['laser_z']) <= 0:
            raise ValueError('Set laser_z to the measured scan height before enabling LiDAR')
    values['simulation'] = LaunchConfiguration('simulation').perform(context)
    package = Path(get_package_share_directory('my_bot'))
    values['controllers_file'] = str(package / 'config/controllers.yaml')
    path = package / 'description/robot.urdf.xacro'
    description = xacro.process_file(str(path), mappings=values).toxml()
    return [Node(
        package='robot_state_publisher', executable='robot_state_publisher',
        output='screen', parameters=[{
            'robot_description': description,
            'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool),
        }],
    )]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('simulation', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('include_lidar', default_value='true', choices=['true', 'false']),
        *[DeclareLaunchArgument(name, default_value='0.10' if name == 'laser_z' else '0.0')
          for name in ('laser_x', 'laser_y', 'laser_z', 'laser_yaw')],
        OpaqueFunction(function=create_publisher),
    ])
