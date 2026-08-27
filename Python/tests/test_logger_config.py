import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from data_sharing_framework_config_api import logger_config


class TestLoggingConfigPaths(unittest.TestCase):
    def test_find_logging_config_path_uses_executable_directory_when_frozen(self):
        with TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "bundle"
            exe_dir.mkdir()
            exe_path = exe_dir / "app.exe"

            with patch.object(logger_config.sys, "frozen", True, create=True), patch.object(
                logger_config.sys, "executable", str(exe_path)
            ):
                config_path = logger_config.find_logging_config_path()

            self.assertEqual(config_path, exe_dir / "logging_config.json")

    def test_resolve_log_file_path_rejects_paths_outside_config_directory(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "logging_config.json"
            with self.assertRaises(ValueError):
                logger_config._resolve_log_file_path(config_path, "../outside.log")

    def test_setup_logging_replaces_handlers_without_duplication(self):
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "logging_config.json"
            config_path.write_text(
                '{"level": "INFO", "log_to_file": true, "log_file_path": "app.log"}',
                encoding="utf-8",
            )
            package_logger = logger_config.logging.getLogger("data_sharing_framework_config_api")
            try:
                with patch.object(logger_config, "find_logging_config_path", return_value=config_path):
                    logger_config.setup_logging()
                    logger_config.setup_logging()
                self.assertEqual(len(package_logger.handlers), 3)
            finally:
                for handler in package_logger.handlers[:]:
                    package_logger.removeHandler(handler)
                    if handler is not logger_config.in_memory_handler:
                        handler.close()

    def test_find_logging_config_path_prefers_executable_directory_over_working_directory(self):
        with TemporaryDirectory() as temp_dir:
            exe_dir = Path(temp_dir) / "bundle"
            exe_dir.mkdir()
            cwd_dir = Path(temp_dir) / "working"
            cwd_dir.mkdir()
            exe_path = exe_dir / "app.exe"
            cwd_config = cwd_dir / "logging_config.json"
            cwd_config.write_text('{"level": "DEBUG"}', encoding="utf-8")

            with patch.object(logger_config.sys, "frozen", True, create=True), patch.object(
                logger_config.sys, "executable", str(exe_path)
            ), patch("data_sharing_framework_config_api.logger_config.Path.cwd", return_value=cwd_dir):
                config_path = logger_config.find_logging_config_path()

            self.assertEqual(config_path, exe_dir / "logging_config.json")
