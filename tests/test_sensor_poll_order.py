from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "ds_air"))

from ds_air_service.ctrl_enum import EnumDevice  # noqa: E402
from ds_air_service.dao import Room, Sensor  # noqa: E402
from ds_air_service.decoder import GetRoomInfoResult, HandShakeResult  # noqa: E402


class FakeService:
    def __init__(self):
        self.messages = []
        self.rooms = []
        self.sensors = []

    def send_msg(self, param):
        self.messages.append(type(param).__name__)

    def set_rooms(self, rooms):
        self.rooms = rooms

    def get_rooms(self):
        return self.rooms

    def set_sensors(self, sensors):
        self.messages.append("set_sensors")
        self.sensors = sensors


class SensorPollOrderTests(unittest.TestCase):
    def test_handshake_only_requests_room_info(self):
        service = FakeService()

        HandShakeResult(1, EnumDevice.SYSTEM).do(service)

        self.assertEqual(service.messages, ["GetRoomInfoParam"])

    def test_sensor_status_is_requested_after_room_sensors_are_loaded(self):
        service = FakeService()
        result = GetRoomInfoResult(1, EnumDevice.SYSTEM)
        result.rooms.append(Room())
        result.sensors.append(Sensor())

        result.do(service)

        self.assertIn("Sensor2InfoParam", service.messages)
        self.assertLess(
            service.messages.index("set_sensors"),
            service.messages.index("Sensor2InfoParam"),
        )
        self.assertLess(
            service.messages.index("set_sensors"),
            service.messages.index("GetAllSensorStateParam"),
        )


if __name__ == "__main__":
    unittest.main()
