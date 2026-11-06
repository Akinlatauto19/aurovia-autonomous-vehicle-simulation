import rclpy
from rclpy.node import Node

from sensor_msgs.msg import NavSatFix


class GnssProcessor(Node):

    def __init__(self):
        super().__init__('gnss_processor')

        self.subscription = self.create_subscription(
            NavSatFix,
            '/audibot/fix',
            self.gnss_callback,
            10
        )

        self.fix_count = 0

        self.get_logger().info(
            'GNSS Processor started.'
        )

        self.get_logger().info(
            'Subscribed to /audibot/fix'
        )

    def gnss_callback(self, msg):
        self.fix_count += 1

        latitude = msg.latitude
        longitude = msg.longitude
        altitude = msg.altitude
        status = msg.status.status

        self.get_logger().info(
            f'GNSS | '
            f'Fix={self.fix_count} | '
            f'Lat={latitude:.6f} | '
            f'Lon={longitude:.6f} | '
            f'Alt={altitude:.2f} m | '
            f'Status={status}'
        )


def main(args=None):
    rclpy.init(args=args)

    node = GnssProcessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
