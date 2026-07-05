import json
import os
import tempfile
import unittest
from unittest import mock

from settings_manager import SettingsManager


class SettingsManagerTests(unittest.TestCase):
    def create_manager(self, initial_settings):
        tempdir = tempfile.TemporaryDirectory()
        app_dir = os.path.join(tempdir.name, "CrossHud")
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

        self.assertEqual(manager.get("version"), "4.0.4")
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
        app_dir = os.path.join(tempdir.name, "CrossHud")
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "settings.json"), "w", encoding="utf-8") as f:
            f.write("{bad json")
        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name):
            manager = SettingsManager()

        self.assertEqual(manager.get("version"), "4.0.4")
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

    def test_unsaved_settings_tracks_reverted_values(self):
        manager, _ = self.create_manager({"size": 20})

        self.assertFalse(manager.has_unsaved_settings())

        self.assertTrue(manager.set("size", 42))
        self.assertTrue(manager.has_unsaved_settings())

        self.assertTrue(manager.set("size", 20))
        self.assertFalse(manager.has_unsaved_settings())

    def test_unknown_runtime_setting_is_rejected(self):
        manager, _ = self.create_manager({})

        self.assertFalse(manager.set("unexpected_key", "value"))

        self.assertIsNone(manager.get("unexpected_key"))
        self.assertTrue(manager.consume_warnings())

    def test_legacy_app_data_is_migrated(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        legacy_dir = os.path.join(tempdir.name, "CrossHud_By_PetyaBlatnoy")
        os.makedirs(legacy_dir, exist_ok=True)
        with open(os.path.join(legacy_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"size": 33}, f)

        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name):
            manager = SettingsManager()

        new_dir = os.path.join(tempdir.name, "CrossHud")
        self.assertEqual(manager.app_data_dir, new_dir)
        self.assertEqual(manager.get("size"), 33.0)
        self.assertTrue(os.path.exists(os.path.join(new_dir, "settings.json")))
        self.assertFalse(os.path.exists(legacy_dir))

    def test_legacy_app_data_is_merged_when_new_log_dir_already_exists(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        legacy_dir = os.path.join(tempdir.name, "CrossHud_By_PetyaBlatnoy")
        legacy_profiles = os.path.join(legacy_dir, "profiles")
        new_dir = os.path.join(tempdir.name, "CrossHud")
        os.makedirs(legacy_profiles, exist_ok=True)
        os.makedirs(os.path.join(new_dir, "logs"), exist_ok=True)
        with open(os.path.join(legacy_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"size": 44, "custom_pixels": [[1, 1, "#00ff00"]]}, f)
        with open(os.path.join(legacy_dir, "client_id.txt"), "w", encoding="utf-8") as f:
            f.write("11111111-1111-4111-8111-111111111111")
        with open(os.path.join(legacy_profiles, "old.json"), "w", encoding="utf-8") as f:
            json.dump({"name": "old", "pixels": []}, f)
        with open(os.path.join(new_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump(SettingsManager.DEFAULT_SETTINGS, f)

        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name):
            manager = SettingsManager()

        self.assertEqual(manager.get("size"), 44.0)
        self.assertEqual(manager.get("custom_pixels"), [[1, 1, "#00FF00"]])
        self.assertEqual(manager.get("custom_templates")[0]["name"], "old")
        with open(os.path.join(new_dir, "client_id.txt"), "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), "11111111-1111-4111-8111-111111111111")
        self.assertFalse(os.path.exists(legacy_dir))

    def test_legacy_app_data_is_migrated_from_local_appdata(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        local_appdata = os.path.join(tempdir.name, "Local")
        legacy_dir = os.path.join(local_appdata, "Crosshud_By_Petyablatnoy")
        os.makedirs(legacy_dir, exist_ok=True)
        with open(os.path.join(legacy_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"gap": 12}, f)

        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name), \
                mock.patch.dict(os.environ, {"LOCALAPPDATA": local_appdata, "APPDATA": os.path.join(tempdir.name, "Roaming")}):
            manager = SettingsManager()

        self.assertEqual(manager.get("gap"), 12.0)
        self.assertFalse(os.path.exists(legacy_dir))

    def test_conflicting_legacy_settings_are_preserved_before_cleanup(self):
        tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(tempdir.cleanup)
        legacy_dir = os.path.join(tempdir.name, "Crosshud_By_Petyablatnoy")
        new_dir = os.path.join(tempdir.name, "CrossHud")
        os.makedirs(legacy_dir, exist_ok=True)
        os.makedirs(new_dir, exist_ok=True)
        with open(os.path.join(legacy_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"size": 55}, f)
        with open(os.path.join(new_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"gap": 12}, f)

        with mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name):
            manager = SettingsManager()

        self.assertEqual(manager.get("gap"), 12.0)
        self.assertFalse(os.path.exists(legacy_dir))
        legacy_backups = [name for name in os.listdir(new_dir) if name.startswith("settings.legacy-")]
        self.assertEqual(len(legacy_backups), 1)
        with open(os.path.join(new_dir, legacy_backups[0]), "r", encoding="utf-8") as f:
            self.assertEqual(json.load(f), {"size": 55})


if __name__ == "__main__":
    unittest.main()
