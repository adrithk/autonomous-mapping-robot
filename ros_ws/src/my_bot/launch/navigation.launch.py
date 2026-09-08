"""Standard Nav2 servers for an existing robot + live SLAM; no AMCL/map server."""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from nav2_common.launch import RewrittenYaml

# Launch only the servers used by this mission, not docking/route/waypoint servers.
SERVERS = (
    ('nav2_controller', 'controller_server'),
    ('nav2_planner', 'planner_server'),
    ('nav2_behaviors', 'behavior_server'),
    ('nav2_bt_navigator', 'bt_navigator'),
    ('nav2_velocity_smoother', 'velocity_smoother'),
    ('nav2_collision_monitor', 'collision_monitor'),
)


def generate_launch_description():
    package = Path(get_package_share_directory('my_bot'))
    clock = {'use_sim_time': ParameterValue(LaunchConfiguration('use_sim_time'), value_type=bool)}
    config = RewrittenYaml(source_file=str(package / 'config/nav2.yaml'),
                           param_rewrites={'use_sim_time': LaunchConfiguration('use_sim_time')},
                           convert_types=True)
    actions = [DeclareLaunchArgument('use_sim_time', default_value='true', choices=['true', 'false'])]
    for pkg, name in SERVERS:
        remaps = []
        if name in ('controller_server', 'behavior_server'):
            remaps = [('cmd_vel', '/cmd_vel_nav')]
        elif name == 'velocity_smoother':
            remaps = [('cmd_vel', '/cmd_vel_nav'), ('cmd_vel_smoothed', '/cmd_vel_smoothed')]
        node = Node(package=pkg, executable=name, name=name, output='screen',
                    parameters=[config, clock], remappings=remaps)
        actions.extend([
            RegisterEventHandler(OnProcessExit(target_action=node,
                on_exit=[EmitEvent(event=Shutdown(reason=f'{name} exited'))])), node])
    manager = Node(package='nav2_lifecycle_manager', executable='lifecycle_manager',
                   name='lifecycle_manager_navigation', output='screen',
                   parameters=[clock, {'autostart': True, 'bond_timeout': 4.0,
                                      'node_names': [name for _, name in SERVERS]}])
    actions.extend([RegisterEventHandler(OnProcessExit(target_action=manager,
        on_exit=[EmitEvent(event=Shutdown(reason='Nav2 lifecycle manager exited'))])), manager])
    return LaunchDescription(actions)
