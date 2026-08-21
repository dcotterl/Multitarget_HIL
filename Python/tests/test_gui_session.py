import tempfile
import sys
import unittest
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from data_sharing_framework_config_api import rdma_definitions as rdma
from data_sharing_framework_config_api.gui.session import ConfigurationSession
from data_sharing_framework_config_api.gui.tree import populate_tree


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

    def test_populate_tree_includes_nested_configuration_objects(self):
        class FakeTree:
            def __init__(self):
                self.nodes = []

            def insert(self, parent, _position, text, open):
                node_id = f"node-{len(self.nodes)}"
                self.nodes.append((node_id, parent, text, open))
                return node_id

        session = ConfigurationSession()
        session.new_configuration()
        tree = FakeTree()
        object_map = {}

        populate_tree(tree, session.configuration, object_map=object_map)

        self.assertTrue(any(isinstance(value, rdma.Plugin) for value in object_map.values()))
        self.assertTrue(any(isinstance(value, rdma.Transfer) for value in object_map.values()))
        self.assertGreaterEqual(len(tree.nodes), 5)


if __name__ == "__main__":
    unittest.main()
