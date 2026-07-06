import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from PySide6.QtCore import QCoreApplication

from qml_ui import UiBridge, UpdateChecker
from settings_manager import SettingsManager


class DummyOverlay:
    def __init__(self):
        self.show_count = 0
        self.hide_count = 0
        self.refresh_count = 0
        self.hotkey_count = 0

    def show(self):
        self.show_count += 1

    def hide(self):
        self.hide_count += 1

    def refresh(self):
        self.refresh_count += 1

    def update_hotkey(self):
        self.hotkey_count += 1

    def request_recreation(self):
        self.refresh_count += 1


class UiBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    def create_bridge(self):
        tempdir = tempfile.TemporaryDirectory()
        app_dir = os.path.join(tempdir.name, "CrossHud")
        os.makedirs(app_dir, exist_ok=True)
        with open(os.path.join(app_dir, "settings.json"), "w", encoding="utf-8") as f:
            json.dump({"check_updates": False, "enabled": False}, f)
        patcher = mock.patch("settings_manager.os.path.expanduser", return_value=tempdir.name)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(tempdir.cleanup)
        settings = SettingsManager()
        overlay = DummyOverlay()
        return UiBridge(settings, overlay), settings, overlay

    def test_set_setting_updates_overlay_and_dirty_state(self):
        bridge, settings, overlay = self.create_bridge()

        bridge.setSetting("enabled", True)
        bridge.setSetting("hotkey", "Home")
        bridge.setSetting("size", 30)

        self.assertTrue(settings.get("enabled"))
        self.assertEqual(settings.get("hotkey"), "Home")
        self.assertEqual(settings.get("size"), 30.0)
        self.assertEqual(overlay.show_count, 1)
        self.assertEqual(overlay.hotkey_count, 1)
        self.assertGreaterEqual(overlay.refresh_count, 1)
        self.assertTrue(bridge.dirty)

    def test_save_settings_clears_dirty(self):
        bridge, settings, _ = self.create_bridge()
        bridge.setSetting("size", 42)

        self.assertTrue(bridge.saveSettings(False))
        self.assertFalse(bridge.dirty)

    def test_reverting_setting_to_saved_value_clears_dirty(self):
        bridge, settings, _ = self.create_bridge()

        bridge.setSetting("size", 42)
        self.assertTrue(bridge.dirty)

        bridge.setSetting("size", 20)
        self.assertFalse(bridge.dirty)

    def test_saving_without_custom_pixels_keeps_pixel_changes_dirty(self):
        bridge, settings, _ = self.create_bridge()

        bridge.setCustomPixelsJson(json.dumps([[1, 1, "#00FF00"]]))
        self.assertTrue(bridge.dirty)

        self.assertTrue(bridge.saveSettings(False))
        self.assertTrue(bridge.dirty)

        self.assertTrue(bridge.saveSettings(True))
        self.assertFalse(bridge.dirty)

    def test_reset_settings_reloads_saved_values(self):
        bridge, settings, overlay = self.create_bridge()
        bridge.setSetting("size", 55)

        self.assertTrue(bridge.dirty)
        self.assertTrue(bridge.resetSettings())

        self.assertEqual(settings.get("size"), 20.0)
        self.assertFalse(bridge.dirty)
        self.assertGreaterEqual(overlay.refresh_count, 1)

    def test_template_crud(self):
        bridge, settings, _ = self.create_bridge()
        bridge.setCustomPixelsJson(json.dumps([[1, 1, "#00FF00"]]))

        self.assertTrue(bridge.saveTemplate("Test Template"))
        templates = json.loads(bridge.templatesJson)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["name"], "Test Template")

        bridge.setCustomPixelsJson(json.dumps([[2, 2, "#FF0000"]]))
        bridge.loadTemplate(0)
        self.assertEqual(settings.get("custom_pixels"), [[1, 1, "#00FF00"]])

        self.assertTrue(bridge.deleteTemplate(0))
        self.assertEqual(json.loads(bridge.templatesJson), [])

    def test_set_resolution_updates_both_dimensions_once(self):
        bridge, settings, overlay = self.create_bridge()

        self.assertTrue(bridge.setResolution(2560, 1440))

        self.assertEqual(settings.get("screen_width"), 2560)
        self.assertEqual(settings.get("screen_height"), 1440)
        self.assertEqual(overlay.refresh_count, 1)
        self.assertTrue(bridge.dirty)

    def test_autostart_saves_immediately_and_clears_dirty_when_only_change(self):
        bridge, settings, _ = self.create_bridge()

        with mock.patch("qml_ui.set_autostart") as set_autostart:
            bridge.setAutostart(True)

        set_autostart.assert_called_once_with(True)
        self.assertTrue(settings.get("autostart"))
        self.assertFalse(bridge.dirty)
        with open(settings.settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["autostart"])

    def test_autostart_save_keeps_other_unsaved_settings_dirty(self):
        bridge, settings, _ = self.create_bridge()

        bridge.setSetting("size", 42)
        with mock.patch("qml_ui.set_autostart") as set_autostart:
            bridge.setAutostart(True)

        set_autostart.assert_called_once_with(True)
        self.assertTrue(bridge.dirty)
        with open(settings.settings_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["autostart"])
        self.assertEqual(data["size"], 20.0)

    def test_update_checker_version_comparison(self):
        self.assertFalse(UpdateChecker.is_newer("Crosshud_By_Petyablatnoy_SetupV.3.1", "4.0.1"))
        self.assertFalse(UpdateChecker.is_newer("v4.0.0", "4.0.1"))
        self.assertTrue(UpdateChecker.is_newer("v4.1.0", "4.0.1"))

    def test_update_checker_display_version(self):
        self.assertEqual(UpdateChecker.display_version("Crosshud_By_Petyablatnoy_SetupV.3.1"), "3.1")
        self.assertEqual(UpdateChecker.display_version("v4.0.0"), "4")

    def test_update_checker_selects_setup_asset(self):
        release = {
            "assets": [
                {"name": "sourcecode.zip", "browser_download_url": "https://example.invalid/source.zip"},
                {"name": "CrossHud_Setup.exe", "browser_download_url": "https://example.invalid/setup.exe"},
            ]
        }

        self.assertEqual(UpdateChecker.installer_url(release), "https://example.invalid/setup.exe")

    def test_update_checker_parses_release_tag_from_url(self):
        self.assertEqual(
            UpdateChecker.release_tag_from_url("https://github.com/petyablatnoy/crosshud/releases/tag/v4.0.5"),
            "v4.0.5",
        )
        self.assertEqual(UpdateChecker.release_tag_from_url("https://github.com/petyablatnoy/crosshud/releases"), "")

    def test_update_checker_falls_back_when_api_fails(self):
        checker = UpdateChecker()
        fallback_data = {
            "tag_name": "v4.0.5",
            "html_url": "https://github.com/petyablatnoy/crosshud/releases/tag/v4.0.5",
            "assets": [
                {
                    "name": "CrossHud_Setup.exe",
                    "browser_download_url": "https://github.com/petyablatnoy/crosshud/releases/latest/download/CrossHud_Setup.exe",
                }
            ],
        }
        with mock.patch.object(checker, "fetch_api_release_data", side_effect=RuntimeError("rate limit")), \
                mock.patch.object(checker, "fetch_fallback_release_data", return_value=fallback_data) as fallback:
            self.assertEqual(checker.fetch_release_data(), fallback_data)
        fallback.assert_called_once()

    def test_update_url_validation_accepts_current_and_legacy_repo_paths(self):
        bridge, _, _ = self.create_bridge()

        self.assertTrue(bridge.isValidUpdateUrl("https://github.com/petyablatnoy/crosshud/releases/tag/v4.0.1"))
        self.assertTrue(bridge.isValidUpdateUrl("https://github.com/petyablatnoy/crosshud/releases/download/v4.0.1/CrossHud_Setup.exe"))
        self.assertTrue(bridge.isValidUpdateUrl("https://github.com/petyablatnoy/Crosshud_By_Petyablatnoy-HudsightKiller/releases/tag/v4.0.0"))
        self.assertFalse(bridge.isValidUpdateUrl("https://github.com/example/crosshud/releases/tag/v4.0.1"))


if __name__ == "__main__":
    unittest.main()
