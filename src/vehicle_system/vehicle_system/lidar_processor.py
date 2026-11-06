import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LidarProcessor(Node):

    def __init__(self):
        super().__init__('lidar_processor')

        self.declare_parameter('front_sector_deg', 15.0)
        self.declare_parameter('side_sector_deg', 15.0)
        self.declare_parameter('obstacle_distance', 5.0)
        self.declare_parameter('self_filter_center_deg', 26.5)
        self.declare_parameter('self_filter_half_width_deg', 8.0)

        self.scan_count = 0
        self.start_subscription()

    def is_self_detection(self, angle_deg):
        center = self.get_parameter('self_filter_center_deg').value
        half_width = self.get_parameter('self_filter_half_width_deg').value

        steering_center = 82.5
        steering_half_width = 8.0

        return (
            abs(angle_deg - center) <= half_width
            or abs(angle_deg + center) <= half_width
            or abs(angle_deg - steering_center) <= steering_half_width
            or abs(angle_deg + steering_center) <= steering_half_width
        )

    def start_subscription(self):
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.get_logger().info('LiDAR Processor started.')
        self.get_logger().info('Subscribing to /scan')

    def get_sector_minimum(self, msg, center_angle, half_width):
        minimum = None

        for index, distance in enumerate(msg.ranges):
            if not math.isfinite(distance):
                continue

            angle = msg.angle_min + index * msg.angle_increment
            angle_deg = math.degrees(angle)

            if self.is_self_detection(angle_deg):
                continue

            if abs(angle - center_angle) <= half_width:
                if msg.range_min <= distance <= msg.range_max:
                    if minimum is None or distance < minimum:
                        minimum = distance

        return minimum

    def scan_callback(self, msg):
        self.scan_count += 1

        front_sector_deg = self.get_parameter(
            'front_sector_deg'
        ).value

        side_sector_deg = self.get_parameter(
            'side_sector_deg'
        ).value

        obstacle_distance = self.get_parameter(
            'obstacle_distance'
        ).value

        front_width = math.radians(front_sector_deg)
        side_width = math.radians(side_sector_deg)

        front_distance = self.get_sector_minimum(
            msg,
            0.0,
            front_width
        )

        left_distance = self.get_sector_minimum(
            msg,
            math.pi / 2,
            side_width
        )

        right_distance = self.get_sector_minimum(
            msg,
            -math.pi / 2,
            side_width
        )

        valid_ranges = []

        for index, distance in enumerate(msg.ranges):
            if not math.isfinite(distance):
                continue

            if not (msg.range_min <= distance <= msg.range_max):
                continue

            angle = msg.angle_min + index * msg.angle_increment
            angle_deg = math.degrees(angle)

            if self.is_self_detection(angle_deg):
                continue

            valid_ranges.append(distance)

        nearest_distance = min(valid_ranges) if valid_ranges else None

        obstacle_detected = (
            nearest_distance is not None
            and nearest_distance <= obstacle_distance
        )

        front_text = (
            f'{front_distance:.2f} m'
            if front_distance is not None
            else 'N/A'
        )

        left_text = (
            f'{left_distance:.2f} m'
            if left_distance is not None
            else 'N/A'
        )

        right_text = (
            f'{right_distance:.2f} m'
            if right_distance is not None
            else 'N/A'
        )

        nearest_text = (
            f'{nearest_distance:.2f} m'
            if nearest_distance is not None
            else 'N/A'
        )

        self.get_logger().info(
            f'LiDAR #{self.scan_count} | '
            f'Front: {front_text} | '
            f'Left: {left_text} | '
            f'Right: {right_text} | '
            f'Nearest: {nearest_text} | '
            f'Obstacle: {"YES" if obstacle_detected else "CLEAR"}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = LidarProcessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
