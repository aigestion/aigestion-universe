"""Perception node — publishes camera/lidar observations."""
from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import Header


class PerceptionNode(Node):
    """Publishes synthetic sensor streams for the embodied agent."""

    def __init__(self) -> None:
        super().__init__("daniela_perception")
        self._image_pub = self.create_publisher(Image, "camera/image", 10)
        self._scan_pub = self.create_publisher(LaserScan, "scan", 10)
        self._timer = self.create_timer(0.1, self._tick)
        self.get_logger().info("Perception node ready")

    def _tick(self) -> None:
        header = Header()
        header.stamp = self.get_clock().now().to_msg()
        header.frame_id = "base_link"

        # Placeholder image (real: capture from camera via v4l2/gstreamer)
        img = Image()
        img.header = header
        img.height = 480
        img.width = 640
        img.encoding = "rgb8"
        img.is_bigendian = 0
        img.step = img.width * 3
        img.data = bytes(img.step * img.height)
        self._image_pub.publish(img)

        # Placeholder 360-degree scan
        scan = LaserScan()
        scan.header = header
        scan.angle_min = -3.14159
        scan.angle_max = 3.14159
        scan.angle_increment = 0.01745
        scan.range_min = 0.1
        scan.range_max = 10.0
        scan.ranges = [5.0] * int((scan.angle_max - scan.angle_min) / scan.angle_increment)
        self._scan_pub.publish(scan)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = PerceptionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
