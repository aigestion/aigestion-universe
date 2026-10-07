"""Motor command node — subscribes to /cmd_vel, drives actuators."""
from __future__ import annotations

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class MotorNode(Node):
    """Translates /cmd_vel into actuator commands."""

    def __init__(self) -> None:
        super().__init__("daniela_motor")
        self._subscription = self.create_subscription(
            Twist,
            "cmd_vel",
            self._on_cmd_vel,
            10,
        )
        self.get_logger().info("Motor node ready")

    def _on_cmd_vel(self, msg: Twist) -> None:
        linear = msg.linear.x
        angular = msg.angular.z
        self.get_logger().debug(
            f"cmd_vel: linear={linear:.2f} angular={angular:.2f}"
        )
        # In production: write to motor controller via micro-ROS / PWM.


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MotorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
