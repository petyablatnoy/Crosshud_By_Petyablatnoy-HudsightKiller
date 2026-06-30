import json
import os
import tempfile
import unittest
from unittest import mock

from settings_manager import SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def create_manager(self, initial_settings):
        tempdir = tempfile.TemporaryDirectory()
        app_dir = os.path.join(tempdir.name, "CrossHud_By_PetyaBlatnoy")
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(initial_settings, f)
        patcher = mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(tempdir.cleanup)
        return SettingsManager(), app_dir

    def test_invalid_settings_are_normalized(self):
        manager, _ = self.create_manager({
            "version": "3.1",
            "enabled": "yes",
            "size": 999,
            "color": "green",
            "rmb_hide_mode": "bad",
            "hotkey": "A",
            "custom_pixels": [[0, 0, "#00ff00"], [999, 0, "#fff"], ["x", 0, "#00ff00"]]
        })

        self.assertEqual(manager.get("version"), "4")
        self.assertIs(manager.get("enabled"), True)
        self.assertEqual(manager.get("size"), 100.0)
        self.assertEqual(manager.get("color"), "#00FF00")
        self.assertEqual(manager.get("rmb_hide_mode"), "hold")
        self.assertEqual(manager.get("hotkey"), "Insert")
        self.assertEqual(manager.get("custom_pixels"), [[0, 0, "#00FF00"]])
        self.assertTrue(manager.consume_warnings())

    def test_broken_json_uses_defaults_and_warns(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        app_dir = os.path.join(tempdir.name, "CrossHud_By_PetyaBlatnoy")
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "settings.json"), "w", encoding="utf-8") as f:
            f.write("{bad json")
        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name):
            manager = SettingsManager()

        self.assertEqual(manager.get("version"), "4")
        self.assertEqual(manager.get("hotkey"), "Insert")
        self.assertTrue(manager.consume_warnings())

    def test_save_settings_preserves_or_writes_custom_pixels_by_flag(self):
        manager, app_dir = self.create_manager({
            "custom_pixels": [[1, 1, "#00ff00"]]
        })

        manager.set("custom_pixels", [[2, 2, "#ff0000"]])
        self.assertTrue(manager.has_unsaved_custom_pixels())

        self.assertTrue(manager.save_settings(include_custom_pixels=False))
        with open(os.path.join(app_dir, "settings.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["custom_pixels"], [[1, 1, "#00FF00"]])
        self.assertTrue(manager.has_unsaved_custom_pixels())

        self.assertTrue(manager.save_settings(include_custom_pixels=True))
        with open(os.path.join(app_dir, "settings.json"), "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["custom_pixels"], [[2, 2, "#FF0000"]])
        self.assertFalse(manager.has_unsaved_custom_pixels())


if __name__ == "__main__":
    unittest.main()
