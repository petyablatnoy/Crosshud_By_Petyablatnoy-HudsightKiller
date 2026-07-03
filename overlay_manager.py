import logging
import queue
from threading import Event, Thread, current_thread

from crosshair_renderer import opacity_byte, render_crosshair_bgra
from input_hooks import ForegroundChangeHook, HOTKEY_VK_MAP, HotkeyListener, MouseButtonMonitor
from overlay_window import OverlayWindow
from win32_api import get_cursor_x, pump_thread_messages


class OverlayManager:
    VK_MAP = HOTKEY_VK_MAP

    def __init__(self, settings_manager, on_toggle_callback=None):
        self.settings_manager = settings_manager
        self.on_toggle_callback = on_toggle_callback
        self.thread_stop_event = Event()
        self.render_event = Event()
        self.command_queue = queue.Queue()
        self.rainbow_hue = 0
        self.is_visible = False
        self.rmb_pressed = False
        self.cleanup_in_progress = False

        self.window = OverlayWindow(self._target_overlay_size())
        self.foreground_hook = ForegroundChangeHook(lambda: self.command_queue.put(("reforce_top", None)))
        self.hotkey_listener = HotkeyListener(settings_manager, on_toggle_callback, self.thread_stop_event)
        self.mouse_monitor = MouseButtonMonitor(
            settings_manager,
            on_toggle_callback,
            self._queue_visibility_command,
            self._set_rmb_pressed,
            self.thread_stop_event,
        )
        self.render_thread = None
        self.topmost_thread = None
        self.start_monitoring()

    def start_monitoring(self) -> None:
        self.foreground_hook.install()
        self.mouse_monitor.start()
        self.hotkey_listener.start()
        self.render_thread = Thread(target=self._render_loop, daemon=True, name="CrossHudRender")
        self.topmost_thread = Thread(target=self._keep_on_top_loop, daemon=True, name="CrossHudTopmost")
        self.render_thread.start()
        self.topmost_thread.start()

    def update_hotkey(self) -> None:
        self.hotkey_listener.update_hotkey()

    def request_recreation(self) -> None:
        self.render_event.set()
        self.command_queue.put(("recreate", None))

    def show(self) -> None:
        self.command_queue.put(("show", None))

    def hide(self) -> None:
        self.command_queue.put(("hide", None))

    def refresh(self) -> None:
        self.render_event.set()
        self.command_queue.put(("refresh", None))

    def _target_overlay_size(self) -> int:
        return int(self.settings_manager.get("overlay_size", 512))

    def _queue_visibility_command(self, command: str) -> None:
        self.command_queue.put((command, None))

    def _set_rmb_pressed(self, pressed: bool) -> None:
        self.rmb_pressed = pressed

    def _keep_on_top_loop(self) -> None:
        while not self.thread_stop_event.is_set():
            if self._can_force_topmost():
                self.window.force_topmost()
            self.thread_stop_event.wait(0.1)

    def _can_force_topmost(self) -> bool:
        return self.window.is_created and self.is_visible and not self.rmb_pressed

    def _render_loop(self) -> None:
        try:
            if not self.window.create():
                logging.error("Overlay window was not created")
                return

            if self.settings_manager.get("enabled", True):
                self._show_overlay()

            while not self.thread_stop_event.is_set():
                try:
                    pump_thread_messages()
                    self._drain_commands()
                    self._tick_render()
                except Exception:
                    logging.exception("Render loop error")
                    self.thread_stop_event.wait(1)
        finally:
            self.window.destroy()

    def _drain_commands(self) -> None:
        while True:
            try:
                command, _ = self.command_queue.get_nowait()
            except queue.Empty:
                return

            if command == "show":
                self._show_overlay()
            elif command == "hide":
                self._hide_overlay()
            elif command == "draw":
                self.draw_crosshair()
            elif command == "recreate":
                self._recreate_surface()
            elif command == "reforce_top":
                if self._can_force_topmost():
                    self.window.force_topmost()
            elif command == "refresh":
                if self.settings_manager.get("enabled", False):
                    self.draw_crosshair()
                else:
                    self._hide_overlay()

    def _tick_render(self) -> None:
        is_animating = self.settings_manager.get("rainbow_mode", False) or self.settings_manager.get("dynamic_color", False)
        if is_animating:
            self.rainbow_hue = (self.rainbow_hue + 2) % 360
            if self.is_visible and not self.rmb_pressed:
                self.draw_crosshair()
            self.thread_stop_event.wait(1 / 30)
            return

        if self.render_event.wait(timeout=0.1):
            self.render_event.clear()
            self.draw_crosshair()

    def _recreate_surface(self) -> None:
        self.window.resize_surface(self._target_overlay_size())
        if self.settings_manager.get("enabled", False):
            self._show_overlay()

    def _show_overlay(self) -> None:
        if not self.window.is_created:
            return
        self.window.show()
        self.is_visible = True
        self.draw_crosshair()

    def _hide_overlay(self) -> None:
        self.window.hide()
        self.is_visible = False

    def draw_crosshair(self) -> None:
        if not self.window.is_created or not self.is_visible:
            return
        try:
            dynamic_x = get_cursor_x() if self.settings_manager.get("dynamic_color", False) else None
            alpha = opacity_byte(self.settings_manager)
            data = render_crosshair_bgra(
                self.settings_manager,
                size=self.window.size,
                hue=self.rainbow_hue,
                dynamic_x=dynamic_x,
            )
            if data is None:
                return
            self.window.update_pixels(data)
            self.window.update_layered(
                self.settings_manager.get("screen_width", 1920),
                self.settings_manager.get("screen_height", 1080),
                alpha,
            )
        except Exception:
            logging.exception("Error in draw_crosshair")

    def cleanup(self) -> None:
        if self.cleanup_in_progress:
            return
        self.cleanup_in_progress = True

        self.foreground_hook.uninstall()
        self.thread_stop_event.set()
        self.render_event.set()
        self.hotkey_listener.update_hotkey()
        self.mouse_monitor.wake()
        self.command_queue.put(("hide", None))

        for thread in [self.render_thread, self.topmost_thread]:
            if thread and thread.is_alive() and thread is not current_thread():
                thread.join(timeout=1.5)

        self.hotkey_listener.join(timeout=1.5)
        self.mouse_monitor.join(timeout=1.5)
