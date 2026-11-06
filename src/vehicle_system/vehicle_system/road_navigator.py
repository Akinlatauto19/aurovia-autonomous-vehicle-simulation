#!/usr/bin/env python3

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.clock import Clock, ClockType
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float64, String
from vehicle_interfaces.msg import DriveCommand


class RoadNavigator(Node):
    """Destination follower with reactive LiDAR obstacle avoidance."""

    WHEELBASE = 2.67
    MAX_STEERING_ANGLE = math.radians(33.0)

    FOLLOW_ROUTE = 'FOLLOW_ROUTE'
    AVOIDING = 'AVOIDING'
    BLOCKED = 'BLOCKED'

    def __init__(self):
        super().__init__('road_navigator')

        self.declare_parameter('enabled', False)
        self.declare_parameter('goal_x', 75.0)
        self.declare_parameter('goal_y', 0.0)
        self.declare_parameter('cruise_speed', 0.5)
        self.declare_parameter('lookahead', 3.0)
        self.declare_parameter('goal_tolerance', 1.5)
        self.declare_parameter('odom_timeout', 30.0)
        self.declare_parameter('scan_timeout', 30.0)
        self.declare_parameter('obstacle_distance', 5.0)
        self.declare_parameter('side_clearance', 3.5)
        self.declare_parameter('avoid_speed', 0.25)
        self.declare_parameter('avoid_lateral_offset', 2.5)
        self.declare_parameter('avoid_min_duration', 1.2)

        self.enabled = bool(self.get_parameter('enabled').value)
        self.goal_x = float(self.get_parameter('goal_x').value)
        self.goal_y = float(self.get_parameter('goal_y').value)
        self.cruise_speed = float(self.get_parameter('cruise_speed').value)
        self.lookahead = float(self.get_parameter('lookahead').value)
        self.goal_tolerance = float(
            self.get_parameter('goal_tolerance').value
        )
        self.odom_timeout = float(self.get_parameter('odom_timeout').value)
        self.scan_timeout = float(self.get_parameter('scan_timeout').value)
        self.obstacle_distance = float(
            self.get_parameter('obstacle_distance').value
        )
        self.side_clearance = float(
            self.get_parameter('side_clearance').value
        )
        self.avoid_speed = float(self.get_parameter('avoid_speed').value)
        self.avoid_lateral_offset = float(
            self.get_parameter('avoid_lateral_offset').value
        )
        self.avoid_min_duration = float(
            self.get_parameter('avoid_min_duration').value
        )

        if self.cruise_speed <= 0 or self.avoid_speed <= 0:
            raise ValueError('Cruise and avoidance speeds must be positive')
        if self.lookahead <= 0 or self.goal_tolerance <= 0:
            raise ValueError('Lookahead and goal tolerance must be positive')
        if self.obstacle_distance <= 0 or self.side_clearance <= 0:
            raise ValueError('Obstacle thresholds must be positive')

        self.x = None
        self.y = None
        self.yaw = None
        self.last_odom_time = None
        self.last_scan_time = None
        self.front_clearance = None
        self.left_clearance = None
        self.right_clearance = None
        self.scan_ready = False

        self.goal_reached = False
        self.state = self.FOLLOW_ROUTE
        self.avoid_side = 0
        self.avoid_started = None
        self.clear_since = None
        self.last_reported_state = None

        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, 10
        )
        self.south_signal_state = None
        self.north_signal_state = None
        self.south_signal_sub = self.create_subscription(
            String, '/project3/traffic_light/south_state',
            self.south_signal_callback, 10
        )
        self.north_signal_sub = self.create_subscription(
            String, '/project3/traffic_light/north_state',
            self.north_signal_callback, 10
        )
        self.drive_pub = self.create_publisher(
            DriveCommand, '/vehicle/autonomous/drive_command', 10
        )
        self.steering_pub = self.create_publisher(
            Float64, '/vehicle/autonomous/steering_command', 10
        )
        self.control_clock = Clock(clock_type=ClockType.STEADY_TIME)
        self.timer = self.create_timer(
            0.05, self.control_loop, clock=self.control_clock
        )

        self.get_logger().info(
            f'Navigator ready; enabled={self.enabled}; '
            f'goal=({self.goal_x:.1f}, {self.goal_y:.1f}). '
            'Waiting for odometry and LiDAR.'
        )

    def odom_callback(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.x = float(p.x)
        self.y = float(p.y)
        self.yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        )
        self.last_odom_time = time.monotonic()

    @staticmethod
    def is_self_detection(angle_deg):
        # Exclude known vehicle-body/steering returns used by this model.
        return (
            abs(abs(angle_deg) - 26.5) <= 8.0
            or abs(abs(angle_deg) - 82.5) <= 8.0
        )

    def sector_clearance(self, msg, low_deg, high_deg):
        readings = []
        sector_samples = 0

        for i, distance in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            angle_deg = math.degrees(angle)

            if not low_deg <= angle_deg <= high_deg:
                continue
            if self.is_self_detection(angle_deg):
                continue

            sector_samples += 1

            if math.isinf(distance) and distance > 0:
                readings.append(float(msg.range_max))
            elif (
                math.isfinite(distance)
                and msg.range_min <= distance <= msg.range_max
            ):
                readings.append(float(distance))

        # Insufficient angular coverage or unusable measurements is unknown,
        # not evidence that the road is clear.
        if sector_samples < 5 or not readings:
            return None

        return min(readings)

    def scan_callback(self, msg):
        if not msg.ranges or msg.angle_increment == 0.0:
            self.scan_ready = False
            return

        front = self.sector_clearance(msg, -12.0, 12.0)
        left = self.sector_clearance(msg, 20.0, 65.0)
        right = self.sector_clearance(msg, -65.0, -20.0)

        self.front_clearance = front
        self.left_clearance = left
        self.right_clearance = right
        self.last_scan_time = time.monotonic()
        self.scan_ready = (
            front is not None and left is not None and right is not None
        )

    def publish_command(self, speed, steering_angle, brake=False):
        drive = DriveCommand()
        drive.speed = float(speed)
        drive.gear = DriveCommand.DRIVE
        drive.brake = bool(brake)
        self.drive_pub.publish(drive)

        steering = Float64()
        steering.data = max(
            -self.MAX_STEERING_ANGLE,
            min(self.MAX_STEERING_ANGLE, float(steering_angle))
        )
        self.steering_pub.publish(steering)

    def south_signal_callback(self, msg):
        self.south_signal_state = msg.data.strip().upper()

    def north_signal_callback(self, msg):
        self.north_signal_state = msg.data.strip().upper()

    def traffic_signal_requires_stop(self):
        crossings = (
            (121.4664, 34.6400, self.south_signal_state, 'south'),
            (121.4664, 54.1400, self.north_signal_state, 'north'),
        )
        if self.x is None or self.y is None or self.yaw is None:
            return False
        if math.cos(self.yaw) < 0.5:
            return False

        for cx, cy, signal, name in crossings:
            distance = cx - self.x
            if not (0.0 <= distance <= 10.0):
                continue
            if abs(self.y - cy) > 3.5:
                continue

            stop = (
                signal is None
                or signal == 'RED'
                or signal not in ('RED', 'AMBER', 'GREEN')
                or (signal == 'AMBER' and distance > 3.0)
            )
            if stop:
                self.publish_stop()
                self.get_logger().info(
                    f'{name.capitalize()} crossing: stopping; '
                    f'signal={signal or "UNKNOWN"}, distance={distance:.1f} m',
                    throttle_duration_sec=2.0
                )
                return True
        return False

    def publish_stop(self):
        self.publish_command(0.0, 0.0, True)

    def set_state(self, new_state):
        if self.state != new_state:
            self.state = new_state
            self.get_logger().info(f'Navigation state: {new_state}')

    def choose_avoidance_side(self):
        left = self.left_clearance
        right = self.right_clearance

        if left is None or right is None:
            return 0

        left_safe = left >= self.side_clearance
        right_safe = right >= self.side_clearance

        if left_safe and right_safe:
            return 1 if left >= right else -1
        if left_safe:
            return 1
        if right_safe:
            return -1
        return 0

    def route_steering(self, dx, dy, distance):
        local_x = math.cos(self.yaw) * dx + math.sin(self.yaw) * dy
        local_y = -math.sin(self.yaw) * dx + math.cos(self.yaw) * dy

        target_distance = max(distance, 0.1)
        curvature = 2.0 * local_y / (target_distance * target_distance)
        return math.atan(self.WHEELBASE * curvature)

    def control_loop(self):
        # Refresh runtime parameters before making navigation decisions.
        self.enabled = bool(self.get_parameter('enabled').value)
        self.goal_x = float(self.get_parameter('goal_x').value)
        self.goal_y = float(self.get_parameter('goal_y').value)
        self.cruise_speed = float(self.get_parameter('cruise_speed').value)

        if not self.enabled:
            return

        now = time.monotonic()

        if (
            self.last_odom_time is None
            or now - self.last_odom_time > self.odom_timeout
        ):
            self.publish_stop()
            return

        if (
            self.last_scan_time is None
            or now - self.last_scan_time > self.scan_timeout
            or not self.scan_ready
        ):
            self.publish_stop()
            return

        if self.goal_reached:
            self.publish_stop()
            return

        dx = self.goal_x - self.x
        dy = self.goal_y - self.y
        distance = math.hypot(dx, dy)

        if distance <= self.goal_tolerance:
            self.goal_reached = True
            self.publish_stop()
            self.get_logger().info('Destination reached.')
            return

        # Signal safety takes priority over route following and LiDAR avoidance.
        if self.traffic_signal_requires_stop():
            return

        front_blocked = self.front_clearance < self.obstacle_distance

        if self.state == self.FOLLOW_ROUTE and front_blocked:
            self.avoid_side = self.choose_avoidance_side()
            if self.avoid_side == 0:
                self.set_state(self.BLOCKED)
                self.publish_stop()
                return
            self.avoid_started = now
            self.clear_since = None
            self.set_state(self.AVOIDING)

        if self.state == self.BLOCKED:
            if not front_blocked:
                self.set_state(self.FOLLOW_ROUTE)
            else:
                side = self.choose_avoidance_side()
                if side == 0:
                    self.publish_stop()
                    return
                self.avoid_side = side
                self.avoid_started = now
                self.clear_since = None
                self.set_state(self.AVOIDING)

        if self.state == self.AVOIDING:
            # If the selected side becomes unsafe, reconsider the other side.
            selected = (
                self.left_clearance if self.avoid_side == 1
                else self.right_clearance
            )
            if selected < self.side_clearance:
                other = self.choose_avoidance_side()
                if other == 0:
                    self.set_state(self.BLOCKED)
                    self.publish_stop()
                    return
                self.avoid_side = other
                self.avoid_started = now
                self.clear_since = None

            elapsed = now - self.avoid_started
            selected = (
                self.left_clearance if self.avoid_side == 1
                else self.right_clearance
            )

            if (
                not front_blocked
                and selected >= self.side_clearance
                and elapsed >= self.avoid_min_duration
            ):
                if self.clear_since is None:
                    self.clear_since = now
                elif now - self.clear_since >= 0.8:
                    self.set_state(self.FOLLOW_ROUTE)
                    self.avoid_side = 0
                    self.clear_since = None
            else:
                self.clear_since = None

            if self.state == self.AVOIDING:
                # Aim at a temporary point ahead and to the chosen side.
                # The normal destination controller resumes when clear.
                lx = self.lookahead
                ly = self.avoid_side * self.avoid_lateral_offset
                target_distance_sq = max(lx * lx + ly * ly, 0.1)
                curvature = 2.0 * ly / target_distance_sq
                steering_angle = math.atan(self.WHEELBASE * curvature)

                # A detected obstacle still directly ahead means continue
                # the manoeuvre; a blocked side causes a safe stop above.
                self.publish_command(
                    min(self.avoid_speed, self.cruise_speed),
                    steering_angle,
                    False
                )
                return

        steering_angle = self.route_steering(dx, dy, distance)
        speed = min(self.cruise_speed, distance * 0.3)

        # Reduce speed while approaching an obstacle without blocking the
        # planned avoidance transition.
        if self.front_clearance < self.obstacle_distance + 2.0:
            speed = min(speed, self.avoid_speed)

        self.publish_command(speed, steering_angle, False)


def main(args=None):
    rclpy.init(args=args)
    node = RoadNavigator()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish_stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
