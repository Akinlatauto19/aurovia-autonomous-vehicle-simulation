import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64


class SteeringController(Node):

    STEERING_RATIO = 17.3
    MAX_BICYCLE_ANGLE = math.radians(33.0)

    def __init__(self):
        super().__init__('steering_controller')

        self.current_bicycle_angle = 0.0

        self.steering_command_subscriber = self.create_subscription(
            Float64,
            '/vehicle/steering_command',
            self.steering_command_callback,
            10
        )

        self.audibot_steering_publisher = self.create_publisher(
            Float64,
            '/audibot/steering_cmd',
            10
        )

        self.publish_timer = self.create_timer(
            0.05,
            self.publish_steering_command
        )

        self.get_logger().info(
            'Steering Controller started.'
        )

        self.get_logger().info(
            'Listening on /vehicle/steering_command'
        )

    def steering_command_callback(self, message):
        requested_angle = message.data

        if not math.isfinite(requested_angle):
            self.get_logger().warn(
                'Ignoring non-finite steering command.'
            )
            return

        self.current_bicycle_angle = max(
            -self.MAX_BICYCLE_ANGLE,
            min(self.MAX_BICYCLE_ANGLE, requested_angle)
        )

    def publish_steering_command(self):
        steering_wheel_angle = (
            self.current_bicycle_angle * self.STEERING_RATIO
        )

        message = Float64()
        message.data = steering_wheel_angle

        self.audibot_steering_publisher.publish(message)


def main(args=None):
    rclpy.init(args=args)

    node = SteeringController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
