"""Tests for :mod:`upd_definitions`."""
import json
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import upd_definitions as upd


class TestIpConversion(unittest.TestCase):
    """Tests for IP address conversion helpers."""

    def test_string_to_ip(self):
        self.assertEqual(upd.string_to_ip("2130706433"), "127.0.0.1")

    def test_ip_to_string(self):
        ip = "127.0.0.1"

        self.assertEqual(upd.ip_to_string(ip), "2130706433")


