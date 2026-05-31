from pathlib import Path
import struct
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "ds_air"))

from ds_air_service.config import Config  # noqa: E402
from ds_air_service.ctrl_enum import EnumCmdType  # noqa: E402
from ds_air_service.dao import Sensor  # noqa: E402
from ds_air_service.decoder import decoder  # noqa: E402
from ds_air_service.service import Service  # noqa: E402


def build_system_frame(cmd_type: EnumCmdType, subbody: bytes, cmd_id: int = 1) -> bytes:
    length = 16 + len(subbody)
    return (
        struct.pack(
            "<BHBBBBIBIBH",
            2,
            length,
            13,
            0,
            1,
            0,
            cmd_id,
            0,
            0,
            1,
            cmd_type.value,
        )
        + subbody
        + b"\x03"
    )


class SensorConnectionStateTests(unittest.TestCase):
    def test_decodes_system_sensor_state_records(self):
        config = Config()
        config.gateway_id = "gateway_a"
        alias = b"08a6f7634148"
        subbody = b"\x01\x01\x01\x00" + bytes.fromhex("08a6f7634148")
        subbody += bytes([len(alias)]) + alias + b"\x01"

        result, remaining = decoder(
            build_system_frame(EnumCmdType.SYS_GET_ALL_SENSOR_STATE, subbody),
            config,
        )

        self.assertEqual(remaining, b"")
        self.assertEqual(result.cmd_type, EnumCmdType.SYS_GET_ALL_SENSOR_STATE)
        self.assertEqual(len(result.sensors), 1)
        sensor = result.sensors[0]
        self.assertEqual(sensor.gateway_id, "gateway_a")
        self.assertEqual(sensor.mac, "08a6f7634148")
        self.assertEqual(sensor.alias, "08a6f7634148")
        self.assertTrue(sensor.connected)

    def test_connection_state_updates_existing_sensor_without_clobbering_values(self):
        service = Service()
        existing = Sensor()
        existing.gateway_id = "gateway_a"
        existing.room_id = 33
        existing.unit_id = 0
        existing.alias = "08a6f7634148"
        existing.temp = 215
        existing.connected = False
        service.set_sensors([existing])
        updated = []
        service.register_sensor_hook(existing.unique_id, updated.append)

        state = Sensor()
        state.gateway_id = "gateway_a"
        state.mac = "08a6f7634148"
        state.alias = "08a6f7634148"
        state.connected = True

        service.set_sensors_connection_state([state])

        self.assertTrue(existing.connected)
        self.assertEqual(existing.mac, "08a6f7634148")
        self.assertEqual(existing.temp, 215)
        self.assertEqual(updated, [existing])


if __name__ == "__main__":
    unittest.main()
