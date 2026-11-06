import rclpy
from rclpy.node import Node

from std_msgs.msg import Float32


class LightSensor(Node):

    def __init__(self):
        super().__init__('light_sensor')

        self.declare_parameter('light_level', 100.0)

        self.publisher = self.create_publisher(
            Float32,
            '/vehicle/light_level',
            10
        )

        self.timer = self.create_timer(
            1.0,
            self.publish_light_level
        )

        self.get_logger().info(
            'Light Sensor started.'
        )

        self.get_logger().info(
            'Publishing /vehicle/light_level'
        )

        self.get_logger().info(
            'Light level parameter: 0.0% to 100.0%'
        )

    def publish_light_level(self):

        level = self.get_parameter(
            'light_level'
        ).get_parameter_value().double_value

        level = max(
            0.0,
            min(100.0, level)
        )

        message = Float32()
        message.data = level

        self.publisher.publish(message)


def main(args=None):

    rclpy.init(args=args)

    node = LightSensor()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
