import unittest
from unittest import mock

import autostart_manager


class FakeRegistryKey:
    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False


class AutostartManagerTests(unittest.TestCase):
    def test_set_autostart_writes_current_key_and_removes_legacy_keys(self):
        deleted = []

        with mock.patch("autostart_manager.app_command", return_value='"C:\\Program Files\\CrossHud\\CrossHud.exe"'), \
                mock.patch("autostart_manager.winreg.OpenKey", return_value=FakeRegistryKey()), \
                mock.patch("autostart_manager.winreg.SetValueEx") as set_value, \
                mock.patch("autostart_manager.winreg.DeleteValue", side_effect=lambda _key, name: deleted.append(name)):
            autostart_manager.set_autostart(True)

        set_value.assert_called_once_with(
            mock.ANY,
            "CrossHud",
            0,
            autostart_manager.winreg.REG_SZ,
            '"C:\\Program Files\\CrossHud\\CrossHud.exe"',
        )
        self.assertIn("CrossHud_PetyaBlatnoy", deleted)
        self.assertIn("Crosshud_By_Petyablatnoy-HudsightKiller", deleted)

    def test_disable_autostart_removes_current_and_legacy_keys(self):
        deleted = []

        with mock.patch("autostart_manager.winreg.OpenKey", return_value=FakeRegistryKey()), \
                mock.patch("autostart_manager.winreg.SetValueEx") as set_value, \
                mock.patch("autostart_manager.winreg.DeleteValue", side_effect=lambda _key, name: deleted.append(name)):
            autostart_manager.set_autostart(False)

        set_value.assert_not_called()
        self.assertIn("CrossHud", deleted)
        self.assertIn("CrossHud_PetyaBlatnoy", deleted)
        self.assertIn("Crosshud_By_Petyablatnoy", deleted)


if __name__ == "__main__":
    unittest.main()
