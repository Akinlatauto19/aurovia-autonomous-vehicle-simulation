import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu


class ImuProcessor(Node):

    def __init__(self):
        super().__init__('imu_processor')

        self.subscription = self.create_subscription(
            Imu,
            '/audibot/imu',
            self.imu_callback,
            10
        )

        self.message_count = 0

        self.get_logger().info(
            'IMU Processor started.'
        )

        self.get_logger().info(
            'Subscribed to /audibot/imu'
        )

    def imu_callback(self, msg):
        self.message_count += 1

        acceleration_x = msg.linear_acceleration.x
        acceleration_y = msg.linear_acceleration.y
        acceleration_z = msg.linear_acceleration.z

        angular_x = msg.angular_velocity.x
        angular_y = msg.angular_velocity.y
        angular_z = msg.angular_velocity.z

        acceleration_magnitude = math.sqrt(
            acceleration_x ** 2
            + acceleration_y ** 2
            + acceleration_z ** 2
        )

        if self.message_count % 10 == 0:
            self.get_logger().info(
                f'IMU | '
                f'Accel: '
                f'X={acceleration_x:.2f} '
                f'Y={acceleration_y:.2f} '
                f'Z={acceleration_z:.2f} m/s² | '
                f'Gyro: '
                f'X={angular_x:.3f} '
                f'Y={angular_y:.3f} '
                f'Z={angular_z:.3f} rad/s | '
                f'Accel Magnitude={acceleration_magnitude:.2f} m/s²'
            )


def main(args=None):
    rclpy.init(args=args)

    node = ImuProcessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
