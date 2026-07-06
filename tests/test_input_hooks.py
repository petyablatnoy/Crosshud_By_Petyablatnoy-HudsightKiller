import unittest
from threading import Event
from unittest import mock

from hotkeys import HOTKEY_VK_MAP
from input_hooks import HotkeyListener
from win32_api import MOD_NOREPEAT


class DummySettings:
    def get(self, key, default=None):
        if key == "hotkey":
            return "Insert"
        return default


class HotkeyListenerTests(unittest.TestCase):
    def test_hotkey_registration_suppresses_key_repeat(self):
        stop_event = Event()
        listener = HotkeyListener(DummySettings(), lambda: None, stop_event)
        calls = []

        def register_hotkey(_hwnd, _hotkey_id, modifiers, vk):
            calls.append((modifiers, vk))
            return True

        def run_once(_vk):
            stop_event.set()

        with mock.patch("input_hooks.kernel32.GetCurrentThreadId", return_value=123), \
                mock.patch("input_hooks.user32.RegisterHotKey", side_effect=register_hotkey), \
                mock.patch("input_hooks.user32.UnregisterHotKey"), \
                mock.patch.object(listener, "_message_loop", side_effect=run_once):
            listener._run()

        self.assertEqual(calls, [(MOD_NOREPEAT, HOTKEY_VK_MAP["Insert"])])


if __name__ == "__main__":
    unittest.main()
