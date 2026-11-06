import math
import time
import tkinter as tk

try:
    from PIL import Image, ImageTk
    from cv_bridge import CvBridge
    CAMERA_DISPLAY_AVAILABLE = True
except ImportError:
    Image = ImageTk = CvBridge = None
    CAMERA_DISPLAY_AVAILABLE = False

import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool, Float32, Float64
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import Image as RosImage, LaserScan
from vehicle_interfaces.msg import VehicleState


class DashboardNode(Node):

    def __init__(self):
        super().__init__('dashboard')

        # Latest vehicle data
        self.actual_speed = 0.0
        self.gear = VehicleState.DRIVE
        self.brake = True
        self.running = False
        self.phase = 'STOPPED'
        self.steering_angle = None
        self.light_level = 100.0
        self.headlamps_on = False

        # Sensor freshness and dashboard-only monitoring state.
        self.last_scan_time = None
        self.front_distance = None
        self.scan_has_valid_front_return = False
        self.last_camera_time = None
        self.camera_image = None
        self.camera_photo = None
        self.camera_bridge = CvBridge() if CAMERA_DISPLAY_AVAILABLE else None

        # ROS subscriptions
        self.create_subscription(
            VehicleState,
            '/vehicle/state',
            self.vehicle_state_callback,
            10
        )

        self.create_subscription(
            TwistStamped,
            '/audibot/twist',
            self.twist_callback,
            10
        )

        self.create_subscription(
            Float64,
            '/vehicle/steering_command',
            self.steering_callback,
            10
        )

        self.create_subscription(
            Float32,
            '/vehicle/light_level',
            self.light_callback,
            10
        )

        self.create_subscription(
            Bool,
            '/vehicle/headlamp_state',
            self.headlamp_callback,
            10
        )

        self.create_subscription(
            LaserScan, '/scan', self.lidar_callback, 10
        )

        if self.camera_bridge is not None:
            self.create_subscription(
                RosImage,
                '/audibot/camera/image_raw',
                self.camera_callback,
                2
            )

        self.get_logger().info('Vehicle Dashboard started.')
        self.get_logger().info('Dashboard is read-only.')

        # Tkinter window
        self.root = tk.Tk()
        self.root.title('Audibot Vehicle Dashboard')
        self.root.geometry('1200x780')
        self.root.minsize(1000, 700)
        self.root.configure(bg='#111315')

        self.build_dashboard()

        # Update ROS and dashboard regularly
        self.root.after(50, self.update_dashboard)

    # ---------------------------------------------------------
    # ROS callbacks
    # ---------------------------------------------------------

    def vehicle_state_callback(self, msg):
        self.running = msg.running
        self.gear = msg.gear
        self.brake = msg.brake
        self.phase = msg.phase

    def twist_callback(self, msg):
        # Convert actual longitudinal velocity to km/h.
        self.actual_speed = abs(msg.twist.linear.x) * 3.6

    def steering_callback(self, msg):
        # Audibot steering command is steering-wheel angle.
        self.steering_angle = msg.data

    def light_callback(self, msg):
        self.light_level = max(0.0, min(100.0, msg.data))

    def headlamp_callback(self, msg):
        self.headlamps_on = msg.data

    def lidar_callback(self, msg):
        now = time.monotonic()
        self.last_scan_time = now
        self.front_distance = None
        self.scan_has_valid_front_return = False

        # Report the nearest valid return across the complete LiDAR scan.
        # This is a general scan distance, not necessarily directly ahead.
        for distance in msg.ranges:
            if not math.isfinite(distance):
                continue
            if not (msg.range_min <= distance <= msg.range_max):
                continue

            self.scan_has_valid_front_return = True
            if self.front_distance is None or distance < self.front_distance:
                self.front_distance = float(distance)

    def camera_callback(self, msg):
        if self.camera_bridge is None:
            return
        try:
            frame = self.camera_bridge.imgmsg_to_cv2(
                msg, desired_encoding='rgb8'
            )
            self.camera_image = Image.fromarray(frame.copy())
            self.last_camera_time = time.monotonic()
        except Exception as error:
            self.get_logger().warning(
                f'Camera preview conversion failed: {error}'
            )

    # ---------------------------------------------------------
    # Dashboard construction
    # ---------------------------------------------------------

    def build_dashboard(self):

        self.canvas = tk.Canvas(
            self.root,
            bg='#111315',
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)

        self.root.bind('<Configure>', self.on_resize)

    def on_resize(self, event):
        if event.widget == self.root:
            self.draw_dashboard()

    # ---------------------------------------------------------
    # Drawing
    # ---------------------------------------------------------

    def draw_dashboard(self):

        width = max(self.root.winfo_width(), 1000)
        height = max(self.root.winfo_height(), 700)
        self.canvas.delete('all')

        self.canvas.create_text(
            width / 2, 25, text='AUDIBOT',
            fill='#eeeeee', font=('DejaVu Sans', 20, 'bold')
        )
        self.canvas.create_text(
            width / 2, 49, text='DIGITAL INSTRUMENT CLUSTER',
            fill='#777b80', font=('DejaVu Sans', 9, 'bold')
        )

        radius = min(width * 0.23, height * 0.30)
        self.draw_speedometer(width * 0.25, height * 0.43, radius)
        self.draw_gear_selector(width * 0.59, height * 0.34)
        self.draw_information_panel(width * 0.82, height * 0.43)

        # Live camera preview; stale data is never presented as live.
        self.draw_camera_panel(width * 0.27, height * 0.80, 440, 130)

        # Compact LiDAR and driving-mode status cards.
        self.draw_lidar_panel(width * 0.70, height * 0.74, 205, 120)
        self.draw_mode_panel(width * 0.89, height * 0.74, 205, 120)

        mode = self.current_mode()
        status_color = (
            '#72d572' if mode in ('MANUAL', 'AUTONOMOUS')
            else '#d4a24c'
        )
        self.canvas.create_text(
            width / 2, height - 20,
            text=f'CONTROLLER  •  {self.phase}     |     MODE  •  {mode}',
            fill=status_color, font=('DejaVu Sans', 10, 'bold')
        )

    def current_mode(self):
        if not self.running:
            return 'NOT READY'
        if self.phase in ('MANUAL', 'AUTONOMOUS'):
            return self.phase
        return 'NOT SELECTED'

    def draw_card(self, cx, cy, card_width, card_height, title):
        left = cx - card_width / 2
        top = cy - card_height / 2
        right = cx + card_width / 2
        bottom = cy + card_height / 2
        self.canvas.create_rectangle(
            left, top, right, bottom,
            fill='#181b1e', outline='#34383d', width=2
        )
        self.canvas.create_text(
            left + 12, top + 16, text=title,
            anchor='w', fill='#aeb1b4',
            font=('DejaVu Sans', 9, 'bold')
        )
        return left, top, right, bottom

    def draw_lidar_panel(self, cx, cy, card_width, card_height):
        left, top, right, bottom = self.draw_card(
            cx, cy, card_width, card_height, 'FRONT LiDAR'
        )
        age = (
            time.monotonic() - self.last_scan_time
            if self.last_scan_time is not None else None
        )

        if age is None or age > 8.0:
            value, color = 'NO LIVE SCAN', '#d4a24c'
            detail = 'Waiting for fresh data'
        elif not self.scan_has_valid_front_return:
            value, color = 'NO VALID RETURN', '#d4a24c'
            detail = 'Front distance unavailable'
        else:
            distance = self.front_distance
            if distance is None:
                value, color = 'NO VALID RETURN', '#d4a24c'
                detail = 'Front distance unavailable'
            elif distance <= 5.0:
                value, color = 'OBSTACLE', '#ff6b6b'
                detail = f'{distance:.2f} m ahead'
            else:
                value, color = 'CLEAR', '#72d572'
                detail = f'{distance:.2f} m nearest scan return'

        self.canvas.create_text(
            cx, cy - 4, text=value, fill=color,
            font=('DejaVu Sans', 12, 'bold')
        )
        self.canvas.create_text(
            cx, cy + 23, text=detail, fill='#aeb1b4',
            font=('DejaVu Sans', 8)
        )

    def draw_mode_panel(self, cx, cy, card_width, card_height):
        left, top, right, bottom = self.draw_card(
            cx, cy, card_width, card_height, 'DRIVING MODE'
        )
        mode = self.current_mode()
        color = (
            '#72d572' if mode in ('MANUAL', 'AUTONOMOUS')
            else '#d4a24c'
        )
        self.canvas.create_text(
            cx, cy - 4, text=mode, fill=color,
            font=('DejaVu Sans', 12, 'bold')
        )
        detail = (
            'Controller mode selected'
            if mode in ('MANUAL', 'AUTONOMOUS')
            else 'Vehicle not enabled for driving'
        )
        self.canvas.create_text(
            cx, cy + 23, text=detail, fill='#aeb1b4',
            font=('DejaVu Sans', 8)
        )

    def draw_camera_panel(self, cx, cy, panel_width, panel_height):
        left, top, right, bottom = self.draw_card(
            cx, cy, panel_width, panel_height, 'FRONT CAMERA'
        )
        now = time.monotonic()
        age = (
            now - self.last_camera_time
            if self.last_camera_time is not None else None
        )

        if (
            self.camera_image is not None
            and age is not None
            and age <= 5.0
            and ImageTk is not None
        ):
            available_width = int(panel_width - 20)
            available_height = int(panel_height - 42)
            preview = self.camera_image.copy()
            preview.thumbnail((available_width, available_height))
            self.camera_photo = ImageTk.PhotoImage(preview)
            self.canvas.create_image(
                cx, top + 30, image=self.camera_photo, anchor='n'
            )
        else:
            if self.camera_bridge is None:
                message = 'Camera preview dependencies unavailable'
            elif age is None:
                message = 'Waiting for camera frames'
            else:
                message = 'Camera data stale — waiting for fresh frames'
            self.canvas.create_text(
                cx, cy + 12, text=message, fill='#d4a24c',
                font=('DejaVu Sans', 9)
            )

    def draw_speedometer(self, cx, cy, radius):

        # Outer rings
        self.canvas.create_oval(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            fill='#181b1e',
            outline='#34383d',
            width=3
        )

        self.canvas.create_oval(
            cx - radius + 15,
            cy - radius + 15,
            cx + radius - 15,
            cy + radius - 15,
            outline='#25292d',
            width=2
        )

        # Scale
        max_speed = 120.0

        for value in range(0, 121, 10):

            angle = math.radians(135 + (value / max_speed) * 270)

            outer_r = radius - 25
            inner_r = radius - (43 if value % 20 == 0 else 35)

            x1 = cx + outer_r * math.cos(angle)
            y1 = cy + outer_r * math.sin(angle)

            x2 = cx + inner_r * math.cos(angle)
            y2 = cy + inner_r * math.sin(angle)

            self.canvas.create_line(
                x1, y1, x2, y2,
                fill='#c5c7c9',
                width=3 if value % 20 == 0 else 1
            )

            if value % 20 == 0:

                label_r = radius - 60

                lx = cx + label_r * math.cos(angle)
                ly = cy + label_r * math.sin(angle)

                self.canvas.create_text(
                    lx,
                    ly,
                    text=str(value),
                    fill='#aeb1b4',
                    font=('DejaVu Sans', 9)
                )

        # Needle
        speed = min(self.actual_speed, max_speed)

        needle_angle = math.radians(
            135 + (speed / max_speed) * 270
        )

        needle_length = radius - 52

        nx = cx + needle_length * math.cos(needle_angle)
        ny = cy + needle_length * math.sin(needle_angle)

        self.canvas.create_line(
            cx,
            cy,
            nx,
            ny,
            fill='#d4a24c',
            width=4
        )

        self.canvas.create_oval(
            cx - 8,
            cy - 8,
            cx + 8,
            cy + 8,
            fill='#d4a24c',
            outline=''
        )

        # Digital speed
        self.canvas.create_text(
            cx,
            cy + radius * 0.34,
            text=f'{self.actual_speed:.1f}',
            fill='#eeeeee',
            font=('DejaVu Sans', 28, 'bold')
        )

        self.canvas.create_text(
            cx,
            cy + radius * 0.48,
            text='km/h',
            fill='#888d92',
            font=('DejaVu Sans', 10)
        )

    def draw_gear_selector(self, cx, cy):

        self.canvas.create_text(
            cx,
            cy - 115,
            text='TRANSMISSION',
            fill='#777b80',
            font=('DejaVu Sans', 10, 'bold')
        )

        gears = [
            ('D', VehicleState.DRIVE),
            ('R', VehicleState.REVERSE),
        ]

        for index, (label, value) in enumerate(gears):

            y = cy + index * 65

            active = self.gear == value

            if active:
                fill = '#d4a24c'
                text_color = '#111315'
                outline = '#d4a24c'
            else:
                fill = '#181b1e'
                text_color = '#777b80'
                outline = '#34383d'

            self.canvas.create_oval(
                cx - 27,
                y - 27,
                cx + 27,
                y + 27,
                fill=fill,
                outline=outline,
                width=2
            )

            self.canvas.create_text(
                cx,
                y,
                text=label,
                fill=text_color,
                font=('DejaVu Sans', 18, 'bold')
            )

    def draw_information_panel(self, cx, cy):

        panel_width = 300
        panel_height = 175

        left = cx - panel_width / 2
        top = cy - panel_height / 2
        right = cx + panel_width / 2
        bottom = cy + panel_height / 2

        self.canvas.create_rectangle(
            left,
            top,
            right,
            bottom,
            fill='#181b1e',
            outline='#303438',
            width=2
        )

        rows = [
            (
                'STEERING',
                '—' if self.steering_angle is None
                else f'{self.steering_angle:.1f}°'
            ),
            (
                'LIGHT LEVEL',
                f'{self.light_level:.0f}%'
            ),
            (
                'HEADLAMPS',
                'ON' if self.headlamps_on else 'OFF'
            ),
            (
                'BRAKE',
                'ON' if self.brake else 'OFF'
            ),
        ]

        for index, (label, value) in enumerate(rows):

            y = top + 28 + index * 35

            self.canvas.create_text(
                left + 20,
                y,
                text=label,
                anchor='w',
                fill='#777b80',
                font=('DejaVu Sans', 9, 'bold')
            )

            if value in ('ON',):
                color = '#72d572'
            elif value == 'OFF':
                color = '#777b80'
            else:
                color = '#dddddd'

            self.canvas.create_text(
                right - 20,
                y,
                text=value,
                anchor='e',
                fill=color,
                font=('DejaVu Sans', 10, 'bold')
            )

    # ---------------------------------------------------------
    # Main GUI update
    # ---------------------------------------------------------

    def update_dashboard(self):

        rclpy.spin_once(
            self,
            timeout_sec=0.0
        )

        self.draw_dashboard()

        self.root.after(
            50,
            self.update_dashboard
        )

    def run(self):

        try:
            self.root.mainloop()
        finally:
            self.destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = DashboardNode()

    try:
        node.run()
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
