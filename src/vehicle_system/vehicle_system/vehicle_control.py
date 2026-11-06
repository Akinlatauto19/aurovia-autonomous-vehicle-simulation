#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Bool, Float64
from vehicle_interfaces.msg import DriveCommand, VehicleState
from vehicle_interfaces.srv import VehicleControl


class VehicleControlNode(Node):
    """Single authority for vehicle readiness, mode selection and motion."""

    DEFAULT_SPEED = 2.0
    VALID_MODES = ('MANUAL', 'AUTONOMOUS')

    def __init__(self):
        super().__init__('vehicle_control')

        # START means ready, not moving.
        self.vehicle_running = False
        self.speed = 0.0
        self.gear = VehicleState.DRIVE
        self.phase = 'STOPPED'
        self.selected_mode = 'NONE'

        # Final outputs: only this node publishes these commands.
        self.drive_command_publisher = self.create_publisher(
            DriveCommand, '/vehicle/drive_command', 10
        )
        self.steering_command_publisher = self.create_publisher(
            Float64, '/vehicle/steering_command', 10
        )
        self.lighting_enable_publisher = self.create_publisher(
            Bool, '/vehicle/lighting_enable', 10
        )
        self.state_publisher = self.create_publisher(
            VehicleState, '/vehicle/state', 10
        )

        # Manual input channels.
        self.manual_drive_subscriber = self.create_subscription(
            DriveCommand,
            '/vehicle/manual/drive_command',
            self.manual_drive_callback,
            10
        )
        self.manual_steering_subscriber = self.create_subscription(
            Float64,
            '/vehicle/manual/steering_command',
            self.manual_steering_callback,
            10
        )

        # Autonomous input channels.
        self.autonomous_drive_subscriber = self.create_subscription(
            DriveCommand,
            '/vehicle/autonomous/drive_command',
            self.autonomous_drive_callback,
            10
        )
        self.autonomous_steering_subscriber = self.create_subscription(
            Float64,
            '/vehicle/autonomous/steering_command',
            self.autonomous_steering_callback,
            10
        )

        self.control_service = self.create_service(
            VehicleControl, '/vehicle/control', self.handle_control
        )

        self.publish_drive_command(0.0, DriveCommand.DRIVE, True)
        self.publish_steering_command(0.0)
        self.publish_lighting_enable(False)
        self.publish_vehicle_state()

        self.state_timer = self.create_timer(
            0.5, self.publish_vehicle_state
        )

        self.get_logger().info(
            'Unified vehicle control ready. START prepares the vehicle '
            'without moving it. Available commands: START, MANUAL, '
            'AUTONOMOUS, STOP, REVERSE, GET_STATE.'
        )

    def publish_drive_command(self, speed, gear, brake):
        command = DriveCommand()
        command.speed = float(speed)
        command.gear = int(gear)
        command.brake = bool(brake)
        self.drive_command_publisher.publish(command)

    def publish_steering_command(self, angle):
        message = Float64()
        message.data = float(angle)
        self.steering_command_publisher.publish(message)

    def publish_lighting_enable(self, enabled):
        message = Bool()
        message.data = bool(enabled)
        self.lighting_enable_publisher.publish(message)

    def publish_vehicle_state(self):
        state = VehicleState()
        state.running = self.vehicle_running
        state.speed = float(self.speed)
        state.gear = int(self.gear)
        state.brake = not self.vehicle_running or self.phase in (
            'READY', 'STOPPED', 'SWITCHING_MODE'
        )
        state.phase = (
            self.selected_mode
            if self.vehicle_running and self.selected_mode != 'NONE'
            else self.phase
        )
        self.state_publisher.publish(state)

    def stop_motion(self, phase=None):
        self.speed = 0.0
        self.gear = VehicleState.DRIVE
        self.publish_drive_command(0.0, DriveCommand.DRIVE, True)
        self.publish_steering_command(0.0)
        if phase is not None:
            self.phase = phase

    def valid_drive_command(self, message):
        return (
            math.isfinite(float(message.speed))
            and message.speed >= 0.0
            and message.gear in (
                DriveCommand.DRIVE, DriveCommand.REVERSE
            )
        )

    def forward_drive_command(self, message):
        if not self.vehicle_running or self.selected_mode == 'NONE':
            return
        if not self.valid_drive_command(message):
            self.get_logger().warning('Rejected invalid drive command.')
            return

        self.speed = min(float(message.speed), 5.0)
        self.gear = (
            VehicleState.REVERSE
            if message.gear == DriveCommand.REVERSE
            else VehicleState.DRIVE
        )

        # A mode input cannot cancel a STOP or command motion while
        # the vehicle is only prepared.
        if message.brake:
            self.stop_motion()
            return

        self.publish_drive_command(
            self.speed, message.gear, False
        )

    def manual_drive_callback(self, message):
        if self.selected_mode == 'MANUAL':
            self.forward_drive_command(message)

    def autonomous_drive_callback(self, message):
        if self.selected_mode == 'AUTONOMOUS':
            self.forward_drive_command(message)

    def manual_steering_callback(self, message):
        if (
            self.vehicle_running
            and self.selected_mode == 'MANUAL'
            and math.isfinite(float(message.data))
        ):
            self.publish_steering_command(message.data)

    def autonomous_steering_callback(self, message):
        if (
            self.vehicle_running
            and self.selected_mode == 'AUTONOMOUS'
            and math.isfinite(float(message.data))
        ):
            self.publish_steering_command(message.data)

    def fill_response(self, response, success, status, message):
        response.success = success
        response.status = status
        response.speed = float(self.speed)
        response.phase = (
            self.selected_mode
            if self.vehicle_running and self.selected_mode != 'NONE'
            else self.phase
        )
        response.message = message
        return response

    def handle_control(self, request, response):
        command = request.command.strip().upper()

        if command == 'START':
            if self.vehicle_running:
                return self.fill_response(
                    response, False, 'ALREADY_READY',
                    'Vehicle is already prepared.'
                )

            self.vehicle_running = True
            self.selected_mode = 'NONE'
            self.stop_motion('READY')
            self.publish_lighting_enable(True)
            self.publish_vehicle_state()

            self.get_logger().info(
                'Vehicle prepared. Stationary; brake applied. '
                'Select MANUAL or AUTONOMOUS to enable movement.'
            )
            return self.fill_response(
                response, True, 'READY',
                'Vehicle prepared and stationary. Select MANUAL '
                'or AUTONOMOUS to enable movement.'
            )

        if command in self.VALID_MODES:
            if not self.vehicle_running:
                return self.fill_response(
                    response, False, 'NOT_STARTED',
                    'Send START first. The vehicle remains stopped.'
                )

            # Brake and neutralise steering before transferring control.
            self.stop_motion('SWITCHING_MODE')
            self.selected_mode = command
            self.phase = command
            self.publish_vehicle_state()

            self.get_logger().info(
                f'Control mode selected: {command}. '
                'Waiting for commands from that mode.'
            )
            return self.fill_response(
                response, True, command,
                f'{command} mode selected. The vehicle is stopped '
                'until the selected controller sends a new command.'
            )

        if command == 'REVERSE':
            if not self.vehicle_running:
                return self.fill_response(
                    response, False, 'NOT_STARTED',
                    'Send START and select MANUAL or AUTONOMOUS first.'
                )

            if self.selected_mode == 'NONE':
                return self.fill_response(
                    response, False, 'NO_MODE_SELECTED',
                    'Select MANUAL or AUTONOMOUS before moving.'
                )

            self.get_logger().warning(
                'REVERSE is not a direct motion command in unified '
                'control. Request reverse through the selected mode '
                'input so mode ownership remains enforced.'
            )
            return self.fill_response(
                response, False, 'USE_SELECTED_MODE',
                'To reverse, send a reverse-gear command through the '
                'selected mode input.'
            )

        if command == 'STOP':
            self.vehicle_running = False
            self.selected_mode = 'NONE'
            self.stop_motion('STOPPED')
            self.publish_lighting_enable(False)
            self.publish_vehicle_state()

            self.get_logger().warning(
                'STOP received. Vehicle motion disabled; brake applied.'
            )
            return self.fill_response(
                response, True, 'STOPPED',
                'Vehicle stopped. Select START before enabling a mode.'
            )

        if command == 'GET_STATE':
            return self.fill_response(
                response, True, 'STATE',
                f'ready={self.vehicle_running}, '
                f'mode={self.selected_mode}, phase={self.phase}.'
            )

        return self.fill_response(
            response, False, 'INVALID_COMMAND',
            f'Unknown command: {request.command}.'
        )


def main(args=None):
    rclpy.init(args=args)
    node = VehicleControlNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.vehicle_running = False
        node.selected_mode = 'NONE'
        node.stop_motion('STOPPED')
        node.publish_lighting_enable(False)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
