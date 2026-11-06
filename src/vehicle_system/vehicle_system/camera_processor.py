import cv2

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class CameraProcessor(Node):

    def __init__(self):
        super().__init__('camera_processor')

        self.bridge = CvBridge()

        self.subscription = self.create_subscription(
            Image,
            '/audibot/camera/image_raw',
            self.image_callback,
            10
        )

        self.frame_count = 0

        self.get_logger().info(
            'Camera Processor started.'
        )

        self.get_logger().info(
            'Subscribed to /audibot/camera/image_raw'
        )

    def image_callback(self, msg):
        try:
            image = self.bridge.imgmsg_to_cv2(
                msg,
                desired_encoding='rgb8'
            )

            self.frame_count += 1

            gray_image = cv2.cvtColor(
                image,
                cv2.COLOR_RGB2GRAY
            )

            edges = cv2.Canny(
                gray_image,
                50,
                150
            )

            if self.frame_count % 5 == 0:
                height, width = gray_image.shape

                edge_pixels = cv2.countNonZero(edges)

                self.get_logger().info(
                    f'CAMERA | '
                    f'Frame={self.frame_count} | '
                    f'Resolution={width}x{height} | '
                    f'Edges={edge_pixels} pixels'
                )

        except Exception as error:
            self.get_logger().error(
                f'Failed to process camera frame: {error}'
            )


def main(args=None):
    rclpy.init(args=args)

    node = CameraProcessor()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
