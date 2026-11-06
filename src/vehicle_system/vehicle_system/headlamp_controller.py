import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool, Float32


class HeadlampController(Node):

    DARK_THRESHOLD = 50.0

    def __init__(self):
        super().__init__('headlamp_controller')

        self.headlamps_on = False
        self.lighting_enabled = False

        self.light_level_subscriber = self.create_subscription(
            Float32,
            '/vehicle/light_level',
            self.light_level_callback,
            10
        )

        self.lighting_enable_subscriber = self.create_subscription(
            Bool,
            '/vehicle/lighting_enable',
            self.lighting_enable_callback,
            10
        )

        self.headlamp_state_publisher = self.create_publisher(
            Bool,
            '/vehicle/headlamp_state',
            10
        )

        self.get_logger().info(
            'Headlamp Controller started.'
        )

        self.get_logger().info(
            'Listening on /vehicle/light_level'
        )

        self.get_logger().info(
            'Dark threshold: 50.0%'
        )

    def lighting_enable_callback(self, message):

        self.lighting_enabled = bool(message.data)

        if not self.lighting_enabled and self.headlamps_on:
            self.headlamps_on = False

            state_message = Bool()
            state_message.data = False

            self.headlamp_state_publisher.publish(
                state_message
            )

            self.get_logger().info(
                'Vehicle stopped -> HEADLAMPS OFF'
            )


    def light_level_callback(self, message):

        light_level = max(
            0.0,
            min(100.0, float(message.data))
        )

        new_state = (
            self.lighting_enabled
            and light_level < self.DARK_THRESHOLD
        )

        if new_state != self.headlamps_on:

            self.headlamps_on = new_state

            state_message = Bool()
            state_message.data = self.headlamps_on

            self.headlamp_state_publisher.publish(
                state_message
            )

            if self.headlamps_on:
                self.get_logger().info(
                    f'Light level: {light_level:.1f}% -> HEADLAMPS ON'
                )
            else:
                self.get_logger().info(
                    f'Light level: {light_level:.1f}% -> HEADLAMPS OFF'
                )


def main(args=None):

    rclpy.init(args=args)

    node = HeadlampController()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
