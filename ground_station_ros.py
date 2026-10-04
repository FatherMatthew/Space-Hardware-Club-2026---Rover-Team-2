import json
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import String, Bool

try:
    from .protocol import validate_command, valid_sensor_packet, is_number
except ImportError:
    from protocol import validate_command, valid_sensor_packet, is_number

def live_qos():
    return QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                      durability=DurabilityPolicy.VOLATILE)

class GroundStationROS(Node):
    def __init__(self, on_status, on_sensors=None):
        super().__init__("ground_station")
        self.on_status = on_status
        self.on_sensors = on_sensors
        self.last_status = None
        self.last_sensors = None
        self.publisher = self.create_publisher(String, "/arm/command", live_qos())
        self.heartbeat = self.create_publisher(Bool, "/arm/heartbeat", live_qos())
        self.subscription = self.create_subscription(
            String, "/arm/status", self.receive_status, live_qos())
        self.sensor_subscription = self.create_subscription(
            String, "/arm/sensors", self.receive_sensors, live_qos())
        self.heartbeat_timer = self.create_timer(0.2, self.send_heartbeat)

    def send_command(self, request):
        request = validate_command(request)
        command = request.get("command")
        if command is not None and command not in ("ARM_ENABLE", "STOP_ALL"):
            raise ValueError("This control command is internal")
        if command != "STOP_ALL" and not self.connected():
            raise ValueError("No recent arm status; command not sent")
        msg = String()
        msg.data = json.dumps(request)
        self.publisher.publish(msg)

    def send_heartbeat(self):
        msg = Bool()
        msg.data = True
        self.heartbeat.publish(msg)

    def receive_status(self, msg):
        try:
            status = json.loads(msg.data)
            if not isinstance(status, dict) or "bridge_mode" not in status:
                return
            targets = status.get("targets", {})
            if not isinstance(targets, dict) or not all(
                is_number(value) for value in targets.values()
            ):
                return
            limits = status.get("limits", {})
            if not isinstance(limits, dict):
                return
            for values in limits.values():
                if not isinstance(values, (list, tuple)) or len(values) != 2:
                    return
                if not all(value is None or is_number(value) for value in values):
                    return
                if status.get("ready") and (None in values or values[0] >= values[1]):
                    return
        except (ValueError, TypeError):
            return
        self.last_status = time.monotonic()
        self.on_status(status)

    def receive_sensors(self, msg):
        try:
            packet = json.loads(msg.data)
        except (ValueError, TypeError):
            return
        if valid_sensor_packet(packet):
            self.last_sensors = time.monotonic()
            if self.on_sensors:
                self.on_sensors(packet)

    def connected(self):
        return self.last_status is not None and time.monotonic() - self.last_status < 1.5

    def poll(self):
        rclpy.spin_once(self, timeout_sec=0.0)

    def close(self):
        self.send_command("STOP_ALL")
        rclpy.spin_once(self, timeout_sec=0.0)
        self.destroy_node()
