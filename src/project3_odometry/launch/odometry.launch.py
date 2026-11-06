from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='project3_odometry',
            executable='odometry_node',
            name='project3_odometry',
            output='screen',
            parameters=[{'use_sim_time': True}],
        ),
    ])
