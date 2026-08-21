import tempfile
import unittest
from pathlib import Path

from multitarget_hil.gui.session import ConfigurationSession


class GuiSessionTests(unittest.TestCase):
    def test_default_config_path_resolves(self):
        session = ConfigurationSession()
        default_path = session.default_config_path()
        self.assertIsNotNone(default_path)
        self.assertTrue(default_path.exists())

    def test_new_configuration_creates_editable_model(self):
        session = ConfigurationSession()
        session.new_configuration()
        self.assertEqual("New configuration", session.label_text())
        self.assertEqual(1, len(session.configuration.plugins))
        self.assertEqual(1, len(session.configuration.plugins[0].threads))

    def test_save_file_adds_dsf_extension(self):
        session = ConfigurationSession()
        session.new_configuration()
        with tempfile.TemporaryDirectory() as tmp_dir:
            saved_path = session.save_file(Path(tmp_dir) / "example")
            self.assertEqual(".dsf", saved_path.suffix)
            self.assertTrue(saved_path.exists())


if __name__ == "__main__":
    unittest.main()
