import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster, StaticTransformBroadcaster


class Project3Odometry(Node):
    def __init__(self):
        super().__init__('project3_odometry')

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.last_stamp = None
        self.received_twist = False
        self.vx = 0.0
        self.vy = 0.0
        self.wz = 0.0

        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.static_broadcaster = StaticTransformBroadcaster(self)

        world_odom = TransformStamped()
        world_odom.header.stamp = self.get_clock().now().to_msg()
        world_odom.header.frame_id = 'world'
        world_odom.child_frame_id = 'odom'
        world_odom.transform.rotation.w = 1.0
        self.static_broadcaster.sendTransform(world_odom)

        self.twist_sub = self.create_subscription(
            TwistStamped, '/audibot/twist', self.twist_callback, 10
        )
        self.timer = self.create_timer(0.05, self.publish_odometry)

        self.get_logger().info(
            'Ready: integrating /audibot/twist; publishing /odom. '
            'Waiting for velocity messages.'
        )

    def twist_callback(self, msg):
        stamp = msg.header.stamp
        current = float(stamp.sec) + float(stamp.nanosec) * 1e-9

        if current <= 0.0:
            return

        self.vx = msg.twist.linear.x
        self.vy = msg.twist.linear.y
        self.wz = msg.twist.angular.z

        if self.last_stamp is not None:
            dt = current - self.last_stamp
            if 0.0 < dt <= 0.5:
                vx = msg.twist.linear.x
                vy = msg.twist.linear.y
                wz = msg.twist.angular.z

                self.x += (vx * math.cos(self.yaw)
                           - vy * math.sin(self.yaw)) * dt
                self.y += (vx * math.sin(self.yaw)
                           + vy * math.cos(self.yaw)) * dt
                self.yaw += wz * dt
                self.yaw = math.atan2(math.sin(self.yaw), math.cos(self.yaw))

        self.last_stamp = current
        self.received_twist = True

    def publish_odometry(self):
        now = self.get_clock().now().to_msg()

        msg = Odometry()
        msg.header.stamp = now
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_footprint'

        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.z = math.sin(self.yaw / 2.0)
        msg.pose.pose.orientation.w = math.cos(self.yaw / 2.0)

        msg.twist.twist.linear.x = self.vx
        msg.twist.twist.linear.y = self.vy
        msg.twist.twist.angular.z = self.wz

        msg.pose.covariance[0] = 0.05
        msg.pose.covariance[7] = 0.05
        msg.pose.covariance[35] = 0.1
        msg.twist.covariance[0] = 0.1
        msg.twist.covariance[7] = 0.1
        msg.twist.covariance[35] = 0.1

        self.odom_pub.publish(msg)

        transform = TransformStamped()
        transform.header.stamp = now
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_footprint'
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.rotation.z = math.sin(self.yaw / 2.0)
        transform.transform.rotation.w = math.cos(self.yaw / 2.0)
        self.tf_broadcaster.sendTransform(transform)

    def destroy_node(self):
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Project3Odometry()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
