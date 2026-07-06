import ctypes
import logging
from threading import Event, Thread
from typing import Callable, Optional

from hotkeys import HOTKEY_VK_MAP
from win32_api import (
    EVENT_SYSTEM_FOREGROUND,
    LOWLEVELMOUSEPROC,
    MOD_NOREPEAT,
    PM_REMOVE,
    WH_MOUSE_LL,
    WINEVENT_OUTOFCONTEXT,
    WINEVENT_SKIPOWNPROCESS,
    WIN_EVENT_PROC,
    WM_HOTKEY,
    WM_QUIT,
    WM_RBUTTONDBLCLK,
    WM_RBUTTONDOWN,
    WM_RBUTTONUP,
    kernel32,
    user32,
)
from ctypes import wintypes


class HotkeyListener:
    HOTKEY_ID = 1

    def __init__(self, settings_manager, on_toggle: Optional[Callable[[], None]], stop_event: Event):
        self.settings = settings_manager
        self.on_toggle = on_toggle
        self.stop_event = stop_event
        self.restart_event = Event()
        self.thread_id = 0
        self.thread: Optional[Thread] = None

    def start(self) -> None:
        self.thread = Thread(target=self._run, daemon=True, name="CrossHudHotkey")
        self.thread.start()

    def update_hotkey(self) -> None:
        self.restart_event.set()
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def join(self, timeout: float) -> None:
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)

    def _run(self) -> None:
        self.thread_id = kernel32.GetCurrentThreadId()
        while not self.stop_event.is_set():
            key_name = self.settings.get("hotkey", "Insert")
            vk = HOTKEY_VK_MAP.get(key_name, HOTKEY_VK_MAP["Insert"])
            if user32.RegisterHotKey(None, self.HOTKEY_ID, MOD_NOREPEAT, vk):
                self.restart_event.clear()
                self._message_loop(vk)
                user32.UnregisterHotKey(None, self.HOTKEY_ID)
            elif user32.RegisterHotKey(None, self.HOTKEY_ID, 0, vk):
                logging.warning("Hotkey repeat suppression unavailable for %s", key_name)
                self.restart_event.clear()
                self._message_loop(vk)
                user32.UnregisterHotKey(None, self.HOTKEY_ID)
            else:
                self.stop_event.wait(1)

    def _message_loop(self, vk: int) -> None:
        msg = wintypes.MSG()
        hotkey_pressed = False
        while not self.stop_event.is_set() and not self.restart_event.is_set():
            while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, PM_REMOVE):
                if msg.message == WM_QUIT:
                    return
                if msg.message == WM_HOTKEY and msg.wParam == self.HOTKEY_ID and self.on_toggle:
                    if not hotkey_pressed:
                        hotkey_pressed = True
                        self.on_toggle()
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            if hotkey_pressed and not (user32.GetAsyncKeyState(vk) & 0x8000):
                hotkey_pressed = False
            self.stop_event.wait(0.01)


class MouseButtonMonitor:
    def __init__(
        self,
        settings_manager,
        on_toggle: Optional[Callable[[], None]],
        on_visibility_command: Callable[[str], None],
        on_pressed_changed: Callable[[bool], None],
        stop_event: Event,
    ):
        self.settings = settings_manager
        self.on_toggle = on_toggle
        self.on_visibility_command = on_visibility_command
        self.on_pressed_changed = on_pressed_changed
        self.stop_event = stop_event
        self.thread_id = 0
        self.thread: Optional[Thread] = None
        self.rmb_pressed = False
        self.hook_handle = None
        self.mouse_hook_proc = LOWLEVELMOUSEPROC(self._low_level_mouse_proc)

    def start(self) -> None:
        self.thread = Thread(target=self._run, daemon=True, name="CrossHudMouseMonitor")
        self.thread.start()

    def join(self, timeout: float) -> None:
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=timeout)

    def wake(self) -> None:
        if self.thread_id:
            user32.PostThreadMessageW(self.thread_id, WM_QUIT, 0, 0)

    def _run(self) -> None:
        self.thread_id = kernel32.GetCurrentThreadId()
        if self._install_mouse_hook():
            self._hook_message_loop()
            return
        self._polling_loop()

    def _hook_message_loop(self) -> None:
        msg = wintypes.MSG()
        try:
            while not self.stop_event.is_set():
                result = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
                if result <= 0:
                    break
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
        except Exception:
            logging.exception("Mouse hook loop error")
        finally:
            self._uninstall_mouse_hook()

    def _polling_loop(self) -> None:
        last_state = False
        while not self.stop_event.is_set():
            try:
                state = user32.GetAsyncKeyState(0x02)
                is_down = bool(state & 0x8000)
                transitioned = bool(state & 0x0001)
                if transitioned and not is_down and not last_state:
                    self._handle_mouse_event(True)
                    self._handle_mouse_event(False)
                if is_down != last_state:
                    self._handle_mouse_event(is_down)
                    last_state = is_down
                self.stop_event.wait(0.005)
            except Exception:
                logging.exception("Mouse polling loop error")
                self.stop_event.wait(1)

    def _install_mouse_hook(self) -> bool:
        try:
            h_instance = kernel32.GetModuleHandleW(None)
            self.hook_handle = user32.SetWindowsHookExW(WH_MOUSE_LL, self.mouse_hook_proc, h_instance, 0)
            if self.hook_handle:
                return True
            logging.warning("Low-level mouse hook unavailable, falling back to polling")
        except Exception:
            logging.exception("Failed to install low-level mouse hook")
        return False

    def _uninstall_mouse_hook(self) -> None:
        if not self.hook_handle:
            return
        try:
            user32.UnhookWindowsHookEx(self.hook_handle)
        except Exception:
            logging.exception("Failed to unhook low-level mouse hook")
        finally:
            self.hook_handle = None

    def _low_level_mouse_proc(self, n_code, w_param, l_param):
        try:
            if n_code >= 0:
                if w_param in (WM_RBUTTONDOWN, WM_RBUTTONDBLCLK):
                    self._handle_mouse_event(True)
                elif w_param == WM_RBUTTONUP:
                    self._handle_mouse_event(False)
        except Exception:
            logging.exception("Low-level mouse hook callback error")
        return user32.CallNextHookEx(self.hook_handle, n_code, w_param, l_param)

    def _handle_mouse_event(self, is_down: bool) -> None:
        mode = self.settings.get("rmb_hide_mode", "disabled")
        enabled = self.settings.get("enabled", False)

        if mode == "hold" and enabled:
            self._set_pressed(is_down)
            self.on_visibility_command("hide" if is_down else "show")
            return

        if mode == "toggle":
            if not is_down and self.rmb_pressed and self.on_toggle:
                self.on_toggle()
            self._set_pressed(is_down)
            return

        if self.rmb_pressed:
            self._set_pressed(False)

    def _set_pressed(self, pressed: bool) -> None:
        self.rmb_pressed = pressed
        self.on_pressed_changed(pressed)


class ForegroundChangeHook:
    def __init__(self, on_foreground_changed: Callable[[], None]):
        self.on_foreground_changed = on_foreground_changed
        self.handle = None
        self._proc = WIN_EVENT_PROC(self._win_event_proc)

    def install(self) -> None:
        try:
            self.handle = user32.SetWinEventHook(
                EVENT_SYSTEM_FOREGROUND,
                EVENT_SYSTEM_FOREGROUND,
                None,
                self._proc,
                0,
                0,
                WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
            )
        except Exception:
            logging.exception("Failed to install foreground hook")

    def uninstall(self) -> None:
        if not self.handle:
            return
        try:
            user32.UnhookWinEvent(self.handle)
        except Exception:
            logging.exception("Failed to unhook foreground hook")
        finally:
            self.handle = None

    def _win_event_proc(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        if event == EVENT_SYSTEM_FOREGROUND:
            self.on_foreground_changed()
