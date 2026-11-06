import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64, UInt32

from vehicle_interfaces.msg import DriveCommand


class DriveController(Node):

    MAX_SPEED = 20.0
    MAX_BRAKE = 4000.0

    def __init__(self):
        super().__init__('drive_controller')

        self.target_speed = 0.0
        self.current_gear = DriveCommand.DRIVE
        self.brake_requested = True

        self.drive_command_subscriber = self.create_subscription(
            DriveCommand,
            '/vehicle/drive_command',
            self.drive_command_callback,
            10
        )

        self.gear_publisher = self.create_publisher(
            UInt32,
            '/audibot/gear_cmd',
            10
        )

        self.speed_publisher = self.create_publisher(
            Float64,
            '/audibot/speed_cmd',
            10
        )

        self.brake_publisher = self.create_publisher(
            Float64,
            '/audibot/brake_cmd',
            10
        )

        self.publish_timer = self.create_timer(
            0.05,
            self.publish_drive_commands
        )

        self.get_logger().info(
            'Drive Controller started.'
        )

        self.get_logger().info(
            'Listening on /vehicle/drive_command'
        )

    def drive_command_callback(self, message):

        if not math.isfinite(message.speed):
            self.get_logger().warn(
                'Ignoring non-finite speed command.'
            )
            return

        if message.gear not in (
            DriveCommand.DRIVE,
            DriveCommand.REVERSE
        ):
            self.get_logger().warn(
                f'Ignoring unsupported gear value: {message.gear}'
            )
            return

        self.target_speed = max(
            0.0,
            min(self.MAX_SPEED, float(message.speed))
        )

        self.current_gear = message.gear
        self.brake_requested = bool(message.brake)

    def publish_drive_commands(self):

        gear_message = UInt32()
        gear_message.data = int(self.current_gear)

        speed_message = Float64()
        speed_message.data = self.target_speed

        brake_message = Float64()

        if self.brake_requested:
            brake_message.data = self.MAX_BRAKE
            speed_message.data = 0.0
        else:
            brake_message.data = 0.0

        self.gear_publisher.publish(gear_message)
        self.speed_publisher.publish(speed_message)
        self.brake_publisher.publish(brake_message)


def main(args=None):
    rclpy.init(args=args)

    node = DriveController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
