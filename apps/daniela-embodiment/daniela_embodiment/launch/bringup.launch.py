"""Bring up the Daniela embodiment (motor + perception)."""
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription([
        Node(
            package="daniela_embodiment",
            executable="motor_node",
            name="daniela_motor",
            output="screen",
        ),
        Node(
            package="daniela_embodiment",
            executable="perception_node",
            name="daniela_perception",
            output="screen",
        ),
    ])
