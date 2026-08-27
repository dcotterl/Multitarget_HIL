"""Comprehensive unit tests for data_sharing_framework_config_api.definitions.

Tests type guards, formatting helpers, Element, ComponentSettings, Channel,
Transfer, TransferGroup, Thread, Plugin, Configuration, and Protocol methods.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import definitions as d


class TestDefinitionsCore(unittest.TestCase):
    """Tests for core helper functions and guard clauses in definitions.py."""

    def test_ensure_dict(self) -> None:
        """Test ensure_dict validation and error handling."""
        valid_dict = {"a": 1}
        self.assertEqual(d.ensure_dict(valid_dict, "context"), valid_dict)

        with self.assertRaises(TypeError) as ctx:
            d.ensure_dict("not a dict", "TestContext")
        self.assertIn("TestContext must be a dictionary", str(ctx.exception))

        with self.assertRaises(TypeError):
            d.ensure_dict([1, 2, 3], "TestList")

    def test_ensure_list(self) -> None:
        """Test ensure_list validation and None handling."""
        self.assertEqual(d.ensure_list(None, "context"), [])
        valid_list = [1, 2, 3]
        self.assertEqual(d.ensure_list(valid_list, "context"), valid_list)

        with self.assertRaises(TypeError) as ctx:
            d.ensure_list("not a list", "TestContext")
        self.assertIn("TestContext must be a list", str(ctx.exception))

    def test_udp_ip_value_formatting(self) -> None:
        """Test _format_udp_ip_value and _format_dict_for_str."""
        # Test 32-bit int IP to string conversion
        formatted_ip = d._format_udp_ip_value("local address", "2130706433")
        self.assertEqual(formatted_ip, "127.0.0.1")

        # Non-address key should be left unchanged
        self.assertEqual(d._format_udp_ip_value("port", "5000"), "5000")

        # Dict formatting with UDP component
        udp_dict = {
            "component": "UDP",
            "values": [
                {"key": "local address", "value": "2130706433"},
                {"key": "local port", "value": "5000"},
            ],
        }
        formatted_dict = d._format_dict_for_str(udp_dict)
        self.assertEqual(formatted_dict["values"][0]["value"], "127.0.0.1")

    def test_pythonic_to_dict_api_and_validation(self) -> None:
        """Test the canonical Pythonic serialization API and strict validation guardrails."""
        element = d.Element("local address", "2130706433")
        self.assertEqual(element.to_dict(), {"key": "local address", "value": "2130706433"})
        self.assertEqual(element.to_dict(), {"key": "local address", "value": "2130706433"})

        with self.assertRaises(ValueError):
            d.Configuration.from_dict({"configuration": {"plugins": "not-a-list"}})
        with self.assertRaises(ValueError):
            d.Configuration.from_dict({"configuration": {"plugins": ["not-a-dict"]}})
        with self.assertRaises(ValueError):
            d.TransferGroup.from_dict({"core": {"direction": 99}})
        with self.assertRaises(ValueError):
            d.Configuration.from_dict({"configuration": {"plugins": [{"core": {"cycle timing": {"priority": "high"}}}]}})
        with self.assertRaises(ValueError):
            d.Configuration.from_dict({
                "configuration": {
                    "plugins": [{
                        "threads": [{
                            "transfer groups": [{
                                "transfers": [{
                                    "channels": [{"core": {"engine data type": "invalid"}}]
                                }]
                            }]
                        }]
                    }]
                }
            })


class TestDefinitionsModel(unittest.TestCase):
    """Tests for base object model classes in definitions.py."""

    def test_element(self) -> None:
        """Test Element creation, dict conversion, import, and string representation."""
        elem = d.Element("local address", "2130706433")
        self.assertEqual(elem.to_dict(), {"key": "local address", "value": "2130706433"})

        # Test __str__ uses IP formatting
        self.assertIn("127.0.0.1", str(elem))

        # Test from_dict & import_from_dict
        rebuilt = d.Element.from_dict({"key": "test_key", "value": 100})
        self.assertEqual(rebuilt.key, "test_key")
        self.assertEqual(rebuilt.value, 100)

        with self.assertRaises(ValueError):
            d.Element.from_dict({"invalid": "data"})

    def test_component_settings(self) -> None:
        """Test ComponentSettings creation, element management, and dict conversion."""
        cs = d.ComponentSettings(component="RDMA")
        self.assertEqual(cs.component, "RDMA")
        self.assertEqual(len(cs.elements), 0)

        cs.add_element("key1", "val1")
        self.assertEqual(len(cs.elements), 1)

        d_serialized = cs.to_dict()
        self.assertEqual(d_serialized["component"], "RDMA")
        self.assertEqual(d_serialized["values"][0], {"key": "key1", "value": "val1"})

        # Round trip
        rebuilt = d.ComponentSettings.from_dict(d_serialized)
        self.assertEqual(rebuilt.component, "RDMA")
        self.assertEqual(len(rebuilt.elements), 1)

        # __str__ output
        self.assertIn("RDMA", str(cs))

    def test_channel(self) -> None:
        """Test Channel creation, component setting management, and round trip."""
        channel = d.Channel(name="Speed", unit="m/s", engine_data_type=2, string_data_type=2, string_offset=0)
        self.assertEqual(channel.name, "Speed")
        self.assertEqual(channel.unit, "m/s")

        cs_new = d.ComponentSettings("CUSTOM")
        channel.component_settings.append(cs_new)
        self.assertEqual(len(channel.component_settings), 2)

        rebuilt = d.Channel.from_dict(channel.to_dict())
        self.assertEqual(rebuilt.name, "Speed")
        self.assertEqual(rebuilt.unit, "m/s")
        self.assertIn("Speed", str(channel))

    def test_transfer(self) -> None:
        """Test Transfer creation, channel management, and round trip."""
        ch = d.Channel(name="Torque", unit="Nm")
        transfer = d.Transfer(
            name="TxTransfer",
            channels=[ch],
            local_address="127.0.0.1",
            local_port=5000,
            destination_address="127.0.0.2",
            destination_port=5001,
        )
        self.assertEqual(transfer.name, "TxTransfer")
        self.assertEqual(len(transfer.channels), 1)

        ch2 = d.Channel(name="Power", unit="kW")
        transfer.add_channel(ch2)
        self.assertEqual(len(transfer.channels), 2)

        rebuilt = d.Transfer.from_dict(transfer.to_dict())
        self.assertEqual(rebuilt.name, "TxTransfer")
        self.assertEqual(len(rebuilt.channels), 2)

        # Test __str__ (collapsed and expanded)
        self.assertIn("[...2 channels...]", str(transfer))
        self.assertIn("Power", transfer.__str__(collapse=False))

    def test_transfer_group(self) -> None:
        """Test TransferGroup creation, direction, transfer management, and round trip."""
        group = d.TransferGroup(
            name="Group1",
            direction=d.Direction.TX,
            priority=100,
            decimation=1,
            offset=0,
            timeout_behaviour=0,
            enable_conversion=True,
        )
        self.assertEqual(group.direction, d.Direction.TX)
        self.assertTrue(group.enable_conversion)

        t1 = d.Transfer(name="T1")
        group.add_transfer(t1)
        self.assertEqual(len(group.transfers), 1)

        rebuilt = d.TransferGroup.from_dict(group.to_dict())
        self.assertEqual(rebuilt.name, "Group1")
        self.assertEqual(rebuilt.direction, d.Direction.TX)
        self.assertTrue(rebuilt.enable_conversion)
        self.assertEqual(len(rebuilt.transfers), 1)

        # Test __str__ with RX and TX
        group.direction = d.Direction.RX
        self.assertIn("RX", str(group))

    def test_thread(self) -> None:
        """Test Thread creation, transfer group management, and round trip."""
        thread = d.Thread(processor=4, priority_offset=10)
        self.assertEqual(thread.processor, 4)
        self.assertEqual(thread.priority_offset, 10)

        tg = d.TransferGroup(name="TG1")
        thread.add_transfer_group(tg)
        self.assertEqual(len(thread.transfer_groups), 1)

        rebuilt = d.Thread.from_dict(thread.to_dict())
        self.assertEqual(rebuilt.processor, 4)
        self.assertEqual(rebuilt.priority_offset, 10)
        self.assertEqual(len(rebuilt.transfer_groups), 1)

        self.assertIn("[...1 transfer groups...]", str(thread))

    def test_plugin(self) -> None:
        """Test Plugin creation, thread management, and round trip."""
        plugin = d.Plugin(name="BasePlugin", priority=5000, decimation=2, offset=1)
        self.assertEqual(plugin.name, "BasePlugin")

        th = d.Thread(processor=1)
        plugin.add_thread(th)
        self.assertEqual(len(plugin.threads), 1)

        rebuilt = d.Plugin.from_dict(plugin.to_dict())
        self.assertEqual(rebuilt.name, "BasePlugin")
        self.assertEqual(len(rebuilt.threads), 1)

        self.assertIn("BasePlugin", str(plugin))

    def test_configuration(self) -> None:
        """Test Configuration creation, plugin management, versioning, and round trip."""
        config = d.Configuration()
        self.assertEqual(config.dsfversion["major"], 1)

        plugin = d.Plugin(name="P1")
        config.add_plugin(plugin)
        self.assertEqual(len(config.plugins), 1)

        rebuilt = d.Configuration.from_dict(config.to_dict())
        self.assertEqual(len(rebuilt.plugins), 1)
        self.assertEqual(rebuilt.plugins[0].name, "P1")

        self.assertIn("[...1 plugins...]", str(config))

    def test_get_version(self) -> None:
        """Test get_version helper function."""
        ver = d.get_version()
        self.assertEqual(ver["major"], 3)
        self.assertEqual(ver["minor"], 0)


if __name__ == "__main__":
    unittest.main()
